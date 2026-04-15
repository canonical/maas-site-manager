from uuid import uuid4

import pytest

from msm.apiserver.db.models.global_site_config import SiteConfigFactory
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
            trigger_image_sync=True,
        )
        site_client.authenticate(
            site_auth_id,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )

        response = await site_client.get("/site-config")
        assert response.status_code == 200
        data = response.json()

        expected_cfg = {**SiteConfigFactory.DEFAULT_CONFIG, "theme": "dark"}
        assert data["global_config"] == expected_cfg
        assert data["selections"] == ["ubuntu/jammy/amd64"]
        assert data["trigger_image_sync"]

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
