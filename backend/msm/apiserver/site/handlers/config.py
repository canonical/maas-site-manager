from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
)
from pydantic import BaseModel

from msm.apiserver.db.models import Site
from msm.apiserver.dependencies import services
from msm.apiserver.exceptions.catalog import (
    BaseExceptionDetail,
    NotFoundException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.exceptions.responses import (
    NotFoundErrorResponseModel,
    UnauthorizedErrorResponseModel,
)
from msm.apiserver.service import ServiceCollection
from msm.apiserver.site.auth import authenticated_site

v1_router = APIRouter(prefix="/v1")


class SiteConfigResponse(BaseModel):
    """Full configuration for a site."""

    global_config: dict[str, Any]
    selections: list[str]
    trigger_image_sync: bool


@v1_router.get(
    "/site-config",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
    },
)
async def get(
    services: Annotated[ServiceCollection, Depends(services)],
    site: Annotated[Site, Depends(authenticated_site)],
) -> SiteConfigResponse:
    """Get the full desired configuration for a site."""
    profile = await services.site_profiles.get_by_site_id(site.id)
    if profile is None:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Site profile does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"Profile for Site ID {site.id} does not exist"],
                    field="id",
                    location="path",
                )
            ],
        )
    return SiteConfigResponse(
        global_config=profile.global_config,
        selections=profile.selections,
        trigger_image_sync=site.trigger_image_sync,
    )
