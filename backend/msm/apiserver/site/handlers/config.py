from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
)

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


@v1_router.get(
    "/site-config",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
    },
)
async def get(
    services: Annotated[ServiceCollection, Depends(services)],
    site: Annotated[Site, Depends(authenticated_site)],
) -> dict[str, Any]:
    """Get the full desired configuration for a site."""
    profile = await services.site_profiles.get_by_site_id(site.id)
    if profile and profile.global_config is not None:
        return profile.global_config
    return dict(SiteConfigFactory.DEFAULT_CONFIG)
