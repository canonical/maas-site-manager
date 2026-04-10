from collections.abc import Iterable
from typing import Any

from sqlalchemy import (
    Select,
    delete,
    insert,
    select,
    update,
)

from msm.apiserver.db import (
    DEFAULT_SITE_PROFILE_ID,
    models,
    queries,
)
from msm.apiserver.db.tables import SiteProfile
from msm.apiserver.schema import SortParam
from msm.apiserver.service.base import Service


class SiteProfileService(Service):
    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[int, Iterable[models.SiteProfile]]:
        count = await queries.row_count(self.conn, SiteProfile, **{})
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        stmt = self._select_all(SiteProfile).order_by(*order_by).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.SiteProfile, result)

    async def get_by_id(self, id: int) -> models.SiteProfile | None:
        stmt = self._select_all(SiteProfile).where(SiteProfile.c.id == id)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.SiteProfile(**row._asdict())
        return None

    async def create(
        self, details: models.SiteProfileCreate
    ) -> models.SiteProfile:
        data = details.model_dump()
        stmt = insert(SiteProfile).returning(*SiteProfile.c.values())
        result = await self.conn.execute(
            stmt,
            [data],
        )
        return models.SiteProfile(**result.one()._asdict())

    async def update(
        self, site_profile_id: int, details: models.SiteProfileUpdate
    ) -> models.SiteProfile:
        data = details.model_dump(exclude_none=True)
        stmt = (
            update(SiteProfile)
            .where(SiteProfile.c.id == site_profile_id)
            .values(data)
            .returning(*SiteProfile.c.values())
        )
        result = await self.conn.execute(stmt)
        return models.SiteProfile(**result.one()._asdict())

    async def delete(self, site_profile_id: int) -> None:
        stmt = delete(SiteProfile).where(SiteProfile.c.id == site_profile_id)
        await self.conn.execute(stmt)

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(SiteProfile)

    async def _ensure_default_profile(self) -> None:
        stmt = self._select_statement(
            SiteProfile.c.id,
        ).where(SiteProfile.c.id == DEFAULT_SITE_PROFILE_ID)
        result = await self.conn.execute(stmt)
        if result.one_or_none() is None:
            data = {
                "id": DEFAULT_SITE_PROFILE_ID,
                "name": "Default Profile",
                "selections": ["ubuntu/resolute/amd64"],
                "global_config": {},
            }
            await self.conn.execute(insert(SiteProfile), [data])

    async def ensure(self) -> None:
        await self._ensure_default_profile()
