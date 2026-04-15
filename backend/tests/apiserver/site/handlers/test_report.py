from typing import Any
from uuid import uuid4

import pytest

from msm.apiserver.db import models
from msm.apiserver.db.tables import Site
from msm.common.enums import TaskStatus
from msm.common.jwt import (
    TokenAudience,
    TokenPurpose,
)
from msm.common.settings import Settings
from msm.common.time import now_utc
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestDetailsPostHandler:
    async def test_update_details(
        self, factory: Factory, site_client: Client
    ) -> None:
        details = {
            "name": "new-name",
            "url": "https://new-url.example.com",
        }
        before_post = now_utc()
        response = await site_client.post("/details", json=details)
        assert response.status_code == 200
        [site] = await factory.get("site")
        [site_data] = await factory.get("site_data")
        assert site["name"] == "new-name"
        assert site["url"] == "https://new-url.example.com"
        assert before_post < site_data["last_seen"]
        assert site_data["last_seen"] < now_utc()

    async def test_creates_stats(
        self, factory: Factory, site_client: Client
    ) -> None:
        machine_counts = {
            "allocated": 10,
            "deployed": 20,
            "ready": 30,
            "error": 40,
            "other": 50,
        }
        assert await factory.get("site_data") == []
        before_post = now_utc()
        response = await site_client.post(
            "/details", json={"machines_by_status": machine_counts}
        )
        assert response.status_code == 200
        [site_data] = await factory.get("site_data")
        assert site_data["machines_allocated"] == 10
        assert site_data["machines_deployed"] == 20
        assert site_data["machines_ready"] == 30
        assert site_data["machines_error"] == 40
        assert site_data["machines_other"] == 50
        assert before_post < site_data["last_seen"]
        assert site_data["last_seen"] < now_utc()

    async def test_update_stats(
        self, factory: Factory, api_site: models.Site, site_client: Client
    ) -> None:
        machine_counts = {
            "allocated": 10,
            "deployed": 20,
            "ready": 30,
            "error": 40,
            "other": 50,
        }
        await factory.make_SiteData(api_site.id)
        before_post = now_utc()
        response = await site_client.post(
            "/details", json={"machines_by_status": machine_counts}
        )
        assert response.status_code == 200
        [site_data] = await factory.get("site_data")
        assert site_data["machines_allocated"] == 10
        assert site_data["machines_deployed"] == 20
        assert site_data["machines_ready"] == 30
        assert site_data["machines_error"] == 40
        assert site_data["machines_other"] == 50
        assert before_post < site_data["last_seen"]
        assert site_data["last_seen"] < now_utc()

    async def test_update_empty(
        self, factory: Factory, api_site: models.Site, site_client: Client
    ) -> None:
        before_post = now_utc()
        response = await site_client.post("/details", json={})
        assert response.status_code == 200
        [site] = await factory.get("site")
        assert site["name"] == api_site.name
        assert site["url"] == api_site.url
        [site_data] = await factory.get("site_data")
        assert site_data["machines_allocated"] == 0
        assert site_data["machines_deployed"] == 0
        assert site_data["machines_ready"] == 0
        assert site_data["machines_error"] == 0
        assert site_data["machines_other"] == 0
        assert before_post < site_data["last_seen"]
        assert site_data["last_seen"] < now_utc()

    async def test_heartbeat_in_response(
        self, factory: Factory, api_site: models.Site, site_client: Client
    ) -> None:
        machine_counts = {
            "allocated": 10,
            "deployed": 20,
            "ready": 30,
            "error": 40,
            "other": 50,
        }
        await factory.make_SiteData(api_site.id)
        response = await site_client.post(
            "/details", json={"machines_by_status": machine_counts}
        )
        heartbeat = Settings().heartbeat_interval_seconds
        response_heartbeat = int(
            response.headers["MSM-Heartbeat-Interval-Seconds"]
        )
        assert heartbeat == response_heartbeat


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
        Test that when errors are specified,
        they are appended to the list in the DB.
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
        Test that when errors are specified as an empty list,
        the list is cleared in the DB.
        """
        await factory.make_SiteStateStatus(
            site_id=api_site.id, errors=["original error"]
        )

        payload: dict[str, Any] = {
            "errors": [],
        }
        response = await site_client.patch("/site-status", json=payload)
        assert response.status_code == 204
        [status] = await factory.get("site_state_status")
        assert status["errors"] == []

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
