from typing import Any

from pydantic import (
    BaseModel,
)

from msm.apiserver.db.models.global_site_config import SiteConfigFactory


class SiteProfile(BaseModel):
    id: int
    name: str
    selections: list[str]
    global_config: dict[str, Any] | None = None

    def fill_out_config(self) -> None:
        self.global_config = {
            cfg_name: self.global_config.get(cfg_name, cfg_default)
            for cfg_name, cfg_default in SiteConfigFactory.DEFAULT_CONFIG.items()
        }


class SiteProfileCreate(BaseModel):
    name: str
    selections: list[str]
    global_config: dict[str, Any] | None = None


class SiteProfileUpdate(BaseModel):
    name: str | None = None
    selections: list[str] | None = None
    global_config: dict[str, Any] | None = None
