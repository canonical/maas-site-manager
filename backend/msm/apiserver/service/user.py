from collections.abc import Iterable
from typing import (
    Any,
)
from uuid import UUID

from sqlalchemy import (
    Select,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.sql import (
    and_,
    or_,
)

from msm.apiserver.db import (
    models,
    queries,
)
from msm.apiserver.db.tables import User
from msm.apiserver.schema import SortParam
from msm.apiserver.service.base import Service
from msm.common.password import (
    hash_password,
    verify_password,
)


class UserService(Service):
    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
        search_text: list[str] | None = None,
        email: list[str] | None = None,
        username: list[str] | None = None,
        full_name: list[str] | None = None,
        is_admin: list[str] | None = None,
    ) -> tuple[int, Iterable[models.User]]:
        filters = queries.filters_from_arguments(
            User,
            email=email,
            username=username,
            full_name=full_name,
            is_admin=is_admin,
        )
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        if search_text:
            filters.append(
                or_(
                    *queries.filters_from_arguments(
                        User,
                        email=search_text,
                        username=search_text,
                        full_name=search_text,
                    )
                )
            )
        count = await queries.row_count(self.conn, User, *filters)
        stmt = (
            self._select_statement()
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.User, result)

    async def get_by_email(self, email: str) -> models.User | None:
        """Gets a user by email."""
        stmt = self._select_statement().where(User.c.email == email)
        if result := await self.conn.execute(stmt):
            if user := result.one_or_none():
                return models.User(**user._asdict())
        return None

    async def get_by_username(self, username: str) -> models.User | None:
        """Gets a user by username."""
        stmt = self._select_statement().where(User.c.username == username)
        if result := await self.conn.execute(stmt):
            if user := result.one_or_none():
                return models.User(**user._asdict())
        return None

    async def get_by_id(self, id: int) -> models.User | None:
        """Gets a user by id."""
        stmt = self._select_statement().where(User.c.id == id)
        if result := await self.conn.execute(stmt):
            if user := result.one_or_none():
                return models.User(**user._asdict())
        return None

    async def get_by_auth_id(self, auth_id: UUID) -> models.User | None:
        """Gets a user by authentication ID."""
        stmt = self._select_statement().where(User.c.auth_id == auth_id)
        if result := await self.conn.execute(stmt):
            if user := result.one_or_none():
                return models.User(**user._asdict())
        return None

    async def create(self, details: models.UserCreate) -> models.User:
        data = details.model_dump()
        if password := data.get("password"):
            data["password"] = hash_password(password)
        result = await self.conn.execute(
            insert(User).returning(
                User.c.id,
                User.c.email,
                User.c.username,
                User.c.full_name,
                User.c.is_admin,
                User.c.auth_id,
            ),
            [data],
        )
        user = result.one()
        return models.User(**user._asdict())

    async def id_exists(self, user_id: int) -> bool:
        search = await self.conn.execute(
            select(User.c.id).select_from(User).filter(User.c.id == user_id)
        )
        return search.first() is not None

    async def exists(
        self,
        email: str | None = None,
        username: str | None = None,
        exclude_id: int | None = None,
    ) -> list[str] | None:
        if not email and not username:
            return None
        elif not username:
            user_filter = User.c.email == email
        elif not email:
            user_filter = User.c.username == username
        else:
            user_filter = or_(
                User.c.email == email, User.c.username == username
            )
        if exclude_id is not None:
            user_filter = and_(user_filter, User.c.id != exclude_id)
        search = await self.conn.execute(
            select(User.c.id, User.c.email, User.c.username)
            .select_from(User)
            .filter(user_filter)
        )
        existing = search.first()
        if existing is None:
            return None
        user = existing._asdict()
        conflicting = []
        if email == user["email"]:
            conflicting.append("email")
        if username == user["username"]:
            conflicting.append("username")
        return conflicting

    async def update_password(
        self,
        user_id: int,
        password: str,
    ) -> None:
        hashed_password = hash_password(password)
        stmt = (
            update(User)
            .where(User.c.id == user_id)
            .values(password=hashed_password)
        )
        await self.conn.execute(stmt)

    async def update(
        self, user_id: int, details: models.UserUpdate
    ) -> models.User:
        data = details.model_dump(exclude_none=True)
        if password := data.get("password"):
            data["password"] = hash_password(password)
        stmt = (
            update(User)
            .where(User.c.id == user_id)
            .values(data)
            .returning(
                User.c.id,
                User.c.email,
                User.c.username,
                User.c.full_name,
                User.c.is_admin,
                User.c.auth_id,
            )
        )
        result = await self.conn.execute(stmt)
        return models.User(**result.one()._asdict())

    async def password_matches(self, user_id: int, password: str) -> bool:
        stmt = (
            select(User.c.password)
            .select_from(User)
            .where(User.c.id == user_id)
        )
        if result := await self.conn.execute(stmt):
            if row := result.one_or_none():
                hashed_password = row[0]
                return verify_password(password, hashed_password)
        return False

    async def count_by_provider(self, provider_id: int) -> int:
        """Counts the number of users associated with a given provider ID."""
        stmt = (
            select(func.count())
            .select_from(User)
            .where(User.c.provider_id == provider_id)
        )
        count = (await self.conn.execute(stmt)).scalar_one()
        return count

    async def delete(self, user_id: int) -> None:
        """Deletes a user by ID."""
        stmt = delete(User).where(User.c.id == user_id)
        await self.conn.execute(stmt)

    def _select_statement(self, include_password: bool = False) -> Select[Any]:
        fields = [
            User.c.id,
            User.c.email,
            User.c.username,
            User.c.full_name,
            User.c.is_admin,
            User.c.auth_id,
        ]
        if include_password:
            fields.append(User.c.password)
        return select(*fields).select_from(User)
