from collections.abc import AsyncIterator, Iterator
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db.models import User
from msm.apiserver.service.user import UserService
from tests.fixtures.factory import Factory


@pytest.fixture
def service(db_connection: AsyncConnection) -> Iterator[UserService]:
    yield UserService(db_connection)


@pytest.fixture
async def user(factory: Factory) -> AsyncIterator[User]:
    yield await factory.make_User(username="admin", password="secret")


@pytest.mark.asyncio
class TestUserService:
    async def test_id_exists(self, user: User, service: UserService) -> None:
        assert await service.id_exists(user.id)
        assert not await service.id_exists(-1)

    @pytest.mark.parametrize(
        "email,username,exists",
        [
            ("", "", None),
            ("admin@example.com", "admin", ["email", "username"]),
            ("admin@example.com", "nonexistent_admin", ["email"]),
            ("nonexistent_admin@example.com", "admin", ["username"]),
            ("nonexistent_admin@example.com", "nonexistent_admin", None),
        ],
    )
    async def test_exists(
        self,
        user: User,
        service: UserService,
        email: str,
        username: str,
        exists: list[str] | None,
    ) -> None:
        assert await service.exists(email=email, username=username) == exists

    @pytest.mark.parametrize(
        "email,username",
        [
            ("admin@example.com", "admin"),
            ("admin@example.com", "nonexistent_admin"),
            ("nonexistent_admin@example.com", "admin"),
            ("nonexistent_admin@example.com", "nonexistent_admin"),
        ],
    )
    async def test_exists_exclude_id(
        self,
        user: User,
        service: UserService,
        email: str,
        username: str,
    ) -> None:
        conflict = await service.exists(
            email=email, username=username, exclude_id=user.id
        )
        assert conflict is None

    @pytest.mark.parametrize(
        "id,exists",
        [
            (1, True),
            (-1, False),
        ],
    )
    async def test_get_by_id(
        self,
        user: User,
        service: UserService,
        id: int,
        exists: bool,
    ) -> None:
        assert await service.get_by_id(id) == (user if exists else None)

    async def test_get_by_auth_id(
        self,
        user: User,
        service: UserService,
    ) -> None:
        assert await service.get_by_auth_id(user.auth_id) == user

    async def test_get_by_auth_id_unknown(
        self,
        service: UserService,
    ) -> None:
        assert await service.get_by_auth_id(uuid4()) is None

    async def test_password_matches(
        self,
        user: User,
        service: UserService,
    ) -> None:
        assert await service.password_matches(user.id, "secret")
        assert not await service.password_matches(user.id, "other-secret")

    async def test_update_password(
        self,
        user: User,
        service: UserService,
    ) -> None:
        new_password = "new-secret"
        await service.update_password(user.id, new_password)
        assert await service.password_matches(user.id, new_password)

    async def test_get_by_username(
        self,
        user: User,
        service: UserService,
    ) -> None:
        assert await service.get_by_username(user.username) == user

    async def test_get_by_username_unknown(
        self,
        service: UserService,
    ) -> None:
        assert await service.get_by_username("unknown_user") is None
