"""Tests for the /site-status/{site_id} handler."""

import pytest

from msm.common.enums import TaskStatus
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestSiteStatusHandler:
    async def test_get_status(
        self,
        user_client: Client,
        factory: Factory,
    ) -> None:
        site = await factory.make_Site()
        await factory.make_SiteStateStatus(
            site_id=site.id,
            status=TaskStatus.COMPLETE,
            selections_status=TaskStatus.STARTED,
            global_config_status=TaskStatus.FAILED,
            image_sync_status=TaskStatus.UNKNOWN,
            errors=["Test error"],
        )
        response = await user_client.get(f"/site-status/{site.id}")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["site_id"] == site.id
        assert response_data["status"] == TaskStatus.COMPLETE.value
        assert response_data["selections_status"] == TaskStatus.STARTED.value
        assert response_data["global_config_status"] == TaskStatus.FAILED.value
        assert response_data["image_sync_status"] == TaskStatus.UNKNOWN.value
        assert response_data["errors"] == ["Test error"]

    async def test_get_status_not_found(
        self,
        user_client: Client,
    ) -> None:
        response = await user_client.get(f"/site-status/999")
        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data
        assert "Status for Site ID not found" in error_data["error"]["message"]

    async def test_get_status_invalid_site_id_format(
        self,
        user_client: Client,
    ) -> None:
        response = await user_client.get("/site-status/invalid")
        assert response.status_code == 422

    async def test_get_status_nonexistent_site_id(
        self,
        user_client: Client,
        factory: Factory,
    ) -> None:
        # Create a site but don't create status for it
        site = await factory.make_Site()
        response = await user_client.get(f"/site-status/{site.id}")
        assert response.status_code == 404
