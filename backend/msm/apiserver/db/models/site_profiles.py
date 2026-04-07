from typing import Any

from pydantic import (
    BaseModel,
)

from msm.common.enums import TaskStatus


class SiteProfile(BaseModel):
    id: int
    name: str
    selections: list[str]
    global_config: dict[str, Any]


class SiteProfileCreateUpdate(BaseModel):
    name: str
    selections: list[str]
    global_config: dict[str, Any]


class SiteStateStatus(BaseModel):
    id: int
    site_id: int
    status: TaskStatus
    selections_status: TaskStatus
    global_config_status: TaskStatus
    image_sync_status: TaskStatus
    errors: list[str]
