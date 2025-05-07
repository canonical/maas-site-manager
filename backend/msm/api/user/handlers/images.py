from datetime import MAXYEAR, UTC, datetime
from hashlib import sha256
from logging import getLogger
from os.path import join
from typing import Annotated, Any, Self
from urllib.parse import urlparse

import boto3  # type: ignore
from fastapi import APIRouter, Depends, Path, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.exc import IntegrityError
from starlette.background import BackgroundTask
from starlette.types import Send
from streaming_form_data import StreamingFormDataParser  # type: ignore
from streaming_form_data.targets import BaseTarget, ValueTarget  # type: ignore
import streaming_form_data.validators  # type: ignore

from msm.api.dependencies import services
from msm.api.exceptions.catalog import (
    AlreadyExistsException,
    BadRequestException,
    BaseExceptionDetail,
    FileTooLargeException,
    ForbiddenException,
    NotFoundException,
)
from msm.api.exceptions.constants import ExceptionCode
from msm.api.exceptions.responses import (
    AlreadyExistsErrorResponseModel,
    BadRequestErrorResponseModel,
    ForbiddenErrorResponseModel,
    NotFoundErrorResponseModel,
    UnauthorizedErrorResponseModel,
    ValidationErrorResponseModel,
)
from msm.api.user.auth import (
    authenticated_user,
    verify_authenticated_user_or_worker,
)
from msm.api.user.forms import (
    BootAssetFilterParams,
    BootAssetItemFilterParams,
    BootAssetVersionFilterParams,
    boot_asset_filter_params,
    boot_asset_item_filter_params,
    boot_asset_version_filter_params,
)
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
    authenticated_user: Annotated[
        models.User | None, Depends(verify_authenticated_user_or_worker)
    ],
    sort_params: Annotated[
        list[SortParam], Depends(boot_asset_sort_parameters)
    ],
    pagination_params: Annotated[PaginationParams, Depends()],
    filter_params: Annotated[
        BootAssetFilterParams, Depends(boot_asset_filter_params)
    ],
) -> BootAssetsGetResponse:
    """Return boot assets."""
    total, results = await services.boot_assets.get(
        sort_params,
        offset=pagination_params.offset,
        limit=pagination_params.size,
        **filter_params._asdict(),
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
        404: {"model": NotFoundErrorResponseModel},
        409: {"model": AlreadyExistsErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def post_boot_assets(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[
        models.User | None, Depends(verify_authenticated_user_or_worker)
    ],
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
    try:
        boot_asset = await services.boot_assets.create(
            models.BootAssetCreate(**post_request.model_dump())
        )
        return BootAssetsPostResponse(id=boot_asset.id)
    except IntegrityError:
        raise AlreadyExistsException(
            code=ExceptionCode.ALREADY_EXISTS,
            message="This boot asset already exists.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.ALREADY_EXISTS,
                    messages=[
                        "This boot asset already exists for the given boot source."
                    ],
                    field="os,release,arch,subarch",
                    location="body",
                )
            ],
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
    "/bootasset-sources/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_boot_source_by_id(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: int,
) -> models.BootSource:
    bs = await services.boot_sources.get_by_id(id)
    if bs is None:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Source does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"BootSource ID {id} does not exist"],
                    field="id",
                    location="path",
                )
            ],
        )
    return bs


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


class BootSourcesPatchRequest(BaseModel):
    priority: int | None = None
    url: str | None = None
    keyring: str | None = None
    sync_interval: int | None = Field(default=None, ge=0)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def check_at_least_one_field_present(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be set.")
        return self


@v1_router.patch(
    "/bootasset-sources/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def patch_boot_source(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: Annotated[
        int, Path(title="The ID of the Boot Source to update", ge=2)
    ],
    patch_request: BootSourcesPatchRequest,
) -> models.BootSource:
    bs = await services.boot_sources.get_by_id(id)
    if bs is None:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Source does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"BootSource ID {id} does not exist"],
                    field="id",
                    location="path",
                )
            ],
        )
    updated_source = await services.boot_sources.update(
        id, models.BootSourceUpdate(**patch_request.model_dump())
    )
    return updated_source


@v1_router.delete(
    "/bootasset-sources/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def delete_boot_source(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: Annotated[
        int, Path(title="The ID of the Boot Source to delete", ge=2)
    ],
) -> None:
    bs = await services.boot_sources.get_by_id(id)
    if bs is None:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Source does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"BootSource ID {id} does not exist"],
                    field="id",
                    location="path",
                )
            ],
        )
    await services.boot_sources.delete(id)


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
        404: {"model": NotFoundErrorResponseModel},
        409: {"model": AlreadyExistsErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def post_boot_asset_version(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[
        models.User | None, Depends(verify_authenticated_user_or_worker)
    ],
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

    try:
        boot_asset_version = await services.boot_asset_versions.create(
            models.BootAssetVersionCreate(
                boot_asset_id=id, version=post_request.version
            )
        )
        return BootAssetVersionPostResponse(id=boot_asset_version.id)
    except IntegrityError:
        raise AlreadyExistsException(
            code=ExceptionCode.ALREADY_EXISTS,
            message="This boot asset version already exists.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.ALREADY_EXISTS,
                    messages=[
                        "This boot asset version already exists for the given boot asset."
                    ],
                    field="version",
                    location="body",
                )
            ],
        )


boot_asset_version_sort_parameters = SortParamParser(
    fields=[
        "version",
    ]
)


class BootAssetVersionsGetResponse(PaginatedResults):
    items: list[models.BootAssetVersion]


@v1_router.get(
    "/bootasset-versions",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def get_boot_asset_versions(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[
        models.User | None, Depends(verify_authenticated_user_or_worker)
    ],
    sort_params: Annotated[
        list[SortParam], Depends(boot_asset_version_sort_parameters)
    ],
    pagination_params: Annotated[PaginationParams, Depends()],
    filter_params: Annotated[
        BootAssetVersionFilterParams, Depends(boot_asset_version_filter_params)
    ],
) -> BootAssetVersionsGetResponse:
    """Return Boot Asset Versions"""
    total, results = await services.boot_asset_versions.get(
        sort_params,
        offset=pagination_params.offset,
        limit=pagination_params.size,
        **filter_params._asdict(),
    )
    return BootAssetVersionsGetResponse(
        total=total,
        page=pagination_params.page,
        size=pagination_params.size,
        items=list(results),
    )


class BootAssetItemPostRequest(BaseModel):
    ftype: str
    sha256: str
    path: str
    file_size: int
    source_package: str | None = None
    source_version: str | None = None
    source_release: str | None = None


class BootAssetItemPostResponse(BaseModel):
    id: int


@v1_router.post(
    "/bootasset-versions/{id}/items",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        409: {"model": AlreadyExistsErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def post_boot_asset_item(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[
        models.User | None, Depends(verify_authenticated_user_or_worker)
    ],
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

    try:
        item = await services.boot_asset_items.create(
            models.BootAssetItemCreate(
                boot_asset_version_id=id, **post_request.model_dump()
            )
        )
        return BootAssetItemPostResponse(id=item.id)
    except IntegrityError:
        raise AlreadyExistsException(
            code=ExceptionCode.ALREADY_EXISTS,
            message="This boot asset item already exists.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.ALREADY_EXISTS,
                    messages=[
                        "This boot asset item already exists for the given boot asset version."
                    ],
                    field="ftype",
                    location="body",
                )
            ],
        )


boot_asset_items_sort_parameters = SortParamParser(
    fields=[
        "ftype",
        "sha256",
        "path",
        "file_size",
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
    authenticated_user: Annotated[
        models.User | None, Depends(verify_authenticated_user_or_worker)
    ],
    sort_params: Annotated[
        list[SortParam], Depends(boot_asset_items_sort_parameters)
    ],
    pagination_params: Annotated[PaginationParams, Depends()],
    filter_params: Annotated[
        BootAssetItemFilterParams, Depends(boot_asset_item_filter_params)
    ],
) -> BootAssetItemsGetResponse:
    total, results = await services.boot_asset_items.get(
        sort_params,
        offset=pagination_params.offset,
        limit=pagination_params.size,
        **filter_params._asdict(),
    )
    return BootAssetItemsGetResponse(
        total=total,
        page=pagination_params.page,
        size=pagination_params.size,
        items=list(results),
    )


@v1_router.delete(
    "/bootasset-items/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def delete_images(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    id: int,
) -> None:
    boot_asset_version = await services.boot_asset_items.get_by_id(id)
    if not boot_asset_version:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Asset Item does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"BootAssetItem ID {id} does not exist"],
                    field="id",
                    location="path",
                )
            ],
        )
    settings = Settings()
    s3 = boto3.resource(
        "s3",
        use_ssl=False,
        verify=False,
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )
    await run_in_threadpool(
        s3.meta.client.delete_object, Bucket=settings.s3_bucket, Key=str(id)
    )
    await services.boot_asset_items.delete(id)


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
        self.filename = (
            join(
                settings.s3_path if settings.s3_path else "",
                filename,
            ),
        )
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
        self.sha256 = sha256()
        super().__init__(
            validator=streaming_form_data.validators.MaxSizeValidator(
                self.max_upload_size_bytes
            )
        )

    def upload(self) -> None:
        multipart_upload_part = self.s3.MultipartUploadPart(
            self.s3_bucket, self.filename, self.upload_id, self.part_no
        )
        part = multipart_upload_part.upload(
            Body=self.current_chunk,
            ChecksumAlgorithm="SHA256",
        )
        self.parts.append({"ETag": part["ETag"], "PartNumber": self.part_no})

    def upload_current_chunk(self) -> None:
        self.upload()
        self.sha256.update(self.current_chunk)
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


CUSTOM_IMAGE_FILE_EXTENSIONS = {
    "tgz": models.ItemFileType.ROOT_TGZ,
    "tbz": models.ItemFileType.ROOT_TBZ,
    "txz": models.ItemFileType.ROOT_TXZ,
    "ddtgz": models.ItemFileType.ROOT_DDTGZ,
    "ddtbz": models.ItemFileType.ROOT_DDTBZ,
    "ddtxz": models.ItemFileType.ROOT_DDTXZ,
    "ddtar": models.ItemFileType.ROOT_DDTAR,
    "ddbz2": models.ItemFileType.ROOT_DDBZ2,
    "ddgz": models.ItemFileType.ROOT_DDGZ,
    "ddxz": models.ItemFileType.ROOT_DDXZ,
    "ddraw": models.ItemFileType.ROOT_DDRAW,
}


class FilenameValueValidator:
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
        ext = chunk.decode().split(".")[-1]
        if ext not in CUSTOM_IMAGE_FILE_EXTENSIONS.keys():
            raise BadRequestException(
                message="Unsupported file type",
                code=ExceptionCode.INVALID_PARAMS,
                details=[
                    BaseExceptionDetail(
                        reason=ExceptionCode.INVALID_PARAMS,
                        messages=[
                            f"Unsupported file type {ext}, must be one of {CUSTOM_IMAGE_FILE_EXTENSIONS.keys()}"
                        ],
                        field="filename",
                        location="body",
                    )
                ],
            )


def get_file_type_from_filename(filename: str) -> models.ItemFileType:
    ext = filename.split(".")[-1]
    # ext is verified above, don't need to handle KeyError
    return CUSTOM_IMAGE_FILE_EXTENSIONS[ext]


@v1_router.post(
    "/images",
    responses={
        400: {"model": BadRequestErrorResponseModel},
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "properties": {
                            "os": {
                                "type": "string",
                                "example": "ubuntu",
                            },
                            "release": {
                                "type": "string",
                                "example": "noble",
                            },
                            "title": {
                                "type": "string",
                                "example": "My Custom Image",
                            },
                            "arch": {
                                "type": "string",
                                "example": "amd64",
                            },
                            "file_size": {
                                "type": "number",
                                "example": 123456789,
                            },
                            "filename": {
                                "type": "string",
                                "example": "custom-image.tgz",
                            },
                            "file": {
                                "type": "string",
                                "format": "binary",
                            },
                        }
                    }
                }
            },
        },
    },
)
async def post_images(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[models.User, Depends(authenticated_user)],
    request: Request,
) -> models.BootAssetItem:
    settings = Settings()
    api_settings = await services.settings.get()
    if not urlparse(settings.s3_endpoint).scheme:
        settings.s3_endpoint = f"http://{settings.s3_endpoint}"

    parser = StreamingFormDataParser(headers=request.headers)
    os = ValueTarget(validator=BootAssetItemValueValidator(str, "os"))
    parser.register("os", os)
    release = ValueTarget(
        validator=BootAssetItemValueValidator(str, "release")
    )
    parser.register("release", release)
    title = ValueTarget(validator=BootAssetItemValueValidator(str, "title"))
    parser.register("title", title)
    arch = ValueTarget(validator=BootAssetItemValueValidator(str, "arch"))
    parser.register("arch", arch)
    file_size = ValueTarget(
        validator=BootAssetItemValueValidator(int, "file_size")
    )
    parser.register("file_size", file_size)
    filename = ValueTarget(validator=FilenameValueValidator(str, "filename"))
    parser.register("filename", filename)

    tmp_item = await services.boot_asset_items.create_temporary()
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
        except BadRequestException:
            await services.boot_asset_items.delete(tmp_item.id)
            raise

    # last part may have been left behind if it was smaller than
    # the minimum upload size.
    # the last upload has no minimum upload size requirement.
    if s3_upload_target.current_chunk:
        await run_in_threadpool(s3_upload_target.upload_current_chunk)

    asset = await services.boot_assets.get_or_create(
        models.BootAssetCreate(
            boot_source_id=1,
            kind=models.BootAssetKind.OS,
            label=models.BootAssetLabel.STABLE,
            os=os.value.decode(),
            release=release.value.decode(),
            codename="",
            title=title.value.decode(),
            arch=arch.value.decode(),
            subarch="",
            compatibility=[],
            flavor="",
            base_image=f"{os.value.decode()}/{release.value.decode()}",
            eol=datetime(MAXYEAR, 12, 31, 23, tzinfo=UTC),
            esm_eol=datetime(MAXYEAR, 12, 31, 23, tzinfo=UTC),
        )
    )
    version = await services.boot_asset_versions.create_next_revision(
        asset.id, datetime.now()
    )
    boot_asset_item = await services.boot_asset_items.update(
        tmp_item.id,
        models.BootAssetItemUpdate(
            boot_asset_version_id=version.id,
            ftype=get_file_type_from_filename(filename.value.decode()),
            file_size=int(file_size.value),
            sha256=s3_upload_target.sha256.hexdigest(),
        ),
    )
    if boot_asset_item.file_size != s3_upload_target.bytes_sent:
        await services.boot_asset_items.delete(boot_asset_item.id)
        await services.boot_asset_versions.delete(version.id)
        await services.boot_assets.delete(asset.id)
        await run_in_threadpool(s3_upload_target.abort_upload)
        raise BadRequestException(
            message="The size of the uploaded file does not match the 'file_size' parameter in the request",
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


class BootAssetItemPatchRequest(BaseModel):
    ftype: str | None = None
    source_package: str | None = None
    source_version: str | None = None
    source_release: str | None = None
    bytes_synced: int | None = None  # can only be changed by workers

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def check_at_least_one_field_present(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be set.")
        return self


@v1_router.patch(
    "/bootasset-items/{id}",
    responses={
        401: {"model": UnauthorizedErrorResponseModel},
        403: {"model": ForbiddenErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
        422: {"model": ValidationErrorResponseModel},
    },
)
async def patch_boot_asset_items(
    services: Annotated[ServiceCollection, Depends(services)],
    authenticated_user: Annotated[
        models.User | None, Depends(verify_authenticated_user_or_worker)
    ],
    id: int,
    patch_request: BootAssetItemPatchRequest,
) -> models.BootAssetItem:
    if (
        patch_request.bytes_synced is not None
        and authenticated_user is not None
    ):
        raise ForbiddenException(
            code=ExceptionCode.MISSING_PERMISSIONS,
            message="Insufficient permissions.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_PERMISSIONS,
                    messages=[
                        "Users cannot change a Boot Asset Item's bytes_synced field."
                    ],
                    field="Authorization",
                    location="header",
                )
            ],
        )
    boot_asset_item = await services.boot_asset_items.get_by_id(id)
    if not boot_asset_item:
        raise NotFoundException(
            code=ExceptionCode.MISSING_RESOURCE,
            message="Boot Asset Item does not exist.",
            details=[
                BaseExceptionDetail(
                    reason=ExceptionCode.MISSING_RESOURCE,
                    messages=[f"BootAssetItem ID {id} does not exist"],
                    field="boot_asset_item_id",
                    location="path",
                )
            ],
        )
    updated_item = await services.boot_asset_items.update(
        id, models.BootAssetItemUpdate(**patch_request.model_dump())
    )
    return updated_item


class S3StreamResponse(StreamingResponse):
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str = "application/octet-stream",
        background: BackgroundTask | None = None,
        file_id: str = "",
    ) -> None:
        super().__init__(content, status_code, headers, media_type, background)
        settings = Settings()
        self.file_path = (
            join(
                settings.s3_path if settings.s3_path else "",
                file_id,
            ),
        )
        self.s3_bucket = settings.s3_bucket
        self.s3 = boto3.resource(
            "s3",
            use_ssl=False,
            verify=False,
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )

    async def stream_response(self, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )

        result = self.s3.meta.client.get_object(
            Bucket=self.s3_bucket, Key=self.file_path
        )

        for chunk in result["Body"]:
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


@v1_router.get(
    "/images/{track}/{risk}/{file_path:path}",
    responses={
        400: {"model": BadRequestErrorResponseModel},
        401: {"model": UnauthorizedErrorResponseModel},
        404: {"model": NotFoundErrorResponseModel},
    },
)
async def download(
    services: Annotated[ServiceCollection, Depends(services)],
    track: str,
    risk: str,
    file_path: str,
) -> StreamingResponse:
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

    boot_item = await services.boot_asset_items.get_by_path(file_path)
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
    return S3StreamResponse(content=None, file_id=str(boot_item.id))
