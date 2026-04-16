from typing import Any
from uuid import uuid4

import pytest

from msm.apiserver.db import models
from msm.apiserver.db.models.global_site_config import SiteConfigFactory
from msm.apiserver.db.tables import Site
from msm.common.enums import TaskStatus
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


@pytest.mark.asyncio
class TestSiteStatusPatchHandler:
    async def test_patch_all_fields_changed(
        self, factory: Factory, api_site: models.Site, site_client: Client
    ) -> None:
        await factory.make_SiteStateStatus(site_id=api_site.id)

        payload = {
            "status": TaskStatus.COMPLETE,
            "selections_status": TaskStatus.FAILED,
            "global_config_status": TaskStatus.STARTED,
            "image_sync_status": TaskStatus.COMPLETE,
            "errors": ["one", "two"],
        }
        response = await site_client.patch("/site-status", json=payload)

        assert response.status_code == 204
        [status] = await factory.get("site_state_status")
        assert status["site_id"] == api_site.id
        assert status["status"] == TaskStatus.COMPLETE
        assert status["selections_status"] == TaskStatus.FAILED
        assert status["global_config_status"] == TaskStatus.STARTED
        assert status["image_sync_status"] == TaskStatus.COMPLETE
        assert status["errors"] == ["one", "two"]

    async def test_patch_errors_appended(
        self, factory: Factory, api_site: models.Site, site_client: Client
    ) -> None:
        """
        Test that errors are appended when clear_errors=False (default)
        """
        await factory.make_SiteStateStatus(
            site_id=api_site.id, errors=["original error"]
        )

        payload = {
            "errors": ["extra error"],
        }
        response = await site_client.patch("/site-status", json=payload)
        assert response.status_code == 204
        [status] = await factory.get("site_state_status")
        assert status["errors"] == ["original error", "extra error"]

    async def test_patch_errors_cleared(
        self, factory: Factory, api_site: models.Site, site_client: Client
    ) -> None:
        """
        Test that existing errors are cleared when clear_errors=True
        """
        await factory.make_SiteStateStatus(
            site_id=api_site.id, errors=["original error"]
        )

        payload: dict[str, Any] = {
            "errors": ["new error"],
            "clear_errors": True,
        }
        response = await site_client.patch("/site-status", json=payload)
        assert response.status_code == 204
        [status] = await factory.get("site_state_status")
        assert status["errors"] == ["new error"]

    async def test_patch_errors_unaffected(
        self, factory: Factory, api_site: models.Site, site_client: Client
    ) -> None:
        await factory.make_SiteStateStatus(
            site_id=api_site.id, errors=["original error"]
        )

        payload = {"status": TaskStatus.COMPLETE}
        response = await site_client.patch("/site-status", json=payload)
        assert response.status_code == 204
        [status] = await factory.get("site_state_status")
        assert status["errors"] == ["original error"]

    @pytest.mark.parametrize(
        "task_status,expected",
        [
            (TaskStatus.STARTED, False),
            (TaskStatus.COMPLETE, False),
            (TaskStatus.FAILED, True),
            (TaskStatus.UNKNOWN, True),
        ],
    )
    async def test_patch_image_sync_status_resets(
        self,
        factory: Factory,
        site_client: Client,
        task_status: TaskStatus,
        expected: bool,
    ) -> None:
        auth_id = uuid4()
        new_site = await factory.make_Site(
            auth_id=auth_id, trigger_image_sync=True
        )
        site_client.authenticate(
            auth_id,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )
        await factory.make_SiteStateStatus(
            site_id=new_site.id,
        )

        payload = {"image_sync_status": task_status}
        response = await site_client.patch("/site-status", json=payload)
        assert response.status_code == 204
        [site] = await factory.get("site", Site.c.id == new_site.id)
        assert site["trigger_image_sync"] == expected

    async def test_patch_no_fields_changed_error_response(
        self, site_client: Client
    ) -> None:
        response = await site_client.patch("/site-status", json={})

        assert response.status_code == 422
        detail = response.json()["error"]["details"][0]
        assert detail["reason"] == "ValueError"
        assert "At least one field must be set." in detail["messages"][0]

    async def test_patch_extra_fields_error_response(
        self, site_client: Client
    ) -> None:
        response = await site_client.patch(
            "/site-status", json={"status": TaskStatus.STARTED, "extra": 1}
        )

        assert response.status_code == 422
        detail = response.json()["error"]["details"][0]
        assert detail["reason"] == "ExtraForbidden"
        assert "Extra inputs are not permitted" in detail["messages"][0]

    async def test_patch_not_found(
        self,
        site_client: Client,
        api_site: models.Site,
    ) -> None:
        response = await site_client.patch(
            "/site-status", json={"status": TaskStatus.STARTED}
        )

        assert response.status_code == 404
        detail = response.json()["error"]["details"][0]
        assert detail["reason"] == "MissingResource"
        assert (
            f"Site state status for site ID {api_site.id} does not exist"
            in detail["messages"][0]
        )
