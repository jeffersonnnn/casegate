"""Retry and backoff for target and judge calls.

Model APIs fail in passing (rate limits, overload, dropped connections). One shared
wrapper decides which errors are worth another try and how long to wait, so the runner
and the judge count attempts the same way and tests can replace the sleep.
"""

from __future__ import annotations

import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

from casegate.errors import RetriesExhausted, RetryableError
from casegate.models import RetryConfig

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore[assignment]

T = TypeVar("T")


def is_retryable(exc: BaseException) -> bool:
    """True when another try can succeed: timeouts, transport faults, 429 and 5xx."""
    # httpx.TimeoutException is a TransportError; it is named for the reader.
    # asyncio.TimeoutError is the builtin TimeoutError on Python 3.11+.
    if isinstance(
        exc, TimeoutError | httpx.TimeoutException | httpx.TransportError | RetryableError
    ):
        return True
    if anthropic is not None:
        if isinstance(
            exc,
            anthropic.RateLimitError | anthropic.APIConnectionError | anthropic.InternalServerError,
        ):
            return True
        # 529 (overloaded) has no own SDK class, so check the status of the base class.
        if isinstance(exc, anthropic.APIStatusError):
            return exc.status_code == 529 or exc.status_code >= 500
    return False


def retry_after(exc: BaseException) -> float | None:
    """The wait the server asked for, in seconds, or None when it asked for none."""
    value = getattr(exc, "retry_after", None)
    if value is not None:
        return float(value)
    if anthropic is not None and isinstance(exc, anthropic.APIStatusError):
        header = exc.response.headers.get("retry-after")
        if header is not None:
            try:
                return float(header)
            except ValueError:  # an HTTP date instead of seconds: fall back to backoff
                return None
    return None


async def with_retries(
    fn: Callable[[], Awaitable[T]],
    cfg: RetryConfig,
    sleep: Callable[[float], Awaitable[None]],
    *,
    jitter: Callable[[float], float] = lambda b: random.uniform(0, 0.25 * b),
) -> tuple[T, int]:
    """Call `fn` up to `cfg.attempts` times; return its value and the number of tries."""
    n = 1
    while True:
        try:
            return await fn(), n
        except Exception as exc:
            if not is_retryable(exc):
                # The caller re-raises this error as is; the runner still needs the try count.
                setattr(exc, "casegate_attempts", n)  # noqa: B010 (mypy rejects a new attribute)
                raise
            if n >= cfg.attempts:
                raise RetriesExhausted(exc, n) from exc
            asked = retry_after(exc)
            if asked is not None:
                wait = min(max(asked, 0.0), cfg.max_retry_after_s)
            else:
                b = cfg.backoff_s[min(n - 1, len(cfg.backoff_s) - 1)]
                wait = b + jitter(b)
            await sleep(wait)
            n += 1
