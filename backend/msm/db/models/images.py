from datetime import datetime
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
)


class BootAssetKind(int, Enum):
    OS = 0
    BOOTLOADER = 1


class BootAssetLabel(str, Enum):
    STABLE = "stable"
    CANDIDATE = "candidate"


class BootAssetItem(BaseModel):
    id: int
    boot_asset_version_id: int
    ftype: str
    sha256: str
    path: str
    size: int
    source_package: str | None = None
    source_version: str | None = None
    source_release: str | None = None
    bytes_synced: int


class BootAssetItemCreate(BaseModel):
    boot_asset_version_id: int
    ftype: str
    sha256: str
    path: str
    size: int
    source_package: str | None = None
    source_version: str | None = None
    source_release: str | None = None


class BootAssetItemUpdate(BaseModel):
    ftype: str | None = None
    sha256: str | None = None
    path: str | None = None
    size: int | None = None
    source_package: str | None = None
    source_version: str | None = None
    source_release: str | None = None


class BootAssetVersion(BaseModel):
    id: int
    boot_asset_id: int
    version: str


class BootAssetVersionCreate(BaseModel):
    boot_asset_id: int
    version: str


class BootAsset(BaseModel):
    id: int
    boot_source_id: int
    kind: BootAssetKind
    label: BootAssetLabel
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


class BootAssetCreate(BaseModel):
    boot_source_id: int
    kind: BootAssetKind
    label: BootAssetLabel
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


class BootSourceSelection(BaseModel):
    id: int
    boot_source_id: int
    label: BootAssetLabel
    os: str
    release: str
    arches: list[str]


class BootSourceSelectionCreate(BaseModel):
    boot_source_id: int
    label: BootAssetLabel
    os: str
    release: str
    arches: list[str]


class BootSourceSelectionUpdate(BaseModel):
    """The allowed updates to a BootSourceSelection from a user."""

    label: BootAssetLabel | None = None
    os: str | None = None
    release: str | None = None
    arches: list[str] | None = None


class BootSource(BaseModel):
    id: int
    priority: int
    url: str
    keyring: str | None = None
    sync_interval: int = Field(ge=0)


class BootSourceCreate(BaseModel):
    priority: int
    url: str
    keyring: str | None = None
    sync_interval: int = Field(ge=0)


class BootSourceUpdate(BaseModel):
    """The allowed updates to a BootSource from a user."""

    priority: int | None = None
    url: str | None = None
    keyring: str | None = None
    sync_interval: int | None = Field(default=None, ge=0)
