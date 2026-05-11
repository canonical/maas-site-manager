import json
from logging import getLogger
from math import ceil
from socket import gethostname
from typing import Annotated, Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from starlette.types import Send

from msm.apiserver.db.models import Site
from msm.apiserver.dependencies import services
from msm.apiserver.exceptions.catalog import (
    BadRequestException,
    BaseExceptionDetail,
    NotFoundException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.exceptions.responses import (
    BadRequestErrorResponseModel,
    NotFoundErrorResponseModel,
    UnauthorizedErrorResponseModel,
)
from msm.apiserver.service import S3Service, ServiceCollection
from msm.apiserver.service.images import reverse_fqdn
from msm.apiserver.site.auth import authenticated_site
from msm.common.enums import (
    DownloadPartition,
    IndexType,
)
from msm.common.settings import Settings

logger = getLogger()

v1_router = APIRouter(prefix="/v1")


class S3StreamResponse(StreamingResponse):
    def __init__(
        self,
        content: Any,
        s3: S3Service,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str = "application/octet-stream",
        background: BackgroundTask | None = None,
        file_id: str = "",
        chunk_size: int = 5 * (1024**2),  # 5 MB
    ) -> None:
        super().__init__(content, status_code, headers, media_type, background)
        self.s3 = s3
        self.file_path = file_id
        self.chunk_size = chunk_size

    async def stream_response(self, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )

        result = await self.s3.get_object(self.file_path)
        body = result["Body"]

        while True:
            chunk = await run_in_threadpool(body.read, self.chunk_size)
            if not chunk:
                break
            await send(
                {
                    "type": "http.response.body",
                    "body": chunk,
                    "more_body": True,
                }
            )

        await send(
            {"type": "http.response.body", "body": b"", "more_body": False}
        )


class IndexStreamResponse(StreamingResponse):
    def __init__(
        self,
        content: Any,
        json_obj: dict[str, Any],
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str = "application/json",
        background: BackgroundTask | None = None,
        chunk_size: int = 1024**2,
    ) -> None:
        super().__init__(content, status_code, headers, media_type, background)
        self.json_obj = json_obj
        self.chunk_size = chunk_size

    async def stream_response(self, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )
        json_str = json.dumps(self.json_obj).encode()
        chunks = ceil(len(json_str) / self.chunk_size)
        for c in range(chunks):
            await send(
                {
                    "type": "http.response.body",
                    "body": json_str[
                        c * self.chunk_size : c * self.chunk_size
                        + self.chunk_size
                    ],
                    "more_body": True,
                }
            )

        await send(
            {"type": "http.response.body", "body": b"", "more_body": False}
        )


def verify_track_risk(track: str, risk: str) -> None:
    errors: list[BaseExceptionDetail] = []

    if track != "latest":
        errors.append(
            BaseExceptionDetail(
                reason=ExceptionCode.INVALID_PARAMS,
                messages=[f"Invalid track '{track}' requested"],
                field="track",
                location="path",
            )
        )

    if risk != "stable":
        errors.append(
            BaseExceptionDetail(
                reason=ExceptionCode.INVALID_PARAMS,
                messages=[f"Invalid risk '{risk}' requested"],
                field="risk",
                location="path",
            )
        )

    if errors:
        raise BadRequestException(
            code=ExceptionCode.INVALID_PARAMS,
            message="Invalid track/risk requested.",
            details=errors,
        )


@v1_router.get(
    "/images/{track}/{risk}/streams/v1/{index_path:path}",
    responses={
        400: {"model": BadRequestErrorResponseModel},
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
    },
)
async def download_index(
    services: Annotated[ServiceCollection, Depends(services)],
    site: Annotated[Site, Depends(authenticated_site)],
    track: str,
    risk: str,
    index_path: str,
) -> StreamingResponse:
    verify_track_risk(track, risk)

    service_url = await services.settings.get_service_url()
    parsed = urlparse(service_url)
    fqdn = parsed.hostname if parsed.hostname else gethostname()
    reversed_fqdn = reverse_fqdn(fqdn)

    if index_path == "index.json":
        index = await services.index_service.get(IndexType.INDEX, fqdn)
        return IndexStreamResponse(None, index)

    download_paths: dict[str, DownloadPartition] = {
        f"{DownloadPartition.UBUNTU.content_id(reversed_fqdn)}.json": DownloadPartition.UBUNTU,
        f"{DownloadPartition.BOOTLOADERS.content_id(reversed_fqdn)}.json": DownloadPartition.BOOTLOADERS,
        f"{DownloadPartition.OTHER.content_id(reversed_fqdn)}.json": DownloadPartition.OTHER,
    }
    if partition := download_paths.get(index_path):
        index = await services.index_service.get(
            IndexType.DOWNLOAD,
            fqdn,
            partition=partition,
        )
        return IndexStreamResponse(None, index)

    raise NotFoundException(
        code=ExceptionCode.MISSING_RESOURCE,
        message="Index file does not exist.",
        details=[
            BaseExceptionDetail(
                reason=ExceptionCode.MISSING_RESOURCE,
                messages=[f"Index file '{index_path}' does not exist"],
                field="index_path",
                location="path",
            )
        ],
    )


@v1_router.get(
    "/images/{track}/{risk}/{boot_source_id}/{file_path:path}",
    responses={
        400: {"model": BadRequestErrorResponseModel},
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
    },
)
async def download(
    request: Request,
    services: Annotated[ServiceCollection, Depends(services)],
    site: Annotated[Site, Depends(authenticated_site)],
    track: str,
    risk: str,
    boot_source_id: int,
    file_path: str,
) -> StreamingResponse:
    verify_track_risk(track, risk)

    boot_item = await services.boot_asset_items.get_by_path(
        boot_source_id, file_path
    )
    if not boot_item:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Asset Item does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"BootAssetItem '{file_path}' does not exist"],
                    field="file_path",
                    location="path",
                )
            ],
        )

    await request.state.release_db_connection()
    settings = Settings()
    return S3StreamResponse(
        content=None,
        file_id=str(boot_item.id),
        s3=services.s3,
        chunk_size=settings.image_serving_chunk_size_bytes,
    )
