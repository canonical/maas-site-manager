# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
"""
Enums shared by the MSM API and Temporal worker.
"""

from enum import IntEnum, StrEnum


class IndexType(StrEnum):
    """The types of simplestream indices."""

    INDEX = "index"
    DOWNLOAD = "download"


class DownloadPartition(StrEnum):
    UBUNTU = "download-ubuntu"
    BOOTLOADERS = "download-bootloaders"
    OTHER = "download-other"

    def content_id(self, reversed_fqdn: str) -> str:
        if self.value == DownloadPartition.UBUNTU:
            return f"{reversed_fqdn}:stream:v3:{self.value}"
        return f"{reversed_fqdn}:stream:v1:{self.value}"


class BootAssetKind(IntEnum):
    """The types of Boot Assets."""

    OS = 0
    BOOTLOADER = 1


class BootAssetLabel(StrEnum):
    """The types of labels for Boot Assets."""

    STABLE = "stable"
    CANDIDATE = "candidate"


class ItemFileType(StrEnum):
    """The allowable file types of Boot Asset Items."""

    # Tarball of root image.
    ROOT_TGZ = "root-tgz"
    ROOT_TBZ = "root-tbz"
    ROOT_TXZ = "root-txz"

    # Tarball of dd image.
    ROOT_DD = "root-dd"
    ROOT_DDTAR = "root-dd.tar"

    # Raw dd image
    ROOT_DDRAW = "root-dd.raw"

    # Compressed dd image types
    ROOT_DDBZ2 = "root-dd.bz2"
    ROOT_DDGZ = "root-dd.gz"
    ROOT_DDXZ = "root-dd.xz"

    # Compressed tarballs of dd images
    ROOT_DDTBZ = "root-dd.tar.bz2"
    ROOT_DDTXZ = "root-dd.tar.xz"
    # For backwards compatibility, DDTGZ files are named root-dd
    ROOT_DDTGZ = "root-dd"

    # Following are not allowed on user upload. Only used for syncing
    # from another simplestreams source. (Most likely images.maas.io)

    # Root Image (gets converted to root-image root-tgz, on the rack)
    ROOT_IMAGE = "root-image.gz"

    # Root image in SquashFS form, does not need to be converted
    SQUASHFS_IMAGE = "squashfs"

    # Boot Kernel
    BOOT_KERNEL = "boot-kernel"

    # Boot Initrd
    BOOT_INITRD = "boot-initrd"

    # Boot DTB
    BOOT_DTB = "boot-dtb"

    # tar.xz of files which need to be extracted so the files are usable
    # by MAAS
    ARCHIVE_TAR_XZ = "archive.tar.xz"

    # Manifest
    MANIFEST = "manifest"


class TaskStatus(StrEnum):
    STARTED = "started"
    COMPLETE = "complete"
    FAILED = "failed"
    UNKNOWN = "unknown"
