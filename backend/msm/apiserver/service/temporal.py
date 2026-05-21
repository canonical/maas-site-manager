from datetime import timedelta
from functools import cached_property
from typing import Any

from sqlalchemy.ext.asyncio import AsyncConnection
from temporalio.client import (
    Client as TemporalClient,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleHandle,
    ScheduleIntervalSpec,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleSpec,
    ScheduleUpdate,
    ScheduleUpdateInput,
)
from temporalio.common import RetryPolicy
from temporalio.service import RPCError, RPCStatusCode
from temporallib.client import Options  # type: ignore
from temporallib.encryption import EncryptionOptions  # type: ignore

from msm.apiserver.service.base import Service
from msm.apiserver.service.config import ConfigService
from msm.apiserver.service.s3 import S3Service
from msm.apiserver.service.settings import SettingsService
from msm.apiserver.service.token import TokenService
from msm.common.jwt import TokenAudience, TokenPurpose
from msm.common.settings import Settings
from msm.common.time import now_utc
import msm.common.workflows.sync as msm_wf

WORKER_TOKEN_DURATION = timedelta(days=2)
BOOT_SELECTION_REFRESH_INTVAL = 5
SYNC_SOURCE_SCHED_ID_PREFIX = "sched-boot-source-"
REFRESH_UPSTREAM_SCHED_ID_PREFIX = "sched-boot-select-"
WORKER_JWT_REFRESH_SCHED_ID = "sched-worker-refresh"
WORKER_JWT_REFRESH_WF_ID = "wf-worker-jwt-refresh"
WORKER_JWT_REFRESH_INTERVAL = timedelta(days=1)


def _sync_source_sched_id(source_id: int) -> str:
    return f"{SYNC_SOURCE_SCHED_ID_PREFIX}{source_id}"


def _bs_id_from_sync_sched_id(sched_id: str) -> int:
    return int(sched_id.removeprefix(SYNC_SOURCE_SCHED_ID_PREFIX))


def _refresh_upstream_sched_id(source_id: int) -> str:
    return f"{REFRESH_UPSTREAM_SCHED_ID_PREFIX}{source_id}"


def _bs_id_from_refresh_sched_id(sched_id: str) -> int:
    return int(sched_id.removeprefix(REFRESH_UPSTREAM_SCHED_ID_PREFIX))


class S3ParametersError(Exception):
    """Raised when S3 configuration is incomplete."""


class TemporalService(Service):
    """Service for managing Temporal workflows and schedules.

    This service provides functionality to interact with Temporal workflows,
    including creating, managing, and scheduling workflows for upstream source
    synchronization and refresh operations.
    """

    def __init__(
        self,
        connection: AsyncConnection,
        config: ConfigService,
        tokens: TokenService,
        settings: SettingsService,
        temporal_client: TemporalClient,
    ):
        super().__init__(connection)
        self.tokens: TokenService = tokens
        self.config: ConfigService = config
        self.settings: SettingsService = settings
        self.application_settings: Settings = Settings()
        self.temporal_client: TemporalClient = temporal_client

    @cached_property
    def options(self) -> Options:
        return Options(
            host=self.application_settings.temporal_server_address,
            queue=self.application_settings.temporal_task_queue,
            namespace=self.application_settings.temporal_namespace,
            tls_root_cas=self.application_settings.temporal_tls_root_cas,
            encryption=EncryptionOptions(),
        )

    async def get_worker_credentials(self) -> tuple[str, str]:
        """Get service URL and worker token for authentication.

        Returns:
            tuple[str, str]: A tuple containing the service URL and worker token value.
        """
        service_url = await self.settings.get_service_url()
        _, tokens = await self.tokens.get(
            audience=[TokenAudience.WORKER], purpose=[TokenPurpose.ACCESS]
        )
        # it's possible for multiple tokens to exist,
        # get the one with the longest expiration
        longest_expiration_token = max(
            tokens, key=lambda token: token.expired, default=None
        )
        if longest_expiration_token is None:
            return service_url, ""
        return service_url, longest_expiration_token.value

    async def schedule_create(
        self,
        scheduler_id: str,
        workflow: str,
        workflow_id: str,
        param: Any,
        interval: int,
    ) -> str:
        """Create a scheduled workflow.

        Args:
            scheduler_id: Unique identifier for the scheduler
            workflow: Name of the workflow to schedule
            workflow_id: Unique identifier for the workflow instance
            param: Parameters to pass to the workflow
            interval: Interval in minutes between workflow executions

        Returns:
            str: The ID of the created schedule handle
        """

        hdl = await self.temporal_client.create_schedule(
            scheduler_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    workflow,
                    param,
                    id=workflow_id,
                    task_queue=self.options.queue or "not-set",
                    retry_policy=RetryPolicy(  # don't spin too fast
                        initial_interval=timedelta(minutes=1),
                        maximum_interval=timedelta(minutes=1),
                    ),
                    execution_timeout=timedelta(minutes=2 * interval),
                ),
                spec=ScheduleSpec(
                    intervals=[
                        ScheduleIntervalSpec(every=timedelta(minutes=interval))
                    ]
                ),
                policy=SchedulePolicy(
                    overlap=ScheduleOverlapPolicy.BUFFER_ONE,
                ),
            ),
        )
        return hdl.id

    async def schedule_cancel(self, scheduler_id: str) -> None:
        """Cancel a scheduled workflow.

        Args:
            scheduler_id: Unique identifier for the scheduler to cancel
        """
        hdl = self.temporal_client.get_schedule_handle(scheduler_id)
        await hdl.delete()

    async def schedule_pause(
        self, scheduler_id: str, note: str | None = None
    ) -> None:
        """Pause a scheduled workflow.

        Args:
            scheduler_id: Unique identifier for the scheduler to pause
            note: Optional note explaining the reason for pausing
        """
        hdl = self.temporal_client.get_schedule_handle(scheduler_id)
        await hdl.pause(note=note)

    async def schedule_resume(
        self, scheduler_id: str, note: str | None = None
    ) -> None:
        """Resume a paused scheduled workflow.

        Args:
            scheduler_id: Unique identifier for the scheduler to resume
            note: Optional note explaining the reason for resuming
        """
        hdl = self.temporal_client.get_schedule_handle(scheduler_id)
        await hdl.unpause(note=note)

    async def schedule_fire(
        self, scheduler_id: str, force: bool = False
    ) -> None:
        """Fire a scheduled workflow immediately.

        Args:
            scheduler_id: Unique identifier for the scheduler to fire
            force: If True, cancel other running instances; if False, buffer the execution
        """
        hdl = self.temporal_client.get_schedule_handle(scheduler_id)
        await hdl.trigger(
            overlap=ScheduleOverlapPolicy.CANCEL_OTHER if force else None
        )

    def get_schedule_handle(self, schedule_id: str) -> ScheduleHandle:
        return self.temporal_client.get_schedule_handle(schedule_id)

    async def rotate_worker_jwt(self) -> tuple[str, str]:
        """Renew the worker's JWT.

        Deletes all expired JWTs and issues a new one. Returns the
        service URL and the encoded value of the new token so callers can
        update any embedded references (e.g., Temporal schedule arguments).

        Returns:
            tuple[str, str]: (service_url, new_jwt)
        """
        config = await self.config.get()
        service_url = await self.settings.get_service_url()

        new_tokens = list(
            await self.tokens.create(
                issuer=config.service_identifier,
                secret_key=config.token_secret_key,
                service_url=service_url,
                audience=TokenAudience.WORKER,
                purpose=TokenPurpose.ACCESS,
                duration=WORKER_TOKEN_DURATION,
            )
        )
        new_jwt = new_tokens[0].value

        await self.tokens.delete_expired(
            audience=TokenAudience.WORKER, purpose=TokenPurpose.ACCESS
        )

        return service_url, new_jwt

    async def ensure(self) -> None:
        """Prepare Site Manager to schedule Temporal workflows.

        Refreshes worker tokens. These tokens are already refreshed by a scheduled
        workflow, but this is a fallback in case the refresh workflow's token is invalid.
        """
        count, tokens = await self.tokens.get(
            audience=[TokenAudience.WORKER], purpose=[TokenPurpose.ACCESS]
        )
        deleted = await self.tokens.delete_expired(
            audience=TokenAudience.WORKER, purpose=TokenPurpose.ACCESS
        )
        expiring_soon = any(
            token.expired
            < now_utc() + WORKER_JWT_REFRESH_INTERVAL + timedelta(minutes=5)
            for token in tokens
        )
        if deleted or count == 0 or expiring_soon:
            config = await self.config.get()
            service_url = await self.settings.get_service_url()
            _ = await self.tokens.create(
                issuer=config.service_identifier,
                secret_key=config.token_secret_key,
                service_url=service_url,
                audience=TokenAudience.WORKER,
                purpose=TokenPurpose.ACCESS,
                duration=WORKER_TOKEN_DURATION,
            )

        msm_url, msm_jwt = await self.get_worker_credentials()
        try:
            hdl = self.get_schedule_handle(WORKER_JWT_REFRESH_SCHED_ID)

            def update_schedule(
                inp: ScheduleUpdateInput,
            ) -> ScheduleUpdate:
                if isinstance(
                    inp.description.schedule.action,
                    ScheduleActionStartWorkflow,
                ):
                    inp.description.schedule.action.args = [
                        msm_wf.WorkerJwtRefreshParams(
                            msm_url=msm_url,
                            msm_jwt=msm_jwt,
                        )
                    ]
                return ScheduleUpdate(schedule=inp.description.schedule)

            await hdl.update(update_schedule)
        except RPCError as exc:
            if exc.status != RPCStatusCode.NOT_FOUND:
                raise
            await self.temporal_client.create_schedule(
                WORKER_JWT_REFRESH_SCHED_ID,
                Schedule(
                    action=ScheduleActionStartWorkflow(
                        msm_wf.WORKER_JWT_REFRESH_WF_NAME,
                        msm_wf.WorkerJwtRefreshParams(
                            msm_url=msm_url,
                            msm_jwt=msm_jwt,
                        ),
                        id=WORKER_JWT_REFRESH_WF_ID,
                        task_queue=self.options.queue or "not-set",
                        retry_policy=RetryPolicy(
                            initial_interval=timedelta(minutes=1),
                            maximum_interval=timedelta(minutes=1),
                        ),
                        execution_timeout=timedelta(minutes=5),
                    ),
                    spec=ScheduleSpec(
                        intervals=[
                            ScheduleIntervalSpec(
                                every=WORKER_JWT_REFRESH_INTERVAL
                            )
                        ]
                    ),
                    policy=SchedulePolicy(
                        overlap=ScheduleOverlapPolicy.BUFFER_ONE,
                    ),
                ),
            )


class BootSourceWorkflowService(Service):
    def __init__(
        self,
        connection: AsyncConnection,
        s3: S3Service,
        temporal: TemporalService,
    ):
        super().__init__(connection)
        self.s3: S3Service = s3
        self.temporal: TemporalService = temporal

    @cached_property
    def s3_params(self) -> msm_wf.S3Params:
        """S3 parameters for workflows."""
        if not all(
            [
                self.s3.s3_endpoint,
                self.s3.s3_bucket,
                self.s3.s3_access_key,
                self.s3.s3_secret_key,
            ]
        ):
            raise S3ParametersError()

        return msm_wf.S3Params(
            endpoint=self.s3.s3_endpoint,
            bucket=self.s3.s3_bucket,
            access_key=self.s3.s3_access_key,
            secret_key=self.s3.s3_secret_key,
            path=self.s3.s3_path,
        )

    async def refresh_worker_jwt(self) -> str:
        """Rotate the worker JWT and update all active Temporal schedules.

        Creates a fresh worker JWT, replaces the old one in the database, and
        updates every boot-source and worker-refresh schedule so subsequent
        workflow runs use the new token.

        Returns:
            str: The encoded value of the newly issued worker JWT.
        """
        msm_url, new_jwt = await self.temporal.rotate_worker_jwt()
        schedules = await self.temporal.temporal_client.list_schedules()
        async for sched_desc in schedules:
            sched_id: str = sched_desc.id
            hdl = self.temporal.temporal_client.get_schedule_handle(sched_id)

            if sched_id.startswith(SYNC_SOURCE_SCHED_ID_PREFIX):
                boot_source_id = _bs_id_from_sync_sched_id(sched_id)
                s3_params = self.s3_params

                def update_schedule(
                    inp: ScheduleUpdateInput,
                ) -> ScheduleUpdate:
                    if isinstance(
                        inp.description.schedule.action,
                        ScheduleActionStartWorkflow,
                    ):
                        inp.description.schedule.action.args = [
                            msm_wf.SyncUpstreamSourceParams(
                                msm_url=msm_url,
                                msm_jwt=new_jwt,
                                boot_source_id=boot_source_id,
                                s3_params=s3_params,
                            )
                        ]
                    return ScheduleUpdate(schedule=inp.description.schedule)

                await hdl.update(update_schedule)

            elif sched_id.startswith(REFRESH_UPSTREAM_SCHED_ID_PREFIX):
                boot_source_id = _bs_id_from_refresh_sched_id(sched_id)

                def update_schedule(
                    inp: ScheduleUpdateInput,
                ) -> ScheduleUpdate:
                    if isinstance(
                        inp.description.schedule.action,
                        ScheduleActionStartWorkflow,
                    ):
                        inp.description.schedule.action.args = [
                            msm_wf.RefreshUpstreamSourceParams(
                                msm_url=msm_url,
                                msm_jwt=new_jwt,
                                boot_source_id=boot_source_id,
                            )
                        ]
                    return ScheduleUpdate(schedule=inp.description.schedule)

                await hdl.update(update_schedule)

            elif sched_id == WORKER_JWT_REFRESH_SCHED_ID:

                def update_schedule(
                    inp: ScheduleUpdateInput,
                ) -> ScheduleUpdate:
                    if isinstance(
                        inp.description.schedule.action,
                        ScheduleActionStartWorkflow,
                    ):
                        inp.description.schedule.action.args = [
                            msm_wf.WorkerJwtRefreshParams(
                                msm_url=msm_url,
                                msm_jwt=new_jwt,
                            )
                        ]
                    return ScheduleUpdate(schedule=inp.description.schedule)

                await hdl.update(update_schedule)

        return new_jwt

    async def enable_sync(
        self,
        boot_source_id: int,
        sync_interval: int,
    ) -> None:
        """
        Enable upstream synchronization for a boot source.

        This method sets up scheduled workflows for synchronizing boot source selections
        and images from upstream sources at specified intervals.

        Args:
            boot_source_id: The ID of the boot source to enable sync for.
            sync_interval: The interval in seconds between synchronization runs.
            msm_url: The API URL for workers. If empty, will be retrieved automatically.
            msm_jwt: The API JWT credentials for workers. If empty, will be retrieved automatically.
        """
        msm_url, msm_jwt = await self.temporal.get_worker_credentials()
        try:
            hdls = [
                self.temporal.get_schedule_handle(
                    _refresh_upstream_sched_id(boot_source_id)
                ),
                self.temporal.get_schedule_handle(
                    _sync_source_sched_id(boot_source_id)
                ),
            ]
            s3_params = self.s3_params

            def update_schedule(input: ScheduleUpdateInput) -> ScheduleUpdate:
                if isinstance(
                    input.description.schedule.action,
                    ScheduleActionStartWorkflow,
                ):
                    if (
                        input.description.schedule.action.workflow
                        == msm_wf.SYNC_UPSTREAM_SOURCE_WF_NAME
                    ):
                        input.description.schedule.action.args = [
                            msm_wf.SyncUpstreamSourceParams(
                                msm_url=msm_url,
                                msm_jwt=msm_jwt,
                                boot_source_id=boot_source_id,
                                s3_params=s3_params,
                            )
                        ]
                        input.description.schedule.spec = ScheduleSpec(
                            intervals=[
                                ScheduleIntervalSpec(
                                    every=timedelta(minutes=sync_interval)
                                )
                            ]
                        )
                    elif (
                        input.description.schedule.action.workflow
                        == msm_wf.REFRESH_UPSTREAM_SOURCE_WF_NAME
                    ):
                        input.description.schedule.action.args = [
                            msm_wf.RefreshUpstreamSourceParams(
                                msm_url=msm_url,
                                msm_jwt=msm_jwt,
                                boot_source_id=boot_source_id,
                            )
                        ]
                        input.description.schedule.spec = ScheduleSpec(
                            intervals=[
                                ScheduleIntervalSpec(
                                    every=timedelta(
                                        minutes=max(
                                            sync_interval // 2,
                                            BOOT_SELECTION_REFRESH_INTVAL,
                                        ),
                                    )
                                )
                            ]
                        )
                return ScheduleUpdate(schedule=input.description.schedule)

            for hdl in hdls:
                await hdl.update(update_schedule)
        except RPCError:
            # sync selections
            _ = await self.temporal.schedule_create(
                scheduler_id=_refresh_upstream_sched_id(boot_source_id),
                workflow=msm_wf.REFRESH_UPSTREAM_SOURCE_WF_NAME,
                workflow_id=f"wf-refresh-bootsel-{boot_source_id}",
                param=msm_wf.RefreshUpstreamSourceParams(
                    msm_url=msm_url,
                    msm_jwt=msm_jwt,
                    boot_source_id=boot_source_id,
                ),
                interval=max(
                    sync_interval // 2, BOOT_SELECTION_REFRESH_INTVAL
                ),
            )

            # sync images
            _ = await self.temporal.schedule_create(
                scheduler_id=_sync_source_sched_id(boot_source_id),
                workflow=msm_wf.SYNC_UPSTREAM_SOURCE_WF_NAME,
                workflow_id=f"wf-sync-upstream-{boot_source_id}",
                param=msm_wf.SyncUpstreamSourceParams(
                    msm_url=msm_url,
                    msm_jwt=msm_jwt,
                    boot_source_id=boot_source_id,
                    s3_params=self.s3_params,
                ),
                interval=sync_interval,
            )

    async def disable_sync(self, boot_source_id: int) -> None:
        """Disable upstream synchronization for a boot source."""
        await self.temporal.schedule_cancel(
            _refresh_upstream_sched_id(boot_source_id)
        )
        await self.temporal.schedule_cancel(
            _sync_source_sched_id(boot_source_id)
        )

    async def trigger_sync(self, boot_source_id: int) -> None:
        """Trigger synchronization for a boot source."""
        await self.temporal.schedule_fire(
            _sync_source_sched_id(boot_source_id)
        )
        await self.temporal.schedule_fire(
            _refresh_upstream_sched_id(boot_source_id)
        )
