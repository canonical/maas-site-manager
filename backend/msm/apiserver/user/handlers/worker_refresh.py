# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
"""
Handler for the /api/v1/worker-refresh endpoint.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from msm.apiserver.db.models import Worker
from msm.apiserver.dependencies import services
from msm.apiserver.exceptions.responses import UnauthorizedErrorResponseModel
from msm.apiserver.service import ServiceCollection
from msm.apiserver.user.auth import authenticated_worker

v1_router = APIRouter(prefix="/v1")


class WorkerRefreshResponse(BaseModel):
    """Response containing the newly issued worker JWT."""

    token: str


@v1_router.post(
    "/worker-refresh",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
    },
)
async def post(
    _worker: Annotated[Worker, Depends(authenticated_worker)],
    services: Annotated[ServiceCollection, Depends(services)],
) -> WorkerRefreshResponse:
    """Rotate the worker JWT and update all active scheduled workflows.

    This endpoint is called by the WorkerJwtRefresh Temporal workflow on a
    schedule. It issues a new worker JWT, replaces the previous one in the
    database, and updates the embedded credentials in every active Temporal
    boot-source and worker-refresh schedule so that subsequent workflow runs
    use the new token.
    """
    new_jwt = await services.workflow_service.refresh_worker_jwt()
    return WorkerRefreshResponse(token=new_jwt)
