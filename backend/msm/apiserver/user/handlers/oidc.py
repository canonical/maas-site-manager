from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from msm.apiserver.db.models import (
    User,
)
from msm.apiserver.dependencies import (
    cookie_manager,
    services,
)
from msm.apiserver.exceptions.catalog import (
    BaseExceptionDetail,
    NotFoundException,
    UnauthorizedException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.exceptions.responses import (
    ConflictErrorResponseModel,
    ForbiddenErrorResponseModel,
    NotFoundErrorResponseModel,
    UnauthorizedErrorResponseModel,
    ValidationErrorResponseModel,
)
from msm.apiserver.service import ServiceCollection
from msm.apiserver.user.auth import authenticated_admin
from msm.common.api.oidc import (
    CallbackTargetResponse,
    OIDCProviderCreateRequest,
    OIDCProviderResponse,
    OIDCProviderUpdateRequest,
)
from msm.common.cookie_manager import EncryptedCookieManager, MSMOAuth2Cookie

v1_router = APIRouter(prefix="/v1")


@v1_router.get(
    "/external-auth",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        403: {"model": ForbiddenErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
    },
)
async def get_active_provider(
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
    "/external-auth",
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


@v1_router.patch(
    "/external-auth/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        409: {"model": ConflictErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def update(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_admin: Annotated[User, Depends(authenticated_admin)],
    id: int,
    put_request: OIDCProviderUpdateRequest,
) -> OIDCProviderResponse:
    provider = await services.oidc.update(id, put_request)
    user_count = await services.users.count_by_provider(provider.id)
    return OIDCProviderResponse.from_model(provider, user_count)


@v1_router.delete(
    "/external-auth/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        409: {"model": ConflictErrorResponseModel},
    },
)
async def delete(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_admin: Annotated[User, Depends(authenticated_admin)],
    id: int,
) -> None:
    await services.oidc.delete(id)


@v1_router.get(
    "/external-auth/callback",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def callback(
    cookie_manager: Annotated[EncryptedCookieManager, Depends(cookie_manager)],
    services: Annotated[ServiceCollection, Depends(services)],
    code: str,
    state: str,
) -> CallbackTargetResponse:
    """Handle the OAuth callback by exchanging the authorization code for tokens."""
    stored_state = cookie_manager.get_cookie(key=MSMOAuth2Cookie.AUTH_STATE)
    stored_nonce = cookie_manager.get_cookie(key=MSMOAuth2Cookie.AUTH_NONCE)
    if not stored_state or not stored_nonce or stored_state != state:
        raise UnauthorizedException(
            code=ExceptionCode.INVALID_CREDENTIALS,
            message="Invalid state parameter.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.INVALID_CREDENTIALS,
                    messages=["Invalid or missing OAuth state/nonce."],
                    field="state",
                    location="query",
                )
            ],
        )
    # Exchange the authorization code for tokens
    tokens = await services.oidc.get_callback(code=code, nonce=stored_nonce)
    cookie_manager.set_auth_cookie(
        key=MSMOAuth2Cookie.OAUTH2_ACCESS_TOKEN,
        value=tokens.access_token
        if isinstance(tokens.access_token, str)
        else tokens.access_token.encoded,
    )
    cookie_manager.set_auth_cookie(
        key=MSMOAuth2Cookie.OAUTH2_ID_TOKEN, value=tokens.id_token.encoded
    )
    cookie_manager.set_auth_cookie(
        key=MSMOAuth2Cookie.OAUTH2_REFRESH_TOKEN, value=tokens.refresh_token
    )
    return CallbackTargetResponse.from_state(state)
