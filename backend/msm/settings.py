from typing import Any

from pydantic import Field, SecretStr, validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from sqlalchemy import URL


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(case_sensitive=True)

    cors_allowed_origins: list[str] = Field(
        default=[
            "http://localhost:8405",
            "http://127.0.0.1:8405",
            "http://[::1]:8405",
        ],
        validation_alias="MSM_ALLOWED_ORIGINS",
    )
    dev_mode: bool = Field(default=False, validation_alias="MSM_DEV_MODE")
    db_host: str = Field(
        default="localhost",
        validation_alias="MSM_DB_HOST",
    )
    db_port: int = Field(
        default=5432,
        validation_alias="MSM_DB_PORT",
    )
    db_name: str | None = Field(
        default=None,
        validation_alias="MSM_DB_NAME",
    )
    db_user: str | None = Field(
        default=None,
        validation_alias="MSM_DB_USER",
    )
    db_password: SecretStr | None = Field(
        default=None,
        validation_alias="MSM_DB_PASSWORD",
    )
    api_port: int = Field(default=8000, validation_alias="MSM_API_PORT")
    api_socket: str = Field(
        default="api.socket", validation_alias="MSM_API_SOCKET"
    )
    s3_access_key: str | None = Field(
        default=None,
        validation_alias="MSM_S3_ACCESS_KEY",
    )
    s3_secret_key: str | None = Field(
        default=None,
        validation_alias="MSM_S3_SECRET_KEY",
    )
    s3_endpoint: str | None = Field(
        default=None,
        validation_alias="MSM_S3_ENDPOINT",
    )
    s3_bucket: str | None = Field(
        default=None, validation_alias="MSM_S3_BUCKET"
    )
    s3_path: str | None = Field(default=None, validation_alias="MSM_S3_PATH")
    heartbeat_interval_seconds: int = Field(
        default=300, validation_alias="MSM_HEARTBEAT_INTERVAL_SEC"
    )
    conn_lost_threshold_seconds: int = Field(
        default=600, validation_alias="MSM_CONN_LOST_THRESHOLD_SEC"
    )
    metrics_refresh_interval_seconds: int = Field(
        default=300, validation_alias="MSM_METRICS_REFRESH_INTVAL_SEC"
    )

    @property
    def static_dir(self) -> str:
        return "static"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        sources = super().settings_customise_sources(
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
        return sources

    def db_dsn(self, async_engine: bool = True) -> URL:
        """The DSN, from configured settings."""
        password = (
            self.db_password.get_secret_value() if self.db_password else None
        )
        return URL.create(
            "postgresql+asyncpg" if async_engine else "postgresql+psycopg",
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            username=self.db_user,
            password=password,
        )

    @validator("conn_lost_threshold_seconds")
    def conn_lost_threshold_validator(
        cls, threshold: int, values: dict[str, Any]
    ) -> int:
        if (
            "heartbeat_interval_seconds" in values
            and threshold <= values["heartbeat_interval_seconds"]
        ):
            raise ValueError(
                f"connection lost threshold ({threshold}s) should be greater "
                "than heartbeat interval "
                f"({values['heartbeat_interval_seconds']}s)"
            )
        return threshold
