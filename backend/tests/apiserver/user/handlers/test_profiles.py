from collections.abc import Callable
from typing import Any

import pytest

from msm.apiserver.db import DEFAULT_SITE_PROFILE_ID
from msm.apiserver.db.models import BootSourceSelection
from msm.apiserver.db.models.global_site_config import SiteConfigFactory
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestProfilesGetHandler:
    async def test_get(self, user_client: Client, factory: Factory) -> None:
        """Test GET /profiles returns all profiles."""
        profile1 = await factory.make_SiteProfile(
            name="Test Profile 1",
            selections=["ubuntu/jammy/amd64"],
            global_config={},
        )
        profile2 = await factory.make_SiteProfile(
            name="Test Profile 2",
            selections=["ubuntu/noble/amd64"],
            global_config={},
        )

        response = await user_client.get("/profiles")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert data["page"] == 1
        assert data["size"] == 20
        assert len(data["items"]) == 2

    async def test_get_with_pagination(
        self, user_client: Client, factory: Factory
    ) -> None:
        """Test GET /profiles with pagination."""
        # Create test profiles
        await factory.make_SiteProfile(
            name="Profile A", selections=["ubuntu/jammy/amd64"]
        )
        await factory.make_SiteProfile(
            name="Profile B", selections=["ubuntu/noble/amd64"]
        )

        response = await user_client.get("/profiles?page=1&size=1")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 1
        assert len(data["items"]) == 1

    async def test_get_by_id(
        self, user_client: Client, factory: Factory
    ) -> None:
        """Test GET /profiles/{id} returns a specific profile with all global config options."""
        profile = await factory.make_SiteProfile(
            name="Test Profile",
            selections=["ubuntu/jammy/amd64"],
        )

        response = await user_client.get(f"/profiles/{profile.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile.id
        assert data["name"] == "Test Profile"
        assert data["selections"] == ["ubuntu/jammy/amd64"]

        expected_config_keys = set(SiteConfigFactory.DEFAULT_CONFIG.keys())
        actual_config_keys = set(data["global_config"].keys())

        assert actual_config_keys == expected_config_keys, (
            f"Missing config keys: {expected_config_keys - actual_config_keys}, "
            f"Extra config keys: {actual_config_keys - expected_config_keys}"
        )

        for key, expected_value in SiteConfigFactory.DEFAULT_CONFIG.items():
            assert data["global_config"][key] == expected_value, (
                f"Config key '{key}' has value {data['global_config'][key]} "
                f"but expected {expected_value}"
            )

    async def test_get_by_id_not_found(
        self, user_client: Client, factory: Factory
    ) -> None:
        """Test GET /profiles/{id} returns 404 for non-existent profile."""
        response = await user_client.get("/profiles/99999")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "MissingResource"
        assert "does not exist" in data["error"]["message"]

    @pytest.mark.parametrize(
        "page,size", [(1, 0), (0, 1), (-1, -1), (1, 1001)]
    )
    async def test_get_422(
        self, user_client: Client, page: int, size: int
    ) -> None:
        """Test GET /profiles returns 422 for invalid pagination params."""
        response = await user_client.get(f"/profiles?page={page}&size={size}")
        assert response.status_code == 422


@pytest.mark.asyncio
class TestProfilesPostHandler:
    @pytest.mark.parametrize(
        "name,selections,global_config,expected_config_check",
        [
            (
                "New Profile",
                ["ubuntu/jammy/amd64"],
                {"theme": "dark"},
                lambda cfg: cfg.get("theme") == "dark",
            ),
            (
                "Minimal Profile",
                ["ubuntu/noble/amd64"],
                None,
                lambda cfg: all(
                    cfg.get(key) == value
                    for key, value in SiteConfigFactory.DEFAULT_CONFIG.items()
                ),
            ),
            (
                "Empty Config Profile",
                ["ubuntu/jammy/amd64"],
                {},
                lambda cfg: all(
                    cfg.get(key) == value
                    for key, value in SiteConfigFactory.DEFAULT_CONFIG.items()
                ),
            ),
            (
                "Multiple Existing Selections",
                ["ubuntu/jammy/amd64", "ubuntu/noble/amd64"],
                None,
                lambda cfg: all(
                    cfg.get(key) == value
                    for key, value in SiteConfigFactory.DEFAULT_CONFIG.items()
                ),
            ),
        ],
    )
    async def test_post_success(
        self,
        user_client: Client,
        factory: Factory,
        sel_ubuntu_jammy: list[BootSourceSelection],
        sel_ubuntu_noble: list[BootSourceSelection],
        name: str,
        selections: list[str],
        global_config: dict[str, Any] | None,
        expected_config_check: Callable[[Any], bool],
    ) -> None:
        """Test POST /profiles successfully creates profiles with valid selections."""
        data: dict[str, Any] = {
            "name": name,
            "selections": selections,
        }
        if global_config is not None:
            data["global_config"] = global_config

        response = await user_client.post("/profiles", json=data)
        assert response.status_code == 201

        result = response.json()
        assert result["name"] == name
        assert result["selections"] == selections
        assert expected_config_check(result["global_config"])
        assert "id" in result

    @pytest.mark.parametrize(
        "name,selections,expected_error_text",
        [
            (
                "Nonexistent Selection",
                ["nonexistent/release/arch"],
                "do not exist",
            ),
            (
                "Mixed Selections",
                ["ubuntu/noble/amd64", "nonexistent/release/arch"],
                "nonexistent/release/arch",
            ),
            (
                "Multiple Nonexistent Selections",
                ["nonexistent1/release/arch", "nonexistent2/other/i386"],
                "do not exist",
            ),
        ],
    )
    async def test_post_with_nonexistent_selections(
        self,
        user_client: Client,
        factory: Factory,
        sel_ubuntu_jammy: list[BootSourceSelection],
        sel_ubuntu_noble: list[BootSourceSelection],
        name: str,
        selections: list[str],
        expected_error_text: str,
    ) -> None:
        """Test POST /profiles returns 404 when selections don't exist in database."""
        data: dict[str, Any] = {
            "name": name,
            "selections": selections,
        }

        response = await user_client.post("/profiles", json=data)
        assert response.status_code == 404

        result = response.json()
        assert expected_error_text.lower() in str(result).lower()

    @pytest.mark.parametrize(
        "data,expected_error_text",
        [
            (
                {"selections": ["ubuntu/jammy/amd64"]},
                None,  # Missing name
            ),
            (
                {"name": "No Selections Profile"},
                None,
            ),
            (
                {"name": "Empty Selections", "selections": []},
                None,
            ),
            (
                {
                    "name": "Invalid Selections",
                    "selections": [
                        "ubuntu/jammy/amd64",
                        "",
                        "ubuntu/noble/amd64",
                    ],
                },
                None,
            ),
            (
                {"name": "Invalid Format", "selections": ["ubuntu/jammy"]},
                "string should match pattern",
            ),
            (
                {"name": "Empty Parts", "selections": ["ubuntu//amd64"]},
                "string should match pattern",
            ),
            (
                {
                    "name": "Invalid Config Key",
                    "selections": ["ubuntu/jammy/amd64"],
                    "global_config": {"invalid_key": "value"},
                },
                "Invalid global_config keys: invalid_key",
            ),
            (
                {
                    "name": "Invalid Config Value",
                    "selections": ["ubuntu/jammy/amd64"],
                    "global_config": {"maas_proxy_port": 99999},
                },
                "maas_proxy_port",  # Invalid value (port out of range)
            ),
        ],
    )
    async def test_post_format_validation_failures(
        self,
        user_client: Client,
        factory: Factory,
        data: dict[str, Any],
        expected_error_text: str | None,
    ) -> None:
        """Test POST /profiles returns errors for format/schema validation failures."""
        response = await user_client.post("/profiles", json=data)
        assert response.status_code == 422

        if expected_error_text:
            result = response.json()
            assert expected_error_text.lower() in str(result).lower()


@pytest.mark.asyncio
class TestProfilesDeleteHandler:
    async def test_delete(self, user_client: Client, factory: Factory) -> None:
        profile = await factory.make_SiteProfile(
            name="Test Profile to Delete",
            selections=["ubuntu/jammy/amd64"],
        )

        response = await user_client.delete(f"/profiles/{profile.id}")
        assert response.status_code == 204

        rows = await factory.get("site_profile")
        profile_ids = [row["id"] for row in rows]
        assert profile.id not in profile_ids

    async def test_delete_not_found(
        self, user_client: Client, factory: Factory
    ) -> None:
        response = await user_client.delete("/profiles/99999")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "MissingResource"

    async def test_delete_default_profile(
        self, user_client: Client, factory: Factory
    ) -> None:
        """Test that deleting the default profile is not allowed."""
        await factory.make_SiteProfile(
            id=DEFAULT_SITE_PROFILE_ID,
            name="Default Profile",
            selections=["ubuntu/jammy/amd64"],
        )

        response = await user_client.delete(
            f"/profiles/{DEFAULT_SITE_PROFILE_ID}"
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "InvalidParameters"

        rows = await factory.get("site_profile")
        profile_ids = [row["id"] for row in rows]
        assert DEFAULT_SITE_PROFILE_ID in profile_ids
