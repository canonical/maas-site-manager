from collections.abc import Iterable

from prometheus_client import CollectorRegistry
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.service.base import Service
from msm.service.config import ConfigService
from msm.service.images import (
    BootAssetItemService,
    BootAssetService,
    BootAssetVersionService,
    BootSourceSelectionService,
    BootSourceService,
)
from msm.service.settings import SettingsService
from msm.service.site import InvalidPendingSites, SiteService
from msm.service.token import TokenService
from msm.service.user import UserService


class ServiceCollection:
    """Provide all services."""

    def __init__(self, connection: AsyncConnection):
        self.sites = SiteService(connection)
        self.tokens = TokenService(connection)
        self.users = UserService(connection)
        self.settings = SettingsService(connection)
        self.boot_assets = BootAssetService(connection)
        self.boot_asset_items = BootAssetItemService(connection)
        self.boot_asset_versions = BootAssetVersionService(connection)
        self.boot_sources = BootSourceService(connection)
        self.boot_source_selections = BootSourceSelectionService(connection)

    @property
    def services(self) -> Iterable[Service]:
        """Service collection."""
        return [
            self.sites,
            self.tokens,
            self.users,
            self.settings,
            self.boot_assets,
            self.boot_asset_items,
            self.boot_asset_versions,
            self.boot_sources,
            self.boot_source_selections,
        ]

    @classmethod
    def register_metrics(cls, registry: CollectorRegistry) -> None:
        """Add metrics to registry."""
        Service.register_metrics(registry)

    async def collect_metrics(self) -> None:
        """Update metrics for this service."""
        for svc in self.services:
            await svc.collect_metrics()


__all__ = [
    "BootAssetService",
    "BootAssetItemService",
    "BootAssetVersionService",
    "BootSourceService",
    "BootSourceSelectionService",
    "ConfigService",
    "InvalidPendingSites",
    "ServiceCollection",
    "SettingsService",
    "SiteService",
    "TokenService",
    "UserService",
]
