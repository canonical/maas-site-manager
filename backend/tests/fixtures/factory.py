from collections.abc import Iterator
from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Any,
    cast,
)
from uuid import (
    UUID,
    uuid4,
)

import pytest
from sqlalchemy import (
    ColumnOperators,
    Sequence,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db.models import (
    BootAsset,
    BootAssetItem,
    BootAssetVersion,
    BootSource,
    BootSourceSelection,
    ConnectionStatus,
    Coordinates,
    PendingSite,
    Site,
    SiteData,
    SiteProfile,
    Token,
    User,
)
from msm.apiserver.db.tables import METADATA
from msm.apiserver.schema import TimeZone
from msm.common.enums import (
    BootAssetKind,
    BootAssetLabel,
    ItemFileType,
)
from msm.common.jwt import (
    JWT,
    TokenAudience,
    TokenPurpose,
)
from msm.common.password import hash_password
from msm.common.time import now_utc


class Factory:
    """Helper for creating test fixtures."""

    def __init__(self, conn: AsyncConnection):
        self.conn = conn
        self._now = now_utc()

    @property
    def now(self) -> datetime:
        return self._now

    @property
    def now_json(self) -> str:
        return self._now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    async def next_id(self, table: str, pk_field: str = "id") -> int:
        """Return next ID for a table primary key."""
        # this assumes default PostgreSQL naming
        sequence = Sequence(f"{table}_{pk_field}_seq")
        result = await self.conn.execute(sequence.next_value())
        return cast(int, result.scalar())

    async def create(
        self,
        table: str,
        data: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Insert one or more entries in a table."""
        result = await self.conn.execute(
            METADATA.tables[table].insert().returning("*"), data
        )
        return [row._asdict() for row in result]

    async def get(
        self,
        table: str,
        *filters: ColumnOperators,
    ) -> list[dict[str, Any]]:
        """Get ore on more entries from a table."""
        tbl = METADATA.tables[table]
        result = await self.conn.execute(
            tbl.select()
            .where(*filters)  # type: ignore[arg-type]
            .order_by(*tbl.primary_key.columns)  # predictable order
        )
        return [row._asdict() for row in result]

    async def delete(self, table: str, id: int) -> None:
        tbl = METADATA.tables[table]
        await self.conn.execute(tbl.delete().where(tbl.c.id == id))

    async def flush(self, table: str) -> None:
        tbl = METADATA.tables[table]
        await self.conn.execute(tbl.delete())

    async def count(
        self,
        table: str,
        *filters: ColumnOperators,
    ) -> int:
        """Count entries from a table."""
        tbl = METADATA.tables[table]
        result = await self.conn.execute(
            func.count().select().select_from(tbl).where(*filters)  # type: ignore[arg-type]
        )
        return result.scalar() or 0

    async def make_User(
        self,
        username: str | None = None,
        password: str | None = None,
        email: str | None = None,
        full_name: str | None = None,
        is_admin: bool = False,
    ) -> User:
        """Create a User."""
        id = await self.next_id("user")
        if username is None:
            username = f"user{id}"
        if password is None:
            password = username
        if email is None:
            email = f"{username}@example.com"
        if full_name is None:
            full_name = username.capitalize()
        [row] = await self.create(
            "user",
            [
                {
                    "id": id,
                    "username": username,
                    "email": email,
                    "full_name": full_name,
                    "is_admin": is_admin,
                    "password": hash_password(password),
                }
            ],
        )
        return User(**row)

    async def make_Token(
        self,
        issuer: str = "issuer",
        auth_id: UUID | None = None,
        lifetime: timedelta = timedelta(minutes=5),
        key: str = "",
        audience: TokenAudience = TokenAudience.SITE,
        purpose: TokenPurpose = TokenPurpose.ENROLMENT,
        site_id: int | None = None,
    ) -> Token:
        """Create a Token."""
        id = await self.next_id("token")
        if auth_id is None:
            auth_id = uuid4()
        token = JWT.create(
            issuer=issuer,
            subject=str(auth_id),
            audience=audience,
            purpose=purpose,
            key=key,
            duration=lifetime,
        )
        [row] = await self.create(
            "token",
            [
                {
                    "id": id,
                    "auth_id": auth_id,
                    "value": token.encoded,
                    "created": self.now,
                    "expired": token.expiration,
                    "audience": audience,
                    "purpose": purpose,
                    "site_id": site_id,
                }
            ],
        )
        return Token(**row)

    async def make_Site(
        self,
        name: str | None = None,
        city: str = "",
        country: str = "",
        url: str | None = None,
        timezone: str | None = None,
        coordinates: Coordinates | None = None,
        address: str = "",
        note: str = "",
        postal_code: str = "",
        state: str = "",
        connection_status: ConnectionStatus = ConnectionStatus.UNKNOWN,
        auth_id: UUID | None = None,
        cluster_uuid: str | None = None,
        accepted: bool = True,
    ) -> Site:
        """Create a Site."""
        id = await self.next_id("site")
        if name is None:
            name = f"site{id}"
        if url is None:
            url = f"https://{name}.example.com/"
        if auth_id is None:
            auth_id = uuid4()
        if cluster_uuid is None:
            cluster_uuid = str(uuid4())
        coords_dict = None
        if coordinates is not None:
            coords_dict = coordinates.model_dump()
        [row] = await self.create(
            "site",
            [
                {
                    "id": id,
                    "name": name,
                    "url": url,
                    "city": city,
                    "country": country,
                    "timezone": (
                        getattr(TimeZone, timezone) if timezone else ""
                    ),
                    "address": address,
                    "note": note,
                    "postal_code": postal_code,
                    "state": state,
                    "coordinates": coords_dict,
                    "accepted": accepted,
                    "created": self.now,
                    "cluster_uuid": cluster_uuid,
                }
            ],
        )
        await self.make_Token(auth_id=auth_id, site_id=row["id"])
        # compute the name_unique attribute
        site_table = METADATA.tables["site"]
        result = await self.conn.execute(
            select(func.count() == 1)
            .select_from(site_table)
            .filter(site_table.c.name == name)
        )
        row["name_unique"] = result.one()[0]
        # because self.create uses 'returning("*")', the custom Coordinates
        # type is not properly translated and is instead a Point. We fix this here:
        if row["coordinates"] is not None:
            coords_tuple = tuple(row["coordinates"])
            row["coordinates"] = {
                "latitude": coords_tuple[0],
                "longitude": coords_tuple[1],
            }
        return Site(connection_status=connection_status, **row)

    async def make_PendingSite(
        self,
        name: str | None = None,
        url: str | None = None,
        auth_id: UUID | None = None,
        cluster_uuid: str | None = None,
    ) -> PendingSite:
        """Create a PendingSite."""
        id = await self.next_id("site")
        if name is None:
            name = f"site{id}"
        if url is None:
            url = f"https://{name}.example.com/"
        if auth_id is None:
            auth_id = uuid4()
        if cluster_uuid is None:
            cluster_uuid = str(uuid4())
        [row] = await self.create(
            "site",
            {
                "id": id,
                "name": name,
                "url": url,
                "accepted": False,
                "created": self.now,
                "cluster_uuid": cluster_uuid,
            },
        )
        await self.make_Token(auth_id=auth_id, site_id=row["id"])
        return PendingSite(**row)

    async def make_SiteData(
        self,
        site_id: int,
        machines_allocated: int = 0,
        machines_deployed: int = 0,
        machines_ready: int = 0,
        machines_error: int = 0,
        machines_other: int = 0,
        last_seen: datetime | None = None,
    ) -> SiteData:
        """Create SiteData for a Site."""
        if last_seen is None:
            last_seen = self.now
        [row] = await self.create(
            "site_data",
            [
                {
                    "site_id": site_id,
                    "machines_allocated": machines_allocated,
                    "machines_deployed": machines_deployed,
                    "machines_ready": machines_ready,
                    "machines_error": machines_error,
                    "machines_other": machines_other,
                    "last_seen": last_seen,
                }
            ],
        )
        machines_total = (
            machines_allocated
            + machines_deployed
            + machines_ready
            + machines_error
            + machines_other
        )
        return SiteData(machines_total=machines_total, **row)

    async def make_SiteProfile(
        self,
        name: str,
        selections: list[str],
        global_config: dict[str, Any] | None = None,
        id: int | None = None,
    ) -> SiteProfile:
        """Create a SiteProfile."""
        data: dict[str, Any] = {
            "name": name,
            "selections": selections,
            "global_config": global_config or {},
        }
        if id is not None:
            data["id"] = id
        [row] = await self.create("site_profile", [data])
        return SiteProfile(**row)

    async def make_Config(self, name: str, value: Any = None) -> None:
        """Create an entry in the global configuration."""
        await self.create("config", {"name": name, "value": value})

    async def make_Setting(self, name: str, value: Any = None) -> None:
        """Create an entry in the global settings."""
        await self.create("setting", {"name": name, "value": value})

    async def make_BootSource(
        self,
        priority: int = 1,
        url: str = "",
        keyring: str | None = None,
        sync_interval: int = 0,
        name: str = "",
        last_sync: datetime | None = None,
    ) -> BootSource:
        [row] = await self.create(
            "boot_source",
            [
                {
                    "priority": priority,
                    "url": url,
                    "keyring": keyring,
                    "sync_interval": sync_interval,
                    "name": name,
                    "last_sync": last_sync or self.now,
                }
            ],
        )
        return BootSource(**row)

    async def make_custom_BootSource(
        self,
        priority: int = 1,
        url: str = "",
        keyring: str | None = None,
        sync_interval: int = 0,
        name: str = "",
        last_sync: datetime | None = None,
    ) -> BootSource:
        [row] = await self.create(
            "boot_source",
            [
                {
                    "id": 1,
                    "priority": priority,
                    "url": url,
                    "keyring": keyring,
                    "sync_interval": sync_interval,
                    "name": name,
                    "last_sync": last_sync or self.now,
                }
            ],
        )
        return BootSource(**row)

    async def make_BootSourceSelection(
        self,
        boot_source_id: int,
        label: str = BootAssetLabel.STABLE,
        os: str = "",
        release: str = "",
        arch: str = "",
        selected: bool = False,
    ) -> BootSourceSelection:
        [row] = await self.create(
            "boot_source_selection",
            [
                {
                    "boot_source_id": boot_source_id,
                    "label": label,
                    "os": os,
                    "release": release,
                    "arch": arch,
                    "selected": selected,
                }
            ],
        )
        return BootSourceSelection(**row)

    async def make_BootAsset(
        self,
        boot_source_id: int,
        kind: int = BootAssetKind.OS,
        label: str = BootAssetLabel.STABLE,
        os: str = "",
        arch: str = "",
        release: str | None = None,
        version: str | None = None,
        krel: str | None = None,
        codename: str | None = None,
        title: str | None = None,
        subarch: str | None = None,
        compatibility: list[str] | None = None,
        flavor: str | None = None,
        base_image: str | None = None,
        bootloader_type: str | None = None,
        eol: datetime | None = None,
        esm_eol: datetime | None = None,
        signed: bool = False,
    ) -> BootAsset:
        [row] = await self.create(
            "boot_asset",
            [
                {
                    "boot_source_id": boot_source_id,
                    "kind": kind,
                    "label": label,
                    "os": os,
                    "arch": arch,
                    "release": release,
                    "version": version,
                    "krel": krel,
                    "codename": codename,
                    "title": title,
                    "subarch": subarch,
                    "compatibility": compatibility,
                    "flavor": flavor,
                    "base_image": base_image,
                    "bootloader_type": bootloader_type,
                    "eol": eol,
                    "esm_eol": esm_eol,
                    "signed": signed,
                }
            ],
        )
        return BootAsset(**row)

    async def make_BootAssetVersion(
        self,
        boot_asset_id: int,
        version: str = "",
        last_seen: datetime | None = None,
    ) -> BootAssetVersion:
        [row] = await self.create(
            "boot_asset_version",
            [
                {
                    "boot_asset_id": boot_asset_id,
                    "version": version,
                    "last_seen": last_seen or self.now,
                }
            ],
        )
        return BootAssetVersion(**row)

    async def make_BootAssetItem(
        self,
        boot_asset_version_id: int,
        ftype: ItemFileType = ItemFileType.ARCHIVE_TAR_XZ,
        sha256: str = "",
        path: str = "",
        file_size: int = 0,
        bytes_synced: int = 0,
        source_package: str | None = None,
        source_version: str | None = None,
        source_release: str | None = None,
    ) -> BootAssetItem:
        [row] = await self.create(
            "boot_asset_item",
            [
                {
                    "boot_asset_version_id": boot_asset_version_id,
                    "ftype": ftype,
                    "sha256": sha256,
                    "path": path,
                    "file_size": file_size,
                    "source_package": source_package,
                    "source_version": source_version,
                    "source_release": source_release,
                    "bytes_synced": bytes_synced,
                }
            ],
        )
        return BootAssetItem(**row)


@pytest.fixture
def factory(db_connection: AsyncConnection) -> Iterator[Factory]:
    yield Factory(db_connection)
