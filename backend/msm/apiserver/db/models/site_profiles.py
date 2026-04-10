from typing import Any

from pydantic import (
    BaseModel,
)


class SiteProfile(BaseModel):
    id: int
    name: str
    selections: list[str]
    global_config: dict[str, Any] | None = None


class SiteProfileCreate(BaseModel):
    name: str
    selections: list[str]
    global_config: dict[str, Any] | None = None


class SiteProfileUpdate(BaseModel):
    name: str | None = None
    selections: list[str] | None = None
    global_config: dict[str, Any] | None = None
