from pydantic import (
    AwareDatetime,
    BaseModel,
)

from msm.common.time import now_utc


class Token(BaseModel):
    """A registration token for a site."""

    id: int
    value: str
    audience: str
    purpose: str
    expired: AwareDatetime
    created: AwareDatetime
    site_id: int | None = None

    def is_expired(self) -> bool:
        """Whether the token is expired."""
        return self.expired < now_utc()


class OIDCRevokedToken(BaseModel):
    """A revoked OIDC refresh token entry."""

    id: int
    token_hash: str
    revoked_at: AwareDatetime
    user_email: str
    provider_id: int
