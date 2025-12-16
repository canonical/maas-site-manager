from collections.abc import AsyncIterator
from typing import cast

import pytest
from pytest_mock import MockerFixture, MockType
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db.models import (
    BootAssetItem,
    BootSource,
)
from msm.apiserver.service import IndexService, S3Service
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.fixture(autouse=True)
def mock_now(mocker: MockerFixture, factory: Factory) -> MockType:
    return mocker.patch(
        "msm.apiserver.user.handlers.images.now_utc",
        return_value=factory.now,
    )


@pytest.fixture
def mock_s3_service(mocker: MockerFixture) -> MockType:
    mock_s3 = mocker.patch("msm.apiserver.service.S3Service", spec=S3Service)
    mock = mock_s3.return_value
    mock.create_multipart_upload.return_value = ("test-key", "test-upload-id")
    mock.upload_part.return_value = "test-etag"
    mock.complete_upload.return_value = None
    mock.abort_upload.return_value = None
    mock.delete_object.return_value = None
    mock.get_object.return_value = {"Body": [b"cadecafe"]}
    return cast(MockType, mock)


@pytest.mark.asyncio
class TestBootAssetItemsDownloadHandler:
    @pytest.fixture
    async def index_service(
        self, db_connection: AsyncConnection
    ) -> AsyncIterator[IndexService]:
        index_service = IndexService(db_connection)
        yield index_service

    async def test_download(
        self,
        site_client: Client,
        boot_source: BootSource,
        items_ubuntu_jammy_1: list[BootAssetItem],
        mock_s3_service: MockType,
    ) -> None:
        file_path = items_ubuntu_jammy_1[0].path
        resp = await site_client.get(
            f"/images/latest/stable/{boot_source.id}/{file_path}"
        )
        assert resp.status_code == 200

    async def test_download_not_found(
        self, site_client: Client, boot_source: BootSource
    ) -> None:
        resp = await site_client.get(
            f"/images/latest/stable/{boot_source.id}/ubuntu/noble/unknown-file"
        )
        assert resp.status_code == 404

    async def test_invalid_track(
        self, site_client: Client, boot_source: BootSource
    ) -> None:
        resp = await site_client.get(
            f"/images/1.0/stable/{boot_source.id}/ubuntu/noble/boot-kernel"
        )
        assert resp.status_code == 400

    async def test_invalid_risk(
        self, site_client: Client, boot_source: BootSource
    ) -> None:
        resp = await site_client.get(
            f"/images/latest/edge/{boot_source.id}/ubuntu/noble/boot-kernel"
        )
        assert resp.status_code == 400

    async def test_download_index(
        self,
        site_client: Client,
        factory: Factory,
        index_service: IndexService,
    ) -> None:
        await factory.make_Setting(
            "service_url",
            value="https://maas.site.manager",
        )
        resp = await site_client.get(
            "/images/latest/stable/streams/v1/index.json"
        )
        assert resp.status_code == 200
        index = resp.json()
        expected_index = {
            "format": "index:1.0",
            "index": {},
            "updated": index["updated"],
        }
        assert index == expected_index

    async def test_download_download_index(
        self,
        site_client: Client,
        factory: Factory,
        index_service: IndexService,
    ) -> None:
        await factory.make_Setting(
            "service_url",
            value="https://maas.site.manager",
        )
        resp = await site_client.get(
            "/images/latest/stable/streams/v1/manager.site.maas:stream:v3:download-ubuntu.json"
        )
        assert resp.status_code == 200
        dl_index = resp.json()
        expected_index = {
            "content_id": "manager.site.maas:stream:v3:download-ubuntu",
            "datatype": "image-ids",
            "format": "products:1.0",
            "products": {},
            "updated": dl_index["updated"],
        }
        assert dl_index == expected_index
