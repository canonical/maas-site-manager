from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from msm.apiserver.db.models import (
    User,
)
from msm.apiserver.dependencies import (
    services,
)
from msm.apiserver.exceptions.catalog import (
    BaseExceptionDetail,
    NotFoundException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.exceptions.responses import (
    ForbiddenErrorResponseModel,
    NotFoundErrorResponseModel,
    UnauthorizedErrorResponseModel,
    ValidationErrorResponseModel,
)
from msm.apiserver.service import ServiceCollection
from msm.apiserver.user.auth import authenticated_admin
from msm.common.api.oidc import (
    OIDCProviderCreateRequest,
    OIDCProviderResponse,
)

v1_router = APIRouter(prefix="/v1")


@v1_router.get(
    "/external_auth:get_active",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        403: {"model": ForbiddenErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
    },
)
async def get_active(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_admin: Annotated[User, Depends(authenticated_admin)],
) -> OIDCProviderResponse:
    if provider := await services.oidc.get_by_enabled():
        user_count = await services.users.count_by_provider(provider.id)
        return OIDCProviderResponse.from_model(provider, user_count)
    raise NotFoundException(
        code=ExceptionCode.MISSING_PROVIDER_CONFIG,
        message="No active OIDC provider found.",
        details=[
            BaseExceptionDetail(
                reason=ExceptionCode.MISSING_PROVIDER_CONFIG,
                messages=[
                    "There is no external OIDC provider currently enabled."
                ],
                field="provider",
                location="body",
            )
        ],
    )


@v1_router.post(
    "/external_auth",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def create(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_admin: Annotated[User, Depends(authenticated_admin)],
    post_request: OIDCProviderCreateRequest,
) -> OIDCProviderResponse:
    provider = await services.oidc.create(post_request)
    return OIDCProviderResponse.from_model(provider, user_count=0)
