# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
"""
Worker JWT refresh activity.
"""

from dataclasses import dataclass

from temporalio import activity
from temporalio.exceptions import ApplicationError

from .base import BaseActivity, compose_url

WORKER_JWT_REFRESH_ACTIVITY = "worker-jwt-refresh"


@dataclass
class WorkerJwtRefreshParams:
    """Parameters for the worker JWT refresh activity.

    Args:
        msm_base_url: Base URL of the MSM API server.
        msm_jwt: Current JWT token used to authenticate the refresh request.
    """

    msm_base_url: str
    msm_jwt: str


class WorkerRefreshActivities(BaseActivity):
    """Temporal activities for refreshing worker JWT credentials."""

    @activity.defn(name=WORKER_JWT_REFRESH_ACTIVITY)
    async def worker_jwt_refresh(self, params: WorkerJwtRefreshParams) -> None:
        """Request a refreshed worker JWT from the MSM API.

        Calls the /api/v1/worker-refresh endpoint authenticated with the current
        worker JWT.

        Args:
            params: Parameters including the MSM base URL and current JWT.

        Raises:
            ApplicationError: If the API request fails or returns a non-200 status.
        """
        url = compose_url(params.msm_base_url, "api/v1/worker-refresh")
        headers = self._get_header(params.msm_jwt)
        response = await self.client.post(url, headers=headers)
        if response.status_code == 401:
            raise ApplicationError(
                f"The token used to refresh the worker token is no longer valid",
                non_retryable=True,
            )
        elif response.status_code != 200:
            raise ApplicationError(
                f"Unexpected response from MSM: {response.status_code} {response.text}"
            )
