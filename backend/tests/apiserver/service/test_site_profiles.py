import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db import DEFAULT_SITE_PROFILE_ID
from msm.apiserver.db.models import (
    SiteProfile,
    SiteProfileCreate,
    SiteProfileUpdate,
)
from msm.apiserver.schema import SortParam
from msm.apiserver.service.site_profiles import SiteProfileService
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestSiteProfileService:
    async def test_get(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        prof1 = await factory.make_SiteProfile(
            name="zulu",
            selections=["ubuntu/jammy/amd64"],
            global_config={
                "use_peer_proxy": False,
                "maas_proxy_port": 8000,
                "theme": "light",
            },
        )
        prof2 = await factory.make_SiteProfile(
            name="alpha",
            selections=["ubuntu/noble/amd64"],
            global_config={
                "use_peer_proxy": True,
                "maas_proxy_port": 8001,
                "theme": "dark",
            },
        )
        service = SiteProfileService(db_connection)

        count, profiles = await service.get(
            sort_params=[SortParam(field="name", asc=False)]
        )

        assert count == 2
        assert [p for p in profiles] == [prof1, prof2]

    async def test_get_with_offset_and_limit(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_SiteProfile(
            name="alpha",
            selections=["ubuntu/jammy/amd64"],
        )
        await factory.make_SiteProfile(
            name="beta",
            selections=["ubuntu/noble/amd64"],
        )
        await factory.make_SiteProfile(
            name="charlie",
            selections=["ubuntu/resolute/amd64"],
        )
        service = SiteProfileService(db_connection)

        count, profiles = await service.get(
            sort_params=[SortParam(field="name", asc=True)],
            offset=1,
            limit=1,
        )

        assert count == 3
        assert [profile.name for profile in profiles] == ["beta"]

    async def test_get_by_id(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        profile = await factory.make_SiteProfile(
            name="profile-a",
            selections=["ubuntu/noble/amd64"],
            global_config={"key": "value"},
        )
        service = SiteProfileService(db_connection)

        found = await service.get_by_id(profile.id)
        missing = await service.get_by_id(-1)

        assert found is not None
        assert found.id == profile.id
        assert found.name == "profile-a"
        assert missing is None

    async def test_create(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        service = SiteProfileService(db_connection)

        created = await service.create(
            SiteProfileCreate(
                name="new-profile",
                selections=["ubuntu/noble/amd64"],
                global_config={
                    "use_peer_proxy": True,
                    "maas_proxy_port": 8001,
                    "theme": "dark",
                },
            )
        )

        [row] = await factory.get("site_profile")
        assert SiteProfile(
            id=created.id,
            name="new-profile",
            selections=["ubuntu/noble/amd64"],
            global_config={
                "use_peer_proxy": True,
                "maas_proxy_port": 8001,
                "theme": "dark",
            },
        ) == SiteProfile(**row)

    async def test_update(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        profile = await factory.make_SiteProfile(
            name="profile-a",
            selections=["ubuntu/jammy/amd64"],
            global_config={"feature": False},
        )
        service = SiteProfileService(db_connection)

        updated = await service.update(
            profile.id,
            SiteProfileUpdate(
                name="profile-b",
                selections=["ubuntu/noble/amd64"],
                global_config={"feature": True},
            ),
        )

        [row] = await factory.get("site_profile")
        assert updated == SiteProfile(**row)

    async def test_delete(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        profile1 = await factory.make_SiteProfile(
            name="profile-a",
            selections=["ubuntu/jammy/amd64"],
        )
        profile2 = await factory.make_SiteProfile(
            name="profile-b",
            selections=["ubuntu/noble/amd64"],
        )
        service = SiteProfileService(db_connection)

        await service.delete(profile1.id)

        rows = await factory.get("site_profile")
        assert [row["id"] for row in rows] == [profile2.id]

    async def test_ensure_creates_default_profile(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        service = SiteProfileService(db_connection)

        await service.ensure()

        [profile] = await factory.get("site_profile")
        assert profile["id"] == DEFAULT_SITE_PROFILE_ID
        assert profile["name"] == "Default Profile"
        assert profile["selections"] == ["ubuntu/resolute/amd64"]
        assert profile["global_config"] == {}

    async def test_ensure_keeps_existing_default_profile(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        await factory.make_SiteProfile(
            id=DEFAULT_SITE_PROFILE_ID,
            name="Custom Default",
            selections=["ubuntu/noble/amd64"],
            global_config={"existing": True},
        )
        service = SiteProfileService(db_connection)

        await service.ensure()

        [profile] = await factory.get("site_profile")
        assert profile["id"] == DEFAULT_SITE_PROFILE_ID
        assert profile["name"] == "Custom Default"
        assert profile["selections"] == ["ubuntu/noble/amd64"]
        assert profile["global_config"] == {"existing": True}
