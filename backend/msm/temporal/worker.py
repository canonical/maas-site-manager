# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
"""
MSM Temporal worker definition.
"""

import asyncio
import logging

from temporalio.contrib.pydantic import pydantic_data_converter
from temporallib.client import Client, Options  # type: ignore
from temporallib.encryption import EncryptionOptions  # type: ignore
from temporallib.worker import (  # type: ignore
    SentryOptions,
    Worker,
    WorkerOptions,
)

import msm.temporal.activities as msm_act
import msm.temporal.workflows as msm_wf

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    """Connect Temporal worker to Temporal server."""
    client = await Client.connect(
        data_converter=pydantic_data_converter,
        client_opt=Options(encryption=EncryptionOptions()),
    )
    ba_act = msm_act.BootAssetActivities()
    img_act = msm_act.ImageManagementActivities()
    ss_act = msm_act.SimpleStreamActivities()
    wr_act = msm_act.WorkerRefreshActivities()
    worker = Worker(
        client=client,
        workflows=[
            msm_wf.DeleteItemsWorkflow,
            msm_wf.DownloadUpstreamImageWorkflow,
            msm_wf.RefreshUpstreamSourceWorkflow,
            msm_wf.RemoveStaleImagesWorkflow,
            msm_wf.SyncUpstreamSourceWorkflow,
            msm_wf.WorkerJwtRefreshWorkflow,
        ],
        activities=[
            ba_act.get_boot_asset_item,
            ba_act.get_boot_source,
            ba_act.get_source_last_sync,
            ba_act.put_asset_list,
            ba_act.put_available_asset_list,
            ba_act.get_source_versions,
            ba_act.remove_stale_versions,
            img_act.download_asset,
            img_act.delete_item,
            ss_act.fetch_ss_asset_list,
            ss_act.load_product_map,
            ss_act.parse_ss_index,
            wr_act.worker_jwt_refresh,
        ],
        worker_opt=WorkerOptions(
            sentry=SentryOptions(dsn=None, release=None, environment=None)
        ),
    )

    await worker.run()


def main() -> None:
    """Entrypoint"""
    asyncio.run(run_worker())


if __name__ == "__main__":  # pragma: nocover
    main()
