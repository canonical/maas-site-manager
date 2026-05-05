from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db import models
from msm.apiserver.service.site_profiles import SiteProfileService
from msm.apiserver.utils import desired_config, hash_desired_config
from msm.common.jwt import TokenAudience, TokenPurpose
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
        assert response.json()["config_hash"] == ""
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

    async def test_config_hash_empty_without_profile(
        self, factory: Factory, api_site: models.Site, site_client: Client
    ) -> None:
        response = await site_client.post(
            "/details", json={"version": api_site.version}
        )
        assert response.status_code == 200
        assert response.json()["config_hash"] == ""

    async def test_config_hash_non_empty_with_profile(
        self, factory: Factory, site_client: Client
    ) -> None:
        site_auth_id = uuid4()
        profile = await factory.make_SiteProfile(
            name="hash-test",
            selections=["ubuntu/jammy/amd64"],
            global_config={"theme": "dark"},
        )
        site = await factory.make_Site(
            auth_id=site_auth_id,
            site_profile_id=profile.id,
        )
        site_client.authenticate(
            site_auth_id,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )

        response = await site_client.post(
            "/details", json={"version": site.version}
        )
        assert response.status_code == 200
        config_hash = response.json()["config_hash"]
        assert len(config_hash) == 64
        assert config_hash != ""

    async def test_config_hash_is_stable(
        self, factory: Factory, site_client: Client
    ) -> None:
        site_auth_id = uuid4()
        profile = await factory.make_SiteProfile(
            name="stable-hash",
            selections=["ubuntu/noble/amd64"],
            global_config={},
        )
        site = await factory.make_Site(
            auth_id=site_auth_id,
            site_profile_id=profile.id,
        )
        site_client.authenticate(
            site_auth_id,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )

        r1 = await site_client.post("/details", json={"version": site.version})
        r2 = await site_client.post("/details", json={"version": site.version})
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["config_hash"] == r2.json()["config_hash"]
        assert r1.json()["config_hash"] != ""

    async def test_config_hash_changes_with_different_trigger_image_sync(
        self, factory: Factory, site_client: Client
    ) -> None:
        profile = await factory.make_SiteProfile(
            name="sync-hash",
            selections=["ubuntu/jammy/amd64"],
            global_config={},
        )

        site_auth_id_a = uuid4()
        site_a = await factory.make_Site(
            auth_id=site_auth_id_a,
            site_profile_id=profile.id,
            trigger_image_sync=False,
        )
        site_auth_id_b = uuid4()
        site_b = await factory.make_Site(
            auth_id=site_auth_id_b,
            site_profile_id=profile.id,
            trigger_image_sync=True,
        )

        site_client.authenticate(
            site_auth_id_a,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )
        r_a = await site_client.post(
            "/details", json={"version": site_a.version}
        )

        site_client.authenticate(
            site_auth_id_b,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )
        r_b = await site_client.post(
            "/details", json={"version": site_b.version}
        )

        assert r_a.status_code == 200
        assert r_b.status_code == 200
        assert r_a.json()["config_hash"] != r_b.json()["config_hash"]

    async def test_config_hash_matches_stored_preimage(
        self,
        factory: Factory,
        site_client: Client,
        db_connection: AsyncConnection,
    ) -> None:
        site_auth_id = uuid4()
        profile = await factory.make_SiteProfile(
            name="alignment-test",
            selections=["ubuntu/jammy/amd64", "ubuntu/noble/amd64"],
            global_config={"theme": "dark"},
        )
        site = await factory.make_Site(
            auth_id=site_auth_id,
            site_profile_id=profile.id,
            trigger_image_sync=True,
        )
        site_client.authenticate(
            site_auth_id,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )

        heartbeat_response = await site_client.post(
            "/details", json={"version": site.version}
        )
        assert heartbeat_response.status_code == 200

        profile_service = SiteProfileService(db_connection)
        stored = await profile_service.get_stored_by_site_id(site.id)
        assert stored is not None
        preimage = desired_config(stored, site.trigger_image_sync)
        assert preimage is not None
        expected_hash = hash_desired_config(preimage)
        assert heartbeat_response.json()["config_hash"] == expected_hash

    async def test_config_hash_retains_upstream_dns_order(
        self,
        factory: Factory,
        site_client: Client,
        db_connection: AsyncConnection,
    ) -> None:
        site_auth_id = uuid4()
        profile = await factory.make_SiteProfile(
            name="alignment-test",
            selections=["ubuntu/jammy/amd64", "ubuntu/noble/amd64"],
            global_config={
                "theme": "dark",
                "upstream_dns": ["2.2.2.2", "1.1.1.1"],
                "maas_auto_ipmi_workaround_flags": ["b", "a"],
            },
        )
        site = await factory.make_Site(
            auth_id=site_auth_id,
            site_profile_id=profile.id,
            trigger_image_sync=True,
        )
        site_client.authenticate(
            site_auth_id,
            token_audience=TokenAudience.SITE,
            token_purpose=TokenPurpose.ACCESS,
        )

        heartbeat_response = await site_client.post(
            "/details", json={"version": site.version}
        )
        assert heartbeat_response.status_code == 200

        profile_service = SiteProfileService(db_connection)
        stored = await profile_service.get_stored_by_site_id(site.id)
        assert stored is not None
        preimage = desired_config(stored, site.trigger_image_sync)
        assert preimage is not None
        assert preimage["global_config"]["upstream_dns"] == [
            "2.2.2.2",
            "1.1.1.1",
        ]
        assert preimage["global_config"][
            "maas_auto_ipmi_workaround_flags"
        ] == ["a", "b"]
        expected_hash = hash_desired_config(preimage)
        assert heartbeat_response.json()["config_hash"] == expected_hash
