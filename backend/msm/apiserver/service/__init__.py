from collections.abc import Iterable

from prometheus_client import CollectorRegistry
from sqlalchemy.ext.asyncio import AsyncConnection
from temporalio.client import Client as TemporalClient

from msm.apiserver.service.base import Service
from msm.apiserver.service.config import ConfigService
from msm.apiserver.service.images import (
    BootAssetItemService,
    BootAssetService,
    BootAssetVersionService,
    BootSourceSelectionService,
    BootSourceService,
    IndexNotFound,
    IndexService,
)
from msm.apiserver.service.s3 import S3Service
from msm.apiserver.service.settings import SettingsService
from msm.apiserver.service.site import InvalidPendingSites, SiteService
from msm.apiserver.service.site_profiles import SiteProfileService
from msm.apiserver.service.temporal import (
    BootSourceWorkflowService,
    TemporalService,
)
from msm.apiserver.service.token import TokenService
from msm.apiserver.service.user import UserService


class ServiceCollection:
    """Provide all services."""

    def __init__(
        self, connection: AsyncConnection, temporal_client: TemporalClient
    ):
        self.config = ConfigService(connection)
        self.sites = SiteService(connection)
        self.tokens = TokenService(connection)
        self.users = UserService(connection)
        self.settings = SettingsService(connection)
        self.temporal_service = TemporalService(
            connection,
            tokens=self.tokens,
            config=self.config,
            settings=self.settings,
            temporal_client=temporal_client,
        )
        self.s3 = S3Service(connection)
        self.workflow_service = BootSourceWorkflowService(
            connection, s3=self.s3, temporal=self.temporal_service
        )
        self.index_service = IndexService(connection)
        self.boot_asset_versions = BootAssetVersionService(connection)
        self.boot_asset_items = BootAssetItemService(connection)
        self.boot_assets = BootAssetService(
            connection,
            s3=self.s3,
            boot_asset_versions=self.boot_asset_versions,
            boot_asset_items=self.boot_asset_items,
            index_service=self.index_service,
        )
        self.boot_source_selections = BootSourceSelectionService(
            connection,
            workflows=self.workflow_service,
        )
        self.boot_sources = BootSourceService(
            connection,
            boot_assets=self.boot_assets,
            boot_source_selections=self.boot_source_selections,
            settings=self.settings,
            workflows=self.workflow_service,
        )
        self.site_profiles = SiteProfileService(connection)

    @property
    def services(self) -> Iterable[Service]:
        """Service collection.

        Keep this sorted by dependency order.
        """
        return [
            self.config,
            self.settings,
            self.s3,
            self.temporal_service,
            self.workflow_service,
            self.tokens,
            self.users,
            self.sites,
            self.boot_sources,
            self.boot_source_selections,
            self.boot_assets,
            self.boot_asset_versions,
            self.boot_asset_items,
            self.index_service,
            self.site_profiles,
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
    "BootAssetItemService",
    "BootAssetService",
    "BootAssetVersionService",
    "BootSourceSelectionService",
    "BootSourceService",
    "BootSourceWorkflowService",
    "ConfigService",
    "IndexNotFound",
    "IndexService",
    "InvalidPendingSites",
    "S3Service",
    "ServiceCollection",
    "SettingsService",
    "SiteService",
    "SiteProfileService",
    "TemporalService",
    "TokenService",
    "UserService",
]
