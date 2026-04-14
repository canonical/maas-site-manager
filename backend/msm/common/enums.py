# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
"""
Enums shared by the MSM API and Temporal worker.
"""

from datetime import timedelta
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


class DNSSEC(StrEnum):
    AUTO = "auto"
    YES = "yes"
    NO = "no"

    def __str__(self) -> str:
        return str(self.value)


def _timedelta_to_whole_seconds(
    minutes: int = 0, hours: int = 0, days: int = 0
) -> int:
    """Convert arbitrary timedelta to whole seconds."""
    return int(
        timedelta(minutes=minutes, hours=hours, days=days).total_seconds()
    )


class ActiveDiscoveryInterval(IntEnum):
    NEVER = 0
    EVERY_WEEK = _timedelta_to_whole_seconds(days=7)
    EVERY_DAY = _timedelta_to_whole_seconds(days=1)
    EVERY_12_HOURS = _timedelta_to_whole_seconds(hours=12)
    EVERY_6_HOURS = _timedelta_to_whole_seconds(hours=6)
    EVERY_3_HOURS = _timedelta_to_whole_seconds(hours=3)
    EVERY_HOUR = _timedelta_to_whole_seconds(hours=1)
    EVERY_30_MINUTES = _timedelta_to_whole_seconds(minutes=30)
    EVERY_10_MINUTES = _timedelta_to_whole_seconds(minutes=10)


class IPMICipherSuiteID(StrEnum):
    SUITE_17 = "17"
    SUITE_3 = "3"
    DEFAULT = ""
    SUITE_8 = "8"
    SUITE_12 = "12"

    def __str__(self) -> str:
        return str(self.value)


class IPMIPrivilegeLevel(StrEnum):
    USER = "USER"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"

    def __str__(self) -> str:
        return str(self.value)


class IPMIWorkaroundFlags(StrEnum):
    OPENSESSPRIV = "opensesspriv"
    AUTHCAP = "authcap"
    IDZERO = "idzero"
    UNEXPECTEDAUTH = "unexpectedauth"
    FORCEPERMSG = "forcepermsg"
    ENDIANSEQ = "endianseq"
    INTEL20 = "intel20"
    SUPERMICRO20 = "supermicro20"
    SUN20 = "sun20"
    NOCHECKSUMCHECK = "nochecksumcheck"
    INTEGRITYCHECKVALUE = "integritycheckvalue"
    IPMIPING = "ipmiping"
    NONE = ""

    def __str__(self) -> str:
        return str(self.value)


class StorageLayout(StrEnum):
    BCACHE = "bcache"
    BLANK = "blank"
    CUSTOM = "custom"
    FLAT = "flat"
    LVM = "lvm"
    VMFS6 = "vmfs6"
    VMFS7 = "vmfs7"

    def __str__(self) -> str:
        return str(self.value)


class InterfaceType(StrEnum):
    """The vocabulary of possible types for `Interface`."""

    PHYSICAL = "physical"
    BOND = "bond"
    BRIDGE = "bridge"
    VLAN = "vlan"
    ALIAS = "alias"
    # Interface that is created when it is not linked to a node.
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)


class InterfaceLinkType(StrEnum):
    """The vocabulary of possible types to link a `Subnet` to a `Interface`."""

    AUTO = "auto"
    DHCP = "dhcp"
    STATIC = "static"
    LINK_UP = "link_up"

    def __str__(self) -> str:
        return str(self.value)
