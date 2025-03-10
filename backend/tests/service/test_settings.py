import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.db.models import Settings
from msm.jwt import DEFAULT_TOKEN_DURATION
from msm.service import settings as settings_module
from msm.service.settings import SettingsService
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestSettingsService:
    async def test_get(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_Setting(
            "service_url",
            value="https://sitemanager.example.com",
        )
        await factory.make_Setting(
            "token_lifetime_minutes",
            value=10,
        )
        await factory.make_Setting(
            "max_image_upload_size_gb",
            value=50,
        )
        service = SettingsService(db_connection)
        settings = await service.get()
        assert settings == Settings(
            service_url="https://sitemanager.example.com",
            token_lifetime_minutes=10,
            max_image_upload_size_gb=50,
        )

    async def test_get_no_extra_entries(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_Setting("some_setting", value=42)
        service = SettingsService(db_connection)
        settings = await service.get()
        assert settings == Settings()

    async def test_ensure_create_missing(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        service = SettingsService(db_connection)
        await service.ensure()
        settings = await factory.get("setting")
        assert {setting["name"] for setting in settings} == set(
            Settings.model_fields
        )

    async def test_ensure_sets_service_url(
        self,
        mocker: MockerFixture,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        mocker.patch.object(
            settings_module, "gethostname"
        ).return_value = "sitemanager"
        service = SettingsService(db_connection)
        await service.ensure()
        settings = await factory.get("setting")
        assert settings == [
            {
                "name": "max_image_upload_size_gb",
                "value": 100,
            },
            {"name": "service_url", "value": ""},
            {
                "name": "token_lifetime_minutes",
                "value": DEFAULT_TOKEN_DURATION.total_seconds() // 60,
            },
            {
                "name": "token_rotation_interval_minutes",
                "value": (DEFAULT_TOKEN_DURATION.total_seconds() // 60) // 2,
            },
        ]

    async def test_ensure_keep_existing(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_Setting(
            "service_url", value="http://sitemanager:8000"
        )
        await factory.make_Setting("token_lifetime_minutes", value=10)
        await factory.make_Setting(
            "token_rotation_interval_minutes", value=100
        )
        await factory.make_Setting("max_image_upload_size_gb", value=50)
        service = SettingsService(db_connection)
        await service.ensure()
        settings = await factory.get("setting")
        assert settings == [
            {"name": "max_image_upload_size_gb", "value": 50},
            {"name": "service_url", "value": "http://sitemanager:8000"},
            {"name": "token_lifetime_minutes", "value": 10},
            {"name": "token_rotation_interval_minutes", "value": 100},
        ]

    async def test_ensure_remove_extra(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_Setting("some_setting", value=42)
        await factory.make_Setting("another", value="test")
        service = SettingsService(db_connection)
        await service.ensure()
        settings = await factory.get("setting")
        assert {setting["name"] for setting in settings} == set(
            Settings.model_fields
        )

    async def test_get_service_url_from_default(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "msm.service.settings.gethostname", lambda: "msm-host"
        )
        monkeypatch.delenv("MSM_BASE_PATH", raising=False)
        await factory.make_Setting("service_url", value="")
        service = SettingsService(db_connection)
        service_url = await service.get_service_url()
        assert service_url == "http://msm-host:8000"

    async def test_get_service_url_from_env(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv(
            "MSM_BASE_PATH", "https://sitemanager.example.com/juju-model/"
        )
        await factory.make_Setting("service_url", value="")
        service = SettingsService(db_connection)
        service_url = await service.get_service_url()
        assert service_url == "https://sitemanager.example.com/juju-model/"

    async def test_get_service_url_from_db(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv(
            "MSM_BASE_PATH", "https://sitemanager.example.com/juju-model/"
        )
        await factory.make_Setting(
            "service_url",
            value="https://sitemanager.example.com",
        )
        service = SettingsService(db_connection)
        service_url = await service.get_service_url()
        assert service_url == "https://sitemanager.example.com"
