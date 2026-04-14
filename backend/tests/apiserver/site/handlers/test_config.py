import pytest
from sqlalchemy import update

from msm.apiserver.db.models import Site
from msm.apiserver.db.models.global_site_config import SiteConfigFactory
from msm.apiserver.db.tables import Site as SiteTable
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestSiteConfigGetHandler:
    async def test_get_config_with_profile(
        self, factory: Factory, api_site: Site, site_client: Client
    ) -> None:
        """Test GET /site-config returns config and selections from linked profile."""
        profile = await factory.make_SiteProfile(
            name="Test Profile",
            selections=["ubuntu/jammy/amd64"],
            global_config={"theme": "dark"},
        )
        await factory.conn.execute(
            update(SiteTable)
            .where(SiteTable.c.id == api_site.id)
            .values(site_profile_id=profile.id)
        )

        response = await site_client.get("/site-config")
        assert response.status_code == 200
        data = response.json()

        assert set(data["global_config"].keys()) == set(
            SiteConfigFactory.DEFAULT_CONFIG.keys()
        )
        assert data["global_config"]["theme"] == "dark"
        assert data["selections"] == ["ubuntu/jammy/amd64"]
        assert "trigger_image_sync" in data

    async def test_get_config_without_profile(
        self, factory: Factory, api_site: Site, site_client: Client
    ) -> None:
        """Test GET /site-config returns defaults and empty selections when no profile."""
        response = await site_client.get("/site-config")
        assert response.status_code == 200
        data = response.json()

        for key, value in SiteConfigFactory.DEFAULT_CONFIG.items():
            assert data["global_config"][key] == value, (
                f"Config key '{key}' has value {data['global_config'][key]} "
                f"but expected {value}"
            )
        assert data["selections"] == []
        assert data["trigger_image_sync"] is False

    async def test_get_config_trigger_image_sync(
        self, factory: Factory, api_site: Site, site_client: Client
    ) -> None:
        """Test GET /site-config reflects trigger_image_sync from the site row."""
        await factory.conn.execute(
            update(SiteTable)
            .where(SiteTable.c.id == api_site.id)
            .values(trigger_image_sync=True)
        )

        response = await site_client.get("/site-config")
        assert response.status_code == 200
        assert response.json()["trigger_image_sync"] is True

    async def test_get_config_unauthenticated(
        self, site_client: Client
    ) -> None:
        """Test GET /site-config returns 401 without valid token."""
        site_client.authenticate(None)
        response = await site_client.get("/site-config")
        assert response.status_code == 401
