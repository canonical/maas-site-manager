# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
"""
Workflow for refreshing worker JWT credentials used by scheduled workflows.
"""

from datetime import timedelta

from temporalio import workflow

from msm.common.workflows.sync import (
    WORKER_JWT_REFRESH_WF_NAME,
    WorkerJwtRefreshParams,
)
import msm.temporal.activities as act

WORKER_JWT_REFRESH_TIMEOUT = timedelta(minutes=5)


@workflow.defn(name=WORKER_JWT_REFRESH_WF_NAME, sandboxed=False)
class WorkerJwtRefreshWorkflow:
    """Workflow that refreshes worker JWT credentials for scheduled workflows.

    This workflow is intended to run on a schedule and calls the MSM API
    worker-refresh endpoint to rotate the worker JWT. The endpoint is
    responsible for issuing a new token and updating all active scheduled
    workflows so that subsequent runs use the refreshed credentials.
    """

    @workflow.run
    async def run(self, params: WorkerJwtRefreshParams) -> None:
        """Execute the worker JWT refresh.

        Args:
            params: Parameters including the MSM API URL and current worker JWT.
        """
        await workflow.execute_activity(
            act.WORKER_JWT_REFRESH_ACTIVITY,
            act.WorkerJwtRefreshParams(
                msm_base_url=params.msm_url,
                msm_jwt=params.msm_jwt,
            ),
            start_to_close_timeout=WORKER_JWT_REFRESH_TIMEOUT,
        )
