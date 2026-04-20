import hashlib
import json

import pytest

from msm.apiserver.db.models.site_profiles import (
    SiteProfile,
    SiteProfileStored,
)
from msm.common.config_hash import (
    desired_config,
    hash_desired_config,
    merged_config_for_response,
)


def _make_stored(
    selections: list[str],
    global_config: dict | None = None,
) -> SiteProfileStored:
    return SiteProfileStored(
        id=1, name="test", selections=selections, global_config=global_config
    )


class TestDesiredConfig:
    def test_returns_none_without_profile(self) -> None:
        assert desired_config(None, trigger_image_sync=False) is None

    def test_selections_sorted(self) -> None:
        profile = _make_stored(["ubuntu/noble/amd64", "ubuntu/jammy/amd64"])
        result = desired_config(profile, trigger_image_sync=False)
        assert result is not None
        assert result["selections"] == [
            "ubuntu/jammy/amd64",
            "ubuntu/noble/amd64",
        ]

    def test_global_config_keys_sorted(self) -> None:
        profile = _make_stored([], global_config={"z_key": "z", "a_key": "a"})
        result = desired_config(profile, trigger_image_sync=False)
        assert result is not None
        assert list(result["global_config"].keys()) == sorted(
            result["global_config"].keys()
        )

    @pytest.mark.parametrize("value", [True, False])
    def test_trigger_image_sync_propagated(self, value: bool) -> None:
        result = desired_config(_make_stored([]), trigger_image_sync=value)
        assert result is not None
        assert result["trigger_image_sync"] is value

    def test_profile_id_and_name_excluded(self) -> None:
        result = desired_config(_make_stored([]), trigger_image_sync=False)
        assert result is not None
        assert "id" not in result
        assert "name" not in result

    def test_stored_global_config_only_no_defaults(self) -> None:
        profile = _make_stored([], global_config={"theme": "dark"})
        result = desired_config(profile, trigger_image_sync=False)
        assert result is not None
        assert result["global_config"] == {"theme": "dark"}

    def test_nested_dict_keys_sorted_recursively(self) -> None:
        profile = _make_stored(
            [], global_config={"outer": {"z": 1, "a": 2}, "first": "v"}
        )
        result = desired_config(profile, trigger_image_sync=False)
        assert result is not None
        nested = result["global_config"].get("outer")
        if isinstance(nested, dict):
            assert list(nested.keys()) == sorted(nested.keys())

    def test_unordered_string_list_sorted_in_global_config(self) -> None:
        profile = _make_stored(
            [],
            global_config={"tags": ["zebra", "alpha"]},
        )
        result = desired_config(profile, trigger_image_sync=False)
        assert result is not None
        assert result["global_config"]["tags"] == ["alpha", "zebra"]


class TestMergedConfigForResponse:
    def test_includes_merged_defaults(self) -> None:
        profile = SiteProfile(
            id=1,
            name="merged",
            selections=["ubuntu/jammy/amd64"],
            global_config={"theme": "dark"},
        )
        result = merged_config_for_response(profile, trigger_image_sync=False)
        assert len(result["global_config"]) > 1
        assert result["global_config"]["theme"] == "dark"


class TestHashDesiredConfig:
    def _payload(self) -> dict:
        return {
            "global_config": {"theme": "light"},
            "selections": ["ubuntu/jammy/amd64"],
            "trigger_image_sync": False,
        }

    def test_matches_manual_sha256(self) -> None:
        payload = self._payload()
        serialized = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        assert (
            hash_desired_config(payload)
            == hashlib.sha256(serialized).hexdigest()
        )

    @pytest.mark.parametrize(
        "field,values",
        [
            ("trigger_image_sync", [True, False]),
            ("selections", [["ubuntu/jammy/amd64"], ["ubuntu/noble/amd64"]]),
        ],
    )
    def test_different_inputs_give_different_hashes(
        self, field: str, values: list
    ) -> None:
        p1 = {**self._payload(), field: values[0]}
        p2 = {**self._payload(), field: values[1]}
        assert hash_desired_config(p1) != hash_desired_config(p2)
