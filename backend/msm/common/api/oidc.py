"""
OIDC API request and response models.
"""

import base64
from typing import Self

from pydantic import BaseModel

from msm.apiserver.db.models.oidc_provider import (
    OIDCProvider,
    OIDCProviderCreate,
    OIDCProviderUpdate,
)


class OIDCProviderCreateRequest(OIDCProviderCreate):
    """Request model for creating an OIDC provider."""

    pass


class OIDCProviderUpdateRequest(OIDCProviderUpdate):
    """Request model for updating an OIDC provider."""

    pass


class OIDCProviderResponse(OIDCProvider):
    """Response model for getting an OIDC provider."""

    user_count: int | None = None

    @classmethod
    def from_model(cls, model: OIDCProvider, user_count: int) -> Self:
        """Create an instance from a database model."""
        return cls(**model.model_dump(), user_count=user_count)


class CallbackTargetResponse(BaseModel):
    """Response model for the OIDC redirect target."""

    redirect_target: str

    @classmethod
    def from_state(cls, state: str) -> Self:
        encoded_target, _ = state.split(".", 1)
        target = base64.urlsafe_b64decode(encoded_target.encode()).decode()
        return cls(redirect_target=target)
