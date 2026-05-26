from dataclasses import dataclass
from functools import cached_property
from typing import Any, Self

from authlib.jose import JWTClaims, KeySet, jwt  # type: ignore[import-untyped]
from authlib.jose.errors import (  # type: ignore[import-untyped]
    DecodeError,
    InvalidClaimError,
)

from msm.apiserver.db.models.oidc_provider import OIDCProvider


class JWTDecodeException(Exception):
    """JWT decoding failed"""


class JWTValidationException(Exception):
    """JWT validation failed"""


@dataclass(frozen=True)
class BaseOAuthToken:
    TOKEN_ALGORITHM = "RS256"

    claims: JWTClaims
    encoded: str
    provider: OIDCProvider

    _REQUIRED_FIELDS: frozenset[str] = frozenset(
        ("aud", "iss", "sub", "exp", "iat")
    )

    @cached_property
    def issuer(self) -> str:
        return str(self.claims["iss"]).rstrip("/")

    @cached_property
    def audience(self) -> list[str]:
        aud = self.claims["aud"]
        return aud if isinstance(aud, list) else [aud]

    @cached_property
    def email(self) -> str:
        return str(self.claims["email"])

    @classmethod
    def from_token(
        cls,
        provider: OIDCProvider,
        encoded: str,
        jwks: KeySet,
        nonce: str | None = None,
        skip_validation: bool = False,
    ) -> Self:
        try:
            claims = jwt.decode(encoded, jwks)
        except DecodeError as e:
            raise JWTDecodeException() from e

        token = cls(claims=claims, encoded=encoded, provider=provider)
        if skip_validation:
            return token
        token.validate(nonce=nonce)

        return token

    def validate(self, **kwargs: Any) -> None:
        """Base validation of the token claims."""
        if self._REQUIRED_FIELDS - set(self.claims) or (
            self.issuer != str(self.provider.issuer_url).rstrip("/")
        ):
            raise JWTValidationException()

        try:
            self.claims.validate()
        except InvalidClaimError as e:
            raise JWTValidationException() from e


@dataclass(frozen=True)
class OAuthAccessToken(BaseOAuthToken):
    pass


@dataclass(frozen=True)
class OAuthIDToken(BaseOAuthToken):
    def validate(self, *, nonce: str | None = None, **kwargs: Any) -> None:
        super().validate()
        alg = self.claims.header.get("alg")
        azp = self.claims.get("azp")
        if (
            alg != self.TOKEN_ALGORITHM
            or (azp is not None and azp != self.provider.client_id)
            or (self.claims.get("nonce") != nonce)
            or (self.provider.client_id not in self.audience)
        ):
            raise JWTValidationException()
