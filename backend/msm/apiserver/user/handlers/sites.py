from collections.abc import Iterable
from typing import (
    Annotated,
    Self,
    cast,
)

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from msm.apiserver.db import models
from msm.apiserver.dependencies import services
from msm.apiserver.exceptions.catalog import (
    BadRequestException,
    BaseExceptionDetail,
    NotFoundException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.exceptions.responses import (
    BadRequestErrorResponseModel,
    NotFoundErrorResponseModel,
    UnauthorizedErrorResponseModel,
    ValidationErrorResponseModel,
)
from msm.apiserver.schema import (
    PaginatedResults,
    PaginationParams,
    SortParam,
    SortParamParser,
    TimeZone,
)
from msm.apiserver.service import (
    InvalidPendingSites,
    ServiceCollection,
)
from msm.apiserver.user.auth import authenticated_user
from msm.apiserver.user.forms import (
    SiteFilterParams,
    site_filter_parameters,
)

v1_router = APIRouter(prefix="/v1")

site_sort_parameters = SortParamParser(
    fields=[
        "name",
        "name_unique",
        "country",
        "city",
        "state",
        "address",
        "postal_code",
        "timezone",
        "connection_status",
    ]
)


class PendingSitesGetResponse(PaginatedResults[models.PendingSite]):
    pass


@v1_router.get(
    "/sites/pending",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_pending(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    pagination_params: Annotated[PaginationParams, Depends()],
) -> PendingSitesGetResponse:
    """Return pending sites."""
    total, results = await services.sites.get_pending(
        offset=pagination_params.offset,
        limit=pagination_params.size,
    )
    return PendingSitesGetResponse(
        total=total,
        page=pagination_params.page,
        size=pagination_params.size,
        items=list(results),
    )


class PendingSitesPostRequest(BaseModel):
    """Request to accept/reject sites."""

    ids: list[int]
    accept: bool


@v1_router.post(
    "/sites/pending",
    status_code=204,
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
        400: {"model": BadRequestErrorResponseModel},
    },
)
async def post_pending(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    action: PendingSitesPostRequest,
) -> None:
    """Accept or reject pending sites."""
    try:
        await services.sites.accept_reject_pending(
            action.ids,
            action.accept,
        )
    except InvalidPendingSites as error:
        raise BadRequestException(
            code=ExceptionCode.INVALID_PENDING_SITES,
            message=f"Unknown pending sites, ids: {error.ids}",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.INVALID_PENDING_SITES,
                    messages=[
                        f"Sites {error.ids} either do not exist or are not pending"
                    ],
                    field="ids",
                    location="body",
                )
            ],
        )

    return None


class SitesGetResponse(PaginatedResults[models.Site]):
    """Response with paginated accepted sites."""


@v1_router.get(
    "/sites",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    pagination_params: Annotated[PaginationParams, Depends()],
    filter_params: Annotated[
        SiteFilterParams, Depends(site_filter_parameters)
    ],
    sort_params: Annotated[list[SortParam], Depends(site_sort_parameters)],
    coordinates: bool
    | None = Query(  # don't add to SiteFilterParams, since it's also used for /get/coordinates
        default=None, title="Filter for site with coordinates"
    ),
) -> SitesGetResponse:
    """Return accepted sites."""
    total, results = await services.sites.get(
        sort_params=sort_params,
        offset=pagination_params.offset,
        limit=pagination_params.size,
        **filter_params._asdict(),
        coordinates=coordinates,
    )
    return SitesGetResponse(
        total=total,
        page=pagination_params.page,
        size=pagination_params.size,
        items=list(results),
    )


@v1_router.get(
    "/sites/coordinates",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_coordinates(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    filter_params: Annotated[
        SiteFilterParams, Depends(site_filter_parameters)
    ],
) -> Iterable[models.SiteCoordinates]:
    """Return coordinates for all accepted sites."""
    return await services.sites.get_coordinates(**filter_params._asdict())


@v1_router.get(
    "/sites/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_id(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: int,
) -> models.Site:
    """Return a specific site."""
    if site := await services.sites.get_by_id(id):
        return site
    raise NotFoundException(
        code=ExceptionCode.MISSING_RESOURCE,
        message="Site does not exist.",
        details=[
            BaseExceptionDetail(
                reason=ExceptionCode.MISSING_RESOURCE,
                messages=[f"Site ID {id} does not exist"],
                field="id",
                location="path",
            )
        ],
    )


class SiteUpdateRequest(BaseModel):
    """Update a site."""

    city: str | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)
    coordinates: models.Coordinates | None = None
    note: str | None = None
    state: str | None = None
    address: str | None = None
    postal_code: str | None = None
    # XXX: mypy can't grok that this is an str/enum with lots of members
    timezone: TimeZone | None = None  # type: ignore[valid-type]
    site_profile_id: int | None = None

    @model_validator(mode="after")
    def check_at_least_one_field_present(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be set.")
        return self


@v1_router.patch(
    "/sites/{id}",
    responses={
        400: {"model": BadRequestErrorResponseModel},
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def patch(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: int,
    patch_request: SiteUpdateRequest,
) -> models.Site:
    """Modify a site."""
    site = await services.sites.get_by_id(id)
    if site is None:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Site does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"Site ID {id} does not exist"],
                    field="id",
                    location="path",
                )
            ],
        )
    if patch_request.site_profile_id:
        profile = await services.site_profiles.get_by_id(
            patch_request.site_profile_id
        )
        if profile is None:
            raise NotFoundException(
                message="Site profile does not exist",
                code=ExceptionCode.MISSING_RESOURCE,
                details=[
                    BaseExceptionDetail(
                        reason=ExceptionCode.MISSING_RESOURCE,
                        messages=[
                            f"Site profile with ID {patch_request.site_profile_id} does not exist"
                        ],
                        field="site_profile_id",
                        location="body",
                    )
                ],
            )
        profile_options = set(
            profile.model_dump(exclude={"id", "name"}).keys()
        )
        unknown_cfg_opts = profile_options - set(site.known_config_options)
        if unknown_cfg_opts:
            raise BadRequestException(
                message="Site profile contains configuration options that are not known by this Site.",
                code=ExceptionCode.INVALID_PARAMS,
                details=[
                    BaseExceptionDetail(
                        reason=ExceptionCode.INVALID_PARAMS,
                        messages=[
                            f"The following profile items are not known by this Site: {unknown_cfg_opts}"
                        ],
                        field="site_profile_id",
                        location="body",
                    )
                ],
            )

    data = patch_request.model_dump(exclude_none=True)
    await services.sites.update(id, models.SiteUpdate(**data))
    return cast(models.Site, await services.sites.get_by_id(id))


@v1_router.delete(
    "/sites/{id}",
    status_code=204,
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def delete(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: int,
) -> None:
    """Delete a site from the database."""
    await services.sites.delete(id)
    return None


@v1_router.delete(
    "/sites",
    status_code=204,
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def delete_many(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    ids: Annotated[list[int], Query()],
) -> None:
    """Delete multiple sites from the database."""
    requested_ids = set(ids)
    deleted_ids = await services.sites.delete_many(ids)
    if deleted_ids != requested_ids:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message=f"Some of the requested IDs were not found.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[
                        f"The following IDs were not found: {requested_ids - deleted_ids}."
                    ],
                    field="ids",
                    location="query",
                )
            ],
        )
    return None


@v1_router.get(
    "/site-status/{site_id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_status(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    site_id: int,
) -> models.SiteStateStatus:
    """Get the status of a site's configuration tasks by the site ID."""
    status = await services.site_state.get_by_site_id(site_id)
    if status is None:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message=f"Status for Site ID not found.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[
                        f"The status for Site ID {site_id} was not found."
                    ],
                    field="site_id",
                    location="path",
                )
            ],
        )
    return status
