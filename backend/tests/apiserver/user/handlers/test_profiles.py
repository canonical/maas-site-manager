import pytest

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
            selections=["ubuntu/focal/amd64"],
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
            name="Profile B", selections=["ubuntu/focal/amd64"]
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
