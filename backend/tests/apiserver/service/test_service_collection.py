from collections.abc import Iterator

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncConnection
from temporalio.client import Client as TemporalClient

from msm.apiserver.service import ServiceCollection


@pytest.fixture
def collection(
    db_connection: AsyncConnection, temporal_client: TemporalClient
) -> Iterator[ServiceCollection]:
    yield ServiceCollection(db_connection, temporal_client)


@pytest.mark.asyncio
class TestServiceCollection:
    async def test_services_property_returns_all_services(
        self, collection: ServiceCollection
    ) -> None:
        """Test that services property returns all service instances."""
        services = list(collection.services)

        assert len(services) == 15
        assert collection.boot_asset_items in services
        assert collection.boot_asset_versions in services
        assert collection.boot_assets in services
        assert collection.boot_source_selections in services
        assert collection.boot_sources in services
        assert collection.config in services
        assert collection.index_service in services
        assert collection.s3 in services
        assert collection.settings in services
        assert collection.sites in services
        assert collection.temporal_service in services
        assert collection.tokens in services
        assert collection.users in services
        assert collection.workflow_service in services
        assert collection.site_profiles in services

    async def test_collect_metrics_calls_all_services(
        self, collection: ServiceCollection, mocker: MockerFixture
    ) -> None:
        """Test that collect_metrics calls collect_metrics on all services."""
        # Mock collect_metrics for each service
        for service in collection.services:
            mocker.patch.object(service, "collect_metrics")

        await collection.collect_metrics()

        # Verify collect_metrics was called on each service
        for service in collection.services:
            service.collect_metrics.assert_called_once()  # type: ignore

    def test_register_metrics_calls_base_service_register_metrics(
        self, mocker: MockerFixture
    ) -> None:
        """Test that register_metrics delegates to base Service class."""
        mock_registry = mocker.Mock()
        mock_service_register = mocker.patch(
            "msm.apiserver.service.base.Service.register_metrics"
        )

        ServiceCollection.register_metrics(mock_registry)

        mock_service_register.assert_called_once_with(mock_registry)
