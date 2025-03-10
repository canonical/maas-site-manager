#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.


"""Temporal client worker."""

import asyncio
import logging

from temporallib.client import Client, Options
from temporallib.encryption import EncryptionOptions
from temporallib.worker import SentryOptions, Worker, WorkerOptions
from workflows.custom_image_upload import Placeholder, placeholder

logger = logging.getLogger(__name__)


async def run_worker():
    """Connect Temporal worker to Temporal server."""
    client = await Client.connect(
        client_opt=Options(encryption=EncryptionOptions()),
    )

    worker = Worker(
        client=client,
        workflows=[Placeholder],
        activities=[placeholder],
        worker_opt=WorkerOptions(sentry=SentryOptions()),
    )

    await worker.run()


if __name__ == "__main__":  # pragma: nocover
    asyncio.run(run_worker())
