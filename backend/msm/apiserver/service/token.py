from collections.abc import Iterable
from datetime import timedelta
from typing import (
    Any,
)
import uuid

from prometheus_client import Counter
from sqlalchemy import (
    Select,
    delete,
    select,
)

from msm.apiserver.db import (
    models,
    queries,
)
from msm.apiserver.db.tables import Token
from msm.apiserver.service.base import Service
from msm.common.jwt import (
    JWT,
    TokenAudience,
    TokenPurpose,
)
from msm.common.time import now_utc


class TokenService(Service):
    token_issued = Counter(
        "token_issued",
        "Total tokens issued",
        labelnames=(
            "audience",
            "purpose",
        ),
        registry=Service._registry,
    )

    async def create(
        self,
        issuer: str,
        duration: timedelta,
        count: int = 1,
        secret_key: str = "",
        service_url: str = "",
        audience: TokenAudience = TokenAudience.SITE,
        purpose: TokenPurpose = TokenPurpose.ENROLMENT,
        site_id: int | None = None,
    ) -> Iterable[models.Token]:
        """Create tokens, returning their expiration and values."""
        data = []
        for _ in range(count):
            auth_id = uuid.uuid4()
            token = JWT.create(
                issuer=issuer,
                subject=str(auth_id),
                audience=audience,
                service_url=service_url,
                purpose=purpose,
                key=secret_key,
                duration=duration,
            )
            data.append(
                {
                    "expired": token.expiration,
                    "created": token.issued,
                    "value": token.encoded,
                    "auth_id": auth_id,
                    "audience": audience,
                    "purpose": purpose,
                    "site_id": site_id,
                }
            )
        result = await self.conn.execute(
            Token.insert().returning(
                Token.c.id,
                Token.c.value,
                Token.c.audience,
                Token.c.purpose,
                Token.c.expired,
                Token.c.created,
                Token.c.site_id,
            ),
            data,
        )
        self.token_issued.labels(audience=audience, purpose=purpose).inc(count)
        return self.objects_from_result(models.Token, result)

    async def get(
        self,
        offset: int = 0,
        limit: int | None = None,
        id: list[int] | None = None,
        value: list[str] | None = None,
        site_id: list[int] | None = None,
        audience: list[TokenAudience] | None = None,
        purpose: list[TokenPurpose] | None = None,
    ) -> tuple[int, Iterable[models.Token]]:
        """Return active tokens."""
        filters = queries.filters_from_arguments(
            Token,
            id=id,
            value=value,
            site_id=site_id,
            audience=audience or [TokenAudience.SITE],
            purpose=purpose or [TokenPurpose.ENROLMENT],
        )
        filters.extend(
            [
                Token.c.site_id == None,
                Token.c.expired > now_utc(),
            ]
        )
        count = await queries.row_count(self.conn, Token, *filters)
        stmt = (
            self._select_statement()
            .where(*filters)
            .order_by(Token.c.id)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.conn.execute(stmt)
        return count, self.objects_from_result(models.Token, result)

    async def get_by_auth_id(
        self,
        auth_id: uuid.UUID,
        audience: TokenAudience = TokenAudience.SITE,
        purpose: TokenPurpose = TokenPurpose.ENROLMENT,
    ) -> models.Token | None:
        """Get a token by authentication ID.

        The token is returned even if it's expired.
        """
        stmt = self._select_statement().where(
            Token.c.auth_id == auth_id,
            Token.c.audience == audience,
            Token.c.purpose == purpose,
        )
        result = await self.conn.execute(stmt)
        if row := result.one_or_none():
            return models.Token(**row._asdict())
        return None

    async def delete(self, id: int) -> None:
        """Deletes a token by ID."""
        stmt = delete(Token).where(Token.c.id == id)
        await self.conn.execute(stmt)

    async def delete_many(self, ids: list[int]) -> set[int]:
        stmt = delete(Token).where(Token.c.id.in_(ids)).returning(Token.c.id)
        result = await self.conn.execute(stmt)
        return set([x[0] for x in result.all()])

    async def delete_expired(
        self,
        audience: TokenAudience | None = None,
        purpose: TokenPurpose | None = None,
    ) -> int:
        """Delete expired tokens, optionally filtering for audience and purpose.

        Return the number of tokens deleted.
        """
        filters = [Token.c.expired < now_utc()]
        if audience is not None:
            filters.append(Token.c.audience == audience)
        if purpose is not None:
            filters.append(Token.c.purpose == purpose)
        stmt = delete(Token).where(*filters).returning(Token.c.id)
        result = await self.conn.execute(stmt)
        return len(result.all())

    def _select_statement(self) -> Select[Any]:
        return select(
            Token.c.id,
            Token.c.value,
            Token.c.audience,
            Token.c.purpose,
            Token.c.expired,
            Token.c.created,
            Token.c.site_id,
        ).select_from(Token)
