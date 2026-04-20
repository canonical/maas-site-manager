# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.
"""
Site configuration hash utilities.
"""

import hashlib
import json
from typing import Any

from msm.apiserver.db.models.site_profiles import (
    SiteProfile,
    SiteProfileStored,
)


def _normalize_config_value(obj: Any) -> Any:
    """Recursively sort dict keys, sort all-string lists, and recurse into values."""
    if isinstance(obj, dict):
        return {k: _normalize_config_value(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        if obj and all(isinstance(x, str) for x in obj):
            return sorted(obj)
        return [_normalize_config_value(x) for x in obj]
    return obj


def desired_config(
    profile: SiteProfileStored | None,
    trigger_image_sync: bool,
) -> dict[str, Any] | None:
    """Build preimage from stored profile JSON only"""
    if profile is None:
        return None
    return {
        "global_config": _normalize_config_value(profile.global_config or {}),
        "selections": sorted(profile.selections),
        "trigger_image_sync": trigger_image_sync,
    }


def merged_config_for_response(
    profile: SiteProfile,
    trigger_image_sync: bool,
) -> dict[str, Any]:
    """Build stable GET /site-config body from merged SiteProfile."""
    return {
        "global_config": _normalize_config_value(profile.global_config or {}),
        "selections": sorted(profile.selections),
        "trigger_image_sync": trigger_image_sync,
    }


def hash_desired_config(payload: dict[str, Any]) -> str:
    """Return the SHA-256 hex digest of payload."""
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()
