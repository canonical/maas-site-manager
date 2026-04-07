from uuid import uuid4

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
)
from sqlalchemy.schema import Sequence
from sqlalchemy.types import DateTime

from msm.apiserver.db.types import Point
from msm.common.enums import TaskStatus
from msm.common.time import now_utc, utc_from_timestamp

METADATA = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_`%(constraint_name)s`",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


# Internal configuration options that are shared by units of the service
# installation
Config = Table(
    "config",
    METADATA,
    Column("name", Text, primary_key=True),
    Column("value", JSONB, nullable=False),
)

# Global application settings that can be configured through the API
Setting = Table(
    "setting",
    METADATA,
    Column("name", Text, primary_key=True),
    Column("value", JSONB, nullable=False),
)


Site = Table(
    "site",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column("name", Text, nullable=False, index=True, default=""),
    Column("address", Text, nullable=False, default=""),
    Column("city", Text, nullable=False, default=""),
    Column("country", Text, nullable=False, default=""),  # ISO 3166 Alpha2
    Column("coordinates", Point),
    Column("note", Text, nullable=False, default=""),
    Column("postal_code", Text, nullable=False, default=""),
    Column("state", Text, nullable=False, default=""),
    Column("timezone", Text, nullable=False, default=""),
    Column("url", Text, nullable=False, default=""),
    Column("accepted", Boolean, nullable=False, default=False, index=True),
    Column(
        "created", DateTime(timezone=True), nullable=False, default=now_utc
    ),
    Column("deleted", DateTime(timezone=True), nullable=True, default=None),
    Column("cluster_uuid", Text, nullable=False, unique=True, default=""),
    Column("known_config_options", ARRAY(Text), nullable=False, default=[]),
    Column("version", Text, nullable=True),
    Column("trigger_image_sync", Boolean, nullable=False, default=False),
    Column(
        "site_profile_id",
        Integer,
        ForeignKey(
            "site_profile.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    ),
)


User = Table(
    "user",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column("email", Text, nullable=False, unique=True, index=True),
    Column("username", Text, nullable=False, unique=True, index=True),
    Column("full_name", Text, nullable=False, default=""),
    Column("password", Text, nullable=False),  # this is the hashed password
    Column("is_admin", Boolean, nullable=False, default=False),
    Column(
        "auth_id",
        UUID(as_uuid=True),
        nullable=False,
        default=uuid4,
        unique=True,
        index=True,
    ),
)


Token = Table(
    "token",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column("value", Text, nullable=False),
    Column("audience", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column(
        "auth_id",
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
    ),
    Column(
        "site_id",
        Integer,
        ForeignKey("site.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    ),
    Column("expired", DateTime(timezone=True), nullable=False),
    Column(
        "created", DateTime(timezone=True), nullable=False, default=now_utc
    ),
    Index(None, "audience", "purpose"),
)


SiteData = Table(
    "site_data",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "site_id",
        Integer,
        ForeignKey("site.id", onupdate="CASCADE", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    ),
    Column("machines_allocated", Integer, nullable=False, default=0),
    Column("machines_deployed", Integer, nullable=False, default=0),
    Column("machines_ready", Integer, nullable=False, default=0),
    Column("machines_error", Integer, nullable=False, default=0),
    Column("machines_other", Integer, nullable=False, default=0),
    Column("last_seen", DateTime(timezone=True)),
)


BootSource = Table(
    "boot_source",
    METADATA,
    Column(
        "id",
        Integer,
        Sequence("source_id_sequence", start=2, increment=1),
        primary_key=True,
    ),
    Column("priority", Integer, nullable=False, default=1),
    Column("url", Text, nullable=False),
    Column("keyring", Text, nullable=True),
    Column("sync_interval", Integer),
    Column("name", Text, nullable=False),
    Column(
        "last_sync",
        DateTime(timezone=True),
        nullable=False,
        default=utc_from_timestamp(0.0),
    ),
)

BootSourceSelection = Table(
    "boot_source_selection",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "boot_source_id",
        Integer,
        ForeignKey("boot_source.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("label", Text, nullable=False),
    Column("os", Text, nullable=False),
    Column("release", Text, nullable=False),
    Column("arch", Text, nullable=False),
    Column("selected", Boolean, nullable=False),
)

BootAsset = Table(
    "boot_asset",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "boot_source_id",
        Integer,
        ForeignKey("boot_source.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("kind", Integer, nullable=False, default=0),
    Column("label", Text, nullable=False),
    Column("os", Text, nullable=False),
    Column("release", Text, nullable=True),
    Column("version", Text, nullable=True),
    Column("krel", Text, nullable=True),
    Column("codename", Text, nullable=True),
    Column("title", Text, nullable=True),
    Column("arch", Text, nullable=False),
    Column("subarch", Text, nullable=True),
    Column("compatibility", ARRAY(Text), nullable=True),
    Column("flavor", Text, nullable=True),
    Column("base_image", Text, nullable=True),
    Column("bootloader_type", Text, nullable=True),
    Column("eol", DateTime(timezone=True), nullable=True),
    Column("esm_eol", DateTime(timezone=True), nullable=True),
    Column("signed", Boolean, nullable=False, default=False),
    UniqueConstraint("boot_source_id", "os", "release", "arch", "subarch"),
)

BootAssetVersion = Table(
    "boot_asset_version",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "boot_asset_id",
        Integer,
        ForeignKey("boot_asset.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("version", Text, nullable=False),
    Column(
        "last_seen", DateTime(timezone=True), nullable=False, default=now_utc
    ),
    UniqueConstraint("boot_asset_id", "version"),
)

BootAssetItem = Table(
    "boot_asset_item",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "boot_asset_version_id",
        Integer,
        ForeignKey("boot_asset_version.id", ondelete="RESTRICT"),
        nullable=True,
    ),
    Column("ftype", Text, nullable=False),
    Column("sha256", Text, nullable=False),
    Column("path", Text, nullable=False),
    Column("file_size", BigInteger, nullable=False),
    Column("source_package", Text, nullable=True),
    Column("source_version", Text, nullable=True),
    Column("source_release", Text, nullable=True),
    Column("bytes_synced", BigInteger, nullable=False, default=0),
    UniqueConstraint("boot_asset_version_id", "ftype", "path"),
)


SiteProfile = Table(
    "site_profile",
    METADATA,
    Column(
        "id",
        Integer,
        Sequence("site_profile_id_sequence", start=2, increment=1),
        primary_key=True,
    ),
    Column("name", Text, unique=True, nullable=False),
    Column("selections", ARRAY(Text), nullable=False),
    Column("global_config", JSONB, nullable=True),
)

SiteStateStatus = Table(
    "site_state_status",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "site_id",
        Integer,
        ForeignKey("site.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    Column(
        "status", Enum(TaskStatus), nullable=False, default=TaskStatus.UNKNOWN
    ),
    Column(
        "selections_status",
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.UNKNOWN,
    ),
    Column(
        "global_config_status",
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.UNKNOWN,
    ),
    Column(
        "image_sync_status",
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.UNKNOWN,
    ),
    Column("errors", ARRAY(Text), nullable=False, default=[]),
)
