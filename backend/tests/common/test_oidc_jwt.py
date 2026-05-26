from unittest.mock import MagicMock, patch

from authlib.jose import JWTClaims, KeySet  # type: ignore[import-untyped]
from authlib.jose.errors import (  # type: ignore[import-untyped]
    DecodeError,
    InvalidClaimError,
)
import pytest

from msm.apiserver.db.models.oidc_provider import (
    OIDCProvider,
    OIDCProviderMetadata,
)
from msm.common.enums import OIDCProviderAccessTokenType
from msm.common.oidc_jwt import (
    BaseOAuthToken,
    JWTDecodeException,
    JWTValidationException,
    OAuthIDToken,
)
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

TEST_KEYSET = KeySet(keys=[])


@pytest.mark.asyncio
class TestBaseOAuthToken:
    @patch("msm.common.oidc_jwt.jwt.decode")
    @patch("msm.common.oidc_jwt.BaseOAuthToken.validate")
    async def test_from_token_success(
        self,
        mock_validate: MagicMock,
        mock_decode: MagicMock,
    ) -> None:
        mock_decode.return_value = {
            "aud": "abc123",
            "iss": "https://issuer.com",
            "sub": "user1",
            "exp": 9999999999,
            "iat": 1111111111,
        }
        mock_validate.return_value = None

        token = BaseOAuthToken.from_token(
            provider=TEST_PROVIDER,
            encoded="fake_token",
            jwks=TEST_KEYSET,
        )

        assert token.encoded == "fake_token"
        assert token.claims["sub"] == "user1"
        assert token.provider == TEST_PROVIDER

    @patch("msm.common.oidc_jwt.jwt.decode")
    @patch("msm.common.oidc_jwt.BaseOAuthToken.validate")
    async def test_from_token_skips_validation(
        self,
        mock_validate: MagicMock,
        mock_decode: MagicMock,
    ) -> None:
        mock_decode.return_value = {
            "aud": "abc123",
            "iss": "https://issuer.com",
            "sub": "user1",
            "exp": 9999999999,
            "iat": 1111111111,
        }

        token = BaseOAuthToken.from_token(
            provider=TEST_PROVIDER,
            encoded="fake_token",
            jwks=TEST_KEYSET,
            skip_validation=True,
        )

        mock_validate.assert_not_called()
        assert token.encoded == "fake_token"
        assert token.claims["sub"] == "user1"
        assert token.provider == TEST_PROVIDER

    @patch("msm.common.oidc_jwt.jwt.decode")
    async def test_from_token_decode_error(
        self, mock_decode: MagicMock
    ) -> None:
        mock_decode.side_effect = DecodeError(
            "Failed to decode token: missing required claims."
        )

        with pytest.raises(JWTDecodeException):
            BaseOAuthToken.from_token(
                provider=TEST_PROVIDER,
                encoded="fake_token",
                jwks=TEST_KEYSET,
            )

    @patch("msm.common.oidc_jwt.JWTClaims.validate")
    async def test_validate_success(self, mock_validate: MagicMock) -> None:
        mock_claims = JWTClaims(
            header={},
            payload={
                "aud": "abc123",
                "iss": "https://issuer.com",
                "sub": "user1",
                "exp": 9999999999,
                "iat": 1111111111,
            },
        )
        mock_claims.validate = mock_validate
        token = BaseOAuthToken(
            claims=mock_claims,
            encoded="fake_token",
            provider=TEST_PROVIDER,
        )
        token.validate()

        mock_validate.assert_called_once()

    @patch("msm.common.oidc_jwt.JWTClaims.validate")
    async def test_validate_failure(self, mock_validate: MagicMock) -> None:
        mock_validate.side_effect = InvalidClaimError("Invalid claim")
        mock_claims = JWTClaims(
            header={},
            payload={
                "aud": "abc123",
                "iss": "https://issuer.com",
                "sub": "user1",
                "alg": "RS256",
            },
        )
        mock_claims.validate = mock_validate
        token = BaseOAuthToken(
            claims=mock_claims,
            encoded="fake_token",
            provider=TEST_PROVIDER,
        )

        with pytest.raises(JWTValidationException):
            token.validate()


class TestOAuthIDToken:
    @patch("msm.common.oidc_jwt.BaseOAuthToken.validate")
    async def test_validate_success(
        self, mock_validate_super: MagicMock
    ) -> None:
        mock_claims = JWTClaims(
            header={"alg": "RS256"},
            payload={
                "aud": "abc123",
                "iss": "https://issuer.com",
                "sub": "user1",
                "nonce": "test_nonce",
            },
        )
        mock_validate_super.return_value = None
        token = OAuthIDToken(
            claims=mock_claims,
            encoded="fake_token",
            provider=TEST_PROVIDER,
        )

        token.validate(nonce="test_nonce")
        mock_validate_super.assert_called_once()

    @patch("msm.common.oidc_jwt.BaseOAuthToken.validate")
    async def test_validate_invalid_claim(
        self, mock_validate_super: MagicMock
    ) -> None:
        mock_claims = JWTClaims(
            header={},
            payload={
                "aud": "abc123",
                "iss": "https://issuer.com",
                "sub": "user1",
                "nonce": "wrong_nonce",
            },
        )
        mock_validate_super.return_value = None
        token = OAuthIDToken(
            claims=mock_claims,
            encoded="fake_token",
            provider=TEST_PROVIDER,
        )

        with pytest.raises(JWTValidationException):
            token.validate(nonce="test_nonce")

    @patch("msm.common.oidc_jwt.BaseOAuthToken.validate")
    async def test_validate_invalid_aud(
        self, mock_validate_super: MagicMock
    ) -> None:
        mock_claims = JWTClaims(
            header={},
            payload={
                "aud": "wrong_aud",
                "iss": "https://issuer.com",
                "sub": "user1",
                "nonce": "test_nonce",
            },
        )
        mock_validate_super.return_value = None
        token = OAuthIDToken(
            claims=mock_claims,
            encoded="fake_token",
            provider=TEST_PROVIDER,
        )

        with pytest.raises(JWTValidationException):
            token.validate(nonce="test_nonce")
