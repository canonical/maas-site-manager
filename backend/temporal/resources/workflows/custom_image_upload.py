# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from dataclasses import dataclass
from typing import Any

from temporalio import workflow, activity


@dataclass
class PlaceholderParams:
    foo: str
    bar: str



@activity.defn(name="placeholder")
async def placeholder(foo: str, bar: str) -> dict[str, Any]:
   return {
       "foo": foo,
       "bar": bar,
   }


@workflow.defn(name="Placeholder")
class Placeholder:
    @workflow.run
    async def run(self, params: PlaceholderParams) -> dict[str, Any]:
        result = await workflow.execute_activity(
            placeholder,
            params.foo,
            params.bar,
        )
        return result
