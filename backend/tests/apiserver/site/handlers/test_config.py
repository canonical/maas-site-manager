from uuid import uuid4

import pytest

from msm.common.jwt import (
    TokenAudience,
    TokenPurpose,
)
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestSiteConfigGetHandler:
    async def test_get_config_with_profile(
        self, factory: Factory, site_client: Client
    ) -> None:
        """Test GET /site-config returns config and selections from linked profile."""
        site_auth_id = uuid4()
        profile = await factory.make_SiteProfile(
            name="Test Profile",
            selections=["ubuntu/jammy/amd64"],
            global_config={"theme": "dark"},
        )
        await factory.make_Site(
            auth_id=site_auth_id,
            site_profile_id=profile.id,
        )
        site_client.authenticate(
            site_auth_id,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )

        response = await site_client.get("/site-config")
        assert response.status_code == 200
        data = response.json()

        assert data["global_config"]["theme"] == "dark"
        assert data["selections"] == ["ubuntu/jammy/amd64"]
        assert "trigger_image_sync" in data

    async def test_get_config_without_profile(
        self, factory: Factory, site_client: Client
    ) -> None:
        """Test GET /site-config returns 404 when no profile is linked."""
        site_auth_id = uuid4()
        await factory.make_Site(auth_id=site_auth_id)
        site_client.authenticate(
            site_auth_id,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )

        response = await site_client.get("/site-config")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "MissingResource"

    async def test_get_config_trigger_image_sync(
        self, factory: Factory, site_client: Client
    ) -> None:
        """Test GET /site-config reflects trigger_image_sync from the site row."""
        site_auth_id = uuid4()
        profile = await factory.make_SiteProfile(
            name="Trigger profile",
            selections=["ubuntu/resolute/amd64"],
            global_config={},
        )
        await factory.make_Site(
            auth_id=site_auth_id,
            trigger_image_sync=True,
            site_profile_id=profile.id,
        )
        site_client.authenticate(
            site_auth_id,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
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
