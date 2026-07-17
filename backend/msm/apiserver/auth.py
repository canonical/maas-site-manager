from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import (
    Annotated,
)
from uuid import UUID

from fastapi import (
    Depends,
    Request,
)
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel

from msm.apiserver.db.models import Config, Token
from msm.apiserver.dependencies import config
from msm.apiserver.exceptions.catalog import (
    BaseExceptionDetail,
    UnauthorizedException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.common.jwt import (
    DEFAULT_TOKEN_DURATION,
    DEFAULT_TOKEN_ROTATION,
    JWT,
    InvalidToken,
    TokenAudience,
    TokenPurpose,
)

# a dependency callable that returns the token
BearerToken = Callable[[Request], Awaitable[str | None]]


async def bearer_token(request: Request) -> str:
    """Returns the authentication token from the request header."""
    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise UnauthorizedException(
            code=ExceptionCode.NOT_AUTHENTICATED,
            message="This endpoint requires authentication.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.NOT_AUTHENTICATED,
                    messages=["Authorization token is missing."],
                    field="Authorization",
                    location="header",
                )
            ],
        )
    return token


def auth_id_from_token(
    bearer_token: BearerToken,
    token_audience: TokenAudience,
    token_purpose: TokenPurpose | None = None,
) -> Callable[[Config, str], UUID]:
    """Return a dependency callable to get the auth ID from the token."""

    def auth_id_dep(
        config: Annotated[Config, Depends(config)],
        token: Annotated[str, Depends(bearer_token)],
    ) -> UUID:
        try:
            decoded_token = JWT.decode(
                token,
                key=config.token_secret_key,
                issuer=config.service_identifier,
                audience=token_audience,
                purpose=token_purpose,
            )
        except (ValueError, InvalidToken):
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
        return UUID(decoded_token.subject)

    return auth_id_dep


def auth_id_from_token_multi_aud(
    bearer_token: BearerToken,
    token_audiences: list[TokenAudience],
    token_purpose: TokenPurpose | None = None,
) -> Callable[[Config, str], tuple[UUID, TokenAudience]]:
    """Return a dependency callable to get the auth ID from the token,
    allowing for one of many possible audiences."""

    def auth_id_dep(
        config: Annotated[Config, Depends(config)],
        token: Annotated[str, Depends(bearer_token)],
    ) -> tuple[UUID, TokenAudience]:
        for token_audience in token_audiences:
            try:
                decoded_token = JWT.decode(
                    token,
                    key=config.token_secret_key,
                    issuer=config.service_identifier,
                    audience=token_audience,
                    purpose=token_purpose,
                )
            except (ValueError, InvalidToken):
                continue
            return (UUID(decoded_token.subject), token_audience)
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

    return auth_id_dep


class AccessTokenResponse(BaseModel):
    """Content for a response returning a JWT."""

    token_type: str
    access_token: str
    rotation_interval_minutes: int


class AuthInfoResponse(BaseModel):
    """Content for a response returning authentication flow information."""

    auth_url: str | None = None
    provider_name: str | None = None
    oidc: bool


def token_response(
    config: Config,
    auth_id: UUID,
    audience: TokenAudience,
    purpose: TokenPurpose | None = None,
    duration: timedelta = DEFAULT_TOKEN_DURATION,
    rotation_interval_minutes: int = DEFAULT_TOKEN_ROTATION,
) -> AccessTokenResponse:
    """Return an AccessTokenResponse, generating a token."""
    token = JWT.create(
        issuer=config.service_identifier,
        subject=str(auth_id),
        audience=audience,
        purpose=purpose,
        key=config.token_secret_key,
        duration=duration,
    )
    return AccessTokenResponse(
        token_type="Bearer",
        access_token=token.encoded,
        rotation_interval_minutes=rotation_interval_minutes,
    )


def token_response_from_token(
    token: Token,
    rotation_interval_minutes: int = DEFAULT_TOKEN_ROTATION,
) -> AccessTokenResponse:
    """Return an AccessTokenResponse."""
    return AccessTokenResponse(
        token_type="Bearer",
        access_token=token.value,
        rotation_interval_minutes=rotation_interval_minutes,
    )
