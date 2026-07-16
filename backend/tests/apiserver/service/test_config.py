import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db.models import Config
from msm.apiserver.service import config
from msm.apiserver.service.config import ConfigService
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestConfigService:
    async def test_get(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_Config("service_identifier", value="12345")
        await factory.make_Config("token_secret_key", value="secret")
        await factory.make_Config("encryption_key", value="abcde")
        service = ConfigService(db_connection)
        config = await service.get()
        assert config == Config(
            service_identifier="12345",
            token_secret_key="secret",
            encryption_key="abcde",
        )

    async def test_get_no_extra_entries(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_Config("some_config", value=42)
        service = ConfigService(db_connection)
        config = await service.get()
        assert config == Config()

    async def test_ensure_create_missing(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        service = ConfigService(db_connection)
        await service.ensure()
        configs = await factory.get("config")
        assert {config["name"] for config in configs} == set(
            Config.model_fields
        )

    async def test_ensure_creates_defaults(
        self,
        mocker: MockerFixture,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        mocker.patch.object(config, "uuid4").return_value = "a-b-c"
        mocker.patch.object(config, "generate_key").return_value = "abcde"

        service = ConfigService(db_connection)
        await service.ensure()
        configs = await factory.get("config")
        assert sorted(configs, key=lambda c: c["name"]) == [
            {"name": "encryption_key", "value": "abcde"},
            {"name": "service_identifier", "value": "a-b-c"},
            {"name": "token_secret_key", "value": "abcde"},
        ]

    async def test_ensure_keep_existing(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_Config("service_identifier", value="12345")
        await factory.make_Config("token_secret_key", value="secret")
        await factory.make_Config("encryption_key", value="abcde")
        service = ConfigService(db_connection)
        await service.ensure()
        configs = await factory.get("config")
        assert sorted(configs, key=lambda c: c["name"]) == [
            {"name": "encryption_key", "value": "abcde"},
            {"name": "service_identifier", "value": "12345"},
            {"name": "token_secret_key", "value": "secret"},
        ]

    async def test_ensure_remove_extra(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_Config("some_config", value=42)
        await factory.make_Config("another", value="test")
        service = ConfigService(db_connection)
        await service.ensure()
        configs = await factory.get("config")
        assert {config["name"] for config in configs} == set(
            Config.model_fields
        )
