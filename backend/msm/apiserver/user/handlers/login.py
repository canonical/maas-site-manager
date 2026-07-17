from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.security import OAuth2PasswordRequestForm

from msm.apiserver.auth import (
    AccessTokenResponse,
    AuthInfoResponse,
    token_response,
)
from msm.apiserver.db.models import Config
from msm.apiserver.dependencies import (
    config,
    cookie_manager,
    services,
)
from msm.apiserver.exceptions.catalog import (
    BaseExceptionDetail,
    ConflictException,
    UnauthorizedException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.exceptions.responses import (
    ConflictErrorResponseModel,
    UnauthorizedErrorResponseModel,
    ValidationErrorResponseModel,
)
from msm.apiserver.service import ServiceCollection
from msm.apiserver.user.auth import authenticate_user
from msm.common.cookie_manager import EncryptedCookieManager, MSMOAuth2Cookie
from msm.common.jwt import TokenAudience

v1_router = APIRouter(prefix="/v1")


@v1_router.post(
    "/login",
    responses={
        422: {"model": ValidationErrorResponseModel},
        401: {"model": UnauthorizedErrorResponseModel},
    },
)
async def post(
    config: Annotated[Config, Depends(config)],
    services: Annotated[ServiceCollection, Depends(services)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> AccessTokenResponse:
    user = await authenticate_user(
        services.users, form_data.username, form_data.password
    )
    if not user:
        # do not specify details here, as to not clue which parameter is wrong in case of an attack
        raise UnauthorizedException(
            code=ExceptionCode.INVALID_CREDENTIALS,
            message="Wrong username or password.",
        )
    return token_response(config, user.auth_id, TokenAudience.API)


@v1_router.get(
    "/login-info",
    responses={
        409: {"model": ConflictErrorResponseModel},
    },
)
async def get_login_info(
    email: str,
    services: Annotated[ServiceCollection, Depends(services)],
    cookie_manager: Annotated[EncryptedCookieManager, Depends(cookie_manager)],
    redirect_target: str | None = None,
) -> AuthInfoResponse:
    """Decide whether the login should proceed via OIDC or local login."""
    provider = await services.oidc.get_by_enabled()
    user = await services.users.get_by_username(email)
    user_provider_id = user.provider_id if user else None
    enabled_provider_id = provider.id if provider else None

    # A profile bound to an OIDC provider can only authenticate through
    # that exact provider.
    if (
        user_provider_id is not None
        and user_provider_id != enabled_provider_id
    ):
        raise ConflictException(
            code=ExceptionCode.MISSING_PROVIDER_CONFIG,
            message="The user is bound to a different OIDC provider.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_PROVIDER_CONFIG,
                    messages=[
                        "This account is linked to an OIDC provider "
                        "that is not currently enabled."
                    ],
                    field="provider",
                    location="body",
                )
            ],
        )

    # No enabled provider, or this is an existing local profile:
    # fall back to password auth.
    if provider is None or (user is not None and user_provider_id is None):
        return AuthInfoResponse(oidc=False)

    # OIDC is enabled and the user is either new or bound to an enabled provider
    client = await services.oidc._get_oauth_client()
    data = client.generate_authorization_url(
        redirect_target=redirect_target or "/",
    )
    cookie_manager.set_auth_cookie(
        key=MSMOAuth2Cookie.AUTH_STATE, value=data.state
    )
    cookie_manager.set_auth_cookie(
        key=MSMOAuth2Cookie.AUTH_NONCE, value=data.nonce
    )
    return AuthInfoResponse(
        oidc=True, auth_url=data.authorization_url, provider_name=provider.name
    )
