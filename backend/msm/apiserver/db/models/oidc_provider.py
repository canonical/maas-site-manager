from pydantic import (
    AnyHttpUrl,
    AwareDatetime,
    BaseModel,
)

from msm.common.enums import OIDCProviderAccessTokenType


class OIDCProviderMetadata(BaseModel):
    """Metadata for an OIDC provider."""

    # Based on the OpenID Connect Discovery specification (https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata)
    # We only include the fields that are relevant for our use case
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str | None = None
    introspection_endpoint: str | None = None
    revocation_endpoint: str | None = None
    jwks_uri: str


class OIDCProvider(BaseModel):
    """An OIDC provider."""

    id: int
    created: AwareDatetime
    updated: AwareDatetime
    name: str
    client_id: str
    client_secret: str
    issuer_url: AnyHttpUrl
    redirect_uri: AnyHttpUrl
    scopes: str
    token_type: OIDCProviderAccessTokenType
    enabled: bool
    metadata: OIDCProviderMetadata


class OIDCProviderCreate(BaseModel):
    """Creating a new OIDC provider."""

    name: str
    client_id: str
    client_secret: str
    issuer_url: AnyHttpUrl
    redirect_uri: AnyHttpUrl
    scopes: str
    token_type: OIDCProviderAccessTokenType
    enabled: bool
