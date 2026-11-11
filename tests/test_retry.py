import asyncio

import httpx
import pytest

from casegate.errors import HttpStatusRetryable, RetriesExhausted, RetryableError
from casegate.models import RetryConfig
from casegate.retry import is_retryable, retry_after, with_retries


class FakeSleep:
    def __init__(self) -> None:
        self.waits: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.waits.append(seconds)


def scripted(*steps: object):
    """A call that raises each exception in `steps` in order and returns any other value."""
    calls = iter(steps)

    async def fn() -> object:
        step = next(calls)
        if isinstance(step, BaseException):
            raise step
        return step

    return fn


def no_jitter(b: float) -> float:
    return 0.0


async def test_success_first_try_does_not_sleep() -> None:
    sleep = FakeSleep()
    value, attempts = await with_retries(scripted("ok"), RetryConfig(), sleep)
    assert (value, attempts) == ("ok", 1)
    assert sleep.waits == []


async def test_backoff_sequence() -> None:
    sleep = FakeSleep()
    fn = scripted(RetryableError("a"), RetryableError("b"), RetryableError("c"), "ok")
    cfg = RetryConfig(attempts=4, backoff_s=[1, 2, 4])
    value, attempts = await with_retries(fn, cfg, sleep, jitter=no_jitter)
    assert (value, attempts) == ("ok", 4)
    assert sleep.waits == [1, 2, 4]


async def test_backoff_reuses_last_step() -> None:
    sleep = FakeSleep()
    fn = scripted(*[RetryableError("x")] * 4, "ok")
    cfg = RetryConfig(attempts=5, backoff_s=[1, 2])
    await with_retries(fn, cfg, sleep, jitter=no_jitter)
    assert sleep.waits == [1, 2, 2, 2]


async def test_jitter_is_added_to_backoff() -> None:
    sleep = FakeSleep()
    fn = scripted(RetryableError("x"), "ok")
    cfg = RetryConfig(attempts=2, backoff_s=[2])
    await with_retries(fn, cfg, sleep, jitter=lambda b: 0.25 * b)
    assert sleep.waits == [2.5]


async def test_default_jitter_stays_within_a_quarter() -> None:
    sleep = FakeSleep()
    fn = scripted(*[RetryableError("x")] * 20, "ok")
    cfg = RetryConfig(attempts=10, backoff_s=[4])
    with pytest.raises(RetriesExhausted):
        await with_retries(fn, cfg, sleep)
    assert len(sleep.waits) == 9
    assert all(4.0 <= w <= 5.0 for w in sleep.waits)


async def test_retry_after_is_used_and_capped() -> None:
    sleep = FakeSleep()
    fn = scripted(
        RetryableError("slow", retry_after=100),
        HttpStatusRetryable(429, retry_after=3),
        RetryableError("now", retry_after=0),
        "ok",
    )
    cfg = RetryConfig(attempts=4, backoff_s=[1], max_retry_after_s=30)
    value, attempts = await with_retries(fn, cfg, sleep, jitter=no_jitter)
    assert (value, attempts) == ("ok", 4)
    assert sleep.waits == [30, 3, 0]


async def test_retries_exhausted_keeps_last_error() -> None:
    sleep = FakeSleep()
    last = HttpStatusRetryable(503)
    fn = scripted(RetryableError("first"), last)
    with pytest.raises(RetriesExhausted) as info:
        await with_retries(fn, RetryConfig(attempts=2, backoff_s=[1]), sleep, jitter=no_jitter)
    assert info.value.last is last
    assert info.value.attempts == 2
    assert str(info.value) == "HttpStatusRetryable: HTTP 503"
    assert sleep.waits == [1]


async def test_non_retryable_passes_through_on_first_try() -> None:
    sleep = FakeSleep()
    err = ValueError("bad input")
    with pytest.raises(ValueError) as info:
        await with_retries(scripted(err), RetryConfig(), sleep)
    assert info.value is err
    assert info.value.casegate_attempts == 1  # type: ignore[attr-defined]
    assert sleep.waits == []


async def test_non_retryable_after_a_retry_counts_both_tries() -> None:
    sleep = FakeSleep()
    err = KeyError("missing")
    fn = scripted(RetryableError("busy"), err)
    with pytest.raises(KeyError) as info:
        await with_retries(fn, RetryConfig(), sleep, jitter=no_jitter)
    assert info.value is err
    assert info.value.casegate_attempts == 2  # type: ignore[attr-defined]


async def test_cancellation_is_not_retried() -> None:
    sleep = FakeSleep()
    with pytest.raises(asyncio.CancelledError):
        await with_retries(scripted(asyncio.CancelledError()), RetryConfig(), sleep)
    assert sleep.waits == []


REQUEST = httpx.Request("POST", "https://api.example.test/v1")


@pytest.mark.parametrize(
    "exc",
    [
        TimeoutError(),
        httpx.ReadTimeout("t", request=REQUEST),
        httpx.ConnectError("c", request=REQUEST),
        RetryableError("busy"),
        HttpStatusRetryable(500),
    ],
)
def test_retryable_errors(exc: BaseException) -> None:
    assert is_retryable(exc)


@pytest.mark.parametrize("exc", [ValueError("x"), RuntimeError("x"), KeyError("x")])
def test_other_errors_are_not_retryable(exc: BaseException) -> None:
    assert not is_retryable(exc)


def test_retry_after_none_without_hint() -> None:
    assert retry_after(RetryableError("x")) is None
    assert retry_after(ValueError("x")) is None


def _api_error(status: int, headers: dict[str, str] | None = None) -> Exception:
    anthropic = pytest.importorskip("anthropic")
    response = httpx.Response(status, headers=headers or {}, request=REQUEST)
    classes = {
        400: anthropic.BadRequestError,
        429: anthropic.RateLimitError,
        500: anthropic.InternalServerError,
    }
    cls = classes.get(status, anthropic.APIStatusError)
    err: Exception = cls(f"status {status}", response=response, body=None)
    return err


@pytest.mark.parametrize(
    ("status", "retryable"),
    [(429, True), (500, True), (529, True), (503, True), (400, False), (404, False)],
)
def test_anthropic_status_errors(status: int, retryable: bool) -> None:
    assert is_retryable(_api_error(status)) is retryable


def test_anthropic_connection_errors_are_retryable() -> None:
    anthropic = pytest.importorskip("anthropic")
    assert is_retryable(anthropic.APIConnectionError(request=REQUEST))
    assert is_retryable(anthropic.APITimeoutError(request=REQUEST))


def test_anthropic_retry_after_header() -> None:
    assert retry_after(_api_error(429, {"retry-after": "7"})) == 7.0
    assert retry_after(_api_error(529, {"retry-after": "Wed, 21 Oct 2026 07:28:00 GMT"})) is None
    assert retry_after(_api_error(529)) is None


async def test_anthropic_retry_after_header_is_capped() -> None:
    sleep = FakeSleep()
    fn = scripted(_api_error(429, {"retry-after": "120"}), "ok")
    cfg = RetryConfig(attempts=2, backoff_s=[1], max_retry_after_s=30)
    value, attempts = await with_retries(fn, cfg, sleep, jitter=no_jitter)
    assert (value, attempts) == ("ok", 2)
    assert sleep.waits == [30]
