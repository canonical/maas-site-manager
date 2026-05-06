import hashlib
import json
from typing import Any

from pydantic import IPvAnyAddress, TypeAdapter
import pytest

from msm.apiserver.db.models.site_profiles import SiteProfileStored
from msm.apiserver.utils import (
    desired_config,
    hash_desired_config,
)
from msm.common.enums import IPMIWorkaroundFlags


def _make_stored(
    selections: list[str],
    global_config: dict[str, Any] | None = None,
) -> SiteProfileStored:
    return SiteProfileStored(
        id=1, name="test", selections=selections, global_config=global_config
    )


@pytest.fixture
def hash_preimage_payload() -> dict[str, Any]:
    return {
        "global_config": {"theme": "light"},
        "selections": ["ubuntu/jammy/amd64"],
        "trigger_image_sync": False,
    }


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

    def test_hash_stable_when_strenum_lists_are_permuted(self) -> None:
        ta = TypeAdapter(list[IPvAnyAddress])
        ips = [
            str(x)
            for x in ta.validate_python(
                ["192.0.2.2", "192.0.2.1", "2001:db8::1"]
            )
        ]
        flags_a = [
            IPMIWorkaroundFlags.OPENSESSPRIV,
            IPMIWorkaroundFlags.AUTHCAP,
        ]
        flags_b = [
            IPMIWorkaroundFlags.AUTHCAP,
            IPMIWorkaroundFlags.OPENSESSPRIV,
        ]
        p_a = _make_stored(
            [],
            global_config={
                "maas_auto_ipmi_workaround_flags": flags_a,
            },
        )
        p_b = _make_stored(
            [],
            global_config={
                "maas_auto_ipmi_workaround_flags": flags_b,
            },
        )
        ca = desired_config(p_a, trigger_image_sync=False)
        cb = desired_config(p_b, trigger_image_sync=False)
        assert ca is not None and cb is not None
        assert hash_desired_config(ca) == hash_desired_config(cb)

    def test_hash_upstream_dns_order_preserved(self) -> None:
        ta = TypeAdapter(list[IPvAnyAddress])
        ips = [
            str(x)
            for x in ta.validate_python(
                ["192.0.2.2", "192.0.2.1", "2001:db8::1"]
            )
        ]
        p_a = _make_stored(
            [],
            global_config={
                "upstream_dns": ips,
            },
        )
        p_b = _make_stored(
            [],
            global_config={
                "upstream_dns": list(reversed(ips)),
            },
        )
        ca = desired_config(p_a, trigger_image_sync=False)
        cb = desired_config(p_b, trigger_image_sync=False)
        assert ca is not None and cb is not None
        assert hash_desired_config(ca) != hash_desired_config(cb)


class TestHashDesiredConfig:
    def test_matches_manual_sha256(
        self, hash_preimage_payload: dict[str, Any]
    ) -> None:
        payload = hash_preimage_payload
        serialized = json.dumps(
            payload, separators=(",", ":"), ensure_ascii=False
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
        self,
        hash_preimage_payload: dict[str, Any],
        field: str,
        values: list[Any],
    ) -> None:
        p1 = {**hash_preimage_payload, field: values[0]}
        p2 = {**hash_preimage_payload, field: values[1]}
        assert hash_desired_config(p1) != hash_desired_config(p2)
