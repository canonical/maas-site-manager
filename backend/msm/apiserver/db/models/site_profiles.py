from typing import Any

from pydantic import (
    BaseModel,
)


class SiteProfile(BaseModel):
    id: int
    name: str
    selections: list[str]
    global_config: dict[str, Any]


class SiteProfileCreateUpdate(BaseModel):
    name: str
    selections: list[str]
    global_config: dict[str, Any]
