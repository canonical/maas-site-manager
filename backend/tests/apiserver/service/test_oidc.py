from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, Mock

from httpx import ConnectError
import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.db.models.oidc_provider import (
    OIDCProvider,
    OIDCProviderCreate,
    OIDCProviderMetadata,
)
from msm.apiserver.db.tables import OIDCProvider as OIDCProviderTable
from msm.apiserver.exceptions.catalog import (
    BadGatewayException,
    ConflictException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.service.oidc import OIDCService
from msm.common.enums import OIDCProviderAccessTokenType
from tests.fixtures.factory import Factory

METADATA = {
    "authorization_endpoint": "https://issuer.com/authorize",
    "token_endpoint": "https://issuer.com/token",
    "userinfo_endpoint": "https://issuer.com/userinfo",
    "introspection_endpoint": "https://issuer.com/introspect",
    "revocation_endpoint": "https://issuer.com/revoke",
    "jwks_uri": "https://issuer.com/jwks",
}


@pytest.fixture
def service(db_connection: AsyncConnection) -> Iterator[OIDCService]:
    yield OIDCService(db_connection)


def make_create_details(
    name: str = "provider",
    issuer_url: str = "https://issuer.com/",
    enabled: bool = True,
    token_type: OIDCProviderAccessTokenType = (
        OIDCProviderAccessTokenType.OPAQUE
    ),
) -> OIDCProviderCreate:
    return OIDCProviderCreate(
        name=name,
        client_id="client",
        client_secret="secret",
        issuer_url=issuer_url,
        redirect_uri="https://example.com/callback",
        scopes="openid profile email",
        token_type=token_type,
        enabled=enabled,
    )


async def insert_provider(
    factory: Factory,
    name: str = "provider",
    enabled: bool = True,
    issuer_url: str = "https://issuer.com/",
    token_type: OIDCProviderAccessTokenType = (
        OIDCProviderAccessTokenType.OPAQUE
    ),
    metadata: dict[str, Any] | None = None,
) -> OIDCProvider:
    await factory.create(
        "oidc_provider",
        [
            {
                "name": name,
                "client_id": "client",
                "client_secret": "secret",
                "issuer_url": issuer_url,
                "redirect_uri": "https://example.com/callback",
                "scopes": "openid profile email",
                "token_type": token_type,
                "enabled": enabled,
                "metadata": metadata if metadata is not None else METADATA,
            }
        ],
    )
    [row] = await factory.get(
        "oidc_provider", OIDCProviderTable.c.name == name
    )
    return OIDCProvider(**row)


def mock_metadata_response(
    status_code: int = 200, json_data: dict[str, Any] | None = None
) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json = Mock(
        return_value=json_data if json_data is not None else METADATA
    )
    return response


def patch_httpx_client(
    mocker: MockerFixture, service: OIDCService, get_mock: AsyncMock
) -> Mock:
    client = Mock()
    client.get = get_mock
    mocker.patch.object(service, "httpx_client", client)
    return client


@pytest.mark.asyncio
class TestOIDCService:
    async def test_returns_none_when_no_providers(
        self, service: OIDCService
    ) -> None:
        assert await service.get_by_enabled() is None

    async def test_returns_none_when_only_disabled_providers_exist(
        self, factory: Factory, service: OIDCService
    ) -> None:
        await insert_provider(factory, name="disabled", enabled=False)
        assert await service.get_by_enabled() is None

    async def test_returns_enabled_provider(
        self, factory: Factory, service: OIDCService
    ) -> None:
        provider = await insert_provider(factory, name="enabled", enabled=True)
        result = await service.get_by_enabled()
        assert result == provider

    async def test_create_success(
        self,
        mocker: MockerFixture,
        factory: Factory,
        service: OIDCService,
    ) -> None:
        get_mock = AsyncMock(return_value=mock_metadata_response())
        client = patch_httpx_client(mocker, service, get_mock)

        details = make_create_details(enabled=True)
        provider = await service.create(details)

        assert isinstance(provider, OIDCProvider)
        assert provider.name == "provider"
        assert provider.enabled is True
        assert str(provider.issuer_url) == "https://issuer.com/"
        assert str(provider.redirect_uri) == "https://example.com/callback"
        assert provider.token_type == OIDCProviderAccessTokenType.OPAQUE
        assert provider.metadata == OIDCProviderMetadata(**METADATA)

        client.get.assert_awaited_once_with(
            "https://issuer.com/.well-known/openid-configuration"
        )

        rows = await factory.get("oidc_provider")
        assert len(rows) == 1
        assert rows[0]["issuer_url"] == "https://issuer.com/"
        assert rows[0]["metadata"] == METADATA

    async def test_create_conflict_when_enabled_exists(
        self,
        mocker: MockerFixture,
        factory: Factory,
        service: OIDCService,
    ) -> None:
        await insert_provider(factory, name="existing", enabled=True)
        get_mock = AsyncMock(return_value=mock_metadata_response())
        client = patch_httpx_client(mocker, service, get_mock)

        details = make_create_details(name="new", enabled=True)
        with pytest.raises(ConflictException) as excinfo:
            await service.create(details)

        assert excinfo.value.code == ExceptionCode.ALREADY_EXISTS
        client.get.assert_not_awaited()

    async def test_fetch_metadata_success(
        self,
        mocker: MockerFixture,
        service: OIDCService,
    ) -> None:
        get_mock = AsyncMock(return_value=mock_metadata_response())
        client = patch_httpx_client(mocker, service, get_mock)

        metadata = await service._fetch_metadata("https://issuer.com")

        assert metadata == OIDCProviderMetadata(**METADATA)
        client.get.assert_awaited_once_with(
            "https://issuer.com/.well-known/openid-configuration"
        )

    async def test_fetch_metadata_request_error(
        self,
        mocker: MockerFixture,
        service: OIDCService,
    ) -> None:
        get_mock = AsyncMock(side_effect=ConnectError("boom"))
        patch_httpx_client(mocker, service, get_mock)

        with pytest.raises(BadGatewayException) as excinfo:
            await service._fetch_metadata("https://issuer.com")

        assert (
            excinfo.value.code == ExceptionCode.PROVIDER_COMMUNICATION_FAILED
        )

    async def test_fetch_metadata_non_200(
        self,
        mocker: MockerFixture,
        service: OIDCService,
    ) -> None:
        get_mock = AsyncMock(
            return_value=mock_metadata_response(status_code=500)
        )
        patch_httpx_client(mocker, service, get_mock)

        with pytest.raises(BadGatewayException) as excinfo:
            await service._fetch_metadata("https://issuer.com")

        assert (
            excinfo.value.code == ExceptionCode.PROVIDER_COMMUNICATION_FAILED
        )
