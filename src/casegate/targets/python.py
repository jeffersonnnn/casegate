"""A target that calls an async Python function in the same process.

This is the shortest path from "I have an agent function" to an eval: no server, no
serialisation. A timeout bounds each call so one hung case cannot stall the whole run.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from casegate.models import Output

DEFAULT_TIMEOUT_S = 120.0

TargetFunction = Callable[[dict[str, Any]], Awaitable[Output | dict[str, Any]]]


class PythonTarget:
    def __init__(self, func: TargetFunction, timeout_s: float | None = None) -> None:
        self.func = func
        self.timeout_s = timeout_s if timeout_s is not None else DEFAULT_TIMEOUT_S

    async def run(self, case_input: dict[str, Any], *, case_id: str = "") -> Output:
        # A timeout raises TimeoutError, which the retry loop treats as retryable.
        result = await asyncio.wait_for(self.func(case_input), self.timeout_s)
        if isinstance(result, Output):
            return result
        if isinstance(result, dict):
            return Output.model_validate(result)
        raise TypeError(f"target returned {type(result).__name__}, expected Output or dict")

    async def aclose(self) -> None:
        return None
