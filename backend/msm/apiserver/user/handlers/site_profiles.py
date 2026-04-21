from typing import (
    Annotated,
    Any,
    Self,
)

from fastapi import (
    APIRouter,
    Depends,
    Path,
)
from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

from msm.apiserver.db import DEFAULT_SITE_PROFILE_ID, models
from msm.apiserver.db.models.global_site_config import SiteConfigFactory
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

SELECTIONS_PATTERN = r"^[^\s/]+/[^\s/]+/[^\s/]+$"


def _validate_global_config(
    global_config: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Validate global_config keys and values according to SiteConfigFactory."""
    if global_config is None:
        return None

    invalid_keys = set(global_config.keys()) - set(
        SiteConfigFactory.ALL_CONFIGS.keys()
    )
    if invalid_keys:
        raise ValueError(
            f"Invalid global_config keys: {', '.join(sorted(invalid_keys))}. "
            f"Valid keys are: {', '.join(sorted(SiteConfigFactory.ALL_CONFIGS.keys()))}"
        )

    for key, value in global_config.items():
        config_class = SiteConfigFactory.ALL_CONFIGS[key]
        try:
            config_class(value=value)
        except ValidationError as e:
            error_messages = "; ".join(
                [
                    f"{err['loc'][0] if err['loc'] else key}: {err['msg']}"
                    for err in e.errors()
                ]
            )
            raise ValueError(
                f"Invalid value for '{key}': {error_messages}"
            ) from e

    return global_config


def _filter_default_values(
    global_config: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Filter out values that match system defaults for storage optimization."""
    if global_config is None:
        return None

    filtered = {
        key: value
        for key, value in global_config.items()
        if value != SiteConfigFactory.DEFAULT_CONFIG.get(key)
    }
    return filtered if filtered else None


async def validate_selections_exist(
    services: ServiceCollection, selections: list[str]
) -> None:
    """
    Validate that all selections exist in boot source selections.

    Raises:
        NotFoundException: If any selections do not exist in available boot sources.
    """
    missing_selections = []
    for selection in selections:
        os, release, arch = selection.split("/")
        count, _ = await services.boot_source_selections.get(
            [],
            os=[os],
            release=[release],
            arch=[arch],
        )
        if count == 0:
            missing_selections.append(selection)

    if missing_selections:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Some selections do not exist in available boot sources.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[
                        f"The following selections do not exist: {', '.join(missing_selections)}"
                    ],
                    field="selections",
                    location="body",
                )
            ],
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


class ProfilesPostRequest(BaseModel):
    """Request to create a Site Profile."""

    name: str = Field(min_length=1, max_length=255)
    selections: list[
        Annotated[str, StringConstraints(pattern=SELECTIONS_PATTERN)]
    ] = Field(min_length=1)
    global_config: dict[str, Any] | None = None

    @field_validator("global_config")
    @classmethod
    def validate_global_config(
        cls, v: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        return _validate_global_config(v)


class ProfilesPatchRequest(BaseModel):
    """Request to update a Site Profile."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    selections: (
        list[Annotated[str, StringConstraints(pattern=SELECTIONS_PATTERN)]]
        | None
    ) = Field(default=None, min_length=1)
    global_config: dict[str, Any] | None = None

    @field_validator("global_config")
    @classmethod
    def validate_global_config(
        cls, v: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        return _validate_global_config(v)

    @model_validator(mode="after")
    def check_at_least_one_field_present(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be set.")
        return self


@v1_router.post(
    "/profiles",
    status_code=201,
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def post(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    post_request: ProfilesPostRequest,
) -> models.SiteProfile:
    """Create a new site profile."""
    await validate_selections_exist(services, post_request.selections)

    data = post_request.model_dump()
    if "global_config" in data:
        data["global_config"] = _filter_default_values(data["global_config"])

    return await services.site_profiles.create(
        models.SiteProfileCreate(**data)
    )


@v1_router.patch(
    "/profiles/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def patch(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: Annotated[
        int,
        Path(
            title="The ID of the Site Profile to be updated",
            gt=DEFAULT_SITE_PROFILE_ID,
        ),
    ],
    patch_request: ProfilesPatchRequest,
) -> models.SiteProfile:
    """Update a site profile.

    Raises:
        NotFoundException: If the profile with the given ID does not exist,
            or if any of the selections do not exist in available boot sources.
    """
    existing_profile = await services.site_profiles.get_by_id(id)
    if not existing_profile:
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

    if patch_request.selections is not None:
        await validate_selections_exist(services, patch_request.selections)

    update_data = patch_request.model_dump(exclude_none=True)

    if patch_request.global_config is not None:
        stored_config = await services.site_profiles.get_stored_config_by_id(
            id
        )
        merged_config = stored_config | patch_request.global_config
        filtered_config = _filter_default_values(merged_config)
        update_data["global_config"] = filtered_config

    return await services.site_profiles.update(
        id, models.SiteProfileUpdate(**update_data)
    )


@v1_router.delete(
    "/profiles/{id}",
    status_code=204,
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def delete(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: Annotated[
        int,
        Path(
            title="The ID of the Site Profile to delete",
            gt=DEFAULT_SITE_PROFILE_ID,
        ),
    ],
) -> None:
    """Delete a site profile.

    Raises:
        NotFoundException: If the profile with the given ID does not exist.
    """
    if not await services.site_profiles.get_by_id(id):
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
    await services.site_profiles.delete(id)
    return None
