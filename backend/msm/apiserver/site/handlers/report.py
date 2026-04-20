from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Response,
)
from pydantic import BaseModel

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
from msm.common.config_hash import desired_config, hash_desired_config
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

    version: str
    name: str | None = None
    url: str | None = None
    machines_by_status: MachineStatsByStatus | None = None
    known_config_options: list[str] | None = None

    def requires_update(self, current_version: str | None) -> bool:
        return (
            self.name is not None
            or self.url is not None
            or (self.version != current_version)
            or self.known_config_options is not None
        )


class DetailsPostResponse(BaseModel):
    """Response model for POST request to /details"""

    config_options_requested: bool = False
    config_hash: str = ""


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
) -> DetailsPostResponse:
    """Update site details."""
    if post_request.requires_update(site.version):
        await services.sites.update(
            site.id,
            SiteDetailsUpdate(
                name=post_request.name,
                url=post_request.url,
                version=post_request.version,
                known_config_options=post_request.known_config_options,
            ),
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

    # Reload the site row so trigger_image_sync reflects any concurrent PATCH.
    fresh_site = await services.sites.get_by_id(site.id)
    profile = await services.site_profiles.get_stored_by_site_id(site.id)
    trigger_image_sync = (
        fresh_site.trigger_image_sync
        if fresh_site
        else site.trigger_image_sync
    )
    state = desired_config(profile, trigger_image_sync)
    config_hash = hash_desired_config(state) if state is not None else ""

    return DetailsPostResponse(
        config_options_requested=site.version != post_request.version,
        config_hash=config_hash,
    )
