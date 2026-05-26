import json
from unittest.mock import AsyncMock, Mock
import urllib.parse

from authlib.jose import JWTClaims, KeySet  # type: ignore[import-untyped]
from authlib.jose.errors import (  # type: ignore[import-untyped]
    BadSignatureError,
)
from httpx import HTTPStatusError, Request, Response
import pytest
from pytest_mock import MockerFixture

from msm.apiserver.db.models.oidc_provider import (
    OIDCProvider,
    OIDCProviderMetadata,
)
from msm.apiserver.exceptions.catalog import (
    BadGatewayException,
    UnauthorizedException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.common.enums import OIDCProviderAccessTokenType
from msm.common.oauth2_client import (
    OAuth2Client,
    OAuthCallbackData,
    OAuthTokenData,
    OAuthUserData,
)
from msm.common.oidc_jwt import OAuthAccessToken, OAuthIDToken
from msm.common.time import now_utc

TEST_PROVIDER = OIDCProvider(
    id=1,
    name="Test provider",
    client_id="abc123",
    client_secret="2be32df",
    scopes="openid profile email",
    issuer_url="https://issuer.com",
    redirect_uri="https://example.com/callback",
    created=now_utc(),
    updated=now_utc(),
    enabled=True,
    token_type=OIDCProviderAccessTokenType.JWT,
    metadata=OIDCProviderMetadata(
        authorization_endpoint="https://issuer.com/authorize",
        token_endpoint="https://issuer.com/token",
        jwks_uri="https://issuer.com/jwks",
    ),
)


class TestOauth2Client:
    def test_generate_authorization_url(self, mocker: MockerFixture) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        mocker.patch.object(
            client, "_generate_state", new=Mock(return_value="abc.def")
        )
        data = client.generate_authorization_url(redirect_target="/machines")
        expected_scope = "+".join(TEST_PROVIDER.scopes.split(" "))
        expected_url = (
            TEST_PROVIDER.metadata.authorization_endpoint
            + "?response_type=code"
            + "&client_id="
            + TEST_PROVIDER.client_id
            + "&redirect_uri="
            + urllib.parse.quote_plus(str(TEST_PROVIDER.redirect_uri))
            + "&scope="
            + expected_scope
            + "&state="
            + "abc.def"
            + "&nonce="
            + data.nonce
        )
        assert data.authorization_url == expected_url

    def test_get_provider_name(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        assert client.get_provider_name() == TEST_PROVIDER.name

    async def test__validate_id_token_success(
        self, mocker: MockerFixture
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        mocker.patch.object(
            client,
            "_get_provider_jwks",
            new=AsyncMock(return_value="fake_jwks"),
        )
        mock_from_token = mocker.patch(
            "msm.common.oidc_jwt.OAuthIDToken.from_token"
        )

        mock_token_instance = Mock()
        mock_token_instance.validate = Mock(return_value=None)
        mock_from_token.return_value = mock_token_instance

        await client._validate_id_token("valid_token", nonce="testnonce")

        mock_from_token.assert_called_once_with(
            provider=TEST_PROVIDER,
            encoded="valid_token",
            jwks="fake_jwks",
            nonce="testnonce",
        )

    async def test__validate_id_token_retries_with_new_jwks(
        self, mocker: MockerFixture
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        mocker.patch.object(
            client,
            "_get_provider_jwks",
            new=AsyncMock(side_effect=["stale_jwks", "fresh_jwks"]),
        )
        mock_from_token = mocker.patch(
            "msm.common.oidc_jwt.OAuthIDToken.from_token"
        )

        mock_token_instance = Mock()
        mock_token_instance.validate = Mock(return_value=None)
        mock_from_token.side_effect = [
            BadSignatureError("Invalid signature"),
            mock_token_instance,
        ]

        await client._validate_id_token("valid_token", nonce="testnonce")

        assert mock_from_token.call_count == 2
        mock_from_token.assert_any_call(
            provider=TEST_PROVIDER,
            encoded="valid_token",
            jwks="stale_jwks",
            nonce="testnonce",
        )
        mock_from_token.assert_any_call(
            provider=TEST_PROVIDER,
            encoded="valid_token",
            jwks="fresh_jwks",
            nonce="testnonce",
        )

    async def test_validate_access_token_jwt(
        self,
        mocker: MockerFixture,
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        mocker.patch.object(
            client,
            "_get_provider_jwks",
            new=AsyncMock(return_value="mock_jwks"),
        )
        mock_from_token = mocker.patch(
            "msm.common.oidc_jwt.OAuthAccessToken.from_token"
        )
        mock_token_instance = Mock()
        mock_from_token.return_value = mock_token_instance

        result = await client.validate_access_token("valid_jwt_token")

        assert result == mock_token_instance
        mock_from_token.assert_called_once_with(
            provider=TEST_PROVIDER,
            encoded="valid_jwt_token",
            jwks="mock_jwks",
        )

    async def test_validate_access_token_opaque_cached(
        self,
    ) -> None:
        provider = TEST_PROVIDER.model_copy()
        provider.token_type = OIDCProviderAccessTokenType.OPAQUE
        client = OAuth2Client(provider)
        client._access_token_cache = Mock()
        client._access_token_cache.is_valid = AsyncMock(return_value=True)

        token = await client.validate_access_token("opaque_token")

        assert token == "opaque_token"
        client._access_token_cache.is_valid.assert_awaited_once_with(
            "opaque_token"
        )

    async def test_validate_access_token_opaque_introspection(
        self,
        mocker: MockerFixture,
    ) -> None:
        mock_token_cache = Mock()
        mock_token_cache.is_valid = AsyncMock(return_value=False)
        mock_token_cache.add = AsyncMock()
        provider = TEST_PROVIDER.model_copy()
        provider.token_type = OIDCProviderAccessTokenType.OPAQUE
        provider.metadata.introspection_endpoint = (
            "https://issuer.com/introspect"
        )
        client = OAuth2Client(provider)
        client._access_token_cache = mock_token_cache
        mock_introspect = mocker.patch.object(
            client, "_introspect_token", new=AsyncMock(return_value=None)
        )

        token = await client.validate_access_token("opaque_token")

        assert token == "opaque_token"
        client._access_token_cache.is_valid.assert_awaited_once_with(
            "opaque_token"
        )
        mock_introspect.assert_awaited_once_with(
            url=provider.metadata.introspection_endpoint,
            access_token="opaque_token",
        )
        mock_token_cache.add.assert_awaited_once_with("opaque_token")

    async def test_validate_access_token_opaque_userinfo(
        self,
        mocker: MockerFixture,
    ) -> None:
        mock_token_cache = Mock()
        mock_token_cache.is_valid = AsyncMock(return_value=False)
        mock_token_cache.add = AsyncMock()
        provider = TEST_PROVIDER.model_copy()
        provider.token_type = OIDCProviderAccessTokenType.OPAQUE
        provider.metadata.introspection_endpoint = None
        provider.metadata.userinfo_endpoint = "https://issuer.com/userinfo"
        client = OAuth2Client(provider)
        client._access_token_cache = mock_token_cache
        mock_userinfo = mocker.patch.object(
            client, "_userinfo_request", new=AsyncMock(return_value=None)
        )

        token = await client.validate_access_token("opaque_token")

        assert token == "opaque_token"
        client._access_token_cache.is_valid.assert_awaited_once_with(
            "opaque_token"
        )
        mock_userinfo.assert_awaited_once_with(access_token="opaque_token")
        mock_token_cache.add.assert_awaited_once_with("opaque_token")

    async def test_validate_access_token_unverifiable(
        self,
        mocker: MockerFixture,
    ) -> None:
        mock_token_cache = Mock()
        mock_token_cache.is_valid = AsyncMock(return_value=False)
        provider = TEST_PROVIDER.model_copy()
        provider.token_type = OIDCProviderAccessTokenType.OPAQUE
        provider.metadata.introspection_endpoint = None
        provider.metadata.userinfo_endpoint = None
        client = OAuth2Client(provider)
        client._access_token_cache = mock_token_cache
        mocker.patch.object(
            client,
            "_userinfo_request",
            new=AsyncMock(
                side_effect=BadGatewayException(
                    code=ExceptionCode.MISSING_PROVIDER_CONFIG,
                    message="Userinfo endpoint is not configured for the provider.",
                    details=[],
                )
            ),
        )

        with pytest.raises(UnauthorizedException) as exc_info:
            await client.validate_access_token("opaque_token")
        details = exc_info.value.details
        assert details is not None
        assert details[0].reason == ExceptionCode.MISSING_PROVIDER_CONFIG
        assert (
            details[0].messages[0]
            == "Cannot validate access token: no userinfo or introspection endpoint available, and token is opaque."
        )

    async def test_callback(self, mocker: MockerFixture) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        mocker.patch.object(
            client,
            "_fetch_and_validate_tokens",
            new=AsyncMock(
                return_value=OAuthTokenData(
                    access_token=OAuthAccessToken(
                        claims=Mock(),
                        encoded="access_token_value",
                        provider=TEST_PROVIDER,
                    ),
                    id_token=OAuthIDToken(
                        claims=Mock(),
                        encoded="id_token_value",
                        provider=TEST_PROVIDER,
                    ),
                    refresh_token="refresh_token_value",
                )
            ),
        )
        mocker.patch.object(
            client,
            "get_userinfo",
            new=AsyncMock(
                return_value=OAuthUserData(
                    sub="user123",
                    email="john.doe@example.com",
                    given_name="John",
                    family_name="Doe",
                    name="John Doe",
                )
            ),
        )

        response = await client.callback(
            code="auth_code_value", nonce="testnonce"
        )

        assert isinstance(response, OAuthCallbackData)
        assert isinstance(response.tokens, OAuthTokenData)
        assert isinstance(response.user_info, OAuthUserData)
        assert response.tokens.access_token.encoded == "access_token_value"  # type: ignore
        assert response.tokens.id_token.encoded == "id_token_value"
        assert response.tokens.refresh_token == "refresh_token_value"
        assert response.user_info.sub == "user123"

    async def test_callback_logs_on_failure(
        self, mocker: MockerFixture
    ) -> None:
        mock_logger = mocker.patch("msm.common.oauth2_client.logger")
        client = OAuth2Client(TEST_PROVIDER)
        mocker.patch.object(
            client,
            "_fetch_and_validate_tokens",
            new=AsyncMock(
                side_effect=BadGatewayException(
                    code=ExceptionCode.PROVIDER_COMMUNICATION_FAILED,
                    message="Failed to fetch tokens from OIDC server.",
                    details=[],
                )
            ),
        )

        with pytest.raises(BadGatewayException):
            await client.callback(code="auth_code_value", nonce="testnonce")

        mock_logger.info.assert_called_with(
            "Authentication login unsuccessful"
        )

    async def test_get_userinfo_has_endpoint_uses_id_token_claims(
        self,
    ) -> None:
        mock_claims = JWTClaims(
            payload={
                "sub": "user123",
                "email": "testuser@example.com",
                "given_name": "Test",
                "family_name": "User",
                "name": "Test User",
            },
            header={},
        )
        client = OAuth2Client(TEST_PROVIDER)

        response = await client.get_userinfo(
            access_token="mock_token", id_token_claims=mock_claims
        )

        assert isinstance(response, OAuthUserData)
        assert response.sub == "user123"
        assert response.email == "testuser@example.com"

    async def test_get_userinfo_has_endpoint_uses_userinfo_endpoint(
        self,
        mocker: MockerFixture,
    ) -> None:
        mock_claims = JWTClaims(
            payload={
                "sub": "user123",
                "email": "testuser@example.com",
            },
            header={},
        )
        client = OAuth2Client(TEST_PROVIDER)
        mock_userinfo = mocker.patch.object(
            client,
            "_userinfo_request",
            new=AsyncMock(
                return_value={
                    "sub": "user123",
                    "email": "testuser@example.com",
                    "given_name": "Test",
                    "family_name": "User",
                    "name": "Test User",
                }
            ),
        )

        response = await client.get_userinfo(
            access_token="mock_token", id_token_claims=mock_claims
        )

        mock_userinfo.assert_awaited_once_with(access_token="mock_token")
        assert isinstance(response, OAuthUserData)
        assert response.sub == "user123"
        assert response.email == "testuser@example.com"
        assert response.given_name == "Test"
        assert response.family_name == "User"
        assert response.name == "Test User"

    async def test_get_userinfo_raises_exception_for_sub_mismatch(
        self,
        mocker: MockerFixture,
    ) -> None:
        mock_claims = JWTClaims(
            payload={
                "sub": "user123",
            },
            header={},
        )
        client = OAuth2Client(TEST_PROVIDER)
        mocker.patch.object(
            client,
            "_userinfo_request",
            new=AsyncMock(
                return_value={
                    "sub": "different_user",
                    "email": "differentuser@example.com",
                }
            ),
        )

        with pytest.raises(UnauthorizedException) as exc_info:
            await client.get_userinfo(
                access_token="mock_token", id_token_claims=mock_claims
            )
        details = exc_info.value.details
        assert details is not None
        assert details[0].reason == ExceptionCode.INVALID_TOKEN
        assert (
            details[0].messages[0]
            == "Userinfo 'sub' claim 'different_user' does not match ID token 'sub' claim 'user123'"
        )

    async def test__fetch_and_validate_tokens_success(
        self, mocker: MockerFixture
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        client.client.fetch_token = AsyncMock(
            return_value={
                "access_token": "access_token_value",
                "id_token": "id_token_value",
                "refresh_token": "refresh_token_value",
            }
        )
        mocker.patch.object(
            client,
            "_validate_id_token",
            new=AsyncMock(
                return_value=OAuthIDToken(
                    claims=Mock(),
                    encoded="id_token_value",
                    provider=TEST_PROVIDER,
                )
            ),
        )
        mocker.patch.object(
            client,
            "validate_access_token",
            new=AsyncMock(
                return_value=OAuthAccessToken(
                    claims=Mock(),
                    encoded="access_token_value",
                    provider=TEST_PROVIDER,
                )
            ),
        )

        response = await client._fetch_and_validate_tokens(
            code="auth_code_value", nonce="testnonce"
        )

        assert isinstance(response, OAuthTokenData)
        assert response.access_token.encoded == "access_token_value"  # type: ignore
        assert response.id_token.encoded == "id_token_value"
        assert response.refresh_token == "refresh_token_value"

    async def test__fetch_and_validate_tokens_http_status_error(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        client.client.fetch_token = AsyncMock(
            side_effect=HTTPStatusError(
                "Error fetching tokens",
                request=Request("POST", url="https://issuer.com/token"),
                response=Response(status_code=400),
            )
        )

        with pytest.raises(BadGatewayException) as exc_info:
            await client._fetch_and_validate_tokens(
                code="auth_code_value", nonce="testnonce"
            )
        assert (
            exc_info.value.details[0].reason  # type: ignore
            == ExceptionCode.PROVIDER_COMMUNICATION_FAILED
        )
        assert (
            exc_info.value.details[0].messages[0]  # type: ignore
            == "Failed to fetch tokens from OIDC server."
        )

    async def test__fetch_and_validate_tokens_missing_tokens(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        client.client.fetch_token = AsyncMock(
            return_value={
                "access_token": "access_token_value",
                "id_token": "id_token_value",
            }
        )
        with pytest.raises(BadGatewayException) as exc_info:
            await client._fetch_and_validate_tokens(
                code="auth_code_value", nonce="testnonce"
            )
        assert (
            exc_info.value.details[0].reason  # type: ignore
            == ExceptionCode.PROVIDER_COMMUNICATION_FAILED
        )
        assert (
            exc_info.value.details[0].messages[0]  # type: ignore
            == "Invalid token response from OIDC server. Please ensure the provider is configured correctly."
        )

    async def test__get_provider_jwks_no_cache(
        self, mocker: MockerFixture
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        test_jwks_text = json.dumps(
            {
                "keys": [
                    {
                        "kty": "RSA",
                        "kid": "test-key",
                        "use": "sig",
                        "alg": "RS256",
                        "n": "sXch-9X6c7v9k1k5-Yh0u7iDQoL1jN1kG4V5aSgZkGZfiOuV0OWq5mLzEJ-6uH1AxlXW2g0QkOz6K_XfG4Mkzjh2wDzg50u8bW2ULa0_HpRmVJjQykzq3GzqL6T2VZ7Y1rHzQ9mC8zv3Xc-8Kj1eGkLdKEMIh_EW4nWz6GBaIqPYbV-o",
                        "e": "AQAB",
                    }
                ]
            }
        )
        mock_request = mocker.patch.object(
            client, "_request", new=AsyncMock(return_value=test_jwks_text)
        )

        response = await client._get_provider_jwks()

        mock_request.assert_awaited_once_with(
            url="https://issuer.com/jwks",
        )
        assert isinstance(response, KeySet)

    async def test__get_provider_jwks_cached(
        self, mocker: MockerFixture
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        client._jwks_cache_time = now_utc().timestamp()
        fake_jwks = KeySet(
            keys=[
                {
                    "kty": "RSA",
                    "kid": "test-key",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "sXch-9X6c7v9k1k5-Yh0u7iDQoL1jN1kG4V5aSgZkGZfiOuV0OWq5mLzEJ-6uH1AxlXW2g0QkOz6K_XfG4Mkzjh2wDzg50u8bW2ULa0_HpRmVJjQykzq3GzqL6T2VZ7Y1rHzQ9mC8zv3Xc-8Kj1eGkLdKEMIh_EW4nWz6GBaIqPYbV-o",
                    "e": "AQAB",
                }
            ]
        )
        client._jwks_cache = fake_jwks
        mock_request = mocker.patch.object(client, "_request", new=AsyncMock())

        response = await client._get_provider_jwks()

        mock_request.assert_not_awaited()
        assert response == fake_jwks

    async def test__get_provider_jwks_raises_exception(
        self, mocker: MockerFixture
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        mocker.patch.object(
            client,
            "_request",
            new=AsyncMock(
                side_effect=HTTPStatusError(
                    "Error fetching JWKS",
                    request=Request("GET", url="https://issuer.com/jwks"),
                    response=Response(status_code=500),
                )
            ),
        )

        with pytest.raises(BadGatewayException) as exc_info:
            await client._get_provider_jwks()
        assert (
            exc_info.value.details[0].reason  # type: ignore
            == ExceptionCode.PROVIDER_COMMUNICATION_FAILED
        )
        assert (
            exc_info.value.details[0].messages[0]  # type: ignore
            == "Failed to retrieve JWKS from OIDC server."
        )

    async def test__client_request_success(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        test_response = Response(
            status_code=200,
            content='{"key": "value"}',
            request=Request("GET", url="https://issuer.com/some_endpoint"),
        )

        client.client.get = AsyncMock(return_value=test_response)

        response = await client._request(
            url="https://issuer.com/some_endpoint",
        )
        client.client.get.assert_awaited_once()
        assert response == {"key": "value"}

    async def test__client_request_failure(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        test_response = Response(
            status_code=500,
            content="Internal Server Error",
            request=Request("GET", url="https://issuer.com/some_endpoint"),
        )

        client.client.get = AsyncMock(return_value=test_response)

        with pytest.raises(HTTPStatusError):
            await client._request(
                url="https://issuer.com/some_endpoint",
            )
        client.client.get.assert_awaited_once()

    async def test_revoke_token_no_endpoint(
        self, mocker: MockerFixture
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        mock_revoke = mocker.patch.object(
            client, "_revoke_token", new=AsyncMock(return_value=None)
        )
        mock_cache_remove = mocker.patch.object(
            client._access_token_cache, "remove", new=AsyncMock()
        )

        await client.revoke_token(token="abc123")

        mock_revoke.assert_not_awaited()
        mock_cache_remove.assert_awaited_once_with("abc123")

    async def test_revoke_token_has_endpoint(
        self, mocker: MockerFixture
    ) -> None:
        revoke_url = "https://issuer.com/revoke"
        TEST_PROVIDER.metadata.revocation_endpoint = revoke_url
        client = OAuth2Client(TEST_PROVIDER)
        mock_revoke = mocker.patch.object(
            client, "_revoke_token", new=AsyncMock(return_value=None)
        )
        mock_cache_remove = mocker.patch.object(
            client._access_token_cache, "remove", new=AsyncMock()
        )

        await client.revoke_token(token="abc123")
        mock_cache_remove.assert_awaited_once_with("abc123")

        mock_revoke.assert_awaited_once_with(url=revoke_url, token="abc123")

    async def test__revoke_token_success(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        test_response = Response(
            status_code=200,
            content='{"key": "value"}',
            request=Request("POST", url="https://issuer.com/some_endpoint"),
        )
        req_data = {
            "token": "abc123",
            "token_type_hint": "refresh_token",
            "client_id": TEST_PROVIDER.client_id,
            "client_secret": TEST_PROVIDER.client_secret,
        }
        client.client.post = AsyncMock(return_value=test_response)

        await client._revoke_token(
            url="https://issuer.com/revoke", token="abc123"
        )

        client.client.post.assert_awaited_once_with(
            url="https://issuer.com/revoke", data=req_data
        )

    async def test__revoke_token_failure(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        test_response = Response(
            status_code=500,
            content="Internal Server Error",
            request=Request("POST", url="https://issuer.com/some_endpoint"),
        )
        client.client.post = AsyncMock(return_value=test_response)

        with pytest.raises(HTTPStatusError):
            await client._revoke_token(
                url="https://issuer.com/some_endpoint", token="abc123"
            )

    async def test_parse_raw_id_token(self, mocker: MockerFixture) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        mock_jwks = Mock(KeySet)
        mocker.patch.object(
            client, "_get_provider_jwks", new=AsyncMock(return_value=mock_jwks)
        )
        mock_from_token = mocker.patch(
            "msm.common.oidc_jwt.OAuthIDToken.from_token"
        )

        await client.parse_raw_id_token(id_token="abc123")

        mock_from_token.assert_called_once_with(
            provider=TEST_PROVIDER,
            encoded="abc123",
            jwks=mock_jwks,
            skip_validation=True,
        )

    async def test_refresh_access_token_success(
        self, mocker: MockerFixture
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        client.client.refresh_token = AsyncMock(
            return_value={
                "access_token": "new_access_token_value",
                "id_token": "new_id_token_value",
                "refresh_token": "new_refresh_token_value",
            }
        )
        mocker.patch.object(
            client,
            "validate_access_token",
            new=AsyncMock(return_value="new_access_token_value"),
        )

        tokens = await client.refresh_access_token(
            refresh_token="old_refresh_token_value",
        )

        assert tokens.access_token == "new_access_token_value"
        assert tokens.refresh_token == "new_refresh_token_value"
        client.client.refresh_token.assert_awaited_once_with(
            url=TEST_PROVIDER.metadata.token_endpoint,
            refresh_token="old_refresh_token_value",
        )

    async def test_refresh_access_token_failure(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        client.client.refresh_token = AsyncMock(
            side_effect=HTTPStatusError(
                "Error refreshing tokens",
                request=Request("POST", url="https://issuer.com/token"),
                response=Response(status_code=400),
            )
        )

        with pytest.raises(BadGatewayException) as exc_info:
            await client.refresh_access_token(
                refresh_token="old_refresh_token_value",
            )
        details = exc_info.value.details
        assert details is not None
        assert details[0].reason == ExceptionCode.PROVIDER_COMMUNICATION_FAILED
        assert (
            details[0].messages[0]
            == "Failed to refresh tokens from OIDC server."
        )

    async def test__introspect_token_success(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        TEST_PROVIDER.metadata.introspection_endpoint = (
            "https://issuer.com/introspect"
        )
        client.client.introspect_token = AsyncMock(
            return_value=Response(
                status_code=200,
                content='{"active": true}',
                request=Request("POST", url="https://issuer.com/introspect"),
            )
        )

        await client._introspect_token(
            url=TEST_PROVIDER.metadata.introspection_endpoint,
            access_token="opaque_token",
        )

        client.client.introspect_token.assert_awaited_once_with(
            url=TEST_PROVIDER.metadata.introspection_endpoint,
            token="opaque_token",
        )

    async def test__introspect_token_inactive(
        self, mocker: MockerFixture
    ) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        TEST_PROVIDER.metadata.introspection_endpoint = (
            "https://issuer.com/introspect"
        )
        mock_cache_remove = mocker.patch.object(
            client._access_token_cache, "remove", new=AsyncMock()
        )
        client.client.introspect_token = AsyncMock(
            return_value=Response(
                status_code=200,
                content='{"active": false}',
                request=Request("POST", url="https://issuer.com/introspect"),
            )
        )

        with pytest.raises(UnauthorizedException) as exc_info:
            await client._introspect_token(
                url=TEST_PROVIDER.metadata.introspection_endpoint,
                access_token="opaque_token",
            )
        mock_cache_remove.assert_awaited_once_with("opaque_token")
        details = exc_info.value.details
        assert details is not None
        assert details[0].reason == ExceptionCode.INVALID_TOKEN
        assert details[0].messages[0] == "Access token is not active."

    async def test__userinfo_request_success(self) -> None:
        client = OAuth2Client(TEST_PROVIDER)
        TEST_PROVIDER.metadata.userinfo_endpoint = (
            "https://issuer.com/userinfo"
        )
        client.client.get = AsyncMock(
            return_value=Response(
                status_code=200,
                content='{"sub": "user123", "email": "user@example.com"}',
                request=Request("GET", url="https://issuer.com/userinfo"),
            )
        )
        response = await client._userinfo_request(access_token="opaque_token")
        client.client.get.assert_awaited_once_with(
            url=TEST_PROVIDER.metadata.userinfo_endpoint,
            headers={"Authorization": "Bearer opaque_token"},
        )
        assert response == {"sub": "user123", "email": "user@example.com"}
