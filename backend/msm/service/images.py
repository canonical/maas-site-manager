from collections.abc import Iterable
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

    async def create(self, details: models.BootSource) -> models.BootSource:
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
        self, details: models.BootSourceSelection
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
    ) -> tuple[int, Iterable[models.BootAsset]]:
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
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
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return result.rowcount, self.objects_from_result(
            models.BootAsset, result
        )

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
        details: models.BootAsset,
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

    async def delete(self, boot_asset_id: int) -> None:
        stmt = delete(BootAsset).where(BootAsset.c.id == boot_asset_id)
        await self.conn.execute(stmt)

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(BootAsset)


class BootAssetVersionService(Service):
    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[int, Iterable[models.BootAssetVersion]]:
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        stmt = (
            self._select_statement(
                BootAssetVersion.c.id,
                BootAssetVersion.c.boot_asset_id,
                BootAssetVersion.c.version,
            )
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return result.rowcount, self.objects_from_result(
            models.BootAssetVersion, result
        )

    async def get_by_id(self, id: int) -> models.BootAsset | None:
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
        details: models.BootAssetVersion,
    ) -> models.BootAssetVersion:
        data = details.model_dump()
        stmt = insert(BootAssetVersion).returning(
            BootAssetVersion.c.id,
            BootAssetVersion.c.boot_asset_id,
            BootAssetVersion.c.version,
        )
        result = await self.conn.execute(stmt, [data])
        return models.BootAssetVersion(**result.one()._asdict())

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
    ) -> tuple[int, Iterable[models.BootAssetItem]]:
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        stmt = (
            self._select_statement(
                BootAssetItem.c.id,
                BootAssetItem.c.boot_asset_version_id,
                BootAssetItem.c.ftype,
                BootAssetItem.c.sha256,
                BootAssetItem.c.path,
                BootAssetItem.c.size,
                BootAssetItem.c.source_package,
                BootAssetItem.c.source_version,
                BootAssetItem.c.source_release,
                BootAssetItem.c.percent_synced,
            )
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return result.rowcount, self.objects_from_result(
            models.BootAssetItem, result
        )

    async def get_by_id(self, id: int) -> models.BootAssetItem | None:
        stmt = self._select_statement(
            BootAssetItem.c.id,
            BootAssetItem.c.boot_asset_version_id,
            BootAssetItem.c.ftype,
            BootAssetItem.c.sha256,
            BootAssetItem.c.path,
            BootAssetItem.c.size,
            BootAssetItem.c.source_package,
            BootAssetItem.c.source_version,
            BootAssetItem.c.source_release,
            BootAssetItem.c.percent_synced,
        ).where(BootAssetItem.c.id == id)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.BootAssetItem(**row._asdict())
        return None

    async def create(
        self,
        details: models.BootAssetItem,
    ) -> models.BootAssetItem:
        data = details.model_dump()
        stmt = insert(BootAssetItem).returning(
            BootAssetItem.c.id,
            BootAssetItem.c.boot_asset_version_id,
            BootAssetItem.c.ftype,
            BootAssetItem.c.sha256,
            BootAssetItem.c.path,
            BootAssetItem.c.size,
            BootAssetItem.c.source_package,
            BootAssetItem.c.source_version,
            BootAssetItem.c.source_release,
            BootAssetItem.c.percent_synced,
        )
        result = await self.conn.execute(stmt, [data])
        return models.BootAssetItem(**result.one()._asdict())

    async def update_percent_synced(
        self,
        id: int,
        percent_synced: float,
    ) -> None:
        stmt = (
            update(BootAssetItem)
            .where(BootAssetItem.c.id == id)
            .values({"percent_synced": percent_synced})
        )
        await self.conn.execute(stmt)

    async def delete(self, boot_asset_item_id: int) -> None:
        stmt = delete(BootAssetItem).where(
            BootAssetItem.c.id == boot_asset_item_id
        )
        await self.conn.execute(stmt)

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(BootAssetItem)
