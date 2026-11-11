"""A fake target for the suite_fake fixture: it echoes the case input back as an Output.

It needs no model and no network, so the runner and CLI tests get fixed, known results. One case
asks it to fail once with a RetryableError, which exercises the retry path (attempts == 2).
"""

from typing import Any

from casegate import RetryableError
from casegate.models import Output, ToolCall

# Fail only the first retry_once call per process; tests that run twice reset it with monkeypatch.
_retried = False


async def run(case_input: dict[str, Any]) -> Output:
    global _retried
    if case_input.get("retry_once") and not _retried:
        _retried = True
        raise RetryableError("busy", retry_after=0)
    return Output(
        text=case_input["reply"],
        tool_calls=[ToolCall(name=t) for t in case_input.get("tools", [])],
        state=case_input.get("state", {}),
    )
