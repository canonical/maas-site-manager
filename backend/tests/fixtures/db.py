import asyncio
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import pytest
from pytest_postgresql.executor import PostgreSQLExecutor
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import URL, Connection, text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from msm.apiserver.db import Database
from msm.apiserver.middleware import TransactionMiddleware

TEST_DB_NAME = "msm"
TEMPLATE_DB_NAME = "msm_template"


@dataclass
class DBConfig:
    """Database configuration."""

    db: str
    user: str
    socketdir: str
    port: int

    @property
    def dsn(self) -> URL:
        """DSN URL for the test database."""
        return URL.create(
            "postgresql+asyncpg",
            host=self.socketdir,
            port=self.port,
            database=self.db,
            username=self.user,
        )

    @property
    def settings_environ(self) -> dict[str, str]:
        """Return environment settings for the test database."""
        return {
            "MSM_DB_HOST": self.socketdir,
            "MSM_DB_NAME": self.db,
            "MSM_DB_USER": self.user,
            "MSM_DB_PORT": str(self.port),
        }


@pytest.fixture(scope="session")
def db_template(
    postgresql_proc: PostgreSQLExecutor,
) -> Iterator[DBConfig]:
    """Create a template database with migrations applied once per session."""
    port = postgresql_proc.port
    user = postgresql_proc.user
    socketdir = postgresql_proc.unixsocketdir

    # Create template database
    janitor = DatabaseJanitor(
        user=user,
        host=socketdir,
        port=port,
        dbname=TEMPLATE_DB_NAME,
        version=postgresql_proc.version,
    )

    with janitor:
        config = DBConfig(TEMPLATE_DB_NAME, user, socketdir, port)

        async def setup_template() -> None:
            db = Database(config.dsn, echo=False)

            # Apply migrations once to template
            await db.ensure_schema(migrate=True)

            # Create test-only tables in template
            from msm.apiserver.db.tables import METADATA

            def create_test_tables(conn: Connection) -> None:
                from sqlalchemy import inspect

                inspector = inspect(conn)
                existing_tables = set(inspector.get_table_names())

                tables_to_create = [
                    table
                    for table in METADATA.sorted_tables
                    if table.name not in existing_tables
                ]

                if tables_to_create:
                    for table in tables_to_create:
                        table.create(conn)

            await db._run_sync_in_transaction(create_test_tables)
            await db.aclose()

        # Run async setup synchronously
        asyncio.run(setup_template())

        yield config


@pytest.fixture(scope="session")
def db_setup(postgresql_proc: PostgreSQLExecutor) -> Iterator[DBConfig]:
    """Setup and teardown the database. Return the URL."""
    port = postgresql_proc.port
    user = postgresql_proc.user
    socketdir = postgresql_proc.unixsocketdir
    yield DBConfig(TEST_DB_NAME, user, socketdir, port)


@pytest.fixture
async def db(
    request: pytest.FixtureRequest,
    db_setup: DBConfig,
    db_template: DBConfig,
) -> AsyncIterator[Database]:
    """Set up the database schema by cloning from template."""
    echo = request.config.getoption("sqlalchemy_debug")

    # Create database from template using direct SQL
    # Connect to 'postgres' database to issue CREATE DATABASE
    postgres_dsn = db_setup.dsn.set(database="postgres")
    engine = create_async_engine(
        postgres_dsn,
        echo=False,
        isolation_level="AUTOCOMMIT",
    )

    async with engine.connect() as conn:
        # Terminate any existing connections to the test database
        await conn.execute(
            text(
                f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
                  AND pid <> pg_backend_pid()
                """
            )
        )
        # Drop and recreate from template
        await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        await conn.execute(
            text(f"CREATE DATABASE {TEST_DB_NAME} TEMPLATE {TEMPLATE_DB_NAME}")
        )

    await engine.dispose()

    # Connect to the cloned database
    db = Database(db_setup.dsn, echo=echo)

    yield db
    await db.drop_schema()


@pytest.fixture
async def db_connection(db: Database) -> AsyncIterator[AsyncConnection]:
    """The database connection."""
    async with db.engine.connect() as conn:
        yield conn
        await conn.rollback()


@pytest.fixture
def transaction_middleware_class(
    db_connection: AsyncConnection,
) -> Iterator[type]:
    class ConnectionReusingTransactionMiddleware(TransactionMiddleware):
        @asynccontextmanager
        async def get_connection(self) -> AsyncIterator[AsyncConnection]:
            yield db_connection

    yield ConnectionReusingTransactionMiddleware
