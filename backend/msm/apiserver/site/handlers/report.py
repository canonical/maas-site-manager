from typing import Annotated, Self

from fastapi import (
    APIRouter,
    Depends,
    Response,
)
from pydantic import BaseModel, Field, model_validator

from msm.apiserver.db import models
from msm.apiserver.db.models import (
    Site,
    SiteDataUpdate,
    SiteDetailsUpdate,
)
from msm.apiserver.dependencies import services
from msm.apiserver.exceptions.responses import (
    UnauthorizedErrorResponseModel,
    ValidationErrorResponseModel,
)
from msm.apiserver.service import ServiceCollection
from msm.apiserver.site.auth import authenticated_site
from msm.common.enums import TaskStatus
from msm.common.time import now_utc

v1_router = APIRouter(prefix="/v1")


class MachineStatsByStatus(BaseModel):
    """Machine counts by status."""

    allocated: int
    deployed: int
    ready: int
    error: int
    other: int


class DetailsPostRequest(BaseModel):
    """Request to update site details."""

    name: str | None = None
    url: str | None = None
    machines_by_status: MachineStatsByStatus | None = None


@v1_router.post(
    "/details",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def details(
    response: Response,
    services: Annotated[ServiceCollection, Depends(services)],
    site: Annotated[Site, Depends(authenticated_site)],
    post_request: DetailsPostRequest,
) -> None:
    """Update site details."""
    if post_request.name or post_request.url:
        await services.sites.update(
            site.id,
            SiteDetailsUpdate(name=post_request.name, url=post_request.url),
        )
    if post_request.machines_by_status:
        if site_data := post_request.machines_by_status.model_dump():
            await services.sites.update_data(
                site.id,
                SiteDataUpdate(
                    **{
                        f"machines_{key}": value
                        for key, value in site_data.items()
                    }
                ),
            )
    await services.sites.update_last_seen(
        site.id, now_utc(), update_metrics=True
    )
    interval = await services.sites.get_heartbeat_interval()
    response.headers["MSM-Heartbeat-Interval-Seconds"] = str(interval)


class SiteStateStatusPatchRequest(BaseModel):
    status: TaskStatus | None = None
    selections_status: TaskStatus | None = None
    global_config_status: TaskStatus | None = None
    image_sync_status: TaskStatus | None = None
    errors: list[str] | None = Field(
        default=None,
        description="When specified as a non-empty list, append to the known errors.\
When specified as an empty list, clear the errors.\
When not specified, do not alter the errors",
    )

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def check_at_least_one_field_present(self) -> Self:
        """ "Ensure at least one field is provided for update."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be set.")
        return self


@v1_router.patch(
    "/site-status",
    status_code=204,
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def update_status(
    services: Annotated[ServiceCollection, Depends(services)],
    site: Annotated[Site, Depends(authenticated_site)],
    post_request: SiteStateStatusPatchRequest,
) -> None:
    await services.site_state.update(
        site.id,
        models.SiteStateStatusUpdate(
            **post_request.model_dump(exclude_none=True)
        ),
        append_errors=bool(post_request.errors),
    )
