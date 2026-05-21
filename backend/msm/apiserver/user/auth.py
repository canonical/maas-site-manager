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
from msm.apiserver.dependencies import services
from msm.apiserver.exceptions.catalog import (
    BaseExceptionDetail,
    ForbiddenException,
    UnauthorizedException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.service import (
    ServiceCollection,
    UserService,
)
from msm.common.jwt import TokenAudience, TokenPurpose

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
