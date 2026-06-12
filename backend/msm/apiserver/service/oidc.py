from functools import cached_property
from typing import (
    Any,
)

from httpx import AsyncClient
from sqlalchemy import Select, insert, select

from msm.apiserver.db.models.oidc_provider import (
    OIDCProvider,
    OIDCProviderCreate,
    OIDCProviderMetadata,
)
from msm.apiserver.db.tables import OIDCProvider as OIDCProviderTable
from msm.apiserver.exceptions.catalog import (
    BadGatewayException,
    BaseExceptionDetail,
    ConflictException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.service.base import Service


class OIDCService(Service):
    @cached_property
    def httpx_client(self) -> "AsyncClient":
        """Create an AsyncClient for making HTTP requests to OIDC providers."""
        return AsyncClient()

    async def get_by_enabled(self) -> OIDCProvider | None:
        """Get the enabled OIDC provider, if any."""
        stmt = self._select_statement().where(
            OIDCProviderTable.c.enabled == True
        )
        if result := await self.conn.execute(stmt):
            if provider := result.one_or_none():
                return OIDCProvider(**provider._asdict())
        return None

    async def create(self, details: OIDCProviderCreate) -> OIDCProvider:
        """Create a new OIDC provider."""
        existing_enabled = await self.get_by_enabled()
        if details.enabled and existing_enabled:
            raise ConflictException(
                code=ExceptionCode.ALREADY_EXISTS,
                message="Only one OIDC provider can be enabled at a time.",
                details=[
                    BaseExceptionDetail(
                        reason=ExceptionCode.ALREADY_EXISTS,
                        messages=["An enabled OIDC provider already exists."],
                    )
                ],
            )

        metadata = await self._fetch_metadata(str(details.issuer_url))

        data = details.model_dump()
        data["issuer_url"] = str(details.issuer_url)
        data["redirect_uri"] = str(details.redirect_uri)
        data["metadata"] = metadata.model_dump()
        stmt = insert(OIDCProviderTable).returning(
            *OIDCProviderTable.c.values()
        )
        result = await self.conn.execute(stmt, [data])
        return OIDCProvider(**result.one()._asdict())

    async def _fetch_metadata(self, issuer_url: str) -> OIDCProviderMetadata:
        """Fetch OIDC provider metadata from the well-known endpoint."""
        httpx_client = self.httpx_client
        url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
        try:
            response = await httpx_client.get(url)
        except Exception as e:
            raise BadGatewayException(
                code=ExceptionCode.PROVIDER_COMMUNICATION_FAILED,
                message=f"Failed to fetch provider metadata.",
                details=[
                    BaseExceptionDetail(
                        reason=ExceptionCode.PROVIDER_COMMUNICATION_FAILED,
                        messages=[
                            f"Failed to communicate with OIDC provider at {url}: {e!s}"
                        ],
                    )
                ],
            ) from e

        if response.status_code != 200:
            raise BadGatewayException(
                code=ExceptionCode.PROVIDER_COMMUNICATION_FAILED,
                message=f"Failed to fetch provider metadata.",
                details=[
                    BaseExceptionDetail(
                        reason=ExceptionCode.PROVIDER_COMMUNICATION_FAILED,
                        messages=[
                            f"Received non-200 response from OIDC provider at {url}: {response.status_code}"
                        ],
                    )
                ],
            )

        metadata = response.json()
        return OIDCProviderMetadata(**metadata)

    def _select_statement(self, include_metadata: bool = True) -> Select[Any]:
        fields = [
            OIDCProviderTable.c.id,
            OIDCProviderTable.c.created,
            OIDCProviderTable.c.updated,
            OIDCProviderTable.c.name,
            OIDCProviderTable.c.client_id,
            OIDCProviderTable.c.client_secret,
            OIDCProviderTable.c.issuer_url,
            OIDCProviderTable.c.redirect_uri,
            OIDCProviderTable.c.scopes,
            OIDCProviderTable.c.token_type,
            OIDCProviderTable.c.enabled,
        ]
        if include_metadata:
            fields.append(OIDCProviderTable.c.metadata)
        return select(*fields).select_from(OIDCProviderTable)
