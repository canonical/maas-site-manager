from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.db.models import (
    BootAsset,
    BootAssetItem,
    BootAssetKind,
    BootAssetLabel,
    BootAssetVersion,
    BootSource,
    BootSourceSelection,
    BootSourceSelectionUpdate,
    BootSourceUpdate,
)
from msm.service import (
    BootAssetItemService,
    BootAssetService,
    BootAssetVersionService,
    BootSourceSelectionService,
    BootSourceService,
)
from msm.time import now_utc
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestBootAssetService:
    async def test_get(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        expected_boot_asset = BootAsset(
            id=0,  # not actually used, but need to specify here for pydantic
            boot_source_id=boot_source.id,
            kind=BootAssetKind.BOOTLOADER,
            label=BootAssetLabel.CANDIDATE,
            os="test OS",
            release="test release",
            codename="test codename",
            title="test title",
            arch="test arch",
            subarch="test subarch",
            compatibility=["test", "compatibility"],
            flavor="test flavor",
            base_image="test base image",
            eol=now_utc() + timedelta(days=3650),
            esm_eol=now_utc() + timedelta(days=5000),
        )
        boot_asset = await factory.make_BootAsset(
            boot_source.id,
            expected_boot_asset.kind,
            expected_boot_asset.label,
            expected_boot_asset.os,
            expected_boot_asset.release,
            expected_boot_asset.codename,
            expected_boot_asset.title,
            expected_boot_asset.arch,
            expected_boot_asset.subarch,
            expected_boot_asset.compatibility,
            expected_boot_asset.flavor,
            expected_boot_asset.base_image,
            expected_boot_asset.eol,
            expected_boot_asset.esm_eol,
        )
        expected_boot_asset.id = boot_asset.id

        service = BootAssetService(db_connection)
        count, retrieved_boot_assets = await service.get([])
        assert count == 1
        # should only be one boot asset retrieved, but we need to loop anyway since it's an interable
        for rba in retrieved_boot_assets:
            assert rba == expected_boot_asset

    async def test_create(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        expected_boot_asset = BootAsset(
            id=0,  # not actually used, but need to specify here for pydantic
            boot_source_id=boot_source.id,
            kind=BootAssetKind.BOOTLOADER,
            label=BootAssetLabel.CANDIDATE,
            os="test OS",
            release="test release",
            codename="test codename",
            title="test title",
            arch="test arch",
            subarch="test subarch",
            compatibility=["test", "compatibility"],
            flavor="test flavor",
            base_image="test base image",
            eol=now_utc() + timedelta(days=3650),
            esm_eol=now_utc() + timedelta(days=5000),
        )
        service = BootAssetService(db_connection)
        boot_asset = await service.create(expected_boot_asset)
        expected_boot_asset.id = boot_asset.id
        assert boot_asset == expected_boot_asset
        assets = await factory.get("boot_asset")
        assert len(assets) == 1
        assert assets[0] == expected_boot_asset.model_dump()

    async def test_delete(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        expected_boot_asset = BootAsset(
            id=0,  # not actually used, but need to specify here for pydantic
            boot_source_id=boot_source.id,
            kind=BootAssetKind.BOOTLOADER,
            label=BootAssetLabel.CANDIDATE,
            os="test OS",
            release="test release",
            codename="test codename",
            title="test title",
            arch="test arch",
            subarch="test subarch",
            compatibility=["test", "compatibility"],
            flavor="test flavor",
            base_image="test base image",
            eol=now_utc() + timedelta(days=3650),
            esm_eol=now_utc() + timedelta(days=5000),
        )
        boot_asset = await factory.make_BootAsset(
            boot_source.id,
            expected_boot_asset.kind,
            expected_boot_asset.label,
            expected_boot_asset.os,
            expected_boot_asset.release,
            expected_boot_asset.codename,
            expected_boot_asset.title,
            expected_boot_asset.arch,
            expected_boot_asset.subarch,
            expected_boot_asset.compatibility,
            expected_boot_asset.flavor,
            expected_boot_asset.base_image,
            expected_boot_asset.eol,
            expected_boot_asset.esm_eol,
        )

        service = BootAssetService(db_connection)
        await service.delete(boot_asset.id)
        assets = await factory.get("boot_asset")
        assert len(assets) == 0


@pytest.mark.asyncio
class TestBootSourceSelectionService:
    async def test_get(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        expected_boot_src_selection = BootSourceSelection(
            id=0,
            boot_source_id=boot_source.id,
            label=BootAssetLabel.CANDIDATE,
            os="test os",
            release="test release",
            arches=["test", "arches"],
        )
        boot_source_selection = await factory.make_BootSourceSelection(
            boot_source.id,
            label=expected_boot_src_selection.label,
            os=expected_boot_src_selection.os,
            release=expected_boot_src_selection.release,
            arches=expected_boot_src_selection.arches,
        )

        expected_boot_src_selection.id = boot_source_selection.id

        service = BootSourceSelectionService(db_connection)
        count, retrieved_boot_src_selections = await service.get(
            boot_source.id, []
        )
        assert count == 1
        # should only be one boot asset retrieved, but we need to loop anyway since it's an interable
        for rba in retrieved_boot_src_selections:
            assert rba == expected_boot_src_selection

    async def test_create(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        boot_source = await factory.make_BootSource()
        expected_boot_src_selection = BootSourceSelection(
            id=0,
            boot_source_id=boot_source.id,
            label=BootAssetLabel.CANDIDATE,
            os="test os",
            release="test release",
            arches=["test", "arches"],
        )
        service = BootSourceSelectionService(db_connection)
        boot_src_selection = await service.create(expected_boot_src_selection)
        expected_boot_src_selection.id = boot_src_selection.id
        selections = await factory.get("boot_source_selection")
        assert len(selections) == 1
        assert selections[0] == expected_boot_src_selection.model_dump()

    async def test_update(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        expected_boot_src_selection = BootSourceSelection(
            id=0,
            boot_source_id=boot_source.id,
            label=BootAssetLabel.CANDIDATE,
            os="test os",
            release="test release",
            arches=["test", "arches"],
        )
        boot_source_selection = await factory.make_BootSourceSelection(
            boot_source.id,
            label=expected_boot_src_selection.label,
            os=expected_boot_src_selection.os,
            release=expected_boot_src_selection.release,
            arches=expected_boot_src_selection.arches,
        )

        expected_boot_src_selection.id = boot_source_selection.id

        new_boot_src_selection = BootSourceSelectionUpdate(
            label=BootAssetLabel.STABLE,
            os="new os",
        )
        expected_boot_src_selection.label = new_boot_src_selection.label  # type: ignore
        expected_boot_src_selection.os = new_boot_src_selection.os  # type: ignore

        service = BootSourceSelectionService(db_connection)
        await service.update(
            boot_source.id, boot_source_selection.id, new_boot_src_selection
        )
        selections = await factory.get("boot_source_selection")
        assert len(selections) == 1
        assert selections[0] == expected_boot_src_selection.model_dump()

    async def test_delete(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        expected_boot_src_selection = BootSourceSelection(
            id=0,
            boot_source_id=boot_source.id,
            label=BootAssetLabel.CANDIDATE,
            os="test os",
            release="test release",
            arches=["test", "arches"],
        )
        boot_source_selection = await factory.make_BootSourceSelection(
            boot_source.id,
            label=expected_boot_src_selection.label,
            os=expected_boot_src_selection.os,
            release=expected_boot_src_selection.release,
            arches=expected_boot_src_selection.arches,
        )

        service = BootSourceSelectionService(db_connection)
        await service.delete(boot_source.id, boot_source_selection.id)
        selections = await factory.get("boot_source_selection")
        assert len(selections) == 0


@pytest.mark.asyncio
class TestBootSourceService:
    async def test_get(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        expected_boot_source = BootSource(
            id=0,
            priority=1,
            url="http://some.image.server",
            keyring="test keyring",
            sync_interval=3600,
        )
        boot_source = await factory.make_BootSource(
            priority=expected_boot_source.priority,
            url=expected_boot_source.url,
            keyring=expected_boot_source.keyring,
            sync_interval=expected_boot_source.sync_interval,
        )
        expected_boot_source.id = boot_source.id

        service = BootSourceService(db_connection)
        count, retrieved_boot_sources = await service.get([])
        assert count == 1
        for rbs in retrieved_boot_sources:
            assert rbs == expected_boot_source

    async def test_create(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        expected_boot_source = BootSource(
            id=0,
            priority=1,
            url="http://some.image.server",
            keyring="test keyring",
            sync_interval=3600,
        )
        service = BootSourceService(db_connection)
        boot_source = await service.create(expected_boot_source)
        expected_boot_source.id = boot_source.id
        sources = await factory.get("boot_source")
        assert len(sources) == 1
        assert sources[0] == expected_boot_source.model_dump()

    async def test_update(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        expected_boot_source = BootSource(
            id=0,
            priority=1,
            url="http://some.image.server",
            keyring="test keyring",
            sync_interval=3600,
        )
        boot_source = await factory.make_BootSource(
            priority=expected_boot_source.priority,
            url=expected_boot_source.url,
            keyring=expected_boot_source.keyring,
            sync_interval=expected_boot_source.sync_interval,
        )
        new_boot_source = BootSourceUpdate(
            priority=2, url="http://another.image.server"
        )
        expected_boot_source.id = boot_source.id
        expected_boot_source.priority = new_boot_source.priority  # type: ignore
        expected_boot_source.url = new_boot_source.url  # type: ignore

        service = BootSourceService(db_connection)
        await service.update(boot_source.id, new_boot_source)
        retrieved_boot_sources = await factory.get("boot_source")
        assert len(retrieved_boot_sources) == 1
        assert retrieved_boot_sources[0] == expected_boot_source.model_dump()

    async def test_delete(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        expected_boot_source = BootSource(
            id=0,
            priority=1,
            url="http://some.image.server",
            keyring="test keyring",
            sync_interval=3600,
        )
        boot_source = await factory.make_BootSource(
            priority=expected_boot_source.priority,
            url=expected_boot_source.url,
            keyring=expected_boot_source.keyring,
            sync_interval=expected_boot_source.sync_interval,
        )

        service = BootSourceService(db_connection)
        await service.delete(boot_source.id)
        sources = await factory.get("boot_source")
        assert len(sources) == 0


class TestBootAssetVersionService:
    async def test_get(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        boot_asset = await factory.make_BootAsset(boot_source.id)
        expected_boot_asset_version = BootAssetVersion(
            id=0, boot_asset_id=boot_asset.id, version="20250227.1"
        )
        boot_asset_version = await factory.make_BootAssetVersion(
            boot_asset.id, version=expected_boot_asset_version.version
        )
        expected_boot_asset_version.id = boot_asset_version.id

        service = BootAssetVersionService(db_connection)
        count, retrieved_boot_asset_versions = await service.get([])
        assert count == 1
        for rbav in retrieved_boot_asset_versions:
            assert rbav == expected_boot_asset_version

    async def test_create(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        boot_asset = await factory.make_BootAsset(boot_source.id)
        expected_boot_asset_version = BootAssetVersion(
            id=0,
            boot_asset_id=boot_asset.id,
            version="20250227.1",
        )
        service = BootAssetVersionService(db_connection)
        boot_asset_version = await service.create(expected_boot_asset_version)
        expected_boot_asset_version.id = boot_asset_version.id
        versions = await factory.get("boot_asset_version")
        assert len(versions) == 1
        assert versions[0] == expected_boot_asset_version.model_dump()

    async def test_delete(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        boot_asset = await factory.make_BootAsset(boot_source.id)
        boot_asset_version = await factory.make_BootAssetVersion(
            boot_asset.id, version="20250227.1"
        )

        service = BootAssetVersionService(db_connection)
        await service.delete(boot_asset_version.id)
        versions = await factory.get("boot_asset_version")
        assert len(versions) == 0


class TestBootAssetItemService:
    async def test_get(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        boot_asset = await factory.make_BootAsset(boot_source.id)
        boot_asset_version = await factory.make_BootAssetVersion(boot_asset.id)
        expected_boot_asset_item = BootAssetItem(
            id=0,
            boot_asset_version_id=boot_asset_version.id,
            ftype="kernel",
            sha256="2349asldkfj2309854jhs",
            path="/test",
            size=23425323,
            source_package="ubukernel",
            source_version="23.2",
            source_release="Noble",
            percent_synced=100.0,
        )
        boot_asset_item = await factory.make_BootAssetItem(
            boot_asset_version.id,
            ftype="kernel",
            sha256="2349asldkfj2309854jhs",
            path="/test",
            size=23425323,
            source_package="ubukernel",
            source_version="23.2",
            source_release="Noble",
            percent_synced=100.0,
        )
        expected_boot_asset_item.id = boot_asset_item.id

        service = BootAssetItemService(db_connection)
        count, retrieved_boot_asset_items = await service.get([])
        assert count == 1
        for rbai in retrieved_boot_asset_items:
            assert rbai == expected_boot_asset_item

    async def test_create(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        boot_asset = await factory.make_BootAsset(boot_source.id)
        boot_asset_version = await factory.make_BootAssetVersion(boot_asset.id)
        expected_boot_asset_item = BootAssetItem(
            id=0,
            boot_asset_version_id=boot_asset_version.id,
            ftype="kernel",
            sha256="2349asldkfj2309854jhs",
            path="/test",
            size=23425323,
            source_package="ubukernel",
            source_version="23.2",
            source_release="Noble",
            percent_synced=100.0,
        )
        service = BootAssetItemService(db_connection)
        boot_asset_item = await service.create(expected_boot_asset_item)
        expected_boot_asset_item.id = boot_asset_item.id
        items = await factory.get("boot_asset_item")
        assert len(items) == 1
        assert items[0] == expected_boot_asset_item.model_dump()

    async def test_delete(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        boot_source = await factory.make_BootSource()
        boot_asset = await factory.make_BootAsset(boot_source.id)
        boot_asset_version = await factory.make_BootAssetVersion(boot_asset.id)
        boot_asset_item = await factory.make_BootAssetItem(
            boot_asset_version.id,
            ftype="kernel",
            sha256="2349asldkfj2309854jhs",
            path="/test",
            size=23425323,
            source_package="ubukernel",
            source_version="23.2",
            source_release="Noble",
            percent_synced=100.0,
        )

        service = BootAssetItemService(db_connection)
        await service.delete(boot_asset_item.id)
        versions = await factory.get("boot_asset_item")
        assert len(versions) == 0
