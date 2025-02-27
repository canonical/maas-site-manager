from logging import getLogger
from typing import Annotated
from urllib.parse import urlparse

import boto3
from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from pydantic import BaseModel

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


class BootAssetsPostRequest(BaseModel):
    kind: models.BootAssetKind
    label: models.BootAssetLabel
    os: str
    release: str
    codename: str
    title: str
    arch: str
    subarch: str
    compatibility: list[str]
    flavor: str
    base_image: str


class BootAssetsPostResponse(BaseModel):
    id: int


@v1_router.post(
    "/bootassets",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def post_boot_assets(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    post_request: BootAssetsPostRequest,
) -> BootAssetsPostResponse:
    boot_asset = await services.boot_assets.create(
        models.BootAsset(**post_request.model_dump())
    )
    return BootAssetsPostResponse(boot_asset.id)


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


class BootSourcesPostRequest(BaseModel):
    priority: int
    url: str
    keyring: str
    sync_interval: int


class BootSourcesPostResponse(BaseModel):
    id: int


@v1_router.post(
    "/bootasset-sources",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def post_boot_sources(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    post_request: BootSourcesPostRequest,
) -> BootSourcesPostResponse:
    boot_asset = await services.boot_assets.create(
        models.BootAsset(**post_request)
    )
    return BootSourcesPostResponse(id=boot_asset.id)


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


class BootAssetVersionPostRequest(BaseModel):
    version: str


class BootAssetVersionPostResponse(BaseModel):
    id: int


@v1_router.post(
    "/bootassets/{id}/versions",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def post_boot_asset_version(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: int,
    post_request: BootAssetVersionPostRequest,
) -> BootAssetVersionPostResponse:
    boot_asset_version = await services.boot_asset_versions.create(
        models.BootAssetVersion(boot_asset_id=id, version=post_request.version)
    )
    return BootAssetVersionPostResponse(id=boot_asset_version.id)


class BootAssetItemPostRequest(BaseModel):
    ftype: str
    sha256: str
    path: str
    size: int
    source_package: str | None = None
    source_version: str | None = None
    source_release: str | None = None
    percent_synced: float


class BootAssetItemPostResponse(BaseModel):
    id: int


@v1_router.post(
    "/bootasset-versions/{id}/items",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def post_boot_asset_item(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: int,
    post_request: BootAssetItemPostRequest,
) -> BootAssetItemPostResponse:
    item = await services.boot_asset_items.create(
        models.BootAssetItem(boot_asset_version_id=id, **post_request)
    )
    return BootAssetItemPostResponse(id=item.id)


@v1_router.post(
    "/images/{boot_asset_version_id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def post_images(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    boot_asset_version_id: int,
    request: Request,
) -> None:
    filename = request.headers["filename"]
    settings = Settings()
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
    multipart_upload = s3.meta.client.create_multipart_upload(
        ACL="public-read",
        Bucket=settings.s3_bucket,
        Key=filename,
        ChecksumAlgorithm="SHA256",
    )
    upload_id = multipart_upload["UploadId"]

    part_no = 1
    parts = []
    # 5MiB
    min_part_size = 5 * 1024**2
    part_chunk = b""
    async for chunk in request.stream():
        part_chunk += chunk
        if len(part_chunk) < min_part_size:
            continue
        multipart_upload_part = s3.MultipartUploadPart(
            settings.s3_bucket, filename, upload_id, part_no
        )
        part = multipart_upload_part.upload(
            Body=part_chunk,
            ChecksumAlgorithm="SHA256",
        )
        parts.append({"PartNumber": part_no, "ETag": part["ETag"]})
        part_no += 1
        part_chunk = b""
        # TODO: update DB with % completed

    part_info = {"Parts": parts}
    s3.meta.client.complete_multipart_upload(
        Bucket=settings.s3_bucket,
        Key=filename,
        UploadId=upload_id,
        MultipartUpload=part_info,
    )
