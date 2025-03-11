from datetime import datetime
from logging import getLogger
from typing import Annotated, Any
from urllib.parse import urlparse

import boto3  # type: ignore
from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ValidationError
from streaming_form_data import StreamingFormDataParser  # type: ignore
from streaming_form_data.targets import BaseTarget, ValueTarget  # type: ignore
import streaming_form_data.validators  # type: ignore

from msm.api.dependencies import services
from msm.api.exceptions.catalog import (
    BadRequestException,
    BaseExceptionDetail,
    FileTooLargeException,
    NotFoundException,
)
from msm.api.exceptions.constants import ExceptionCode
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
    boot_source_id: int
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
    eol: datetime
    esm_eol: datetime


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
    if not await services.boot_sources.get_by_id(post_request.boot_source_id):
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Source does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[
                        f"BootSource ID {post_request.boot_source_id} does not exist"
                    ],
                    field="bootsource_id",
                    location="body",
                )
            ],
        )
    boot_asset = await services.boot_assets.create(
        models.BootAssetCreate(**post_request.model_dump())
    )
    return BootAssetsPostResponse(id=boot_asset.id)


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
    boot_source = await services.boot_sources.create(
        models.BootSourceCreate(**post_request.model_dump())
    )
    return BootSourcesPostResponse(id=boot_source.id)


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
    if not await services.boot_assets.get_by_id(id):
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Asset does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"BootAsset ID {id} does not exist"],
                    field="id",
                    location="path",
                )
            ],
        )
    boot_asset_version = await services.boot_asset_versions.create(
        models.BootAssetVersionCreate(
            boot_asset_id=id, version=post_request.version
        )
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
    if not await services.boot_asset_versions.get_by_id(id):
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Asset Version does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"BootAssetVersion ID {id} does not exist"],
                    field="id",
                    location="path",
                )
            ],
        )
    item = await services.boot_asset_items.create(
        models.BootAssetItemCreate(
            boot_asset_version_id=id, **post_request.model_dump()
        )
    )
    return BootAssetItemPostResponse(id=item.id)


boot_asset_items_sort_parameters = SortParamParser(
    fields=[
        "ftype",
        "sha256",
        "path",
        "size",
        "source_package",
        "source_version",
        "source_release",
        "bytes_synced",
    ]
)


class BootAssetItemsGetResponse(PaginatedResults):
    items: list[models.BootAssetItem]


@v1_router.get(
    "/bootasset-items",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_boot_asset_items(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    sort_params: Annotated[
        list[SortParam], Depends(boot_asset_items_sort_parameters)
    ],
    pagination_params: Annotated[PaginationParams, Depends()],
) -> BootAssetItemsGetResponse:
    total, results = await services.boot_asset_items.get(
        sort_params,
        offset=pagination_params.offset,
        limit=pagination_params.size,
    )
    return BootAssetItemsGetResponse(
        total=total,
        page=pagination_params.page,
        size=pagination_params.size,
        items=list(results),
    )


class S3MultipartUploadTarget(BaseTarget):  # type: ignore
    MIN_PART_SIZE = 5 * 1024**2  # 5MiB

    def __init__(
        self, settings: Settings, filename: str, max_upload_size_gb: int
    ) -> None:
        self.s3 = boto3.resource(
            "s3",
            use_ssl=False,
            verify=False,
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )
        self.s3_bucket = settings.s3_bucket
        self.filename = filename
        self.max_upload_size_bytes = max_upload_size_gb * 1000000000
        multipart_upload = self.s3.meta.client.create_multipart_upload(
            ACL="public-read",
            Bucket=settings.s3_bucket,
            Key=filename,
            ChecksumAlgorithm="SHA256",
        )
        self.upload_id = multipart_upload["UploadId"]
        self.current_chunk = b""
        self.part_no = 1
        self.parts: list[dict[str, Any]] = []
        self.bytes_sent = 0
        super().__init__(
            validator=streaming_form_data.validators.MaxSizeValidator(
                self.max_upload_size_bytes
            )
        )

    def upload_current_chunk(self) -> None:
        multipart_upload_part = self.s3.MultipartUploadPart(
            self.s3_bucket, self.filename, self.upload_id, self.part_no
        )
        part = multipart_upload_part.upload(
            Body=self.current_chunk,
            ChecksumAlgorithm="SHA256",
        )
        self.parts.append({"ETag": part["ETag"], "PartNumber": self.part_no})
        self.part_no += 1
        self.bytes_sent += len(self.current_chunk)
        self.current_chunk = b""

    def abort_upload(self) -> None:
        self.s3.meta.client.abort_multipart_upload(
            Bucket=self.s3_bucket,
            Key=self.filename,
            UploadId=self.upload_id,
        )

    def complete_upload(self) -> None:
        self.s3.meta.client.complete_multipart_upload(
            Bucket=self.s3_bucket,
            Key=self.filename,
            UploadId=self.upload_id,
            MultipartUpload={"Parts": self.parts},
        )

    def on_data_received(self, chunk: bytes) -> None:
        self.current_chunk += chunk
        if len(self.current_chunk) < self.MIN_PART_SIZE:
            return
        self.upload_current_chunk()


class BootAssetItemValueValidator:
    def __init__(self, type: type, name: str):
        self._type = type
        self._name = name

    def __call__(self, chunk: bytes) -> None:
        try:
            self._type(chunk)
        except:
            raise BadRequestException(
                message=f"Invalid type for {self._name}, expected {self._type}",
                code=ExceptionCode.INVALID_PARAMS,
                details=[
                    BaseExceptionDetail(
                        reason=ExceptionCode.INVALID_PARAMS,
                        messages=[f"Invalid type for {self._name}"],
                        field=self._name,
                        location="body",
                    )
                ],
            )


@v1_router.post(
    "/bootasset-items/{boot_asset_version_id}",
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
) -> models.BootAssetItem:
    boot_asset_version = await services.boot_asset_versions.get_by_id(
        boot_asset_version_id
    )
    if not boot_asset_version:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Asset Version does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[
                        f"BootAssetVersion ID {boot_asset_version_id} does not exist"
                    ],
                    field="boot_asset_version_id",
                    location="path",
                )
            ],
        )
    settings = Settings()
    api_settings = await services.settings.get()
    if not urlparse(settings.s3_endpoint).scheme:
        settings.s3_endpoint = f"http://{settings.s3_endpoint}"

    parser = StreamingFormDataParser(headers=request.headers)
    ftype = ValueTarget(validator=BootAssetItemValueValidator(str, "ftype"))
    parser.register("ftype", ftype)
    sha256 = ValueTarget(validator=BootAssetItemValueValidator(str, "sha256"))
    parser.register("sha256", sha256)
    path = ValueTarget(validator=BootAssetItemValueValidator(str, "path"))
    parser.register("path", path)
    size = ValueTarget(validator=BootAssetItemValueValidator(int, "size"))
    parser.register("size", size)
    # don't need to pass type as str | None, since validator won't be called if it isn't passed
    source_package = ValueTarget(
        validator=BootAssetItemValueValidator(str, "source_package")
    )
    parser.register("source_package", source_package)
    source_version = ValueTarget(
        validator=BootAssetItemValueValidator(str, "source_version")
    )
    parser.register("source_version", source_version)
    source_release = ValueTarget(
        validator=BootAssetItemValueValidator(str, "source_release")
    )
    parser.register("source_release", source_release)

    tmp_item = await services.boot_asset_items.create_temporary(
        boot_asset_version_id
    )
    s3_upload_target = S3MultipartUploadTarget(
        settings,
        str(tmp_item.id),
        api_settings.max_image_upload_size_gb,
    )
    parser.register("file", s3_upload_target)

    async for chunk in request.stream():
        try:
            await run_in_threadpool(parser.data_received, chunk)
        except streaming_form_data.validators.ValidationError:
            await services.boot_asset_items.delete(tmp_item.id)
            await run_in_threadpool(s3_upload_target.abort_upload)
            raise FileTooLargeException(
                message="Uploaded file is too large",
                code=ExceptionCode.FILE_TOO_LARGE,
                details=[
                    BaseExceptionDetail(
                        reason=ExceptionCode.FILE_TOO_LARGE,
                        messages=["Uploaded file is too large"],
                        field="file",
                        location="body",
                    )
                ],
            )
    try:
        boot_asset_item = await services.boot_asset_items.update(
            tmp_item.id,
            models.BootAssetItemUpdate(
                ftype=ftype.value.decode(),
                sha256=sha256.value.decode(),
                path=path.value.decode(),
                size=int(size.value),
                source_package=source_package.value.decode()
                if source_package.value
                else None,
                source_version=source_version.value.decode()
                if source_version.value
                else None,
                source_release=source_release.value.decode()
                if source_release.value
                else None,
            ),
        )
    except ValidationError as e:
        await services.boot_asset_items.delete(tmp_item.id)
        await run_in_threadpool(s3_upload_target.abort_upload)
        details = []
        for err in e.errors():
            details.append(
                BaseExceptionDetail(
                    reason=ExceptionCode.INVALID_PARAMS,
                    messages=[err["msg"]],
                    location="body",
                    field=err["loc"][0],
                )
            )
        raise BadRequestException(
            message="One or more request parameters are invalid",
            code=ExceptionCode.INVALID_PARAMS,
            details=details,
        )
    # last part may have been left behind if it was smaller than
    # the minimum upload size.
    # the last upload has no minimum upload size requirement.
    if s3_upload_target.current_chunk:
        await run_in_threadpool(s3_upload_target.upload_current_chunk)
    if boot_asset_item.size != s3_upload_target.bytes_sent:
        await services.boot_asset_items.delete(tmp_item.id)
        await run_in_threadpool(s3_upload_target.abort_upload)
        raise BadRequestException(
            message="The size of the uploaded file does not match the 'size' parameter in the request",
            code=ExceptionCode.INVALID_PARAMS,
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.INVALID_PARAMS,
                    messages=["File size does not match uploaded bytes"],
                    field="size",
                    location="body",
                )
            ],
        )
    await services.boot_asset_items.update_bytes_synced(
        boot_asset_item.id, s3_upload_target.bytes_sent
    )
    await run_in_threadpool(s3_upload_target.complete_upload)
    return boot_asset_item
