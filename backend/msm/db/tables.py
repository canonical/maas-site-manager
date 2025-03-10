from uuid import uuid4

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
)
from sqlalchemy.types import DateTime

from msm.db.types import Point
from msm.time import now_utc

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
    Column("id", Integer, primary_key=True),
    Column("priority", Integer, nullable=False, default=1),
    Column("url", Text, nullable=False),
    Column("keyring", Text, nullable=True),
    Column("sync_interval", Integer),
)

BootSourceSelection = Table(
    "boot_source_selection",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "boot_source_id", Integer, ForeignKey("boot_source.id"), nullable=False
    ),
    Column("label", Text, nullable=False),
    Column("os", Text, nullable=False),
    Column("release", Text, nullable=False),
    Column("arches", ARRAY(Text), nullable=False),
)

BootAsset = Table(
    "boot_asset",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "boot_source_id", Integer, ForeignKey("boot_source.id"), nullable=False
    ),
    Column("kind", Integer, nullable=False, default=0),
    Column("label", Text, nullable=False),
    Column("os", Text, nullable=False),
    Column("release", Text, nullable=False),
    Column("codename", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("arch", Text, nullable=False),
    Column("subarch", Text, nullable=False),
    Column("compatibility", ARRAY(Text), nullable=False),
    Column("flavor", Text, nullable=False),
    Column("base_image", Text, nullable=False),
    Column("eol", DateTime(timezone=True), nullable=False),
    Column("esm_eol", DateTime(timezone=True), nullable=False),
)

BootAssetVersion = Table(
    "boot_asset_version",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "boot_asset_id", Integer, ForeignKey("boot_asset.id"), nullable=False
    ),
    Column("version", Text, nullable=False),
)

BootAssetItem = Table(
    "boot_asset_item",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column(
        "boot_asset_version_id",
        Integer,
        ForeignKey("boot_asset_version.id"),
        nullable=False,
    ),
    Column("ftype", Text, nullable=False),
    Column("sha256", Text, nullable=False),
    Column("path", Text, nullable=False),
    Column("size", BigInteger, nullable=False),
    Column("source_package", Text, nullable=True),
    Column("source_version", Text, nullable=True),
    Column("source_release", Text, nullable=True),
    Column("bytes_synced", BigInteger, nullable=False, default=0),
)
