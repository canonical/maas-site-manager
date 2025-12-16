from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection
from temporalio.client import Client as TemporalClient

from msm.apiserver.service import (
    BootAssetItemService,
    BootAssetService,
    BootAssetVersionService,
    BootSourceSelectionService,
    BootSourceService,
    BootSourceWorkflowService,
    IndexService,
    ServiceCollection,
    TemporalService,
)
from msm.apiserver.service.s3 import S3Service


@pytest.fixture
async def service_collection(
    db_connection: AsyncConnection,
    s3_env: None,
    temporal_client: TemporalClient,
) -> AsyncIterator[ServiceCollection]:
    yield ServiceCollection(db_connection, temporal_client)


@pytest.fixture(autouse=True)
async def index_service(
    service_collection: ServiceCollection,
) -> AsyncIterator[IndexService]:
    yield service_collection.index_service


@pytest.fixture
def boot_asset_service(
    service_collection: ServiceCollection,
) -> Iterator[BootAssetService]:
    yield service_collection.boot_assets


@pytest.fixture
def boot_source_selection_service(
    service_collection: ServiceCollection,
) -> Iterator[BootSourceSelectionService]:
    yield service_collection.boot_source_selections


@pytest.fixture
def boot_source_service(
    service_collection: ServiceCollection,
) -> Iterator[BootSourceService]:
    yield service_collection.boot_sources


@pytest.fixture
def boot_asset_version_service(
    service_collection: ServiceCollection,
) -> Iterator[BootAssetVersionService]:
    yield service_collection.boot_asset_versions


@pytest.fixture
def boot_asset_item_service(
    service_collection: ServiceCollection,
) -> Iterator[BootAssetItemService]:
    yield service_collection.boot_asset_items


@pytest.fixture
def temporal_service(
    service_collection: ServiceCollection,
) -> Iterator[TemporalService]:
    yield service_collection.temporal_service


@pytest.fixture
def workflow_service(
    service_collection: ServiceCollection,
) -> Iterator[BootSourceWorkflowService]:
    yield service_collection.workflow_service


@pytest.fixture
def s3_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MSM_S3_BUCKET", "test-bucket")
    monkeypatch.setenv("MSM_S3_ENDPOINT", "http://test-endpoint.com")
    monkeypatch.setenv("MSM_S3_ACCESS_KEY", "test-access-key")
    monkeypatch.setenv("MSM_S3_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("MSM_S3_PATH", "test/path")


@pytest.fixture
def s3_service(
    service_collection: ServiceCollection,
) -> Iterator[S3Service]:
    yield service_collection.s3
