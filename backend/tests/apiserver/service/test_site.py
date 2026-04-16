from datetime import timedelta
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db.models import (
    Coordinates,
    EnrollingSite,
    PendingSiteCreate,
    Site,
    SiteCoordinates,
    SiteDetailsUpdate,
    SiteUpdate,
)
from msm.apiserver.db.tables import Token
from msm.apiserver.service.site import SiteService
from msm.common.jwt import TokenPurpose
from msm.common.settings import Settings
from msm.common.time import now_utc
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestSiteService:
    @pytest.mark.parametrize(
        "id,exists",
        [
            (1, True),
            (-1, False),
        ],
    )
    async def test_get_by_id(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
        id: int,
        exists: bool,
    ) -> None:
        site = await factory.make_Site()
        details = site.model_dump() | {"connection_status": "unknown"}
        service = SiteService(db_connection)
        assert await service.get_by_id(id) == (
            Site(**details) if exists else None
        )

    async def test_get_by_auth_id(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        auth_id = uuid4()
        site = await factory.make_Site(auth_id=auth_id)
        details = site.model_dump() | {"connection_status": "unknown"}
        service = SiteService(db_connection)
        assert await service.get_by_auth_id(auth_id) == Site(**details)
        assert await service.get_by_auth_id(uuid4()) is None

    async def test_get_coordinates(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site1 = await factory.make_Site(
            coordinates=Coordinates(latitude=10, longitude=-1)
        )
        site2 = await factory.make_Site(
            coordinates=Coordinates(latitude=20, longitude=-2)
        )
        # pending site is not included
        await factory.make_PendingSite()
        service = SiteService(db_connection)
        assert list(await service.get_coordinates()) == [
            SiteCoordinates(
                id=site1.id, coordinates=Coordinates(latitude=10, longitude=-1)
            ),
            SiteCoordinates(
                id=site2.id, coordinates=Coordinates(latitude=20, longitude=-2)
            ),
        ]

    async def test_get_coordinates_filter(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        await factory.make_Site(
            coordinates=Coordinates(latitude=10, longitude=-1),
            city="Los Angeles",
        )
        site2 = await factory.make_Site(
            coordinates=Coordinates(latitude=20, longitude=-2), city="Atlantis"
        )
        service = SiteService(db_connection)
        assert list(await service.get_coordinates(city=["Atlantis"])) == [
            SiteCoordinates(
                id=site2.id, coordinates=Coordinates(latitude=20, longitude=-2)
            ),
        ]

    async def test_create_or_update_pending_does_exist(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        auth_id = uuid4()
        await factory.make_Token(auth_id=auth_id)
        cluster_uuid = str(uuid4())
        await factory.make_Site(cluster_uuid=cluster_uuid)
        service = SiteService(db_connection)
        pending_site = PendingSiteCreate(
            name="test_name",
            url="http://msm.example",
            cluster_uuid=cluster_uuid,
            auth_id=auth_id,
        )
        await service.create_or_update_pending(pending_site)
        db_sites = await factory.get("site")
        assert len(db_sites) == 1
        assert db_sites[0]["accepted"] == False
        pending_count, pending_sites = await service.get_pending()
        assert pending_count == 1
        for site in pending_sites:
            assert site.cluster_uuid == cluster_uuid
            assert site.url == pending_site.url
            assert site.name == pending_site.name

    async def test_create_or_update_pending_doesnt_exist(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        auth_id = uuid4()
        await factory.make_Token(auth_id=auth_id)
        cluster_uuid = str(uuid4())
        service = SiteService(db_connection)
        pending_site = PendingSiteCreate(
            name="test_name",
            url="http://msm.example",
            cluster_uuid=cluster_uuid,
            auth_id=auth_id,
        )
        site = await service.create_or_update_pending(pending_site)
        assert site.cluster_uuid == cluster_uuid
        assert site.url == pending_site.url
        assert site.name == pending_site.name

    async def test_create_pending(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        auth_id = uuid4()
        await factory.make_Token(auth_id=auth_id)
        cluster_uuid = str(uuid4())
        service = SiteService(db_connection)
        pending_site = await service.create_pending(
            PendingSiteCreate(
                name="site",
                url="https://site.example.com",
                auth_id=auth_id,
                cluster_uuid=cluster_uuid,
            )
        )
        assert pending_site.name == "site"
        assert pending_site.url == "https://site.example.com"
        assert pending_site.cluster_uuid == cluster_uuid

    async def test_create_pending_after_remove(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        auth_id = uuid4()
        await factory.make_Token(auth_id=auth_id)
        cluster_uuid = str(uuid4())
        service = SiteService(db_connection)
        orig_site = await service.create_pending(
            PendingSiteCreate(
                name="site",
                url="https://site.example.com",
                auth_id=auth_id,
                cluster_uuid=cluster_uuid,
            )
        )
        await service.delete(orig_site.id)
        new_auth_id = uuid4()
        await factory.make_Token(auth_id=new_auth_id)
        new_site = await service.create_pending(
            PendingSiteCreate(
                name="the site",
                url="https://thesite.example.com",
                auth_id=new_auth_id,
                cluster_uuid=cluster_uuid,
            )
        )
        assert new_site.id == orig_site.id
        assert new_site.cluster_uuid == cluster_uuid
        assert new_site.name == "the site"
        assert new_site.url == "https://thesite.example.com"

    async def test_create_pending_avoid_clobbing_existing(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        auth_id = uuid4()
        await factory.make_Token(auth_id=auth_id)
        cluster_uuid = str(uuid4())
        service = SiteService(db_connection)
        orig_site = await service.create_pending(
            PendingSiteCreate(
                name="site",
                url="https://site.example.com",
                auth_id=auth_id,
                cluster_uuid=cluster_uuid,
            )
        )
        new_auth_id = uuid4()
        await factory.make_Token(auth_id=new_auth_id)

        with pytest.raises(IntegrityError):
            await service.create_pending(
                PendingSiteCreate(
                    name="the site",
                    url="https://thesite.example.com",
                    auth_id=new_auth_id,
                    cluster_uuid=cluster_uuid,
                )
            )

    async def test_get_enrolling_accepted(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        auth_id = uuid4()
        site = await factory.make_Site(auth_id=auth_id)

        service = SiteService(db_connection)
        enrolling_site = cast(
            EnrollingSite, await service.get_enrolling(auth_id)
        )
        assert enrolling_site.id == site.id
        assert enrolling_site.accepted

    async def test_get_enrolling_pending(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        auth_id = uuid4()
        pending_site = await factory.make_PendingSite(auth_id=auth_id)

        service = SiteService(db_connection)
        enrolling_site = cast(
            EnrollingSite, await service.get_enrolling(auth_id)
        )
        assert enrolling_site.id == pending_site.id
        assert not enrolling_site.accepted

    async def test_get_enrolling_not_found(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        assert await service.get_enrolling(uuid4()) is None

    async def test_update_details(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        site = await factory.make_Site()
        await service.update(
            site.id,
            SiteDetailsUpdate(
                name="new-name",
                url="https://new-site.example.com",
                version="new.version",
                known_config_options=["new_option"],
            ),
        )
        [db_site] = await factory.get("site")
        assert db_site["name"] == "new-name"
        assert db_site["url"] == "https://new-site.example.com"
        assert db_site["version"] == "new.version"
        assert db_site["known_config_options"] == ["new_option"]

    async def test_update(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        site = await factory.make_Site()
        await service.update(
            site.id, SiteUpdate(city="New York", country="US")
        )
        [db_site] = await factory.get("site")
        assert db_site["city"] == "New York"
        assert db_site["country"] == "US"

    async def test_delete(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        site1 = await factory.make_Site()
        site2 = await factory.make_Site()
        await service.delete(site1.id)
        db_sites = await factory.get("site")
        assert db_sites[0]["deleted"] is not None
        assert db_sites[1]["deleted"] is None

    async def test_delete_many(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        site1 = await factory.make_Site()
        site2 = await factory.make_Site()
        site3 = await factory.make_Site()
        await service.delete_many([site1.id, site2.id])
        db_sites = await factory.get("site")
        assert db_sites[0]["deleted"] is not None
        assert db_sites[1]["deleted"] is not None
        assert db_sites[2]["deleted"] is None

    async def test_get_site_count(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        sites = [await factory.make_Site() for _ in range(5)]
        _ = [await factory.make_PendingSite() for _ in range(3)]
        await factory.make_SiteData(site_id=sites[0].id)
        await factory.make_SiteData(site_id=sites[1].id)
        await factory.make_SiteData(
            site_id=sites[2].id, last_seen=now_utc() - timedelta(days=1)
        )
        n_total, n_enroll, n_connected = await service.get_site_count()
        assert n_total == 8
        assert n_enroll == 5
        assert n_connected == 2

    async def test_get_site_count_empty(
        self,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        n_total, n_enroll, n_connected = await service.get_site_count()
        assert n_total == 0
        assert n_enroll == 0
        assert n_connected == 0

    async def test_get_machine_count(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        sites = [await factory.make_Site() for _ in range(2)]
        await factory.make_SiteData(site_id=sites[0].id, machines_allocated=3)
        await factory.make_SiteData(
            site_id=sites[1].id, machines_allocated=3, machines_ready=1
        )
        stats = await service.get_machine_count()
        assert stats["allocated"] == 6
        assert stats["deployed"] == 0
        assert stats["ready"] == 1
        assert stats["error"] == 0
        assert stats["other"] == 0
        assert stats["total"] == 7

    async def test_get_machine_count_empty(
        self,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        stats = await service.get_machine_count()
        assert stats["allocated"] == 0
        assert stats["deployed"] == 0
        assert stats["ready"] == 0
        assert stats["error"] == 0
        assert stats["other"] == 0
        assert stats["total"] == 0

    async def test_get_machine_count_stale(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteService(db_connection)
        sites = [await factory.make_Site() for _ in range(2)]
        await factory.make_SiteData(site_id=sites[0].id, machines_allocated=3)
        await factory.make_SiteData(
            site_id=sites[1].id,
            machines_allocated=3,
            machines_ready=1,
            last_seen=now_utc() - timedelta(days=1),
        )
        stats = await service.get_machine_count()
        assert stats["allocated"] == 3
        assert stats["deployed"] == 0
        assert stats["ready"] == 0
        assert stats["error"] == 0
        assert stats["other"] == 0
        assert stats["total"] == 3

    async def test_metric_heartbeat_skew(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        last = timedelta(seconds=Settings().heartbeat_interval_seconds)
        now = now_utc()
        service = SiteService(db_connection)
        site = await factory.make_Site()
        await factory.make_SiteData(site_id=site.id, last_seen=now - last)
        await service.update_last_seen(site.id, now, update_metrics=True)
        skew = service._registry.get_sample_value("site_heartbeat_skew_sum")
        assert skew == 0.0

    async def test_metric_heartbeat_skew_delayed(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        intval = Settings().heartbeat_interval_seconds
        last = timedelta(seconds=intval * 2)
        now = now_utc()
        service = SiteService(db_connection)
        site = await factory.make_Site()
        await factory.make_SiteData(site_id=site.id, last_seen=now - last)
        await service.update_last_seen(site.id, now, update_metrics=True)
        skew = service._registry.get_sample_value("site_heartbeat_skew_sum")
        assert skew == intval

    async def test_remove_old_tokens(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site = await factory.make_Site()
        auth_ids = [uuid4() for _ in range(2)]
        for id in auth_ids:
            await factory.make_Token(
                site_id=site.id, auth_id=id, purpose=TokenPurpose.ACCESS
            )

        assert (
            await factory.count(
                "token",
                Token.c.site_id == site.id,
                Token.c.purpose == TokenPurpose.ACCESS,
            )
            == 2
        )
        service = SiteService(db_connection)
        await service.remove_old_tokens(site.id, auth_ids[-1])
        db_tokens = await factory.get(
            "token",
            Token.c.site_id == site.id,
            Token.c.purpose == TokenPurpose.ACCESS,
        )
        assert len(db_tokens) == 1
        assert db_tokens[0]["auth_id"] == auth_ids[-1]
