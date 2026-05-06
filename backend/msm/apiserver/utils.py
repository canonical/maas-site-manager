"""Common utility functions for the API"""

from collections.abc import Iterable
import hashlib
import json
from typing import Any

from fastapi import (
    APIRouter,
    FastAPI,
)

from msm import __version__
from msm.apiserver.db.models.site_profiles import SiteProfileStored

RETAIN_ORDER_CONFIG_OPTIONS = frozenset(["upstream_dns"])


def create_subapp(
    title: str, name: str, routers: Iterable[APIRouter]
) -> FastAPI:
    """Return a FastAPI application with the specified routers registered."""
    app = FastAPI(title=title, name=name, version=__version__)
    for r in routers:
        app.router.include_router(r)
    return app


def _normalize_config_value(obj: Any) -> Any:
    """Recursively sort dict keys and sort all lists."""
    if isinstance(obj, dict):
        return {
            k: (
                _normalize_config_value(obj[k])
                if k not in RETAIN_ORDER_CONFIG_OPTIONS
                else obj[k]
            )
            for k in sorted(obj)
        }
    if isinstance(obj, list):
        return sorted(obj)
    return obj


def desired_config(
    profile: SiteProfileStored | None,
    trigger_image_sync: bool,
) -> dict[str, Any] | None:
    """Build preimage from stored profile JSON only."""
    if profile is None:
        return None
    return {
        "global_config": _normalize_config_value(profile.global_config or {}),
        "selections": sorted(profile.selections),
        "trigger_image_sync": trigger_image_sync,
    }


def hash_desired_config(payload: dict[str, Any]) -> str:
    """Return the SHA-256 hex digest of payload."""
    serialized = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()
