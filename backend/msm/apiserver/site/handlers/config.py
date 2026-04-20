from typing import Annotated, Any, Self

from fastapi import (
    APIRouter,
    Depends,
)
from pydantic import BaseModel, Field, model_validator

from msm.apiserver.db.models import Site, SiteStateStatusUpdate, SiteUpdate
from msm.apiserver.dependencies import services
from msm.apiserver.exceptions.catalog import (
    BaseExceptionDetail,
    NotFoundException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.exceptions.responses import (
    NotFoundErrorResponseModel,
    UnauthorizedErrorResponseModel,
    ValidationErrorResponseModel,
)
from msm.apiserver.service import ServiceCollection
from msm.apiserver.site.auth import authenticated_site
from msm.common.config_hash import merged_config_for_response
from msm.common.enums import TaskStatus

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
    state = merged_config_for_response(profile, site.trigger_image_sync)
    return SiteConfigResponse(**state)


class SiteStateStatusPatchRequest(BaseModel):
    status: TaskStatus | None = None
    selections_status: TaskStatus | None = None
    global_config_status: TaskStatus | None = None
    image_sync_status: TaskStatus | None = None
    clear_errors: bool = False
    errors: list[str] | None = Field(
        default=None,
        description="Appends to the known errors.",
    )

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def check_at_least_one_field_present(self) -> Self:
        """Ensure at least one field is provided for update."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be set.")
        return self


@v1_router.patch(
    "/site-status",
    status_code=204,
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def update_status(
    services: Annotated[ServiceCollection, Depends(services)],
    site: Annotated[Site, Depends(authenticated_site)],
    patch_request: SiteStateStatusPatchRequest,
) -> None:
    """Update a site's configuration task status."""
    status = await services.site_state.get_by_site_id(site.id)
    if status is None:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Site state status does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[
                        f"Site state status for site ID {site.id} does not exist"
                    ],
                    field="id",
                    location="token",
                )
            ],
        )
    await services.site_state.update_by_site_id(
        site.id,
        SiteStateStatusUpdate(
            **patch_request.model_dump(
                exclude_none=True, exclude={"clear_errors"}
            )
        ),
        append_errors=not patch_request.clear_errors,
    )
    if patch_request.image_sync_status in [
        TaskStatus.STARTED,
        TaskStatus.COMPLETE,
    ]:
        await services.sites.update(
            site.id, SiteUpdate(trigger_image_sync=False)
        )
