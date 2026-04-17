import pytest

from msm.apiserver.db import models
from msm.common.settings import Settings
from msm.common.time import now_utc
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestDetailsPostHandler:
    async def test_update_details(
        self, factory: Factory, site_client: Client, api_site: models.Site
    ) -> None:
        details = {
            "name": "new-name",
            "url": "https://new-url.example.com",
            "known_config_options": ["new_config_option"],
            "version": api_site.version,
        }
        before_post = now_utc()
        response = await site_client.post("/details", json=details)
        assert response.status_code == 200
        assert not response.json()["config_options_requested"]
        [site] = await factory.get("site")
        [site_data] = await factory.get("site_data")
        assert site["name"] == "new-name"
        assert site["url"] == "https://new-url.example.com"
        assert site["known_config_options"] == ["new_config_option"]
        assert site["version"] == api_site.version
        assert before_post < site_data["last_seen"]
        assert site_data["last_seen"] < now_utc()

    async def test_update_version_requests_config_options(
        self, factory: Factory, site_client: Client
    ) -> None:
        details = {
            "version": "new.version",
        }
        response = await site_client.post("/details", json=details)
        assert response.status_code == 200
        assert response.json()["config_options_requested"]
        [site] = await factory.get("site")
        assert site["version"] == "new.version"

    async def test_creates_stats(
        self,
        factory: Factory,
        site_client: Client,
        api_site: models.Site,
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
            "/details",
            json={
                "machines_by_status": machine_counts,
                "version": api_site.version,
            },
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
        self,
        factory: Factory,
        api_site: models.Site,
        site_client: Client,
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
            "/details",
            json={
                "machines_by_status": machine_counts,
                "version": api_site.version,
            },
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
        response = await site_client.post(
            "/details", json={"version": api_site.version}
        )
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
            "/details",
            json={
                "machines_by_status": machine_counts,
                "version": api_site.version,
            },
        )
        heartbeat = Settings().heartbeat_interval_seconds
        response_heartbeat = int(
            response.headers["MSM-Heartbeat-Interval-Seconds"]
        )
        assert heartbeat == response_heartbeat

    async def test_no_version_validation_err(
        self, site_client: Client
    ) -> None:
        response = await site_client.post("/details", json={})
        assert response.status_code == 422
        detail = response.json()["error"]["details"][0]
        assert detail["reason"] == "Missing"
        assert f"Field required" in detail["messages"][0]
        assert detail["field"] == "version"
