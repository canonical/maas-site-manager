from datetime import timedelta
import uuid

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from msm.common.workflows.sync import WorkerJwtRefreshParams
from msm.temporal.activities.worker_refresh import (
    WORKER_JWT_REFRESH_ACTIVITY,
    WorkerJwtRefreshParams as ActivityParams,
)
from msm.temporal.workflows.worker_refresh import WorkerJwtRefreshWorkflow

TEST_WF_TIMEOUT = timedelta(seconds=30)


class TestWorkerJwtRefreshWorkflow:
    @pytest.mark.asyncio
    async def test_calls_refresh_activity_with_correct_params(self) -> None:
        """Test that the workflow calls the refresh activity with the correct parameters."""
        called: list[ActivityParams] = []

        @activity.defn(name=WORKER_JWT_REFRESH_ACTIVITY)
        async def worker_jwt_refresh_activity(params: ActivityParams) -> None:
            called.append(params)

        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="msm-queue",
                workflows=[WorkerJwtRefreshWorkflow],
                activities=[worker_jwt_refresh_activity],
            ) as worker:
                await env.client.execute_workflow(
                    WorkerJwtRefreshWorkflow.run,
                    WorkerJwtRefreshParams(
                        msm_url="http://msm.example.com",
                        msm_jwt="worker-jwt-token",
                    ),
                    id=f"workflow-{uuid.uuid4()}",
                    task_queue=worker.task_queue,
                    run_timeout=TEST_WF_TIMEOUT,
                )

        assert len(called) == 1
        assert called[0].msm_base_url == "http://msm.example.com"
        assert called[0].msm_jwt == "worker-jwt-token"
