"""Tests for SiteStateService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db.models.site import (
    SiteStateStatusCreate,
    SiteStateStatusUpdate,
)
from msm.apiserver.service.site import SiteStateService
from msm.common.enums import TaskStatus
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestSiteStateService:
    async def test_create(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site = await factory.make_Site()
        service = SiteStateService(db_connection)

        create_data = SiteStateStatusCreate(
            site_id=site.id,
            status=TaskStatus.STARTED,
            selections_status=TaskStatus.STARTED,
            errors=["error1"],
        )
        result = await service.create(create_data)

        assert result.site_id == site.id
        assert result.status == TaskStatus.STARTED
        assert result.selections_status == TaskStatus.STARTED
        assert result.global_config_status == TaskStatus.UNKNOWN
        assert result.image_sync_status == TaskStatus.UNKNOWN
        assert result.errors == ["error1"]

    async def test_get_by_id_exists(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site = await factory.make_Site()
        site_state = await factory.make_SiteStateStatus(
            site_id=site.id,
            status=TaskStatus.COMPLETE,
        )
        service = SiteStateService(db_connection)

        result = await service.get_by_id(site_state.id)

        assert result is not None
        assert result.id == site_state.id
        assert result.site_id == site.id
        assert result.status == TaskStatus.COMPLETE

    async def test_get_by_id_not_found(
        self,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteStateService(db_connection)

        result = await service.get_by_id(999)

        assert result is None

    async def test_get_by_site_id_exists(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site = await factory.make_Site()
        site_state = await factory.make_SiteStateStatus(
            site_id=site.id,
            status=TaskStatus.FAILED,
            errors=["sync failed"],
        )
        service = SiteStateService(db_connection)

        result = await service.get_by_site_id(site.id)

        assert result == site_state

    async def test_get_by_site_id_not_found(
        self,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteStateService(db_connection)

        result = await service.get_by_site_id(999)

        assert result is None

    async def test_get_all(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site1 = await factory.make_Site()
        site2 = await factory.make_Site()
        site_state1 = await factory.make_SiteStateStatus(
            site_id=site1.id,
            status=TaskStatus.COMPLETE,
        )
        site_state2 = await factory.make_SiteStateStatus(
            site_id=site2.id,
            status=TaskStatus.STARTED,
        )
        service = SiteStateService(db_connection)

        count, results = await service.get(sort_params=[])

        results_list = list(results)
        assert count == 2
        assert len(results_list) == 2
        assert results_list[0] == site_state1
        assert results_list[1] == site_state2

    async def test_get_with_pagination_offset(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site1 = await factory.make_Site()
        site2 = await factory.make_Site()
        site3 = await factory.make_Site()
        status1 = await factory.make_SiteStateStatus(site_id=site1.id)
        status2 = await factory.make_SiteStateStatus(site_id=site2.id)
        status3 = await factory.make_SiteStateStatus(site_id=site3.id)
        service = SiteStateService(db_connection)

        count, results = await service.get(sort_params=[], offset=1, limit=1)

        results_list = list(results)
        assert count == 3
        assert len(results_list) == 1
        assert results_list[0] == status2

    async def test_get_with_pagination_limit(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site1 = await factory.make_Site()
        site2 = await factory.make_Site()
        site3 = await factory.make_Site()
        await factory.make_SiteStateStatus(site_id=site1.id)
        await factory.make_SiteStateStatus(site_id=site2.id)
        await factory.make_SiteStateStatus(site_id=site3.id)
        service = SiteStateService(db_connection)

        count, results = await service.get(sort_params=[], limit=2)

        results_list = list(results)
        assert count == 3
        assert len(results_list) == 2

    async def test_update_multiple_fields(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site = await factory.make_Site()
        site_state = await factory.make_SiteStateStatus(
            site_id=site.id,
            status=TaskStatus.UNKNOWN,
            selections_status=TaskStatus.UNKNOWN,
        )
        service = SiteStateService(db_connection)

        update_data = SiteStateStatusUpdate(
            status=TaskStatus.COMPLETE,
            selections_status=TaskStatus.COMPLETE,
            errors=["warning1", "warning2"],
        )
        result = await service.update(site_state.id, update_data)

        assert result.status == TaskStatus.COMPLETE
        assert result.selections_status == TaskStatus.COMPLETE
        assert result.errors == ["warning1", "warning2"]

    async def test_update_partial_fields(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site = await factory.make_Site()
        original_errors = ["original_error"]
        site_state = await factory.make_SiteStateStatus(
            site_id=site.id,
            status=TaskStatus.STARTED,
            selections_status=TaskStatus.STARTED,
            errors=original_errors,
        )
        service = SiteStateService(db_connection)

        update_data = SiteStateStatusUpdate(
            status=TaskStatus.COMPLETE,
        )
        result = await service.update(site_state.id, update_data)

        assert result.status == TaskStatus.COMPLETE
        assert result.selections_status == TaskStatus.STARTED
        assert result.errors == original_errors

    async def test_delete(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
    ) -> None:
        site = await factory.make_Site()
        site_state = await factory.make_SiteStateStatus(site_id=site.id)
        service = SiteStateService(db_connection)

        await service.delete(site_state.id)

        result = await service.get_by_id(site_state.id)
        assert result is None

    async def test_delete_nonexistent(
        self,
        db_connection: AsyncConnection,
    ) -> None:
        service = SiteStateService(db_connection)

        # Should not raise an error
        await service.delete(999)

    @pytest.mark.parametrize(
        "task_status",
        [
            (TaskStatus.UNKNOWN),
            (TaskStatus.STARTED),
            (TaskStatus.COMPLETE),
            (TaskStatus.FAILED),
        ],
    )
    async def test_all_task_status_values(
        self,
        factory: Factory,
        db_connection: AsyncConnection,
        task_status: TaskStatus,
    ) -> None:
        """Test creating SiteStateStatus with all TaskStatus values."""
        site = await factory.make_Site()
        service = SiteStateService(db_connection)
        create_data = SiteStateStatusCreate(
            site_id=site.id,
            status=task_status,
            selections_status=task_status,
            global_config_status=task_status,
            image_sync_status=task_status,
        )
        result = await service.create(create_data)

        assert result.status == task_status
        assert result.selections_status == task_status
        assert result.global_config_status == task_status
        assert result.image_sync_status == task_status
