from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy import Select, and_, delete, insert, select, update

from msm.db import (
    models,
    queries,
)
from msm.db.tables import (
    BootAsset,
    BootAssetItem,
    BootAssetVersion,
    BootSource,
    BootSourceSelection,
)
from msm.schema import SortParam
from msm.service.base import Service


class BootSourceService(Service):
    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[int, Iterable[models.BootSource]]:
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        stmt = (
            self._select_statement(
                BootSource.c.id,
                BootSource.c.url,
                BootSource.c.keyring,
                BootSource.c.sync_interval,
                BootSource.c.priority,
            )
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return result.rowcount, self.objects_from_result(
            models.BootSource, result
        )

    async def get_by_id(self, id: int) -> models.BootSource | None:
        stmt = self._select_statement(
            BootSource.c.id,
            BootSource.c.url,
            BootSource.c.keyring,
            BootSource.c.sync_interval,
            BootSource.c.priority,
        ).where(BootSource.c.id == id)
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
            .returning(
                BootSource.c.id,
                BootSource.c.url,
                BootSource.c.keyring,
                BootSource.c.sync_interval,
                BootSource.c.priority,
            )
        )
        result = await self.conn.execute(stmt)
        return models.BootSource(**result.one()._asdict())

    async def create(
        self, details: models.BootSourceCreate
    ) -> models.BootSource:
        data = details.model_dump()
        stmt = insert(BootSource).returning(
            BootSource.c.id,
            BootSource.c.url,
            BootSource.c.keyring,
            BootSource.c.sync_interval,
            BootSource.c.priority,
        )
        result = await self.conn.execute(
            stmt,
            [data],
        )
        boot_source = result.one()
        return models.BootSource(**boot_source._asdict())

    async def delete(self, boot_source_id: int) -> None:
        stmt = delete(BootSource).where(BootSource.c.id == boot_source_id)
        await self.conn.execute(stmt)

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(BootSource)

    async def ensure_custom_boot_source(self, service_url: str) -> None:
        """
        Ensure that the custom image boot source is present in the database.
        """
        stmt = self._select_statement(
            BootSource.c.id,
            BootSource.c.url,
        ).where(BootSource.c.id == 1)
        result = await self.conn.execute(stmt)
        if result.one_or_none():
            # update the custom source url in case the MSM url has changed
            await self.update(1, models.BootSourceUpdate(url=service_url))
            return
        data = {
            "id": 1,
            "url": service_url,
            "keyring": "",
            "sync_interval": 0,
            "priority": 1,
        }
        await self.conn.execute(insert(BootSource), [data])


class BootSourceSelectionService(Service):
    async def get(
        self,
        boot_source_id: int,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[int, Iterable[models.BootSourceSelection]]:
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        stmt = (
            self._select_statement(
                BootSourceSelection.c.id,
                BootSourceSelection.c.boot_source_id,
                BootSourceSelection.c.label,
                BootSourceSelection.c.os,
                BootSourceSelection.c.release,
                BootSourceSelection.c.arches,
            )
            .where(BootSourceSelection.c.boot_source_id == boot_source_id)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return result.rowcount, self.objects_from_result(
            models.BootSourceSelection, result
        )

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
            .returning(
                BootSourceSelection.c.id,
                BootSourceSelection.c.boot_source_id,
                BootSourceSelection.c.label,
                BootSourceSelection.c.os,
                BootSourceSelection.c.release,
                BootSourceSelection.c.arches,
            )
        )
        result = await self.conn.execute(stmt)
        return models.BootSourceSelection(**result.one()._asdict())

    async def create(
        self, details: models.BootSourceSelectionCreate
    ) -> models.BootSourceSelection:
        data = details.model_dump()
        stmt = insert(BootSourceSelection).returning(
            BootSourceSelection.c.id,
            BootSourceSelection.c.boot_source_id,
            BootSourceSelection.c.label,
            BootSourceSelection.c.os,
            BootSourceSelection.c.release,
            BootSourceSelection.c.arches,
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

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(BootSourceSelection)


class BootAssetService(Service):
    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
        boot_source_id: list[int] | None = None,
        kind: list[models.BootAssetKind] | None = None,
        label: list[models.BootAssetLabel] | None = None,
        os: list[str] | None = None,
        arch: list[str] | None = None,
        release: list[str] | None = None,
    ) -> tuple[int, Iterable[models.BootAsset]]:
        filters = queries.filters_from_arguments(
            BootAsset,
            boot_source_id=boot_source_id,
            kind=kind,
            label=label,
            os=os,
            arch=arch,
            release=release,
        )
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        count = await queries.row_count(self.conn, BootAsset, *filters)
        stmt = (
            self._select_statement(
                BootAsset.c.id,
                BootAsset.c.boot_source_id,
                BootAsset.c.kind,
                BootAsset.c.label,
                BootAsset.c.os,
                BootAsset.c.release,
                BootAsset.c.codename,
                BootAsset.c.title,
                BootAsset.c.arch,
                BootAsset.c.subarch,
                BootAsset.c.compatibility,
                BootAsset.c.flavor,
                BootAsset.c.base_image,
                BootAsset.c.eol,
                BootAsset.c.esm_eol,
            )
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.BootAsset, result)

    async def get_by_id(self, id: int) -> models.BootAsset | None:
        stmt = self._select_statement(
            BootAsset.c.id,
            BootAsset.c.boot_source_id,
            BootAsset.c.kind,
            BootAsset.c.label,
            BootAsset.c.os,
            BootAsset.c.release,
            BootAsset.c.codename,
            BootAsset.c.title,
            BootAsset.c.arch,
            BootAsset.c.subarch,
            BootAsset.c.compatibility,
            BootAsset.c.flavor,
            BootAsset.c.base_image,
            BootAsset.c.eol,
            BootAsset.c.esm_eol,
        ).where(BootAsset.c.id == id)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAsset(**row._asdict())
        return None

    async def create(
        self,
        details: models.BootAssetCreate,
    ) -> models.BootAsset:
        data = details.model_dump()
        stmt = insert(BootAsset).returning(
            BootAsset.c.id,
            BootAsset.c.boot_source_id,
            BootAsset.c.kind,
            BootAsset.c.label,
            BootAsset.c.os,
            BootAsset.c.release,
            BootAsset.c.codename,
            BootAsset.c.title,
            BootAsset.c.arch,
            BootAsset.c.subarch,
            BootAsset.c.compatibility,
            BootAsset.c.flavor,
            BootAsset.c.base_image,
            BootAsset.c.eol,
            BootAsset.c.esm_eol,
        )
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
            .returning(
                BootAsset.c.id,
                BootAsset.c.boot_source_id,
                BootAsset.c.kind,
                BootAsset.c.label,
                BootAsset.c.os,
                BootAsset.c.release,
                BootAsset.c.codename,
                BootAsset.c.title,
                BootAsset.c.arch,
                BootAsset.c.subarch,
                BootAsset.c.compatibility,
                BootAsset.c.flavor,
                BootAsset.c.base_image,
                BootAsset.c.eol,
                BootAsset.c.esm_eol,
            )
        )
        result = await self.conn.execute(stmt)
        return models.BootAsset(**result.one()._asdict())

    async def delete(self, boot_asset_id: int) -> None:
        stmt = delete(BootAsset).where(BootAsset.c.id == boot_asset_id)
        await self.conn.execute(stmt)

    async def get_or_create(
        self, asset: models.BootAssetCreate
    ) -> models.BootAsset:
        count, assets = await self.get(
            [],
            boot_source_id=[asset.boot_source_id],
            kind=[asset.kind],
            label=[asset.label],
            os=[asset.os],
            arch=[asset.arch],
            release=[asset.release],
        )
        if count == 0:
            return await self.create(asset)
        return next(assets)  # type: ignore

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(BootAsset)


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
            self._select_statement(
                BootAssetVersion.c.id,
                BootAssetVersion.c.boot_asset_id,
                BootAssetVersion.c.version,
            )
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.BootAssetVersion, result)

    async def get_by_id(self, id: int) -> models.BootAssetVersion | None:
        stmt = self._select_statement(
            BootAssetVersion.c.id,
            BootAssetVersion.c.boot_asset_id,
            BootAssetVersion.c.version,
        ).where(BootAssetVersion.c.id == id)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAssetVersion(**row._asdict())
        return None

    async def create(
        self,
        details: models.BootAssetVersionCreate,
    ) -> models.BootAssetVersion:
        data = details.model_dump()
        stmt = insert(BootAssetVersion).returning(
            BootAssetVersion.c.id,
            BootAssetVersion.c.boot_asset_id,
            BootAssetVersion.c.version,
        )
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
                    boot_asset_id=asset_id, version=f"{date_str}{new_rev}"
                )
            )
        return await self.create(
            models.BootAssetVersionCreate(
                boot_asset_id=asset_id, version=f"{date_str}1"
            )
        )

    async def delete(self, boot_asset_version_id: int) -> None:
        stmt = delete(BootAssetVersion).where(
            BootAssetVersion.c.id == boot_asset_version_id
        )
        await self.conn.execute(stmt)

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(BootAssetVersion)


class BootAssetItemService(Service):
    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
        boot_asset_version_id: list[int] | None = None,
        ftype: list[models.ItemFileType] | None = None,
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
            self._select_statement(
                BootAssetItem.c.id,
                BootAssetItem.c.boot_asset_version_id,
                BootAssetItem.c.ftype,
                BootAssetItem.c.sha256,
                BootAssetItem.c.path,
                BootAssetItem.c.file_size,
                BootAssetItem.c.source_package,
                BootAssetItem.c.source_version,
                BootAssetItem.c.source_release,
                BootAssetItem.c.bytes_synced,
            )
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.BootAssetItem, result)

    async def get_by_id(self, id: int) -> models.BootAssetItem | None:
        stmt = self._select_statement(
            BootAssetItem.c.id,
            BootAssetItem.c.boot_asset_version_id,
            BootAssetItem.c.ftype,
            BootAssetItem.c.sha256,
            BootAssetItem.c.path,
            BootAssetItem.c.file_size,
            BootAssetItem.c.source_package,
            BootAssetItem.c.source_version,
            BootAssetItem.c.source_release,
            BootAssetItem.c.bytes_synced,
        ).where(BootAssetItem.c.id == id)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAssetItem(**row._asdict())
        return None

    async def get_by_path(self, path: str) -> models.BootAssetItem | None:
        stmt = self._select_statement(
            BootAssetItem.c.id,
            BootAssetItem.c.boot_asset_version_id,
            BootAssetItem.c.ftype,
            BootAssetItem.c.sha256,
            BootAssetItem.c.path,
            BootAssetItem.c.file_size,
            BootAssetItem.c.source_package,
            BootAssetItem.c.source_version,
            BootAssetItem.c.source_release,
            BootAssetItem.c.bytes_synced,
        ).where(BootAssetItem.c.path == path)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAssetItem(**row._asdict())
        return None

    async def create(
        self,
        details: models.BootAssetItemCreate,
    ) -> models.BootAssetItem:
        data = details.model_dump()
        stmt = insert(BootAssetItem).returning(
            BootAssetItem.c.id,
            BootAssetItem.c.boot_asset_version_id,
            BootAssetItem.c.ftype,
            BootAssetItem.c.sha256,
            BootAssetItem.c.path,
            BootAssetItem.c.file_size,
            BootAssetItem.c.source_package,
            BootAssetItem.c.source_version,
            BootAssetItem.c.source_release,
            BootAssetItem.c.bytes_synced,
        )
        result = await self.conn.execute(stmt, [data])
        return models.BootAssetItem(**result.one()._asdict())

    async def create_temporary(
        self, boot_asset_version_id: int | None = None
    ) -> models.BootAssetItem:
        """Create a temporary BootAssetItem that is meant to be overwritten."""
        details = models.BootAssetItemCreate(
            boot_asset_version_id=boot_asset_version_id,
            ftype=models.ItemFileType.ROOT_TGZ,
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
            .returning(
                BootAssetItem.c.id,
                BootAssetItem.c.boot_asset_version_id,
                BootAssetItem.c.ftype,
                BootAssetItem.c.sha256,
                BootAssetItem.c.path,
                BootAssetItem.c.file_size,
                BootAssetItem.c.source_package,
                BootAssetItem.c.source_version,
                BootAssetItem.c.source_release,
                BootAssetItem.c.bytes_synced,
            )
        )
        result = await self.conn.execute(stmt)
        return models.BootAssetItem(**result.one()._asdict())

    async def delete(self, boot_asset_item_id: int) -> None:
        stmt = delete(BootAssetItem).where(
            BootAssetItem.c.id == boot_asset_item_id
        )
        await self.conn.execute(stmt)

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(BootAssetItem)
