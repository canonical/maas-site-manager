from collections.abc import Iterable
from typing import (
    Any,
)
from uuid import uuid4

from msm.apiserver.db import models
from msm.apiserver.db.tables import Config
from msm.apiserver.service.base import DBBackedModelService
from msm.common.jwt import generate_key


class ConfigService(DBBackedModelService[models.Config]):
    db_table = Config

    def _default_values(self, keys: Iterable[str]) -> list[dict[str, Any]]:
        # override the method to generate a default key.
        values = {
            "service_identifier": str(uuid4()),
            "token_secret_key": generate_key(),
            "encryption_key": generate_key(),
        }
        return [{"name": key, "value": values[key]} for key in keys]

    async def get_encryption_key(self) -> bytes:
        """Return the AES-256-GCM encryption key as raw bytes.

        The key is stored hex-encoded, so it is decoded back into the 32 raw
        bytes expected by AESGCM.
        """
        config = await self.get()
        return bytes.fromhex(config.encryption_key)
