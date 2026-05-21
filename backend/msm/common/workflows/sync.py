# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
"""
Temporal workflow names and parameter classes for boot source synchronization.

These definitions are shared between the workflow implementations in the temporal
package and the API endpoints that initiate workflows, ensuring consistency
across the entire MSM system.
"""

from dataclasses import dataclass

SYNC_UPSTREAM_SOURCE_WF_NAME = "SyncUpstreamSource"
REFRESH_UPSTREAM_SOURCE_WF_NAME = "RefreshUpstreamSource"

DOWNLOAD_UPSTREAM_IMAGE_WF_NAME = "DownloadUpstreamImage"

DELETE_ITEMS_WF_NAME = "DeleteItems"
REMOVE_STALE_IMAGES_WF_NAME = "RemoveStaleImages"

WORKER_JWT_REFRESH_WF_NAME = "WorkerJwtRefresh"


@dataclass
class S3Params:
    """Configuration parameters for S3-compatible storage operations."""

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    path: str


@dataclass
class DownloadUpstreamImageParams:
    """Parameters for the boot asset item download workflow."""

    ss_root_url: str
    msm_url: str
    msm_jwt: str
    boot_asset_item_id: int
    s3_params: S3Params
    timeout: int = 120


@dataclass
class SyncUpstreamSourceParams:
    """Parameters for the boot source synchronization workflow."""

    msm_url: str
    msm_jwt: str
    boot_source_id: int
    s3_params: S3Params


@dataclass
class RefreshUpstreamSourceParams:
    """Parameters for the boot source catalog refresh workflow."""

    msm_url: str
    msm_jwt: str
    boot_source_id: int


@dataclass
class DeleteItemsParams:
    """Parameters for the bulk boot asset deletion workflow."""

    s3_params: S3Params
    item_ids: list[int]


@dataclass
class RemoveStaleImagesParams:
    """Parameters for the stale boot asset cleanup workflow."""

    msm_url: str
    msm_jwt: str
    boot_source_id: int
    versions_to_keep: int = 2


@dataclass
class WorkerJwtRefreshParams:
    """Parameters for the worker JWT refresh workflow."""

    msm_url: str
    msm_jwt: str
