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
    OIDCProviderUpdate,
)
from msm.apiserver.db.tables import OIDCProvider as OIDCProviderTable
from msm.apiserver.exceptions.catalog import (
    BadGatewayException,
    ConflictException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.service.oidc import OIDCService
from msm.apiserver.service.user import UserService
from msm.common.enums import OIDCProviderAccessTokenType
from msm.common.oauth2_client import (
    OAuthCallbackData,
    OAuthTokenData,
    OAuthUserData,
)
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
def mock_users() -> Mock:
    users = Mock(spec=UserService)
    users.get_by_username = AsyncMock(return_value=None)
    users.create = AsyncMock()
    return users


@pytest.fixture
def service(
    db_connection: AsyncConnection, mock_users: Mock
) -> Iterator[OIDCService]:
    yield OIDCService(db_connection, mock_users)


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


def make_user_data(
    email: str = "user@example.com",
    name: str = "Test User",
) -> OAuthUserData:
    return OAuthUserData(
        sub="sub-123",
        email=email,
        given_name="Test",
        family_name="User",
        name=name,
    )


def make_callback_data(
    user_data: OAuthUserData | None = None,
) -> OAuthCallbackData:
    tokens = OAuthTokenData(
        access_token="access-token",
        id_token=Mock(),
        refresh_token="refresh-token",
    )
    return OAuthCallbackData(
        tokens=tokens,
        user_info=user_data or make_user_data(),
    )


def patch_oauth_client(
    mocker: MockerFixture,
    service: OIDCService,
    callback_data: OAuthCallbackData,
) -> Mock:
    mock_client = Mock()
    mock_client.callback = AsyncMock(return_value=callback_data)
    mock_client.provider = Mock()
    mock_client.provider.id = 1
    mocker.patch.object(
        service, "_get_oauth_client", AsyncMock(return_value=mock_client)
    )
    return mock_client


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

    async def test_update_success(
        self,
        mocker: MockerFixture,
        factory: Factory,
        service: OIDCService,
    ) -> None:
        provider = await insert_provider(
            factory, name="provider", enabled=False
        )
        get_mock = AsyncMock(return_value=mock_metadata_response())
        client = patch_httpx_client(mocker, service, get_mock)

        updated = await service.update(
            provider.id, OIDCProviderUpdate(name="renamed")
        )

        assert updated.id == provider.id
        assert updated.name == "renamed"
        # No issuer change, so metadata is not refetched.
        client.get.assert_not_awaited()

    async def test_update_refetches_metadata_on_issuer_change(
        self,
        mocker: MockerFixture,
        factory: Factory,
        service: OIDCService,
    ) -> None:
        provider = await insert_provider(
            factory, name="provider", enabled=False
        )
        new_metadata = {**METADATA, "jwks_uri": "https://new.com/jwks"}
        get_mock = AsyncMock(
            return_value=mock_metadata_response(json_data=new_metadata)
        )
        client = patch_httpx_client(mocker, service, get_mock)

        updated = await service.update(
            provider.id,
            OIDCProviderUpdate(issuer_url="https://new.com/"),
        )

        assert str(updated.issuer_url) == "https://new.com/"
        assert updated.metadata == OIDCProviderMetadata(**new_metadata)
        client.get.assert_awaited_once_with(
            "https://new.com/.well-known/openid-configuration"
        )

    async def test_update_enable_success_when_none_enabled(
        self,
        factory: Factory,
        service: OIDCService,
    ) -> None:
        provider = await insert_provider(
            factory, name="provider", enabled=False
        )

        updated = await service.update(
            provider.id, OIDCProviderUpdate(enabled=True)
        )

        assert updated.enabled is True

    async def test_update_conflict_when_enabling_different_provider(
        self,
        factory: Factory,
        service: OIDCService,
    ) -> None:
        await insert_provider(factory, name="existing", enabled=True)
        other = await insert_provider(
            factory,
            name="other",
            enabled=False,
            issuer_url="https://other.com/",
        )

        with pytest.raises(ConflictException) as excinfo:
            await service.update(other.id, OIDCProviderUpdate(enabled=True))

        assert excinfo.value.code == ExceptionCode.ALREADY_EXISTS

    async def test_delete_success(
        self,
        factory: Factory,
        service: OIDCService,
    ) -> None:
        provider = await insert_provider(
            factory, name="provider", enabled=False
        )

        await service.delete(provider.id)

        rows = await factory.get("oidc_provider")
        assert len(rows) == 0

    async def test_delete_raises_exception_when_enabled(
        self,
        factory: Factory,
        service: OIDCService,
    ) -> None:
        provider = await insert_provider(
            factory, name="provider", enabled=True
        )

        with pytest.raises(ConflictException) as excinfo:
            await service.delete(provider.id)

        assert excinfo.value.code == ExceptionCode.ALREADY_EXISTS
        assert (
            "Cannot delete the enabled OIDC provider." in excinfo.value.message
        )

        rows = await factory.get("oidc_provider")
        assert len(rows) == 1

    async def test_get_callback_returns_tokens(
        self,
        mocker: MockerFixture,
        factory: Factory,
        service: OIDCService,
        mock_users: Mock,
    ) -> None:
        await insert_provider(factory)
        callback_data = make_callback_data()
        mock_client = patch_oauth_client(mocker, service, callback_data)

        result = await service.get_callback(
            code="auth-code", nonce="nonce-123"
        )

        assert result == callback_data.tokens
        mock_client.callback.assert_awaited_once_with(
            code="auth-code", nonce="nonce-123"
        )
        mock_users.create.assert_awaited_once()

    async def test_create_user_if_not_exists_creates_user_when_not_found(
        self,
        service: OIDCService,
        mock_users: Mock,
    ) -> None:
        user_data = make_user_data()
        mock_users.get_by_username.return_value = None

        await service._create_user_if_not_exists(
            user=user_data, provider_id=42
        )

        mock_users.get_by_username.assert_awaited_once_with(user_data.email)
        mock_users.create.assert_awaited_once()
        details = mock_users.create.call_args.kwargs["details"]
        assert details.email == user_data.email
        assert details.username == user_data.email
        assert details.full_name == user_data.name
        assert details.is_admin is False
        assert details.provider_id == 42

    async def test_create_user_if_not_exists_skips_creation_when_user_exists_with_matching_provider(
        self,
        service: OIDCService,
        mock_users: Mock,
    ) -> None:
        user_data = make_user_data()
        existing_user = Mock()
        existing_user.provider_id = 42
        mock_users.get_by_username.return_value = existing_user

        await service._create_user_if_not_exists(
            user=user_data, provider_id=42
        )

        mock_users.get_by_username.assert_awaited_once_with(user_data.email)
        mock_users.create.assert_not_awaited()

    async def test_create_user_if_not_exists_provider_id_mismatch(
        self,
        service: OIDCService,
        mock_users: Mock,
    ) -> None:
        user_data = make_user_data()
        existing_user = Mock()
        existing_user.provider_id = 99  # Different provider
        mock_users.get_by_username.return_value = existing_user

        with pytest.raises(ConflictException) as excinfo:
            await service._create_user_if_not_exists(
                user=user_data, provider_id=42
            )

        assert excinfo.value.code == ExceptionCode.ALREADY_EXISTS
        assert (
            "User already exists with a different OIDC provider."
            in excinfo.value.message
        )
        mock_users.get_by_username.assert_awaited_once_with(user_data.email)
        mock_users.create.assert_not_awaited()
