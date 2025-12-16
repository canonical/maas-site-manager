from datetime import datetime, timedelta
from typing import cast
from unittest.mock import call

import pytest
from pytest_mock import MockerFixture, MockType
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db.models import (
    BootAsset,
    BootAssetCreate,
    BootAssetItem,
    BootAssetItemCreate,
    BootAssetItemUpdate,
    BootAssetUpdate,
    BootAssetVersion,
    BootAssetVersionCreate,
    BootSource,
    BootSourceCreate,
    BootSourceSelection,
    BootSourceSelectionCreate,
    BootSourceSelectionUpdate,
    BootSourceUpdate,
)
from msm.apiserver.service import (
    BootAssetItemService,
    BootAssetService,
    BootAssetVersionService,
    BootSourceSelectionService,
    BootSourceService,
    IndexService,
    S3Service,
)
from msm.common.enums import (
    BootAssetKind,
    BootAssetLabel,
    DownloadPartition,
    IndexType,
    ItemFileType,
)
from msm.common.time import now_utc
from tests.fixtures.factory import Factory


@pytest.fixture
async def single_item(
    factory: Factory, ver_ubuntu_noble_1: BootAssetVersion
) -> BootAssetItem:
    return await factory.make_BootAssetItem(
        ver_ubuntu_noble_1.id, ftype=ItemFileType.ARCHIVE_TAR_XZ
    )


@pytest.fixture
async def multi_item(
    factory: Factory, ver_ubuntu_noble_1: BootAssetVersion
) -> list[BootAssetItem]:
    return [
        await factory.make_BootAssetItem(
            ver_ubuntu_noble_1.id, ftype=ItemFileType.ARCHIVE_TAR_XZ
        ),
        await factory.make_BootAssetItem(
            ver_ubuntu_noble_1.id, ftype=ItemFileType.BOOT_DTB
        ),
    ]


@pytest.fixture
async def multi_version(
    factory: Factory,
    ver_ubuntu_noble_1: BootAssetVersion,
    ver_ubuntu_noble_2: BootAssetVersion,
) -> list[BootAssetItem]:
    return [
        await factory.make_BootAssetItem(
            ver_ubuntu_noble_1.id, ftype=ItemFileType.ARCHIVE_TAR_XZ
        ),
        await factory.make_BootAssetItem(
            ver_ubuntu_noble_2.id, ftype=ItemFileType.BOOT_DTB
        ),
    ]


@pytest.fixture
def mock_s3_service(
    mocker: MockerFixture, boot_asset_service: BootAssetService
) -> MockType:
    mock_s3 = mocker.patch.object(boot_asset_service, "s3", spec=S3Service)
    mock = mock_s3.return_value
    mock.create_multipart_upload.return_value = ("test-key", "test-upload-id")
    mock.upload_part.return_value = "test-etag"
    mock.complete_upload.return_value = None
    mock.abort_upload.return_value = None
    mock.delete_object.return_value = None
    mock.get_object.return_value = {"Body": [b"cadecafe"]}
    return cast(MockType, mock)


@pytest.mark.asyncio
class TestBootAssetService:
    async def test_get(
        self,
        boot_asset_service: BootAssetService,
        ubuntu_noble: BootAsset,
    ) -> None:
        count, [rba] = await boot_asset_service.get([])
        assert count == 1
        assert ubuntu_noble == rba

    async def test_get_null_filter(
        self,
        boot_asset_service: BootAssetService,
        boot_source_grub: BootSource,
        grub: BootAsset,
    ) -> None:
        count, assets = await boot_asset_service.get(
            [],
            boot_source_id=[boot_source_grub.id],
            kind=[grub.kind],
            label=[grub.label],
            os=[grub.os],
            arch=[grub.arch],
            release=[None],  # grub.release is None, but be explicit in test
        )
        assert count == 1
        assert next(iter(assets)) == grub

    @pytest.mark.parametrize(
        "filter_param",
        [
            ("boot_source_id"),
            ("kind"),
            ("label"),
            ("os"),
            ("arch"),
            ("release"),
        ],
    )
    async def test_get_with_filters(
        self,
        boot_asset_service: BootAssetService,
        ubuntu_noble: BootAsset,
        filter_param: str,
    ) -> None:
        filters = {filter_param: [ubuntu_noble.model_dump()[filter_param]]}
        count, [rba] = await boot_asset_service.get(
            sort_params=[], offset=0, limit=None, **filters
        )
        assert count == 1
        assert rba == ubuntu_noble

    @pytest.mark.parametrize(
        "id,exists",
        [
            (1, True),
            (-1, False),
        ],
    )
    async def test_get_by_id(
        self,
        boot_asset_service: BootAssetService,
        ubuntu_noble: BootAsset,
        id: int,
        exists: bool,
    ) -> None:
        assert await boot_asset_service.get_by_id(id) == (
            ubuntu_noble if exists else None
        )

    async def test_create(
        self,
        factory: Factory,
        boot_source: BootSource,
        boot_asset_service: BootAssetService,
    ) -> None:
        new_boot_asset = BootAssetCreate(
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
            bootloader_type="test bootloader type",
            eol=now_utc() + timedelta(days=3650),
            esm_eol=now_utc() + timedelta(days=5000),
            signed=True,
        )
        boot_asset = await boot_asset_service.create(new_boot_asset)
        expected_boot_asset = BootAsset(
            id=boot_asset.id, **new_boot_asset.model_dump()
        )
        assert boot_asset == expected_boot_asset
        assets = await factory.get("boot_asset")
        assert len(assets) == 1
        assert assets[0] == expected_boot_asset.model_dump()

    async def test_delete(
        self,
        factory: Factory,
        boot_asset_service: BootAssetService,
        ubuntu_noble: BootAsset,
    ) -> None:
        await boot_asset_service.delete(ubuntu_noble.id)
        assets = await factory.get("boot_asset")
        assert len(assets) == 0

    async def test_update(
        self,
        factory: Factory,
        boot_asset_service: BootAssetService,
        ubuntu_noble: BootAsset,
    ) -> None:
        asset_updates = BootAssetUpdate(
            kind=BootAssetKind.OS,
            label=BootAssetLabel.STABLE,
            os="ubuntu",
            release="noble",
            krel="noble",
            codename="Numbat",
            title="new title",
            arch="amd64",
            subarch="subarch",
            compatibility=["test"],
            flavor="flavor",
            base_image="ubuntu/noble",
            bootloader_type="pxe",
            eol=now_utc(),
            esm_eol=now_utc(),
            signed=False,
        )

        await boot_asset_service.update(ubuntu_noble.id, asset_updates)
        assets = await factory.get("boot_asset")
        assert len(assets) == 1
        assert assets[0] == asset_updates.model_dump() | {
            "id": ubuntu_noble.id,
            "boot_source_id": ubuntu_noble.boot_source_id,
            "version": "24.04",
        }

    async def test_delete_by_source_id(
        self,
        factory: Factory,
        boot_asset_service: BootAssetService,
        boot_source: BootSource,
        ubuntu_noble: BootAsset,
    ) -> None:
        await boot_asset_service.delete_by_source_id(boot_source.id)
        assets = await factory.get("boot_asset")
        assert len(assets) == 0

    async def test_get_many_by_id(
        self,
        boot_asset_service: BootAssetService,
        ubuntu_noble: BootAsset,
        ubuntu_jammy: BootAsset,
        centos: BootAsset,
    ) -> None:
        _, assets = await boot_asset_service.get_many_by_id(
            [ubuntu_noble.id, ubuntu_jammy.id]
        )
        assert ubuntu_noble in assets
        assert ubuntu_jammy in assets
        assert centos not in assets

    async def test_get_many_by_id_with_filters(
        self,
        boot_asset_service: BootAssetService,
        ubuntu_noble: BootAsset,
        grub: BootAsset,
    ) -> None:
        count, assets = await boot_asset_service.get_many_by_id(
            [ubuntu_noble.id, grub.id], kind=[BootAssetKind.OS]
        )
        assert count == 1
        assert next(iter(assets)) == ubuntu_noble
        count, assets = await boot_asset_service.get_many_by_id(
            [ubuntu_noble.id, grub.id], kind=[BootAssetKind.BOOTLOADER]
        )
        assert count == 1
        assert next(iter(assets)) == grub

    async def test_purge_assets(
        self,
        boot_asset_service: BootAssetService,
        ubuntu_noble: BootAsset,
        ubuntu_jammy: BootAsset,
        items_ubuntu_noble_1: list[BootAssetItem],
        items_ubuntu_noble_2: list[BootAssetItem],
        items_ubuntu_jammy_1: list[BootAssetItem],
        factory: Factory,
        mocker: MockerFixture,
    ) -> None:
        mock_refresh = mocker.patch.object(
            boot_asset_service.index_service, "refresh"
        )
        result = await boot_asset_service.purge_assets(
            [ubuntu_noble.id, ubuntu_jammy.id],
        )
        assert result == [
            i.id
            for i in items_ubuntu_noble_1
            + items_ubuntu_noble_2
            + items_ubuntu_jammy_1
        ]
        mock_refresh.assert_called_once()
        items = await factory.get("boot_asset_item")
        versions = await factory.get("boot_asset_version")
        assets = await factory.get("boot_asset")
        assert len(items) == 0
        assert len(versions) == 0
        assert len(assets) == 0


@pytest.mark.asyncio
class TestBootSourceSelectionService:
    async def test_get(
        self,
        boot_source_selection_service: BootSourceSelectionService,
        sel_ubuntu_noble: list[BootSourceSelection],
    ) -> None:
        (
            count,
            [sel1, sel2],
        ) = await boot_source_selection_service.get(
            [],
            boot_source_id=[sel_ubuntu_noble[0].boot_source_id],
        )
        assert count == 2
        assert sel_ubuntu_noble[0] == sel1
        assert sel_ubuntu_noble[1] == sel2

    @pytest.mark.parametrize(
        "filter_param",
        [
            ("boot_source_id"),
            ("os"),
            ("arch"),
            ("release"),
        ],
    )
    async def test_get_with_filters(
        self,
        boot_source_selection_service: BootSourceSelectionService,
        ubuntu_noble: BootAsset,
        centos: BootAsset,
        factory: Factory,
        filter_param: str,
    ) -> None:
        noble_sel = await factory.make_BootSourceSelection(
            ubuntu_noble.boot_source_id,
            os="ubuntu",
            release="noble",
            arch="amd64",
        )
        await factory.make_BootSourceSelection(
            centos.boot_source_id,
            os="centos",
            release="centos70",
            arch="arm64",
        )
        filters = {filter_param: [ubuntu_noble.model_dump()[filter_param]]}
        count, [sel] = await boot_source_selection_service.get(
            [],
            0,
            None,
            **filters,
        )
        assert count == 1
        assert sel == noble_sel

    async def test_create(
        self,
        factory: Factory,
        boot_source_selection_service: BootSourceSelectionService,
        boot_source: BootSource,
    ) -> None:
        new_boot_src_selection = BootSourceSelectionCreate(
            boot_source_id=boot_source.id,
            label=BootAssetLabel.CANDIDATE,
            os="test os",
            release="test release",
            arch="testarch",
            selected=True,
        )
        boot_src_selection = await boot_source_selection_service.create(
            new_boot_src_selection
        )
        expected_boot_src_selection = BootSourceSelection(
            id=boot_src_selection.id,
            **new_boot_src_selection.model_dump(),
        )
        selections = await factory.get("boot_source_selection")
        assert len(selections) == 1
        assert selections[0] == expected_boot_src_selection.model_dump()

    async def test_update(
        self,
        factory: Factory,
        boot_source_selection_service: BootSourceSelectionService,
        sel_ubuntu_noble: list[BootSourceSelection],
    ) -> None:
        new_boot_src_selection = BootSourceSelectionUpdate(
            label=BootAssetLabel.STABLE,
            os="new os",
        )
        await boot_source_selection_service.update(
            sel_ubuntu_noble[0].boot_source_id,
            sel_ubuntu_noble[0].id,
            new_boot_src_selection,
        )
        selections = await factory.get("boot_source_selection")
        assert len(selections) == 2
        assert selections[0]["os"] == "new os"

    async def test_delete(
        self,
        factory: Factory,
        boot_source_selection_service: BootSourceSelectionService,
        sel_ubuntu_noble: list[BootSourceSelection],
    ) -> None:
        await boot_source_selection_service.delete(
            sel_ubuntu_noble[0].boot_source_id, sel_ubuntu_noble[0].id
        )
        selections = await factory.get("boot_source_selection")
        assert len(selections) == 1
        assert selections[0] == sel_ubuntu_noble[1].model_dump()

    async def test_delete_by_source_id(
        self,
        factory: Factory,
        boot_source_selection_service: BootSourceSelectionService,
        sel_ubuntu_noble: list[BootSourceSelection],
    ) -> None:
        await boot_source_selection_service.delete_by_source_id(
            sel_ubuntu_noble[0].boot_source_id
        )
        selections = await factory.get("boot_source_selection")
        assert len(selections) == 0

    async def test_select_many(
        self,
        factory: Factory,
        mocker: MockerFixture,
        boot_source_selection_service: BootSourceSelectionService,
        sel_ubuntu_noble: list[BootSourceSelection],
        sel_ubuntu_jammy: list[BootSourceSelection],
    ) -> None:
        mock_trigger_sync = mocker.patch.object(
            boot_source_selection_service.workflows,
            "trigger_sync",
            autospec=True,
        )
        await boot_source_selection_service.update_many(
            [
                s.id
                for s in sel_ubuntu_jammy + sel_ubuntu_noble
                if not s.selected
            ],
            True,
        )
        selections = await factory.get("boot_source_selection")
        assert all([s["selected"] for s in selections])
        mock_trigger_sync.assert_called_once_with(
            sel_ubuntu_jammy[0].boot_source_id
        )

    async def test_deselect_many(
        self,
        factory: Factory,
        mocker: MockerFixture,
        boot_source_selection_service: BootSourceSelectionService,
        sel_ubuntu_noble: list[BootSourceSelection],
        sel_ubuntu_jammy: list[BootSourceSelection],
    ) -> None:
        mock_trigger_sync = mocker.patch.object(
            boot_source_selection_service.workflows,
            "trigger_sync",
            autospec=True,
        )
        await boot_source_selection_service.update_many(
            [s.id for s in sel_ubuntu_jammy + sel_ubuntu_noble if s.selected],
            False,
        )
        selections = await factory.get("boot_source_selection")
        assert all([not s["selected"] for s in selections])
        mock_trigger_sync.assert_called_once_with(
            sel_ubuntu_jammy[0].boot_source_id
        )

    async def test_get_many_by_id(
        self,
        boot_source_selection_service: BootSourceSelectionService,
        sel_ubuntu_noble: list[BootSourceSelection],
        sel_ubuntu_jammy: list[BootSourceSelection],
    ) -> None:
        _, selections = await boot_source_selection_service.get_many_by_id(
            [s.id for s in sel_ubuntu_noble]
        )
        assert [s for s in selections] == sel_ubuntu_noble


@pytest.mark.asyncio
class TestBootSourceService:
    async def test_get(
        self,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
    ) -> None:
        count, [rbs] = await boot_source_service.get([])
        assert count == 1
        assert rbs == boot_source_custom

    @pytest.mark.parametrize(
        "id,exists",
        [
            (1, True),
            (-1, False),
        ],
    )
    async def test_get_by_id(
        self,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
        id: int,
        exists: bool,
    ) -> None:
        assert await boot_source_service.get_by_id(id) == (
            boot_source_custom if exists else None
        )

    async def test_create(
        self,
        factory: Factory,
        mocker: MockerFixture,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
    ) -> None:
        mock_enable_sync = mocker.patch.object(
            boot_source_service.workflows, "enable_sync", autospec=True
        )
        mock_trigger_sync = mocker.patch.object(
            boot_source_service.workflows, "trigger_sync", autospec=True
        )
        new_boot_source = BootSourceCreate(
            priority=1,
            url="http://some.image.server",
            keyring="test keyring",
            sync_interval=3600,
            name="Test Boot Source",
            last_sync=factory.now,
        )
        boot_source = await boot_source_service.create(new_boot_source)
        expected_boot_source = BootSource(
            id=boot_source.id, **new_boot_source.model_dump()
        )
        sources = await factory.get("boot_source")
        assert len(sources) == 2
        assert sources[1] == expected_boot_source.model_dump()
        mock_enable_sync.assert_called_once_with(
            boot_source.id, boot_source.sync_interval
        )
        mock_trigger_sync.assert_called_once_with(boot_source.id)

    async def test_update(
        self,
        factory: Factory,
        mocker: MockerFixture,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
        boot_source: BootSource,
    ) -> None:
        mock_enable_sync = mocker.patch.object(
            boot_source_service.workflows, "enable_sync", autospec=True
        )
        mock_disable_sync = mocker.patch.object(
            boot_source_service.workflows, "disable_sync", autospec=True
        )
        new_boot_source = BootSourceUpdate(
            priority=2,
            url="http://another.image.server",
            name="Another Boot Source",
        )
        await boot_source_service.update(boot_source.id, new_boot_source)
        sources = await factory.get("boot_source")
        assert len(sources) == 2
        assert sources[1]["url"] == new_boot_source.url
        mock_disable_sync.assert_not_called()
        mock_enable_sync.assert_not_called()

    async def test_update_sync_interval(
        self,
        factory: Factory,
        mocker: MockerFixture,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
        boot_source: BootSource,
    ) -> None:
        mock_enable_sync = mocker.patch.object(
            boot_source_service.workflows, "enable_sync", autospec=True
        )
        mock_disable_sync = mocker.patch.object(
            boot_source_service.workflows, "disable_sync", autospec=True
        )
        new_boot_source = BootSourceUpdate(
            sync_interval=boot_source.sync_interval + 1
        )
        await boot_source_service.update(boot_source.id, new_boot_source)
        sources = await factory.get("boot_source")
        assert len(sources) == 2
        assert sources[1]["sync_interval"] == new_boot_source.sync_interval
        mock_disable_sync.assert_not_called()
        mock_enable_sync.assert_called_once_with(
            boot_source.id, new_boot_source.sync_interval
        )

    async def test_update_disable_sync(
        self,
        factory: Factory,
        mocker: MockerFixture,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
        boot_source: BootSource,
    ) -> None:
        mock_enable_sync = mocker.patch.object(
            boot_source_service.workflows, "enable_sync", autospec=True
        )
        mock_disable_sync = mocker.patch.object(
            boot_source_service.workflows, "disable_sync", autospec=True
        )
        new_boot_source = BootSourceUpdate(
            priority=2,
            url="http://another.image.server",
            name="Another Boot Source",
            sync_interval=0,
        )
        await boot_source_service.update(boot_source.id, new_boot_source)
        sources = await factory.get("boot_source")
        assert len(sources) == 2
        assert sources[1]["url"] == new_boot_source.url
        mock_disable_sync.assert_called_once_with(boot_source.id)
        mock_enable_sync.assert_not_called()

    async def test_update_enable_sync(
        self,
        factory: Factory,
        mocker: MockerFixture,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
    ) -> None:
        boot_source = await factory.make_BootSource(
            sync_interval=0, name="disabled"
        )
        mock_enable_sync = mocker.patch.object(
            boot_source_service.workflows, "enable_sync", autospec=True
        )
        mock_disable_sync = mocker.patch.object(
            boot_source_service.workflows, "disable_sync", autospec=True
        )
        new_boot_source = BootSourceUpdate(sync_interval=30)
        await boot_source_service.update(boot_source.id, new_boot_source)
        sources = await factory.get("boot_source")
        assert len(sources) == 2
        assert sources[1]["sync_interval"] == new_boot_source.sync_interval
        mock_disable_sync.assert_not_called()
        mock_enable_sync.assert_called_once_with(
            boot_source.id, new_boot_source.sync_interval
        )

    async def test_delete(
        self,
        factory: Factory,
        boot_source_service: BootSourceService,
        boot_source: BootSource,
    ) -> None:
        await boot_source_service.delete(boot_source.id)
        sources = await factory.get("boot_source")
        assert len(sources) == 1

    async def test_purge_source(
        self,
        factory: Factory,
        mocker: MockerFixture,
        mock_s3_service: MockType,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
        boot_source: BootSource,
        sel_ubuntu_noble: BootSourceSelection,
        single_item: BootAssetItem,
    ) -> None:
        mock_disable_sync = mocker.patch.object(
            boot_source_service.workflows, "disable_sync", autospec=True
        )
        await boot_source_service.purge_source(boot_source.id)
        mock_disable_sync.assert_called_once()
        sources = await factory.get("boot_source")
        assets = await factory.get("boot_asset")
        versions = await factory.get("boot_asset_version")
        items = await factory.get("boot_asset_item")
        selections = await factory.get("boot_source_selection")
        assert sources[0]["id"] == boot_source_custom.id
        assert assets == []
        assert versions == []
        assert items == []
        assert selections == []

    async def test_ensure_custom(
        self,
        factory: Factory,
        boot_source_service: BootSourceService,
    ) -> None:
        sources = await factory.get("boot_source")
        assert len(sources) == 0
        await boot_source_service._ensure_custom()

        sources = await factory.get("boot_source")
        assert len(sources) == 1
        assert sources[0]["keyring"] == ""
        assert sources[0]["name"] == "MSM Custom Images"
        assert sources[0]["priority"] == 1
        assert sources[0]["sync_interval"] == 0

    async def test_ensure_custom_exists(
        self,
        factory: Factory,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
    ) -> None:
        sources_before = await factory.get("boot_source")
        assert len(sources_before) == 1

        await boot_source_service._ensure_custom()
        sources_after = await factory.get("boot_source")
        assert len(sources_before) == len(sources_after)
        assert sources_after[0]["id"] == boot_source_custom.id
        assert sources_after[0]["name"] == boot_source_custom.name

    async def test_ensure_sync(
        self,
        mocker: MockerFixture,
        boot_source_service: BootSourceService,
        boot_source: BootSource,
        boot_source_custom: BootSource,
        boot_source_disabled: BootSource,
    ) -> None:
        mock_enable_sync = mocker.patch.object(
            boot_source_service.workflows, "enable_sync", autospec=True
        )

        await boot_source_service._ensure_sync()

        mock_enable_sync.assert_called()

        # Check the workflow parameters
        expected_calls = [
            call(
                boot_source.id,
                boot_source.sync_interval,
            ),
        ]
        assert mock_enable_sync.call_args_list == expected_calls

    async def test_ensure_sync_ignore_custom_source(
        self,
        mocker: MockerFixture,
        boot_source_service: BootSourceService,
        boot_source_custom: BootSource,
    ) -> None:
        mock_enable_sync = mocker.patch.object(
            boot_source_service.workflows, "enable_sync", autospec=True
        )

        await boot_source_service._ensure_sync()

        mock_enable_sync.assert_not_called()

    async def test_ensure(
        self,
        mocker: MockerFixture,
        boot_source_service: BootSourceService,
    ) -> None:
        mock__ensure_custom = mocker.patch.object(
            boot_source_service, "_ensure_custom", autospec=True
        )
        mock__ensure_sync = mocker.patch.object(
            boot_source_service, "_ensure_sync", autospec=True
        )

        await boot_source_service.ensure()

        mock__ensure_custom.assert_called_once()
        mock__ensure_sync.assert_called_once()


@pytest.mark.asyncio
class TestBootAssetVersionService:
    async def test_get(
        self,
        factory: Factory,
        boot_asset_version_service: BootAssetVersionService,
        ver_ubuntu_jammy_1: BootAssetVersion,
    ) -> None:
        count, [rbav] = await boot_asset_version_service.get([])
        assert count == 1
        assert rbav == ver_ubuntu_jammy_1

    async def test_get_by_id(
        self,
        factory: Factory,
        boot_asset_version_service: BootAssetVersionService,
        ver_ubuntu_noble_1: BootAssetVersion,
        ver_ubuntu_noble_2: BootAssetVersion,
    ) -> None:
        rbav = await boot_asset_version_service.get_by_id(
            ver_ubuntu_noble_2.id
        )
        assert rbav == ver_ubuntu_noble_2

    async def test_get_latest_version(
        self,
        factory: Factory,
        boot_asset_version_service: BootAssetVersionService,
        ver_ubuntu_noble_1: BootAssetVersion,
        ver_ubuntu_noble_2: BootAssetVersion,
    ) -> None:
        version = await boot_asset_version_service.get_latest_version(
            ver_ubuntu_noble_1.boot_asset_id
        )
        assert version is not None
        assert version == ver_ubuntu_noble_2

    @pytest.mark.parametrize(
        "filter_param",
        [("boot_asset_id"), ("version")],
    )
    async def test_get_with_filters(
        self,
        factory: Factory,
        boot_asset_version_service: BootAssetVersionService,
        ver_ubuntu_jammy_1: BootAssetVersion,
        ver_ubuntu_noble_1: BootAssetVersion,
        filter_param: str,
    ) -> None:
        count, [rbav] = await boot_asset_version_service.get(
            [],
            0,
            None,
            **{filter_param: [ver_ubuntu_jammy_1.model_dump()[filter_param]]},
        )
        assert count == 1
        assert rbav == ver_ubuntu_jammy_1

    async def test_create(
        self,
        factory: Factory,
        boot_asset_version_service: BootAssetVersionService,
        ubuntu_jammy: BootAsset,
    ) -> None:
        new_boot_asset_version = BootAssetVersionCreate(
            boot_asset_id=ubuntu_jammy.id,
            version="20250227.1",
            last_seen=factory.now,
        )
        boot_asset_version = await boot_asset_version_service.create(
            new_boot_asset_version
        )
        expected_boot_asset_version = BootAssetVersion(
            id=boot_asset_version.id,
            **new_boot_asset_version.model_dump(),
        )
        versions = await factory.get("boot_asset_version")
        assert len(versions) == 1
        assert versions[0] == expected_boot_asset_version.model_dump()

    async def test_delete(
        self,
        factory: Factory,
        boot_asset_version_service: BootAssetVersionService,
        ver_ubuntu_jammy_1: BootAssetVersion,
    ) -> None:
        await boot_asset_version_service.delete(ver_ubuntu_jammy_1.id)
        versions = await factory.get("boot_asset_version")
        assert len(versions) == 0

    async def test_delete_by_asset_id(
        self,
        factory: Factory,
        boot_asset_version_service: BootAssetVersionService,
        ubuntu_jammy: BootAsset,
    ) -> None:
        await boot_asset_version_service.delete_by_asset_id(ubuntu_jammy.id)
        versions = await factory.get("boot_asset_version")
        assert len(versions) == 0

    async def test_upsert(
        self,
        factory: Factory,
        boot_asset_version_service: BootAssetVersionService,
        ubuntu_jammy: BootAsset,
    ) -> None:
        now = factory.now

        # First upsert should insert
        new_version = BootAssetVersionCreate(
            boot_asset_id=ubuntu_jammy.id,
            version="20250227.1",
            last_seen=now,
        )
        upserted = await boot_asset_version_service.upsert(new_version)
        expected = BootAssetVersion(
            id=upserted.id,
            boot_asset_id=ubuntu_jammy.id,
            version="20250227.1",
            last_seen=now,
        )
        assert upserted == expected

        # Second upsert should update
        updated_time = now.replace(year=now.year + 1)
        updated_version = BootAssetVersionCreate(
            boot_asset_id=ubuntu_jammy.id,
            version="20250227.1",
            last_seen=updated_time,
        )
        upserted2 = await boot_asset_version_service.upsert(updated_version)
        expected2 = BootAssetVersion(
            id=upserted.id,
            boot_asset_id=ubuntu_jammy.id,
            version="20250227.1",
            last_seen=updated_time,
        )
        assert upserted2 == expected2

        # There should only be one version in the DB
        versions = await factory.get("boot_asset_version")
        assert len(versions) == 1


class TestBootAssetItemService:
    async def test_get(
        self,
        boot_asset_item_service: BootAssetItemService,
        items_ubuntu_noble_1: list[BootAssetItem],
    ) -> None:
        count, items = await boot_asset_item_service.get([])
        assert count == 3
        got = list(items)
        assert got == items_ubuntu_noble_1

    @pytest.mark.parametrize(
        "filter_param",
        [
            ("boot_asset_version_id"),
            ("ftype"),
            ("sha256"),
            ("path"),
            ("file_size"),
        ],
    )
    async def test_get_with_filters(
        self,
        boot_asset_item_service: BootAssetItemService,
        items_ubuntu_noble_1: list[BootAssetItem],
        filter_param: str,
    ) -> None:
        item = items_ubuntu_noble_1[0]
        filters = {filter_param: [item.model_dump()[filter_param]]}
        count, items = await boot_asset_item_service.get(
            [], 0, None, **filters
        )
        assert count >= 1
        assert next(iter(items)) == item

    @pytest.mark.parametrize(
        "exists",
        [
            (True),
            (False),
        ],
    )
    async def test_get_by_id(
        self,
        boot_asset_item_service: BootAssetItemService,
        items_ubuntu_noble_1: list[BootAssetItem],
        exists: bool,
    ) -> None:
        details = items_ubuntu_noble_1[0].model_dump()
        id = details["id"] if exists else -1

        assert await boot_asset_item_service.get_by_id(id) == (
            BootAssetItem(**details) if exists else None
        )

    @pytest.mark.parametrize(
        "exists",
        [
            (True),
            (False),
        ],
    )
    async def test_get_by_path(
        self,
        boot_asset_item_service: BootAssetItemService,
        ubuntu_noble: BootAsset,
        items_ubuntu_noble_1: list[BootAssetItem],
        exists: bool,
    ) -> None:
        details = items_ubuntu_noble_1[0].model_dump()
        boot_source_id = ubuntu_noble.boot_source_id
        path = details["path"] if exists else "asdf/asdf"

        assert await boot_asset_item_service.get_by_path(
            boot_source_id, path
        ) == (BootAssetItem(**details) if exists else None)

    async def test_row_count(
        self,
        boot_asset_item_service: BootAssetItemService,
        ver_ubuntu_noble_1: BootAssetVersion,
        items_ubuntu_noble_1: list[BootAssetItem],
    ) -> None:
        assert await boot_asset_item_service.row_count(
            boot_asset_version_id=[ver_ubuntu_noble_1.id]
        ) == len(items_ubuntu_noble_1)

    async def test_create(
        self,
        factory: Factory,
        boot_asset_item_service: BootAssetItemService,
        ver_ubuntu_noble_1: BootAssetVersion,
    ) -> None:
        new_boot_asset_item = BootAssetItemCreate(
            boot_asset_version_id=ver_ubuntu_noble_1.id,
            ftype=ItemFileType.ARCHIVE_TAR_XZ,
            sha256="2349asldkfj2309854jhs",
            path="/test",
            file_size=23425323,
            source_package="ubukernel",
            source_version="23.2",
            source_release="Noble",
        )
        boot_asset_item = await boot_asset_item_service.create(
            new_boot_asset_item
        )
        expected_boot_asset_item = BootAssetItem(
            id=boot_asset_item.id,
            bytes_synced=0,
            **new_boot_asset_item.model_dump(),
        )
        items = await factory.get("boot_asset_item")
        assert len(items) == 1
        assert items[0] == expected_boot_asset_item.model_dump()

    async def test_create_temporary(
        self,
        factory: Factory,
        boot_asset_item_service: BootAssetItemService,
        ver_ubuntu_noble_1: BootAssetVersion,
    ) -> None:
        boot_asset_item = await boot_asset_item_service.create_temporary(
            ver_ubuntu_noble_1.id
        )
        items = await factory.get("boot_asset_item")
        assert len(items) == 1
        assert items[0] == {
            "id": boot_asset_item.id,
            "boot_asset_version_id": ver_ubuntu_noble_1.id,
            "ftype": ItemFileType.ROOT_TGZ,
            "sha256": "",
            "path": "",
            "file_size": 0,
            "source_package": None,
            "source_version": None,
            "source_release": None,
            "bytes_synced": 0,
        }

    async def test_update(
        self,
        factory: Factory,
        boot_asset_item_service: BootAssetItemService,
        items_ubuntu_noble_1: list[BootAssetItem],
    ) -> None:
        item = items_ubuntu_noble_1[0]
        updates = BootAssetItemUpdate(
            ftype=ItemFileType.BOOT_INITRD,
            sha256="asdflkj234lkjsdlfkj23",
            path="/another-test",
            file_size=33425323,
            source_package="kern",
            source_version="34.3",
            source_release="Jammy",
            bytes_synced=23425322,
        )
        await boot_asset_item_service.update(item.id, updates)
        items = await factory.get("boot_asset_item")
        assert len(items) == len(items_ubuntu_noble_1)
        updates_dict = updates.model_dump()
        updates_dict.pop("boot_asset_version_id")
        expected_item = BootAssetItem(
            id=item.id,
            boot_asset_version_id=item.boot_asset_version_id,
            **updates_dict,
        )
        assert items[0] == expected_item.model_dump()

    async def test_delete(
        self,
        factory: Factory,
        boot_asset_item_service: BootAssetItemService,
        items_ubuntu_noble_1: list[BootAssetItem],
    ) -> None:
        item = items_ubuntu_noble_1[0]
        await boot_asset_item_service.delete(item.id)
        items = await factory.get("boot_asset_item")
        assert len(items) == len(items_ubuntu_noble_1) - 1

    async def test_update_bytes_synced(
        self,
        factory: Factory,
        boot_asset_item_service: BootAssetItemService,
        items_ubuntu_noble_1: list[BootAssetItem],
    ) -> None:
        item = items_ubuntu_noble_1[0]

        await boot_asset_item_service.update_bytes_synced(item.id, 23425323)
        items = await factory.get("boot_asset_item")
        assert items[0]["bytes_synced"] == 23425323

    async def test_delete_by_version_id(
        self,
        factory: Factory,
        boot_asset_item_service: BootAssetItemService,
        items_ubuntu_noble_1: list[BootAssetItem],
    ) -> None:
        id = items_ubuntu_noble_1[0].boot_asset_version_id
        assert id is not None
        await boot_asset_item_service.delete_by_version_id(id)
        items = await factory.get("boot_asset_item")
        assert len(items) == 0


class TestImagesIndexService:
    async def test_refresh(
        self,
        index_service: IndexService,
        items_ubuntu_jammy_1: list[BootAssetItem],
        items_ubuntu_noble_1: list[BootAssetItem],
        items_ubuntu_noble_2: list[BootAssetItem],
        items_grub: list[BootAssetItem],
        db_connection: AsyncConnection,
    ) -> None:
        await index_service.refresh()
        index = await db_connection.execute(
            text("SELECT * FROM images_index;")
        )
        expected = {
            "ubuntu/noble": {"amd64": 3, "arm64": 0},
            "ubuntu/jammy": {"amd64": 3, "arm64": 0},
            "grub-efi-signed/None": {"amd64": 0, "arm64": 2},
        }
        found_entries = {
            "ubuntu/noble": {"amd64": 0, "arm64": 0},
            "ubuntu/jammy": {"amd64": 0, "arm64": 0},
            "grub-efi-signed/None": {"amd64": 0, "arm64": 0},
        }
        for item in [x._asdict() for x in index.all()]:
            found_entries[f"{item['os']}/{item['release']}"][item["arch"]] += 1
        assert expected == found_entries

    async def test_get_index(
        self,
        index_service: IndexService,
        items_ubuntu_jammy_1: list[BootAssetItem],
        items_ubuntu_noble_1: list[BootAssetItem],
        items_grub: list[BootAssetItem],
    ) -> None:
        await index_service.refresh()
        index = await index_service.get(IndexType.INDEX, "maas.site.manager")

        expected_index = {
            "format": "index:1.0",
            "updated": index["updated"],
            "index": {
                "manager.site.maas:stream:v1:download-bootloaders": {
                    "datatype": "image-ids",
                    "format": "products:1.0",
                    "path": "streams/v1/manager.site.maas:stream:v1:download-bootloaders.json",
                    "products": [
                        "manager.site.maas.stream:1:grub-efi-signed:uefi:arm64",
                    ],
                    "updated": index["updated"],
                },
                "manager.site.maas:stream:v3:download-ubuntu": {
                    "datatype": "image-ids",
                    "format": "products:1.0",
                    "path": "streams/v1/manager.site.maas:stream:v3:download-ubuntu.json",
                    "products": [
                        "manager.site.maas.stream:v3:ubuntu:jammy:amd64:ga-22.04-generic",
                        "manager.site.maas.stream:v3:ubuntu:noble:amd64:hwe-24.04-generic",
                    ],
                    "updated": index["updated"],
                },
            },
        }
        assert index == expected_index

    async def test_get_download_index(
        self,
        mocker: MockerFixture,
        index_service: IndexService,
        items_ubuntu_jammy_1: list[BootAssetItem],
        items_ubuntu_noble_1: list[BootAssetItem],
        items_grub: list[BootAssetItem],
    ) -> None:
        mocker.patch(
            "msm.apiserver.service.images.now_utc",
            return_value=datetime.fromtimestamp(0.0),
        )

        await index_service.refresh()

        ubuntu_index = await index_service.get(
            IndexType.DOWNLOAD,
            "maas.site.manager",
            partition=DownloadPartition.UBUNTU,
        )
        expected_ubuntu = {
            "content_id": "manager.site.maas:stream:v3:download-ubuntu",
            "datatype": "image-ids",
            "format": "products:1.0",
            "products": {
                "manager.site.maas.stream:v3:ubuntu:jammy:amd64:ga-22.04-generic": {
                    "arch": "amd64",
                    "kflavor": "generic",
                    "label": "stable",
                    "os": "ubuntu",
                    "release": "jammy",
                    "krel": "jammy",
                    "release_title": "22.04 LTS",
                    "subarch": "ga-22.04",
                    "support_eol": "2027-04-21",
                    "support_esm_eol": "2032-04-21",
                    "version": "22.04",
                    "versions": {
                        "20250601": {
                            "items": {
                                "boot-initrd": {
                                    "ftype": "boot-initrd",
                                    "path": "2/20250601/ga-22.04/boot-initrd",
                                    "sha256": "abc456",
                                    "size": 465,
                                },
                                "boot-kernel": {
                                    "ftype": "boot-kernel",
                                    "path": "2/20250601/ga-22.04/boot-kernel",
                                    "sha256": "abc123",
                                    "size": 123,
                                },
                                "squashfs": {
                                    "ftype": "squashfs",
                                    "path": "2/20250601/squashfs",
                                    "sha256": "12345555",
                                    "size": 12345555,
                                },
                            },
                        }
                    },
                },
                "manager.site.maas.stream:v3:ubuntu:noble:amd64:hwe-24.04-generic": {
                    "arch": "amd64",
                    "kflavor": "generic",
                    "label": "stable",
                    "os": "ubuntu",
                    "release": "noble",
                    "krel": "noble",
                    "release_title": "24.04 LTS",
                    "subarch": "hwe-24.04",
                    "support_eol": "2029-05-31",
                    "support_esm_eol": "2034-04-25",
                    "version": "24.04",
                    "versions": {
                        "20250701": {
                            "items": {
                                "boot-initrd": {
                                    "ftype": "boot-initrd",
                                    "path": "2/20250701/hwe-24.04/boot-initrd",
                                    "sha256": "abc456",
                                    "size": 465,
                                },
                                "boot-kernel": {
                                    "ftype": "boot-kernel",
                                    "path": "2/20250701/hwe-24.04/boot-kernel",
                                    "sha256": "abc123",
                                    "size": 123,
                                },
                                "squashfs": {
                                    "ftype": "squashfs",
                                    "path": "2/20250701/squashfs",
                                    "sha256": "12345555",
                                    "size": 12345555,
                                },
                            },
                        }
                    },
                },
            },
        }
        expected_ubuntu["updated"] = ubuntu_index["updated"]
        assert ubuntu_index == expected_ubuntu

        bootloader_index = await index_service.get(
            IndexType.DOWNLOAD,
            "maas.site.manager",
            partition=DownloadPartition.BOOTLOADERS,
        )
        expected_bootloader = {
            "content_id": "manager.site.maas:stream:v1:download-bootloaders",
            "datatype": "image-ids",
            "format": "products:1.0",
            "products": {
                "manager.site.maas.stream:1:grub-efi-signed:uefi:arm64": {
                    "arch": "arm64",
                    "label": "candidate",
                    "os": "grub-efi-signed",
                    "bootloader-type": "uefi",
                    "versions": {
                        "20250401": {
                            "items": {
                                "grub2-signed": {
                                    "ftype": "archive.tar.xz",
                                    "path": "3/20250401/grub2-signed.tar.xz",
                                    "sha256": "deadbeef",
                                    "size": 8888,
                                    "src_package": "grub2-signed",
                                    "src_release": "focal",
                                    "src_version": "1.167.2+2.04-1ubuntu44.2",
                                },
                                "shim-signed": {
                                    "ftype": "archive.tar.xz",
                                    "path": "3/20250401/shim-signed.tar.xz",
                                    "sha256": "deadbeef2",
                                    "size": 7777,
                                    "src_package": "shim-signed",
                                    "src_release": "focal",
                                    "src_version": "1.167.2+2.04-1ubuntu44.2",
                                },
                            },
                        }
                    },
                }
            },
        }
        expected_bootloader["updated"] = bootloader_index["updated"]
        assert bootloader_index == expected_bootloader

        other_index = await index_service.get(
            IndexType.DOWNLOAD,
            "maas.site.manager",
            partition=DownloadPartition.OTHER,
        )
        expected_other = {
            "content_id": "manager.site.maas:stream:v1:download-other",
            "datatype": "image-ids",
            "format": "products:1.0",
            "products": {},
            "updated": other_index["updated"],
        }
        assert other_index == expected_other

    async def test_incomplete_set_not_included(
        self,
        index_service: IndexService,
        items_ubuntu_jammy_1: list[BootAssetItem],
        items_ubuntu_noble_2: list[BootAssetItem],
        items_grub: list[BootAssetItem],
    ) -> None:
        await index_service.refresh()
        index = await index_service.get(
            IndexType.INDEX, fqdn="maas.site.manager"
        )
        ubuntu_download = await index_service.get(
            IndexType.DOWNLOAD,
            fqdn="maas.site.manager",
            partition=DownloadPartition.UBUNTU,
        )
        bootloader_download = await index_service.get(
            IndexType.DOWNLOAD,
            fqdn="maas.site.manager",
            partition=DownloadPartition.BOOTLOADERS,
        )

        download_ubuntu_key = "manager.site.maas:stream:v3:download-ubuntu"
        download_bootloader_key = (
            "manager.site.maas:stream:v1:download-bootloaders"
        )

        assert download_ubuntu_key in index["index"]
        assert download_bootloader_key in index["index"]
        assert index["index"][download_ubuntu_key]["products"] == [
            "manager.site.maas.stream:v3:ubuntu:jammy:amd64:ga-22.04-generic"
        ]
        assert len(ubuntu_download["products"]) == 1
        assert len(bootloader_download["products"]) == 1
