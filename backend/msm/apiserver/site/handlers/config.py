from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
)
from pydantic import BaseModel

from msm.apiserver.db.models import (
    Site,
    SiteConfigFactory,
)
from msm.apiserver.dependencies import services
from msm.apiserver.exceptions.responses import (
    UnauthorizedErrorResponseModel,
)
from msm.apiserver.service import ServiceCollection
from msm.apiserver.site.auth import authenticated_site

v1_router = APIRouter(prefix="/v1")


class SiteConfigResponse(BaseModel):
    """Full desired configuration for a site."""

    global_config: dict[str, Any]
    selections: list[str]
    trigger_image_sync: bool


@v1_router.get(
    "/site-config",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
    },
)
async def get(
    services: Annotated[ServiceCollection, Depends(services)],
    site: Annotated[Site, Depends(authenticated_site)],
) -> SiteConfigResponse:
    """Get the full desired configuration for a site."""
    profile = await services.site_profiles.get_by_site_id(site.id)
    if profile:
        return SiteConfigResponse(
            global_config=profile.global_config,
            selections=profile.selections,
            trigger_image_sync=site.trigger_image_sync,
        )
    return SiteConfigResponse(
        global_config=dict(SiteConfigFactory.DEFAULT_CONFIG),
        selections=[],
        trigger_image_sync=site.trigger_image_sync,
    )
