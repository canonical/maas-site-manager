from collections.abc import Iterable
from datetime import MAXYEAR, UTC, datetime
from typing import Any

from sqlalchemy import (
    Select,
    and_,
    delete,
    desc,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncConnection
from temporalio.service import RPCError

from msm.apiserver.db import (
    CUSTOM_IMAGE_SOURCE_ID,
    models,
    queries,
)
from msm.apiserver.db.tables import (
    BootAsset,
    BootAssetItem,
    BootAssetVersion,
    BootSource,
    BootSourceSelection,
)
from msm.apiserver.schema import SortParam
from msm.apiserver.service.base import Service
from msm.apiserver.service.s3 import S3Service
from msm.apiserver.service.settings import SettingsService
from msm.apiserver.service.temporal import (
    BootSourceWorkflowService,
)
from msm.common.enums import (
    BootAssetKind,
    BootAssetLabel,
    DownloadPartition,
    IndexType,
    ItemFileType,
)
from msm.common.time import now_utc, utc_from_timestamp

END_OF_TIME = datetime(MAXYEAR, 12, 31, 23, tzinfo=UTC)

BOOT_SELECTION_REFRESH_INTVAL = 5


class BootSourceService(Service):
    def __init__(
        self,
        connection: AsyncConnection,
        boot_assets: "BootAssetService",
        boot_source_selections: "BootSourceSelectionService",
        settings: SettingsService,
        workflows: BootSourceWorkflowService,
    ):
        super().__init__(connection)
        self.boot_assets = boot_assets
        self.boot_source_selections = boot_source_selections
        self.settings = settings
        self.workflows = workflows

    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[int, Iterable[models.BootSource]]:
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        stmt = self._select_all(BootSource).order_by(*order_by).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return result.rowcount, self.objects_from_result(
            models.BootSource, result
        )

    async def get_by_id(self, id: int) -> models.BootSource | None:
        stmt = self._select_all(BootSource).where(BootSource.c.id == id)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootSource(**row._asdict())
        return None

    async def update(
        self, boot_source_id: int, details: models.BootSourceUpdate
    ) -> models.BootSource:
        data = details.model_dump(exclude_none=True)
        stmt = (
            update(BootSource)
            .where(BootSource.c.id == boot_source_id)
            .values(data)
            .returning(*BootSource.c.values())
        )
        result = await self.conn.execute(stmt)
        boot_source = models.BootSource(**result.one()._asdict())
        if details.sync_interval == 0:
            try:
                await self.workflows.disable_sync(boot_source.id)
            except RPCError:
                # If the previous sync_interval was 0, the schedule won't exist
                # so ignore error thrown trying to disable it
                pass
        elif details.sync_interval is not None:
            await self.workflows.enable_sync(
                boot_source_id, boot_source.sync_interval
            )
        return boot_source

    async def create(
        self, details: models.BootSourceCreate
    ) -> models.BootSource:
        data = details.model_dump()
        stmt = insert(BootSource).returning(*BootSource.c.values())
        result = await self.conn.execute(
            stmt,
            [data],
        )
        boot_source = models.BootSource(**result.one()._asdict())
        if boot_source.sync_interval:
            await self.workflows.enable_sync(
                boot_source.id, boot_source.sync_interval
            )
            await self.workflows.trigger_sync(boot_source.id)
        return boot_source

    async def delete(self, boot_source_id: int) -> None:
        stmt = delete(BootSource).where(BootSource.c.id == boot_source_id)
        await self.conn.execute(stmt)

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(BootSource)

    async def _ensure_custom(self) -> None:
        """
        Ensure that the custom image boot source is present in the database.
        """
        service_url = await self.settings.get_service_url()

        stmt = self._select_statement(
            BootSource.c.id,
            BootSource.c.url,
        ).where(BootSource.c.id == CUSTOM_IMAGE_SOURCE_ID)
        result = await self.conn.execute(stmt)
        if result.one_or_none():
            # update the custom source url in case the MSM url has changed
            await self.update(
                CUSTOM_IMAGE_SOURCE_ID,
                models.BootSourceUpdate(url=service_url),
            )
            return
        data = {
            "id": CUSTOM_IMAGE_SOURCE_ID,
            "url": service_url,
            "keyring": "",
            "name": "MSM Custom Images",
            "sync_interval": 0,
            "priority": 1,
            "last_sync": utc_from_timestamp(0.0),
        }
        await self.conn.execute(insert(BootSource), [data])

    async def _ensure_sync(self) -> None:
        """Start synchronization workflows for enabled boot sources."""
        count, sources = await self.get([])
        if count <= 1:  # ignore custom images source
            return

        active = filter(lambda x: x.sync_interval > 0, sources)
        for source in active:
            await self.workflows.enable_sync(
                source.id,
                source.sync_interval,
            )

    async def ensure(self) -> None:
        """
        Ensure that the boot source service is properly initialized.

        This method performs initialization tasks including setting up the custom
        image source and enabling synchronization workflows for boot sources.
        """
        await super().ensure()
        await self._ensure_custom()
        await self._ensure_sync()

    async def purge_source(self, id: int) -> list[int]:
        """
        Purge all data associated with a boot source.

        This method completely removes a boot source and all its associated data,
        including disabling synchronization, purging all boot assets, removing
        boot source selections, and finally deleting the boot source itself.

        Args:
            id: The ID of the boot source to purge.
        Returns:
            list[int]: A list of Boot Asset Item IDs that need to be deleted
            from storage.
        """
        await self.workflows.disable_sync(id)
        _, assets = await self.boot_assets.get([], boot_source_id=[id])
        ids_to_delete = await self.boot_assets.purge_assets(
            [a.id for a in assets]
        )
        await self.boot_source_selections.delete_by_source_id(id)
        await self.delete(id)
        return ids_to_delete


class BootSourceSelectionService(Service):
    def __init__(
        self,
        connection: AsyncConnection,
        workflows: BootSourceWorkflowService,
    ):
        super().__init__(connection)
        self.workflows = workflows

    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
        boot_source_id: list[int] | None = None,
        os: list[str] | None = None,
        release: list[str] | None = None,
        arch: list[str] | None = None,
    ) -> tuple[int, Iterable[models.BootSourceSelection]]:
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        filters = queries.filters_from_arguments(
            BootSourceSelection,
            boot_source_id=boot_source_id,
            os=os,
            release=release,
            arch=arch,
        )
        count = await queries.row_count(
            self.conn, BootSourceSelection, *filters
        )
        stmt = (
            self._select_all(BootSourceSelection)
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(
            models.BootSourceSelection, result
        )

    async def get_many_by_id(
        self,
        ids: list[int],
    ) -> tuple[int, Iterable[models.BootSourceSelection]]:
        filters = [BootSourceSelection.c.id.in_(ids)]
        count = await queries.row_count(
            self.conn, BootSourceSelection, *filters
        )
        stmt = self._select_all(BootSourceSelection).where(*filters)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(
            models.BootSourceSelection, result
        )

    async def update_many(
        self,
        ids: list[int],
        select: bool,
    ) -> None:
        stmt = (
            update(BootSourceSelection)
            .where(BootSourceSelection.c.id.in_(ids))
            .values({"selected": select})
            .returning(BootSourceSelection.c.boot_source_id)
        )
        result = await self.conn.execute(stmt)
        unique_ids = set(
            int(r._asdict()["boot_source_id"]) for r in result.all()
        )
        for id in unique_ids:
            await self.workflows.trigger_sync(id)

    async def update(
        self,
        boot_source_id: int,
        selection_id: int,
        details: models.BootSourceSelectionUpdate,
    ) -> models.BootSourceSelection:
        data = details.model_dump(exclude_none=True)
        stmt = (
            update(BootSourceSelection)
            .where(
                and_(
                    BootSourceSelection.c.id == selection_id,
                    BootSourceSelection.c.boot_source_id == boot_source_id,
                )
            )
            .values(data)
            .returning(*BootSourceSelection.c.values())
        )
        result = await self.conn.execute(stmt)
        return models.BootSourceSelection(**result.one()._asdict())

    async def create(
        self, details: models.BootSourceSelectionCreate
    ) -> models.BootSourceSelection:
        data = details.model_dump()
        stmt = insert(BootSourceSelection).returning(
            *BootSourceSelection.c.values()
        )
        result = await self.conn.execute(
            stmt,
            [data],
        )
        return models.BootSourceSelection(**result.one()._asdict())

    async def delete(self, boot_source_id: int, selection_id: int) -> None:
        stmt = delete(BootSourceSelection).where(
            and_(
                BootSourceSelection.c.id == selection_id,
                BootSourceSelection.c.boot_source_id == boot_source_id,
            )
        )
        await self.conn.execute(stmt)

    async def delete_by_source_id(self, boot_source_id: int) -> None:
        stmt = delete(BootSourceSelection).where(
            BootSourceSelection.c.boot_source_id == boot_source_id
        )
        await self.conn.execute(stmt)


class BootAssetService(Service):
    def __init__(
        self,
        connection: AsyncConnection,
        s3: S3Service,
        boot_asset_versions: "BootAssetVersionService",
        boot_asset_items: "BootAssetItemService",
        index_service: "IndexService",
    ):
        super().__init__(connection)
        self.s3 = s3
        self.boot_asset_versions = boot_asset_versions
        self.boot_asset_items = boot_asset_items
        self.index_service = index_service

    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
        boot_source_id: list[int] | None = None,
        kind: list[BootAssetKind] | None = None,
        label: list[BootAssetLabel] | None = None,
        os: list[str] | None = None,
        arch: list[str] | None = None,
        release: list[str | None] | None = None,
        version: list[str | None] | None = None,
        krel: list[str | None] | None = None,
        bootloader_type: list[str | None] | None = None,
    ) -> tuple[int, Iterable[models.BootAsset]]:
        filters = queries.filters_from_arguments(
            BootAsset,
            boot_source_id=boot_source_id,
            kind=kind,
            label=label,
            os=os,
            arch=arch,
            release=release,
            version=version,
            krel=krel,
            bootloader_type=bootloader_type,
        )
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        count = await queries.row_count(self.conn, BootAsset, *filters)
        stmt = (
            self._select_all(BootAsset)
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.BootAsset, result)

    async def get_many_by_id(
        self,
        ids: list[int],
        kind: list[BootAssetKind] | None = None,
    ) -> tuple[int, Iterable[models.BootAsset]]:
        filters = queries.filters_from_arguments(
            BootAsset,
            kind=kind,
        )
        filters.append(BootAsset.c.id.in_(ids))
        count = await queries.row_count(self.conn, BootAsset, *filters)
        stmt = self._select_all(BootAsset).where(*filters)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.BootAsset, result)

    async def get_by_id(self, id: int) -> models.BootAsset | None:
        stmt = self._select_all(BootAsset).where(BootAsset.c.id == id)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAsset(**row._asdict())
        return None

    async def create(
        self,
        details: models.BootAssetCreate,
    ) -> models.BootAsset:
        data = details.model_dump()
        stmt = insert(BootAsset).returning(*BootAsset.c.values())
        result = await self.conn.execute(stmt, [data])
        return models.BootAsset(**result.one()._asdict())

    async def update(
        self, id: int, details: models.BootAssetUpdate
    ) -> models.BootAsset:
        data = details.model_dump(exclude_none=True)
        stmt = (
            update(BootAsset)
            .where(BootAsset.c.id == id)
            .values(data)
            .returning(*BootAsset.c.values())
        )
        result = await self.conn.execute(stmt)
        return models.BootAsset(**result.one()._asdict())

    async def delete(self, boot_asset_id: int) -> None:
        stmt = delete(BootAsset).where(BootAsset.c.id == boot_asset_id)
        await self.conn.execute(stmt)

    async def delete_by_source_id(self, boot_source_id: int) -> None:
        stmt = delete(BootAsset).where(
            BootAsset.c.boot_source_id == boot_source_id
        )
        await self.conn.execute(stmt)

    async def get_or_create(
        self, asset: models.BootAssetCreate
    ) -> tuple[bool, models.BootAsset]:
        count, assets = await self.get(
            [],
            boot_source_id=[asset.boot_source_id],
            kind=[asset.kind],
            label=[asset.label],
            os=[asset.os],
            arch=[asset.arch],
            release=[asset.release],
            krel=[asset.krel],
        )
        if count == 0:
            return True, await self.create(asset)
        return False, next(iter(assets))

    async def purge_assets(
        self,
        asset_ids: list[int],
    ) -> list[int]:
        """
        Purge all data associated with a list of Boot Assets.

        Args:
            asset_ids: The IDs of the Boot Assets to purge.
        Returns:
            list[int]: A list of Boot Asset Item IDs that need to be deleted
            from storage.
        """
        ids_to_delete: list[int] = []
        for id in asset_ids:
            if asset := await self.get_by_id(id):
                _, versions = await self.boot_asset_versions.get(
                    [], boot_asset_id=[asset.id]
                )
                for version in versions:
                    _, items = await self.boot_asset_items.get(
                        [], boot_asset_version_id=[version.id]
                    )
                    for item in items:
                        ids_to_delete.append(item.id)
                    await self.boot_asset_items.delete_by_version_id(
                        version.id
                    )
                await self.boot_asset_versions.delete_by_asset_id(asset.id)
                await self.delete(asset.id)
        await self.index_service.refresh()
        return ids_to_delete


class BootAssetVersionService(Service):
    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
        boot_asset_id: list[int] | None = None,
        version: list[str] | None = None,
    ) -> tuple[int, Iterable[models.BootAssetVersion]]:
        filters = queries.filters_from_arguments(
            BootAssetVersion,
            boot_asset_id=boot_asset_id,
            version=version,
        )
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        count = await queries.row_count(self.conn, BootAssetVersion, *filters)
        stmt = (
            self._select_all(BootAssetVersion)
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.BootAssetVersion, result)

    async def get_latest_version(
        self, boot_asset_id: int
    ) -> models.BootAssetVersion | None:
        stmt = (
            self._select_all(BootAssetVersion)
            .where(BootAssetVersion.c.boot_asset_id == boot_asset_id)
            .order_by(desc(BootAssetVersion.c.version))
        )
        result = await self.conn.execute(stmt)
        if row := result.first():
            return models.BootAssetVersion(**row._asdict())
        return None

    async def row_count(
        self,
        boot_asset_id: list[int] | None = None,
        version: list[str] | None = None,
    ) -> int:
        filters = queries.filters_from_arguments(
            BootAssetVersion,
            boot_asset_id=boot_asset_id,
            version=version,
        )
        return await queries.row_count(self.conn, BootAssetVersion, *filters)

    async def get_by_id(self, id: int) -> models.BootAssetVersion | None:
        stmt = self._select_all(BootAssetVersion).where(
            BootAssetVersion.c.id == id
        )
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAssetVersion(**row._asdict())
        return None

    async def create(
        self,
        details: models.BootAssetVersionCreate,
    ) -> models.BootAssetVersion:
        data = details.model_dump()
        stmt = insert(BootAssetVersion).returning(*BootAssetVersion.c.values())
        result = await self.conn.execute(stmt, [data])
        return models.BootAssetVersion(**result.one()._asdict())

    async def create_next_revision(
        self, asset_id: int, date: datetime
    ) -> models.BootAssetVersion:
        date_str = date.strftime("%Y%m%d") + "."
        count, versions = await self.get(
            [],
            boot_asset_id=[asset_id],
            version=[date_str],
        )
        if count > 0:
            latest_rev = max([int(v.version.split(".")[1]) for v in versions])
            new_rev = latest_rev + 1
            return await self.create(
                models.BootAssetVersionCreate(
                    boot_asset_id=asset_id,
                    version=f"{date_str}{new_rev}",
                    last_seen=date,
                )
            )
        return await self.create(
            models.BootAssetVersionCreate(
                boot_asset_id=asset_id,
                version=f"{date_str}1",
                last_seen=date,
            )
        )

    async def upsert(
        self,
        details: models.BootAssetVersionCreate,
    ) -> models.BootAssetVersion:
        """
        Update the BootAssetVersion if it exists, otherwise insert a new one.
        """
        # Update the existing version, if any
        stmt = (
            update(BootAssetVersion)
            .where(
                BootAssetVersion.c.boot_asset_id == details.boot_asset_id,
                BootAssetVersion.c.version == details.version,
            )
            .values({"last_seen": details.last_seen})
            .returning(*BootAssetVersion.c.values())
        )
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAssetVersion(**row._asdict())

        # Insert new version
        return await self.create(details)

    async def delete(self, boot_asset_version_id: int) -> int:
        stmt = (
            delete(BootAssetVersion)
            .where(BootAssetVersion.c.id == boot_asset_version_id)
            .returning(BootAssetVersion.c.boot_asset_id)
        )
        result = await self.conn.execute(stmt)
        return result.one()._asdict()["boot_asset_id"]  # type: ignore

    async def delete_by_asset_id(self, boot_asset_id: int) -> None:
        stmt = delete(BootAssetVersion).where(
            BootAssetVersion.c.boot_asset_id == boot_asset_id
        )
        await self.conn.execute(stmt)


class BootAssetItemService(Service):
    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
        boot_asset_version_id: list[int] | None = None,
        ftype: list[ItemFileType] | None = None,
        sha256: list[str] | None = None,
        path: list[str] | None = None,
        file_size: list[int] | None = None,
    ) -> tuple[int, Iterable[models.BootAssetItem]]:
        filters = queries.filters_from_arguments(
            BootAssetItem,
            boot_asset_version_id=boot_asset_version_id,
            ftype=ftype,
            sha256=sha256,
            path=path,
            file_size=file_size,
        )
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        count = await queries.row_count(self.conn, BootAssetItem, *filters)
        stmt = (
            self._select_all(BootAssetItem)
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.BootAssetItem, result)

    async def row_count(
        self,
        boot_asset_version_id: list[int] | None = None,
        ftype: list[ItemFileType] | None = None,
        sha256: list[str] | None = None,
        path: list[str] | None = None,
        file_size: list[int] | None = None,
    ) -> int:
        filters = queries.filters_from_arguments(
            BootAssetItem,
            boot_asset_version_id=boot_asset_version_id,
            ftype=ftype,
            sha256=sha256,
            path=path,
            file_size=file_size,
        )
        return await queries.row_count(self.conn, BootAssetItem, *filters)

    async def get_by_id(self, id: int) -> models.BootAssetItem | None:
        stmt = self._select_all(BootAssetItem).where(BootAssetItem.c.id == id)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAssetItem(**row._asdict())
        return None

    async def get_by_path(
        self, boot_source_id: int, path: str
    ) -> models.BootAssetItem | None:
        stmt = (
            self._select_all(BootAssetItem)
            .join(
                BootAssetVersion,
                BootAssetVersion.c.id == BootAssetItem.c.boot_asset_version_id,
            )
            .join(
                BootAsset, BootAsset.c.id == BootAssetVersion.c.boot_asset_id
            )
            .where(
                BootAsset.c.boot_source_id == boot_source_id,
                BootAssetItem.c.path == path,
            )
        )
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAssetItem(**row._asdict())
        return None

    async def create(
        self,
        details: models.BootAssetItemCreate,
    ) -> models.BootAssetItem:
        data = details.model_dump()
        stmt = insert(BootAssetItem).returning(*BootAssetItem.c.values())
        result = await self.conn.execute(stmt, [data])
        return models.BootAssetItem(**result.one()._asdict())

    async def create_temporary(
        self, boot_asset_version_id: int | None = None
    ) -> models.BootAssetItem:
        """Create a temporary BootAssetItem that is meant to be overwritten."""
        details = models.BootAssetItemCreate(
            boot_asset_version_id=boot_asset_version_id,
            ftype=ItemFileType.ROOT_TGZ,
            sha256="",
            path="",
            file_size=0,
        )
        return await self.create(details)

    async def update_bytes_synced(
        self,
        id: int,
        bytes_synced: int,
    ) -> None:
        stmt = (
            update(BootAssetItem)
            .where(BootAssetItem.c.id == id)
            .values({"bytes_synced": bytes_synced})
        )
        await self.conn.execute(stmt)

    async def update(
        self, id: int, details: models.BootAssetItemUpdate
    ) -> models.BootAssetItem:
        data = details.model_dump(exclude_none=True)
        stmt = (
            update(BootAssetItem)
            .where(BootAssetItem.c.id == id)
            .values(data)
            .returning(*BootAssetItem.c.values())
        )
        result = await self.conn.execute(stmt)
        return models.BootAssetItem(**result.one()._asdict())

    async def delete(self, boot_asset_item_id: int) -> int:
        stmt = (
            delete(BootAssetItem)
            .where(BootAssetItem.c.id == boot_asset_item_id)
            .returning(BootAssetItem.c.boot_asset_version_id)
        )
        result = await self.conn.execute(stmt)
        return result.one()._asdict()["boot_asset_version_id"]  # type: ignore

    async def delete_by_version_id(self, boot_asset_version_id: int) -> None:
        stmt = delete(BootAssetItem).where(
            BootAssetItem.c.boot_asset_version_id == boot_asset_version_id
        )
        await self.conn.execute(stmt)


class IndexNotFound(Exception):
    """Raised when a refresh or select was made on the index, but it doesn't exist."""


def reverse_fqdn(fqdn: str) -> str:
    sp = fqdn.split(".")
    sp.reverse()
    return ".".join(sp)


class IndexService(Service):
    async def refresh(self) -> None:
        """
        Refresh the images_index materialized view.
        """
        stmt = text("REFRESH MATERIALIZED VIEW CONCURRENTLY images_index;")
        try:
            await self.conn.execute(stmt)
        except ProgrammingError:
            raise IndexNotFound()

    async def get(
        self,
        index_type: IndexType,
        fqdn: str,
        partition: DownloadPartition | None = None,
    ) -> dict[str, Any]:
        """
        Get the specified index type.
        """
        try:
            if index_type == IndexType.INDEX:
                products_with_partition = await self._fetch_products(None)
                effective_partition: DownloadPartition | None = None
            else:
                if partition is None:
                    raise ValueError(
                        "Download partition must be specified for download indices."
                    )
                products_with_partition = await self._fetch_products(partition)
                effective_partition = partition
        except ProgrammingError as ex:
            raise IndexNotFound(str(ex))
        products = [product for product, _ in products_with_partition]
        self._filter_for_fully_downloaded(products)
        retained_products = {
            (product.id, product.path, product.ftype) for product in products
        }
        products_with_partition = [
            (product, partition_key)
            for product, partition_key in products_with_partition
            if (product.id, product.path, product.ftype) in retained_products
        ]
        if index_type == IndexType.INDEX:
            partitioned_products: dict[
                DownloadPartition, list[models.IndexProduct]
            ] = {
                DownloadPartition.BOOTLOADERS: [],
                DownloadPartition.UBUNTU: [],
                DownloadPartition.OTHER: [],
            }
            for product, partition_key in products_with_partition:
                partitioned_products[partition_key].append(product)
            return self.generate_index_json(partitioned_products, fqdn)
        assert effective_partition is not None
        return self.generate_download_json(
            effective_partition,
            [product for product, _ in products_with_partition],
            fqdn,
        )

    def _filter_for_fully_downloaded(
        self, products: list[models.IndexProduct]
    ) -> None:
        """
        Remove items from the list that are not part of a fully downloaded set.
        """
        download_status: dict[int, dict[str, Any]] = {}
        for i, p in enumerate(products):
            if download_status.get(p.id) is None:
                download_status[p.id] = {
                    "indeces": [i],
                    "downloaded": p.bytes_synced == p.file_size,
                }
            else:
                download_status[p.id]["downloaded"] &= (
                    p.bytes_synced == p.file_size
                )
                download_status[p.id]["indeces"].append(i)

        indeces_to_remove = []
        for dl in download_status.values():
            if not dl["downloaded"]:
                indeces_to_remove += dl["indeces"]
        indeces_to_remove.sort(reverse=True)
        for i in indeces_to_remove:
            products.pop(i)

    async def _fetch_products(
        self, partition: DownloadPartition | None
    ) -> list[tuple[models.IndexProduct, DownloadPartition]]:
        query = text(
            """
            WITH partitioned AS (
                SELECT
                    *,
                    CASE
                        WHEN kind = :bootloader_kind THEN :bootloaders_partition
                        WHEN LOWER(os) = 'ubuntu' THEN :ubuntu_partition
                        ELSE :other_partition
                    END AS partition
                FROM images_index
            )
            SELECT * FROM partitioned
            WHERE (cast(:target_partition AS text) IS NULL OR partition = cast(:target_partition AS text));
            """
        )
        params: dict[str, Any] = {
            "bootloader_kind": BootAssetKind.BOOTLOADER.value,
            "bootloaders_partition": DownloadPartition.BOOTLOADERS.value,
            "ubuntu_partition": DownloadPartition.UBUNTU.value,
            "other_partition": DownloadPartition.OTHER.value,
            "target_partition": partition.value if partition else None,
        }
        result = await self.conn.execute(query, params)
        products_with_partition: list[
            tuple[models.IndexProduct, DownloadPartition]
        ] = []
        for row in result.mappings():
            partition_value = DownloadPartition(row["partition"])
            product_data = {k: row[k] for k in row.keys() if k != "partition"}
            products_with_partition.append(
                (models.IndexProduct(**product_data), partition_value)
            )
        return products_with_partition

    def _product_key(
        self, product: models.IndexProduct, reversed_fqdn: str
    ) -> str:
        if product.kind == BootAssetKind.BOOTLOADER:
            return f"{reversed_fqdn}.stream:1:{product.os}:{product.bootloader_type}:{product.arch}"

        product_key = (
            f"{product.os}:{product.release}:{product.arch}:{product.subarch}"
        )
        if product.flavor:
            product_key += f"-{product.flavor}"

        return f"{reversed_fqdn}.stream:v3:{product_key}"

    def generate_index_json(
        self,
        partitioned_products: dict[
            DownloadPartition, list[models.IndexProduct]
        ],
        fqdn: str,
    ) -> dict[str, Any]:
        """
        Create the index json from the list of products in the materialized view.
        """
        reversed_fqdn = reverse_fqdn(fqdn)
        now = now_utc().strftime("%a, %d %b %Y %H:%M:%S %z")
        index_json: dict[str, Any] = {
            "format": "index:1.0",
            "index": {},
            "updated": now,
        }
        for partition in (
            DownloadPartition.BOOTLOADERS,
            DownloadPartition.UBUNTU,
            DownloadPartition.OTHER,
        ):
            products = partitioned_products.get(partition, [])
            if not products:
                continue
            content_id = partition.content_id(reversed_fqdn)
            product_keys = {
                self._product_key(product, reversed_fqdn)
                for product in products
            }
            index_json["index"][content_id] = {
                "datatype": "image-ids",
                "format": "products:1.0",
                "path": f"streams/v1/{content_id}.json",
                "products": sorted(product_keys),
                "updated": now,
            }
        return index_json

    def generate_download_json(
        self,
        partition: DownloadPartition,
        products: list[models.IndexProduct],
        fqdn: str,
    ) -> dict[str, Any]:
        """
        Create the download json from the list of products in the materialized view.
        """
        reversed_fqdn = reverse_fqdn(fqdn)
        content_id = partition.content_id(reversed_fqdn)
        download_json: dict[str, Any] = {
            "content_id": content_id,
            "datatype": "image-ids",
            "format": "products:1.0",
            "products": {},
        }
        for product in products:
            product_key = self._product_key(product, reversed_fqdn)
            if product.kind == BootAssetKind.BOOTLOADER:
                item_json = {
                    "ftype": product.ftype.value,
                    "path": f"{product.boot_source_id}/{product.path}",
                    "sha256": product.sha256,
                    "size": product.file_size,
                    "src_package": product.source_package,
                    "src_release": product.source_release,
                    "src_version": product.source_version,
                }
                item_key = product.source_package
            else:
                item_json = {
                    "ftype": product.ftype.value,
                    "path": f"{product.boot_source_id}/{product.path}",
                    "sha256": product.sha256,
                    "size": product.file_size,
                }
                item_key = product.ftype.value
            if download_json["products"].get(product_key) is None:
                dl_prod = {
                    "arch": product.arch,
                    "kflavor": product.flavor,
                    "label": product.label.value,
                    "os": product.os,
                    "release": product.release,
                    "krel": product.krel,
                    "release_codename": product.codename,
                    "release_title": product.title,
                    "subarch": product.subarch,
                    "version": product.asset_version,
                    "versions": {
                        product.version: {"items": {item_key: item_json}}
                    },
                }
                if product.eol is not None:
                    dl_prod["support_eol"] = product.eol.strftime("%Y-%m-%d")
                if product.esm_eol is not None:
                    dl_prod["support_esm_eol"] = product.esm_eol.strftime(
                        "%Y-%m-%d"
                    )
                if product.kind == BootAssetKind.BOOTLOADER:
                    dl_prod["bootloader-type"] = product.bootloader_type
                    dl_prod["arches"] = ",".join(product.compatibility or [])
                else:
                    dl_prod["subarches"] = ",".join(
                        product.compatibility or []
                    )
                download_json["products"][product_key] = {
                    k: v for k, v in dl_prod.items() if v
                }
            else:
                download_json["products"][product_key]["versions"][
                    product.version
                ]["items"][item_key] = item_json
        download_json["updated"] = now_utc().strftime(
            "%a, %d %b %Y %H:%M:%S %z"
        )
        return download_json
