import base64
from typing import Any
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture, MockType

from msm.apiserver.db.models import Config
from msm.apiserver.db.models.oidc_provider import (
    OIDCProvider,
    OIDCProviderMetadata,
)
from msm.apiserver.db.tables import OIDCProvider as OIDCProviderTable
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.common.cookie_manager import (
    MSM_NONCE_COOKIE_NAME,
    MSM_STATE_COOKIE_NAME,
)
from msm.common.encryptor import Encryptor
from msm.common.enums import OIDCProviderAccessTokenType
from msm.common.oauth2_client import OAuthTokenData
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory

METADATA = {
    "authorization_endpoint": "https://issuer.com/authorize",
    "token_endpoint": "https://issuer.com/token",
    "userinfo_endpoint": "https://issuer.com/userinfo",
    "introspection_endpoint": "https://issuer.com/introspect",
    "revocation_endpoint": "https://issuer.com/revoke",
    "jwks_uri": "https://issuer.com/jwks",
}


def make_create_request(
    name: str = "provider",
    issuer_url: str = "https://issuer.com/",
    enabled: bool = True,
    token_type: OIDCProviderAccessTokenType = (
        OIDCProviderAccessTokenType.OPAQUE
    ),
) -> dict[str, Any]:
    return {
        "name": name,
        "client_id": "client",
        "client_secret": "secret",
        "issuer_url": issuer_url,
        "redirect_uri": "https://example.com/callback",
        "scopes": "openid profile email",
        "token_type": token_type,
        "enabled": enabled,
    }


async def insert_provider(
    factory: Factory,
    name: str = "provider",
    enabled: bool = True,
    issuer_url: str = "https://issuer.com/",
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
                "token_type": OIDCProviderAccessTokenType.OPAQUE,
                "enabled": enabled,
                "metadata": metadata if metadata is not None else METADATA,
            }
        ],
    )
    [row] = await factory.get(
        "oidc_provider", OIDCProviderTable.c.name == name
    )
    return OIDCProvider(**row)


async def link_users(factory: Factory, provider_id: int, count: int) -> None:
    for _ in range(count):
        user_id = await factory.next_id("user")
        await factory.create(
            "user",
            [
                {
                    "id": user_id,
                    "email": f"user{user_id}@example.com",
                    "username": f"user{user_id}",
                    "full_name": "User",
                    "password": "hashed",
                    "is_admin": False,
                    "provider_id": provider_id,
                }
            ],
        )


@pytest.fixture
def mock_fetch_metadata(mocker: MockerFixture) -> MockType:
    return mocker.patch(
        "msm.apiserver.service.oidc.OIDCService._fetch_metadata",
        return_value=OIDCProviderMetadata(**METADATA),
    )


@pytest.mark.asyncio
class TestGetActiveHandler:
    async def test_get_active_returns_enabled_provider(
        self, admin_client: Client, factory: Factory
    ) -> None:
        provider = await insert_provider(factory, enabled=True)
        await link_users(factory, provider.id, 2)

        response = await admin_client.get("/external-auth")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == provider.id
        assert data["name"] == provider.name
        assert data["enabled"] is True
        assert data["user_count"] == 2

    async def test_get_active_not_found(self, admin_client: Client) -> None:
        response = await admin_client.get("/external-auth")

        assert response.status_code == 404
        error = response.json()["error"]
        assert error["code"] == ExceptionCode.MISSING_PROVIDER_CONFIG


@pytest.mark.asyncio
class TestCreateHandler:
    async def test_create_provider(
        self,
        admin_client: Client,
        factory: Factory,
        mock_fetch_metadata: MockType,
    ) -> None:
        response = await admin_client.post(
            "/external-auth", json=make_create_request()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "provider"
        assert data["enabled"] is True
        assert data["user_count"] == 0
        assert data["metadata"] == METADATA

        rows = await factory.get("oidc_provider")
        assert len(rows) == 1
        assert rows[0]["name"] == "provider"

    async def test_create_conflict_when_enabled_exists(
        self,
        admin_client: Client,
        factory: Factory,
        mock_fetch_metadata: MockType,
    ) -> None:
        await insert_provider(factory, name="existing", enabled=True)

        response = await admin_client.post(
            "/external-auth", json=make_create_request(name="new")
        )

        assert response.status_code == 409
        error = response.json()["error"]
        assert error["code"] == ExceptionCode.ALREADY_EXISTS

    async def test_create_invalid_request(self, admin_client: Client) -> None:
        response = await admin_client.post("/external-auth", json={})

        assert response.status_code == 422


def make_state(target: str = "/dashboard") -> str:
    encoded_target = base64.urlsafe_b64encode(target.encode()).decode()
    return f"{encoded_target}.signature"


@pytest.mark.asyncio
class TestCallbackHandler:
    async def test_callback_success(
        self,
        admin_client: Client,
        api_config: Config,
        mocker: MockerFixture,
    ) -> None:
        encryptor = Encryptor(bytes.fromhex(api_config.encryption_key))
        state = make_state("/dashboard")
        nonce = "nonce-123"
        admin_client.cookies.set(
            MSM_STATE_COOKIE_NAME, encryptor.encrypt(state)
        )
        admin_client.cookies.set(
            MSM_NONCE_COOKIE_NAME, encryptor.encrypt(nonce)
        )
        tokens = OAuthTokenData(
            access_token="access-token",
            id_token=Mock(encoded="id-token"),
            refresh_token="refresh-token",
        )
        mock_get_callback = mocker.patch(
            "msm.apiserver.service.oidc.OIDCService.get_callback",
            return_value=tokens,
        )

        response = await admin_client.get(
            "/external-auth/callback",
            params={"code": "auth-code", "state": state},
        )

        assert response.status_code == 200
        assert response.json()["redirect_target"] == "/dashboard"
        mock_get_callback.assert_awaited_once_with(
            code="auth-code", nonce=nonce
        )

    async def test_callback_invalid_state(self, admin_client: Client) -> None:
        response = await admin_client.get(
            "/external-auth/callback",
            params={"code": "auth-code", "state": make_state()},
        )

        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == ExceptionCode.INVALID_CREDENTIALS
