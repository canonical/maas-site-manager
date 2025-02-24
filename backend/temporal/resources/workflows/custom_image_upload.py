# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from dataclasses import dataclass
import os
from datetime import timedelta

from temporalio import workflow, activity


@dataclass
class ComposeGreetingInput:
    greeting: str
    name: str


# Basic activity that logs and does string concatenation
@activity.defn(name="compose_greeting")
async def compose_greeting(arg: ComposeGreetingInput) -> str:
    activity.logger.info("Running activity with parameter %s" % arg)
    env_var = os.getenv("message")
    juju_secret1 = os.getenv("juju-key1")

    return f"{env_var} {juju_secret1}"

# Basic workflow that logs and invokes an activity
@workflow.defn(name="GreetingWorkflow")
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        workflow.logger.info("Running workflow with parameter %s" % name)
        return await workflow.execute_activity(
            compose_greeting,
            ComposeGreetingInput("Hello", name),
            start_to_close_timeout=timedelta(seconds=10),
        )
