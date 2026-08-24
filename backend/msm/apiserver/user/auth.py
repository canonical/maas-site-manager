from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from msm.apiserver.auth import (
    auth_id_from_token,
    auth_id_from_token_multi_aud,
    bearer_token,
)
from msm.apiserver.db.models import User, Worker
from msm.apiserver.dependencies import cookie_manager, services
from msm.apiserver.exceptions.catalog import (
    BadGatewayException,
    BaseExceptionDetail,
    ForbiddenException,
    UnauthorizedException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.service import (
    ServiceCollection,
    UserService,
)
from msm.common.cookie_manager import EncryptedCookieManager, MSMOAuth2Cookie
from msm.common.jwt import TokenAudience, TokenPurpose
from msm.common.oidc_jwt import JWTDecodeException, JWTValidationException

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="v1/login")


async def authenticate_user(
    service: UserService,
    email: str,
    password: str,
) -> User | None:
    if user := await service.get_by_email(email):
        if await service.password_matches(user.id, password):
            return user
    return None


async def authenticated_user(
    services: Annotated[ServiceCollection, Depends(services)],
    auth_id: Annotated[
        UUID, Depends(auth_id_from_token(OAUTH2_SCHEME, TokenAudience.API))
    ],
) -> User:
    if user := await services.users.get_by_auth_id(auth_id):
        return user
    raise UnauthorizedException(
        code=ExceptionCode.INVALID_TOKEN,
        message="The token is not valid.",
        details=[
            BaseExceptionDetail(
                reason=ExceptionCode.INVALID_TOKEN,
                messages=["The token is not valid."],
                field="Authorization",
                location="header",
            )
        ],
    )


def _clear_oauth_cookies(cookie_manager: EncryptedCookieManager) -> None:
    for key in (
        MSMOAuth2Cookie.OAUTH2_ACCESS_TOKEN,
        MSMOAuth2Cookie.OAUTH2_ID_TOKEN,
        MSMOAuth2Cookie.OAUTH2_REFRESH_TOKEN,
    ):
        cookie_manager.clear_cookie(key)


async def oidc_authenticated_user(
    cookie_manager: Annotated[EncryptedCookieManager, Depends(cookie_manager)],
    services: Annotated[ServiceCollection, Depends(services)],
) -> User:
    """
    Authenticate a user from the OIDC cookies.
    """
    access_token = cookie_manager.get_cookie(
        MSMOAuth2Cookie.OAUTH2_ACCESS_TOKEN
    )
    id_token = cookie_manager.get_cookie(MSMOAuth2Cookie.OAUTH2_ID_TOKEN)
    refresh_token = cookie_manager.get_cookie(
        MSMOAuth2Cookie.OAUTH2_REFRESH_TOKEN
    )

    if not id_token or not refresh_token:
        _clear_oauth_cookies(cookie_manager)
        raise UnauthorizedException(
            code=ExceptionCode.NOT_AUTHENTICATED,
            message="This endpoint requires authentication.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.NOT_AUTHENTICATED,
                    messages=["Missing id_token or refresh_token cookies."],
                    field="Authorization",
                    location="cookie",
                )
            ],
        )

    if not await _is_access_token_valid(services, access_token):
        try:
            tokens = await services.oidc.refresh_access_token(refresh_token)
        except (UnauthorizedException, BadGatewayException):
            _clear_oauth_cookies(cookie_manager)
            raise UnauthorizedException(
                code=ExceptionCode.INVALID_TOKEN,
                message="The token is not valid.",
                details=[
                    BaseExceptionDetail(
                        reason=ExceptionCode.INVALID_TOKEN,
                        messages=["Please sign in again to continue."],
                        field="Authorization",
                        location="cookie",
                    )
                ],
            )
        cookie_manager.set_auth_cookie(
            key=MSMOAuth2Cookie.OAUTH2_ACCESS_TOKEN,
            value=tokens.access_token,
        )
        # Some providers issue a new refresh token as well
        if tokens.refresh_token != refresh_token:
            cookie_manager.set_auth_cookie(
                key=MSMOAuth2Cookie.OAUTH2_REFRESH_TOKEN,
                value=tokens.refresh_token,
            )

    return await services.oidc.get_user_from_id_token(id_token)


async def _is_access_token_valid(
    services: ServiceCollection, access_token: str | None
) -> bool:
    if not access_token:
        return False
    try:
        await services.oidc.validate_access_token(access_token)
        return True
    except (
        UnauthorizedException,
        JWTDecodeException,
        JWTValidationException,
    ):
        return False


def authenticated_admin(
    user: Annotated[User, Depends(authenticated_user)],
) -> User:
    if not user.is_admin:
        raise ForbiddenException(
            code=ExceptionCode.MISSING_PERMISSIONS,
            message="Unauthorized credentials.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_PERMISSIONS,
                    messages=[
                        "The current user does not have permissions to perform this action."
                    ],
                    field="Authorization",
                    location="header",
                )
            ],
        )
    return user


async def authenticated_worker(
    services: Annotated[ServiceCollection, Depends(services)],
    auth_id: Annotated[
        UUID,
        Depends(
            auth_id_from_token(
                bearer_token,
                TokenAudience.WORKER,
                token_purpose=TokenPurpose.ACCESS,
            )
        ),
    ],
) -> Worker:
    db_token = await services.tokens.get_by_auth_id(
        auth_id,
        audience=TokenAudience.WORKER,
        purpose=TokenPurpose.ACCESS,
    )
    if db_token is None or db_token.is_expired():
        raise UnauthorizedException(
            code=ExceptionCode.INVALID_TOKEN,
            message=f"The token is not valid.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.INVALID_TOKEN,
                    messages=["The token is not valid."],
                    field="Authorization",
                    location="header",
                )
            ],
        )
    return Worker(auth_id=auth_id)


async def verify_authenticated_user_or_worker(
    services: Annotated[ServiceCollection, Depends(services)],
    auth_id_and_aud: Annotated[
        tuple[UUID, TokenAudience],
        Depends(
            auth_id_from_token_multi_aud(
                OAUTH2_SCHEME, [TokenAudience.API, TokenAudience.WORKER]
            )
        ),
    ],
) -> User | Worker:
    if auth_id_and_aud[1] == TokenAudience.WORKER:
        return await authenticated_worker(services, auth_id_and_aud[0])
    else:
        return await authenticated_user(services, auth_id_and_aud[0])


async def verify_authenticated_admin_or_worker(
    services: Annotated[ServiceCollection, Depends(services)],
    auth_id_and_aud: Annotated[
        tuple[UUID, TokenAudience],
        Depends(
            auth_id_from_token_multi_aud(
                OAUTH2_SCHEME, [TokenAudience.API, TokenAudience.WORKER]
            )
        ),
    ],
) -> User | Worker:
    if auth_id_and_aud[1] == TokenAudience.WORKER:
        return await authenticated_worker(services, auth_id_and_aud[0])
    else:
        user = await authenticated_user(services, auth_id_and_aud[0])
        return authenticated_admin(user)
