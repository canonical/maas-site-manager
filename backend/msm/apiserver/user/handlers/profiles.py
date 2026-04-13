from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from msm.apiserver.db import models
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
from msm.apiserver.schema import (
    PaginatedResults,
    PaginationParams,
    SortParam,
    SortParamParser,
)
from msm.apiserver.service import ServiceCollection
from msm.apiserver.user.auth import authenticated_user

v1_router = APIRouter(prefix="/v1")

profile_sort_parameters = SortParamParser(
    fields=[
        "name",
        "id",
    ]
)


class ProfilesGetResponse(PaginatedResults[models.SiteProfile]):
    """Response with paginated site profiles."""


@v1_router.get(
    "/profiles",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    pagination_params: Annotated[PaginationParams, Depends()],
    sort_params: Annotated[list[SortParam], Depends(profile_sort_parameters)],
) -> ProfilesGetResponse:
    """Return all site profiles."""
    total, results = await services.site_profiles.get(
        sort_params=sort_params,
        offset=pagination_params.offset,
        limit=pagination_params.size,
    )
    return ProfilesGetResponse(
        total=total,
        page=pagination_params.page,
        size=pagination_params.size,
        items=list(results),
    )


@v1_router.get(
    "/profiles/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_id(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: int,
) -> models.SiteProfile:
    """Return a specific site profile."""
    if profile := await services.site_profiles.get_by_id(id):
        return profile
    raise NotFoundException(
        code=ExceptionCode.MISSING_RESOURCE,
        message="Site profile does not exist.",
        details=[
            BaseExceptionDetail(
                reason=ExceptionCode.MISSING_RESOURCE,
                messages=[f"Site profile ID {id} does not exist"],
                field="id",
                location="path",
            )
        ],
    )
