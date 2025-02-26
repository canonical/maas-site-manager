import asyncio
import threading
from typing import Annotated
from urllib.parse import urlparse
from uuid import uuid4

from logging import getLogger

import boto3
from boto3.s3.transfer import TransferConfig
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
)
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporal.resources.workflows.custom_image_upload import ImageUploadChecker, ImageUploadParams, S3Params
from fastapi.responses import StreamingResponse

from msm.api.dependencies import services
from msm.api.exceptions.responses import (
    UnauthorizedErrorResponseModel,
    ValidationErrorResponseModel,
)
from msm.api.user.auth import authenticated_user
from msm.db import models
from msm.schema import (
    PaginatedResults,
    PaginationParams,
    SortParam,
    SortParamParser,
)
from msm.service import ServiceCollection
from msm.settings import Settings

logger = getLogger()

v1_router = APIRouter(prefix="/v1")

boot_asset_sort_parameters = SortParamParser(
    fields=[
        "kind",
        "label",
        "os",
        "release",
        "codename",
        "title",
        "arch",
        "subarch",
        "compatibility",
        "flavor",
        "base_image",
        "eol",
        "esm_eol",
    ]
)


class BootAssetsGetResponse(PaginatedResults):
    items: list[models.BootAsset]


boot_sources_sort_parameters = SortParamParser(
    fields=[
        "url",
        "keyring",
        "sync_interval",
        "priority",
    ]
)


class BootSourcesGetResponse(PaginatedResults):
    items: list[models.BootSource]


boot_source_selection_sort_parameters = SortParamParser(
    fields=[
        "label",
        "os",
        "release",
        "arches",
    ]
)


class BootSourceSelectionsGetResponse(PaginatedResults):
    items: list[models.BootSourceSelection]


@v1_router.get(
    "/bootassets",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_boot_assets(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    sort_params: Annotated[
        list[SortParam], Depends(boot_asset_sort_parameters)
    ],
    pagination_params: Annotated[PaginationParams, Depends()],
) -> BootAssetsGetResponse:
    """Return boot assets."""
    total, results = await services.boot_assets.get(
        sort_params,
        offset=pagination_params.offset,
        limit=pagination_params.size,
    )
    return BootAssetsGetResponse(
        total=total,
        page=pagination_params.page,
        size=pagination_params.size,
        items=list(results),
    )


@v1_router.get(
    "/bootasset-sources",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_boot_sources(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    sort_params: Annotated[
        list[SortParam], Depends(boot_sources_sort_parameters)
    ],
    pagination_params: Annotated[PaginationParams, Depends()],
) -> BootSourcesGetResponse:
    """Return boot sources."""
    total, results = await services.boot_sources.get(
        sort_params,
        offset=pagination_params.offset,
        limit=pagination_params.size,
    )
    return BootSourcesGetResponse(
        total=total,
        page=pagination_params.page,
        size=pagination_params.size,
        items=list(results),
    )


@v1_router.get(
    "/bootasset-sources/{id}/selections",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_boot_source_selections(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: int,
    sort_params: Annotated[
        list[SortParam], Depends(boot_source_selection_sort_parameters)
    ],
    pagination_params: Annotated[PaginationParams, Depends()],
) -> BootSourceSelectionsGetResponse:
    """Return boot source selections."""
    total, results = await services.boot_source_selections.get(
        id,
        sort_params,
        offset=pagination_params.offset,
        limit=pagination_params.size,
    )
    return BootSourceSelectionsGetResponse(
        total=total,
        page=pagination_params.page,
        size=pagination_params.size,
        items=list(results),
    )


class ProgressPercentage:
    def __init__(self, size: int):
        self._size = size
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._percentage = 0.0
        self._updated = False

    def __call__(self, bytes_amount: int):
        with self._lock:
            self._seen_so_far += bytes_amount
            self._percentage = (self._seen_so_far / self._size) * 100
            self._updated = True

    def get_percentage(self):
        with self._lock:
            if self._updated and self._percentage != 100:
                self._updated = False
                yield self._percentage


@v1_router.post(
    "/images",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
def post_images(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    file: UploadFile = File(...),
) -> StreamingResponse:
    settings = Settings()

    if settings.image_upload_dir is None:
        # TODO: return error? Which one?
        raise RuntimeError("storage not ready")
    if not urlparse(settings.s3_endpoint).scheme:
        settings.s3_endpoint = f"http://{settings.s3_endpoint}"
    s3 = boto3.resource(
        "s3",
        use_ssl=False,
        verify=False,
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )

    config = TransferConfig(max_concurrency=10, use_threads=True)

    progress_percentage = ProgressPercentage(file.size)
    s3.meta.client.upload_fileobj(
        file.file,
        settings.s3_bucket,
        file.filename,
        Config=config,
        Callback=progress_percentage,
    )

    temporal_client = asyncio.run(Client.connect(settings.temporal_server_host, namespace=settings.temporal_namespace))
    workflow_id = f"image-upload-{uuid4()}"
    params = ImageUploadParams(
        filename=file.filename,
        s3_params=S3Params(
            endpoint=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            bucket=settings.s3_bucket,
            path=settings.s3_path,
        )
    )
    temporal_client.execute_workflow(
        ImageUploadChecker.run,
        params,
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
        id_reuse_policy=WorkflowIDReusePolicy.TERMINATE_IF_RUNNING
    )

    return StreamingResponse(progress_percentage.get_percentage)
