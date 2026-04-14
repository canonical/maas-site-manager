from collections import defaultdict
from collections.abc import Iterable
from datetime import (
    datetime,
    timedelta,
)
from typing import Any, ClassVar
from uuid import UUID

from prometheus_client import Gauge, Histogram
from sqlalchemy import (
    Integer,
    Select,
    case,
    cast,
    delete,
    exists,
    func,
    literal,
    or_,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from msm.apiserver.db import (
    models,
    queries,
)
from msm.apiserver.db.tables import (
    Site,
    SiteData,
    SiteStateStatus,
    Token,
)
from msm.apiserver.schema import SortParam
from msm.apiserver.service.base import Service
from msm.common.jwt import TokenAudience, TokenPurpose
from msm.common.settings import Settings
from msm.common.time import now_utc


class InvalidPendingSites(Exception):
    """Raised when unknown pending site IDs are provided."""

    def __init__(self, ids: Iterable[int]):
        self.ids = sorted(ids)
        super().__init__("Unknown pending sites")


class JWTClaimFailed(Exception):
    """Raised when a Site tries to claim a JWT already in use."""


class SiteService(Service):
    sites_status = Gauge(
        "sites_total",
        "Total number of sites connected",
        labelnames=("status",),
        registry=Service._registry,
    )
    machine_status = Gauge(
        "site_machine_status_total",
        "Total number of machines in each status",
        labelnames=("status",),
        registry=Service._registry,
    )
    heartbeat_skew = Histogram(
        "site_heartbeat_skew",
        "Site heartbeat skew, in seconds",
        registry=Service._registry,
    )
    # these columns are searched by the query filter
    # see msm.apiserver.db.queries._search.query_all_columns
    site_query_filter_columns: ClassVar[list[str]] = [
        "city",
        "country",
        "name",
        "note",
        "state",
        "postal_code",
        "address",
        "url",
    ]

    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
        city: list[str] | None = None,
        country: list[str] | None = None,
        name: list[str] | None = None,
        note: list[str] | None = None,
        state: list[str] | None = None,
        postal_code: list[str] | None = None,
        address: list[str] | None = None,
        timezone: list[str] | None = None,
        url: list[str] | None = None,
        coordinates: bool | None = None,
        cluster_uuid: list[str] | None = None,
        query: str | None = None,
    ) -> tuple[int, Iterable[models.Site]]:
        """Return accepted sites, with optional filtering."""
        filters = queries.filters_from_arguments(
            Site,
            address=address,
            city=city,
            country=country,
            name=name,
            note=note,
            postal_code=postal_code,
            state=state,
            timezone=timezone,
            url=url,
            cluster_uuid=cluster_uuid,
        )
        filters.extend(
            queries.query_all_columns(
                Site,
                query,
                self.site_query_filter_columns,
            )
        )
        filters.append(Site.c.accepted == True)
        if coordinates is not None:
            if coordinates:
                filters.append(Site.c.coordinates != None)
            else:
                filters.append(Site.c.coordinates == None)
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        count = await queries.row_count(self.conn, Site, *filters)
        stmt = (
            self._select_statement_join_data()
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.Site, result)

    async def get_by_id(self, id: int) -> models.Site | None:
        """Get a site by id."""
        stmt = self._select_statement_join_data().where(Site.c.id == id)
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.Site(**row._asdict())
        return None

    async def get_by_auth_id(self, auth_id: UUID) -> models.Site | None:
        """Get a site by authentication ID."""
        stmt = self._select_statement_join_data(with_token=True).where(
            Token.c.auth_id == auth_id
        )
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.Site(**row._asdict())
        return None

    async def id_exists(self, id: int) -> bool:
        """Check if the given site exists"""
        stmt = self._select_statement(exists(Site)).where(Site.c.id == id)
        result = await self.conn.execute(stmt)
        return result.scalar() is True

    async def update(
        self, id: int, details: models.SiteUpdate | models.SiteDetailsUpdate
    ) -> None:
        """Update details about a site."""
        stmt = (
            update(Site)
            .where(Site.c.id == id)
            .values(details.model_dump(exclude_none=True))
        )
        await self.conn.execute(stmt)

    async def update_last_seen(
        self, id: int, last_seen: datetime, update_metrics: bool = False
    ) -> None:
        """Update when a site has been last seen."""
        if update_metrics:
            stmt_metrics = select(SiteData.c.last_seen).where(
                SiteData.c.id == id
            )
            result = await self.conn.execute(stmt_metrics)
            if previous := result.scalar():
                intval = await self.get_heartbeat_interval()
                deadline: datetime = previous + timedelta(seconds=intval)
                skew = (last_seen - deadline).total_seconds()
                self.heartbeat_skew.observe(max(0.0, skew))

        stmt = (
            insert(SiteData)
            .values(site_id=id, last_seen=last_seen)
            .on_conflict_do_update(
                index_elements=[SiteData.c.site_id],
                set_={"last_seen": last_seen},
            )
        )
        await self.conn.execute(stmt)

    async def update_data(
        self, id: int, details: models.SiteDataUpdate
    ) -> None:
        """Update stats data for a site."""
        stmt = (
            update(SiteData)
            .where(SiteData.c.site_id == id)
            .values(details.model_dump())
        )
        await self.conn.execute(stmt)

    async def delete(self, id: int) -> None:
        """Deletes a site by ID."""
        stmt = (
            update(Site).where(Site.c.id == id).values({"deleted": now_utc()})
        )
        await self.conn.execute(stmt)

    async def delete_many(self, ids: list[int]) -> set[int]:
        stmt = (
            update(Site)
            .where(Site.c.id.in_(ids))
            .values({"deleted": now_utc()})
            .returning(Site.c.id)
        )
        result = await self.conn.execute(stmt)
        return set([x[0] for x in result.all()])

    async def create_or_update_pending(
        self, details: models.PendingSiteCreate
    ) -> models.PendingSite:
        """Either mark a site as pending and update its details or create a
        new one if it does not exist."""
        stmt = self._select_statement(Site.c.id).where(
            Site.c.cluster_uuid == details.cluster_uuid
        )
        result = await self.conn.execute(stmt)
        if result.first() is not None:
            return await self.update_pending(details)
        return await self.create_pending(details)

    async def claim_jwt(self, site_id: int, auth_id: UUID) -> None:
        """Claim an existing JWT for this site"""
        claim_stmt = (
            update(Token)
            .where(
                Token.c.auth_id == auth_id,
                or_(Token.c.site_id == None, Token.c.site_id == site_id),
            )
            .values(site_id=site_id)
        )
        clain_ret = await self.conn.execute(claim_stmt)
        if clain_ret.rowcount != 1:
            raise JWTClaimFailed()

    async def remove_old_tokens(self, site_id: int, cur_auth_id: UUID) -> None:
        """Remove old access Tokens for this site."""
        stmt = delete(Token).where(
            Token.c.site_id == site_id,
            Token.c.audience == TokenAudience.SITE,
            Token.c.purpose == TokenPurpose.ACCESS,
            Token.c.auth_id != cur_auth_id,
        )
        await self.conn.execute(stmt)

    async def update_pending(
        self, details: models.PendingSiteCreate
    ) -> models.PendingSite:
        """Update the site details and mark it as pending."""
        values = details.model_dump(exclude_none=True, exclude={"auth_id"})
        values["accepted"] = False
        stmt = (
            update(Site)
            .where(Site.c.cluster_uuid == details.cluster_uuid)
            .values(values)
            .returning(
                Site.c.id,
                Site.c.name,
                Site.c.url,
                Site.c.cluster_uuid,
                Site.c.created,
            )
        )
        result = await self.conn.execute(stmt)
        site = models.PendingSite(**(result.one()._asdict()))
        if details.auth_id:
            await self.claim_jwt(site.id, details.auth_id)
        return site

    async def create_pending(
        self, details: models.PendingSiteCreate
    ) -> models.PendingSite:
        """Create a pending site."""
        data = details.model_dump(exclude_none=True, exclude={"auth_id"})
        try:
            async with self.conn.begin_nested():
                stmt = insert(Site).returning(
                    Site.c.id,
                    Site.c.name,
                    Site.c.url,
                    Site.c.created,
                    Site.c.cluster_uuid,
                )
                result = await self.conn.execute(stmt, [data])
        except IntegrityError:
            # Cluster UUID collision, try to recover
            data["accepted"] = False
            data["deleted"] = None
            upstmt = (
                update(Site)
                .where(
                    Site.c.cluster_uuid == details.cluster_uuid,
                    Site.c.deleted != None,
                )
                .values(data)
                .returning(
                    Site.c.id,
                    Site.c.name,
                    Site.c.url,
                    Site.c.cluster_uuid,
                    Site.c.created,
                )
            )
            result = await self.conn.execute(upstmt)
            if result.rowcount == 0:
                raise

        pending_site = models.PendingSite(**(result.one()._asdict()))
        await self.claim_jwt(pending_site.id, details.auth_id)
        return pending_site

    async def get_pending(
        self,
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[int, Iterable[models.PendingSite]]:
        """Return pending sites."""
        filters = [Site.c.accepted == False, Site.c.deleted == None]
        count = await queries.row_count(self.conn, Site, *filters)
        stmt = (
            self._select_statement(
                Site.c.id,
                Site.c.name,
                Site.c.url,
                Site.c.created,
                Site.c.cluster_uuid,
            )
            .where(Site.c.accepted == False)
            .order_by(Site.c.id)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.PendingSite, result)

    async def get_coordinates(
        self,
        city: list[str] | None = None,
        country: list[str] | None = None,
        name: list[str] | None = None,
        note: list[str] | None = None,
        state: list[str] | None = None,
        postal_code: list[str] | None = None,
        address: list[str] | None = None,
        timezone: list[str] | None = None,
        url: list[str] | None = None,
        cluster_uuid: list[str] | None = None,
        query: str | None = None,
    ) -> Iterable[models.SiteCoordinates]:
        """Return coordinates for all sites, with optional filtering."""
        filters = queries.filters_from_arguments(
            Site,
            address=address,
            city=city,
            country=country,
            name=name,
            note=note,
            postal_code=postal_code,
            state=state,
            timezone=timezone,
            url=url,
            cluster_uuid=cluster_uuid,
        )
        filters.extend(
            queries.query_all_columns(
                Site,
                query,
                self.site_query_filter_columns,
            )
        )
        filters.append(Site.c.accepted == True)
        stmt = self._select_statement(Site.c.id, Site.c.coordinates).where(
            *filters
        )
        result = await self.conn.execute(stmt)
        return self.objects_from_result(models.SiteCoordinates, result)

    async def accept_reject_pending(
        self,
        ids: list[int],
        accept: bool,
    ) -> None:
        """Accept or reject pending sites."""
        site_ids = set(ids)
        stmt = self._select_statement(Site.c.id).where(
            Site.c.id.in_(site_ids),
            Site.c.accepted == False,
        )
        result = await self.conn.execute(stmt)
        pending_ids = set(row[0] for row in result.all())
        if unknown_ids := site_ids - pending_ids:
            raise InvalidPendingSites(unknown_ids)

        if accept:
            await self.conn.execute(
                update(Site)
                .where(Site.c.id.in_(site_ids))
                .values(accepted=True)
            )
        else:
            await self.conn.execute(
                update(Site)
                .where(Site.c.id.in_(site_ids))
                .values({"deleted": now_utc()})
            )
        return None

    async def get_enrolling(
        self, auth_id: UUID
    ) -> models.EnrollingSite | None:
        """Return details for a site in enrollment process, if found."""
        stmt = (
            self._select_statement(
                Site.c.id,
                Site.c.accepted,
            )
            .select_from(Site.join(Token, Token.c.site_id == Site.c.id))
            .where(Token.c.auth_id == auth_id)
        )
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.EnrollingSite(**row._asdict())
        return None

    async def get_heartbeat_interval(self) -> int:
        """The heartbeat interval, for sites to report to site manager"""
        return Settings().heartbeat_interval_seconds

    async def get_site_count(self) -> tuple[int, int, int]:
        """Get the number of sites connected to this manager.

        Returns:
            tuple[int, int, int]: total number of sites, number of enrolled sites
            and the number of *stable* connections.
        """
        conn_lost_threshold = Settings().conn_lost_threshold_seconds
        conn_lost_limit = now_utc() - timedelta(seconds=conn_lost_threshold)
        stmt = (
            select(
                func.count(Site.c.id).label("n_total"),
                func.coalesce(
                    func.sum(cast(Site.c.accepted, Integer)), literal(0)
                ).label("n_accepted"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                SiteData.c.last_seen > conn_lost_limit,
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    literal(0),
                ).label("n_connected"),
            )
            .select_from(
                Site.join(
                    SiteData, SiteData.c.site_id == Site.c.id, isouter=True
                )
            )
            .where(Site.c.deleted == None)
        )
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return row.n_total, row.n_accepted, row.n_connected
        else:
            return 0, 0, 0

    async def get_machine_count(self) -> dict[str, int]:
        """Get the number of machines enrollled to connected sites.

        Only *stable* connections are counted."""
        conn_lost_threshold = Settings().conn_lost_threshold_seconds
        conn_lost_limit = now_utc() - timedelta(seconds=conn_lost_threshold)
        stmt = (
            select(
                queries.sum_or_zero(SiteData, "machines_allocated"),
                queries.sum_or_zero(SiteData, "machines_deployed"),
                queries.sum_or_zero(SiteData, "machines_ready"),
                queries.sum_or_zero(SiteData, "machines_error"),
                queries.sum_or_zero(SiteData, "machines_other"),
            )
            .select_from(SiteData.join(Site, SiteData.c.site_id == Site.c.id))
            .where(
                SiteData.c.last_seen > conn_lost_limit, Site.c.deleted == None
            )
        )
        result = await self.conn.execute(stmt)
        ret = defaultdict(int)
        if row := result.one_or_none():
            ret["allocated"] = row.n_machines_allocated
            ret["deployed"] = row.n_machines_deployed
            ret["ready"] = row.n_machines_ready
            ret["error"] = row.n_machines_error
            ret["other"] = row.n_machines_other
            ret["total"] = (
                row.n_machines_allocated
                + row.n_machines_deployed
                + row.n_machines_ready
                + row.n_machines_error
                + row.n_machines_other
            )
        return ret

    def _select_statement(self, *columns: Any) -> Select[Any]:
        return select(*columns).select_from(Site).where(Site.c.deleted == None)

    def _select_statement_join_data(
        self, with_token: bool = False
    ) -> Select[Any]:
        connection_lost_threshold = Settings().conn_lost_threshold_seconds
        connection_lost_limit = now_utc() - timedelta(
            seconds=connection_lost_threshold
        )
        from_clause = Site.join(
            SiteData, SiteData.c.site_id == Site.c.id, isouter=True
        )

        if with_token:
            from_clause = from_clause.join(Token, Token.c.site_id == Site.c.id)
        return (
            select(
                Site.c.id,
                Site.c.address,
                Site.c.city,
                Site.c.country,
                Site.c.coordinates,
                Site.c.name,
                Site.c.name.notin_(
                    select(Site.c.name)
                    .select_from(Site)
                    .group_by(Site.c.name)
                    .having(func.count(Site.c.name) > 1)
                ).label("name_unique"),
                Site.c.note,
                Site.c.postal_code,
                Site.c.state,
                Site.c.timezone,
                Site.c.url,
                Site.c.cluster_uuid,
                case(
                    (
                        SiteData.c.site_id == None,
                        models.ConnectionStatus.UNKNOWN,
                    ),
                    (
                        SiteData.c.last_seen > connection_lost_limit,
                        models.ConnectionStatus.STABLE,
                    ),
                    else_=models.ConnectionStatus.LOST,
                ).label("connection_status"),
                case(
                    (
                        SiteData.c.site_id != None,
                        func.json_build_object(
                            "machines_total",
                            (
                                SiteData.c.machines_allocated
                                + SiteData.c.machines_deployed
                                + SiteData.c.machines_ready
                                + SiteData.c.machines_error
                                + SiteData.c.machines_other
                            ).label("machines_total"),
                            "machines_allocated",
                            SiteData.c.machines_allocated,
                            "machines_deployed",
                            SiteData.c.machines_deployed,
                            "machines_ready",
                            SiteData.c.machines_ready,
                            "machines_error",
                            SiteData.c.machines_error,
                            "machines_other",
                            SiteData.c.machines_other,
                            "last_seen",
                            SiteData.c.last_seen,
                        ),
                    ),
                    else_=None,
                ).label("stats"),
            )
            .select_from(from_clause)
            .where(Site.c.deleted == None)
        )

    async def collect_metrics(self) -> None:
        n_total, n_enroll, n_connected = await self.get_site_count()
        self.sites_status.labels(status="all").set(n_total)
        self.sites_status.labels(status="pending").set(n_total - n_enroll)
        self.sites_status.labels(status="connected").set(n_connected)

        machines = await self.get_machine_count()
        for status in [
            "allocated",
            "deployed",
            "ready",
            "error",
            "other",
            "total",
        ]:
            self.machine_status.labels(status=status).set(machines[status])


class SiteStateService(Service):
    async def get(
        self,
        sort_params: list[SortParam],
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[int, Iterable[models.SiteStateStatus]]:
        count = await queries.row_count(self.conn, SiteStateStatus)
        order_by = queries.order_by_from_arguments(sort_params=sort_params)
        stmt = (
            self._select_all(SiteStateStatus)
            .order_by(*order_by)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.SiteStateStatus, result)

    async def get_by_id(self, id: int) -> models.SiteStateStatus | None:
        stmt = self._select_all(SiteStateStatus).where(
            SiteStateStatus.c.id == id
        )
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.SiteStateStatus(**row._asdict())
        return None

    async def get_by_site_id(
        self, site_id: int
    ) -> models.SiteStateStatus | None:
        stmt = self._select_all(SiteStateStatus).where(
            SiteStateStatus.c.site_id == site_id
        )
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.SiteStateStatus(**row._asdict())
        return None

    async def create(
        self, details: models.SiteStateStatusCreate
    ) -> models.SiteStateStatus:
        data = details.model_dump()
        stmt = insert(SiteStateStatus).returning(*SiteStateStatus.c.values())
        result = await self.conn.execute(stmt, [data])
        return models.SiteStateStatus(**result.one()._asdict())

    async def update(
        self, id: int, details: models.SiteStateStatusUpdate
    ) -> models.SiteStateStatus:
        data = details.model_dump(exclude_none=True)
        stmt = (
            update(SiteStateStatus)
            .where(SiteStateStatus.c.id == id)
            .values(data)
            .returning(*SiteStateStatus.c.values())
        )
        result = await self.conn.execute(stmt)
        return models.SiteStateStatus(**result.one()._asdict())

    async def delete(self, id: int) -> None:
        stmt = delete(SiteStateStatus).where(SiteStateStatus.c.id == id)
        await self.conn.execute(stmt)
