from copy import copy
from datetime import (
    datetime,
    timedelta,
)
from typing import Any

import pytest

from msm.apiserver.db.models import SiteConfigFactory, SiteProfile, Token
from msm.common.jwt import TokenAudience, TokenPurpose
from msm.common.time import now_utc


class TestToken:
    @pytest.mark.parametrize(
        "expired,is_expired",
        [
            (now_utc() + timedelta(hours=1), False),
            (now_utc() - timedelta(hours=1), True),
        ],
    )
    def test_is_expired(self, expired: datetime, is_expired: bool) -> None:
        token = Token(
            id=1,
            value="a-b-c",
            audience=TokenAudience.SITE,
            purpose=TokenPurpose.ENROLMENT,
            expired=expired,
            created=now_utc(),
        )
        assert token.is_expired() is is_expired


class TestSiteProfile:
    @pytest.mark.parametrize(
        "global_config",
        [
            (None),
            ({}),
        ],
    )
    def test_site_profile_init_expands_config(
        self, global_config: dict[str, Any] | None
    ) -> None:
        profile = SiteProfile(
            id=1,
            name="site profile name",
            selections=["ubuntu/noble/amd64"],
            global_config=global_config,
        )
        assert profile.global_config == SiteConfigFactory.DEFAULT_CONFIG

    def test_site_profile_init_retains_non_defaults(self) -> None:
        profile = SiteProfile(
            id=1,
            name="site profile name",
            selections=["ubuntu/noble/amd64"],
            global_config={"ntp_external_only": True},
        )
        cfg = copy(SiteConfigFactory.DEFAULT_CONFIG)
        cfg.update({"ntp_external_only": True})
        assert profile.global_config == cfg
