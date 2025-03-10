from typing import Self

from pydantic import BaseModel, model_validator

from msm.jwt import DEFAULT_TOKEN_DURATION


class Settings(BaseModel):
    """Application settings that can be changed via the API."""

    max_image_upload_size_gb: int = 100
    service_url: str = ""
    token_lifetime_minutes: int = int(
        DEFAULT_TOKEN_DURATION.total_seconds() // 60
    )
    token_rotation_interval_minutes: int = int(
        ((DEFAULT_TOKEN_DURATION.total_seconds()) // 60) // 2
    )


class SettingsUpdate(BaseModel):
    """Change application settings."""

    max_image_upload_size_gb: int | None = None
    service_url: str | None = None
    token_lifetime_minutes: int | None = None
    token_rotation_interval_minutes: int | None = None

    @model_validator(mode="after")
    def check_at_least_one_field_present(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be set.")
        return self
