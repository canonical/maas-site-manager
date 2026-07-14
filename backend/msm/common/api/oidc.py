"""
OIDC API request and response models.
"""

from typing import Self

from msm.apiserver.db.models.oidc_provider import (
    OIDCProvider,
    OIDCProviderCreate,
)


class OIDCProviderCreateRequest(OIDCProviderCreate):
    """Request model for creating an OIDC provider."""
    pass


class OIDCProviderResponse(OIDCProvider):
    """Response model for getting an OIDC provider."""

    user_count: int | None = None

    @classmethod
    def from_model(cls, model: OIDCProvider, user_count: int) -> Self:
        """Create an instance from a database model."""
        return cls(**model.model_dump(), user_count=user_count)
