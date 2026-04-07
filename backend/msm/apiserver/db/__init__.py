from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar, cast

from sqlalchemy import (
    URL,
    Connection,
    text,
)
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    create_async_engine,
)

from msm.apiserver.db.alembic import migrate_db
from msm.apiserver.db.tables import METADATA

MIN_POSTGRES_VERSION = (14, 0)
CUSTOM_IMAGE_SOURCE_ID = 1
DEFAULT_SITE_PROFILE_ID = 1

FuncResult = TypeVar("FuncResult")


class Database:
    def __init__(self, dsn: URL, echo: bool = False):
        self.dsn = dsn
        self.engine = create_async_engine(dsn, echo=echo)

    async def aclose(self) -> None:
        """Disconnect from the database.

        This allow using the object with `contextlib.aclosing`.
        """
        await self.engine.dispose()

    async def ensure_schema(self, migrate: bool = True) -> None:
        """Ensure the database schema is up to date.

        When `migrate` is True, this is done applying pending migrations (if
        any).  Otherwise, the current schema is created.

        """
        func: Callable[[Connection], Any]
        if migrate:
            func = migrate_db
        else:
            func = METADATA.create_all
        await self._run_sync_in_transaction(func)

    async def drop_schema(self) -> None:
        """Drop the database schema."""

        def drop_all(conn: Connection) -> None:
            # Drop materialized view first since it depends on tables
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS images_index"))
            METADATA.drop_all(conn)
            # Alembic table is not tracked by metadata, manually delete it
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))

        await self._run_sync_in_transaction(drop_all)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncConnection]:
        """Context manager to run a code section in a transaction."""
        async with self.engine.connect() as conn:
            async with conn.begin():
                yield conn

    async def execute_in_transaction(
        self,
        func: Callable[..., Awaitable[FuncResult]],
        *args: Any,
    ) -> FuncResult:
        """Execute the given async function in a transaction."""
        async with self.transaction() as conn:
            return await func(conn, *args)

    async def _run_sync_in_transaction(
        self, func: Callable[[Connection], FuncResult]
    ) -> FuncResult:
        async with self.transaction() as conn:
            return await conn.run_sync(func)


async def check_server_version(conn: AsyncConnection) -> None:
    """Raise an exception if th PostgreSQL version is not supported."""
    result = await conn.execute(text("SHOW server_version"))
    row = cast(str, result.scalar())
    # format is "major.minor [optional additional info]"
    major, minor = row.split(" ", 1)[0].split(".", 1)
    if (int(major), int(minor)) < MIN_POSTGRES_VERSION:
        raise RuntimeError(f"Unsupported PostgreSQL version: {major}.{minor}")
