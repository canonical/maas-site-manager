from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
)

from msm.apiserver.schema import TimeZone


class ConnectionStatus(StrEnum):
    STABLE = "stable"
    LOST = "lost"
    UNKNOWN = "unknown"


class SiteData(BaseModel):
    """Data for a site."""

    machines_total: int
    machines_allocated: int
    machines_deployed: int
    machines_ready: int
    machines_error: int
    machines_other: int
    last_seen: AwareDatetime


class Coordinates(BaseModel):
    latitude: float = Field(default=0.0, ge=-90.0, le=90.0)
    longitude: float = Field(default=0.0, ge=-180.0, le=180.0)


class Site(BaseModel):
    """A MAAS installation."""

    id: int
    name: str
    city: str = ""
    country: str = ""
    coordinates: Coordinates | None
    note: str = ""
    state: str = ""
    address: str = ""
    postal_code: str = ""
    # XXX: mypy can't grok that this is an str/enum with lots of members
    timezone: TimeZone | Literal[""] = ""  # type: ignore[valid-type]
    url: str = ""
    cluster_uuid: str
    name_unique: bool
    connection_status: ConnectionStatus
    stats: SiteData | None = None


class PendingSite(BaseModel):
    """A pending MAAS site."""

    id: int
    name: str
    url: str
    cluster_uuid: str
    created: AwareDatetime


class EnrollingSite(BaseModel):
    """Details for a site that's in the enrollment process."""

    id: int
    accepted: bool


class SiteCoordinates(BaseModel):
    """Coordinates for a MAAS site."""

    id: int
    coordinates: Coordinates | None = None


class SiteUpdate(BaseModel):
    """The allowed updates to a Site from a user."""

    city: str | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)
    coordinates: Coordinates | None = None
    note: str | None = None
    state: str | None = None
    address: str | None = None
    postal_code: str | None = None
    # XXX: mypy can't grok that this is an str/enum with lots of members
    timezone: TimeZone | None = None  # type: ignore[valid-type]


class SiteDetailsUpdate(BaseModel):
    """Allowed updates for a Site from the site itself."""

    name: str | None
    url: str | None


class SiteDataUpdate(BaseModel):
    """Update site data."""

    machines_allocated: int | None
    machines_deployed: int | None
    machines_ready: int | None
    machines_error: int | None
    machines_other: int | None


class PendingSiteCreate(BaseModel):
    """Details to create a pending site."""

    name: str
    url: str
    cluster_uuid: str
    auth_id: UUID
    city: str | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)
    coordinates: Coordinates | None = None
    note: str | None = None
    state: str | None = None
    address: str | None = None
    postal_code: str | None = None
    # XXX: mypy can't grok that this is an str/enum with lots of members
    timezone: TimeZone | None = None  # type: ignore[valid-type]
