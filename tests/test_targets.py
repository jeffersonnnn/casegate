import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from pydantic import ValidationError

from casegate.errors import HttpStatusRetryable, RetriesExhausted, SuiteError
from casegate.models import Output, RetryConfig, TargetConfig
from casegate.retry import with_retries
from casegate.targets import HttpTarget, PythonTarget, build_target

URL = "http://agent.test/run"


async def no_sleep(_: float) -> None:
    return None


def python_cfg(path: str, timeout_s: float | None = None) -> TargetConfig:
    return TargetConfig(type="python", path=path, version="t@1", model="none", timeout_s=timeout_s)


def http_cfg(headers: dict[str, str] | None = None) -> TargetConfig:
    return TargetConfig(type="http", url=URL, headers=headers or {}, version="t@1", model="none")


@pytest.fixture
def make_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Write a throwaway module on sys.path and return its unique name."""
    monkeypatch.syspath_prepend(str(tmp_path))
    names: list[str] = []

    def make(source: str) -> str:
        name = f"cg_target_{uuid.uuid4().hex[:8]}"
        (tmp_path / f"{name}.py").write_text(source)
        names.append(name)
        return name

    yield make
    for name in names:
        sys.modules.pop(name, None)


# --- PythonTarget -------------------------------------------------------------


async def test_python_dict_return_is_validated_into_output(make_module: Any) -> None:
    mod = make_module(
        "async def run(case_input):\n"
        "    return {'text': case_input['q'], 'state': {'done': True}}\n"
    )
    target = build_target(python_cfg(f"{mod}:run"))
    assert isinstance(target, PythonTarget)
    out = await target.run({"q": "hi"}, case_id="ignored")
    assert out == Output(text="hi", state={"done": True})
    await target.aclose()


async def test_python_output_return_is_kept() -> None:
    async def run(case_input: dict[str, Any]) -> Output:
        return Output(text="ok", input_tokens=3)

    out = await PythonTarget(run).run({})
    assert out.text == "ok" and out.input_tokens == 3


async def test_python_bad_dict_raises_validation_error() -> None:
    async def run(case_input: dict[str, Any]) -> dict[str, Any]:
        return {"text": "x", "unknown": 1}

    with pytest.raises(ValidationError):
        await PythonTarget(run).run({})


async def test_python_other_return_type_raises() -> None:
    async def run(case_input: dict[str, Any]) -> Any:
        return "just text"

    with pytest.raises(TypeError, match="expected Output or dict"):
        await PythonTarget(run).run({})


async def test_python_timeout() -> None:
    async def run(case_input: dict[str, Any]) -> Output:
        await asyncio.sleep(5)
        return Output(text="late")

    target = PythonTarget(run, timeout_s=0.01)
    with pytest.raises(TimeoutError):
        await target.run({})


def test_python_default_timeout(make_module: Any) -> None:
    mod = make_module("async def run(case_input):\n    return {'text': ''}\n")
    target = build_target(python_cfg(f"{mod}:run"))
    assert isinstance(target, PythonTarget) and target.timeout_s == 120.0
    target = build_target(python_cfg(f"{mod}:run", timeout_s=3))
    assert isinstance(target, PythonTarget) and target.timeout_s == 3


def test_sync_function_rejected(make_module: Any) -> None:
    mod = make_module("def run(case_input):\n    return {'text': ''}\n")
    with pytest.raises(SuiteError) as err:
        build_target(python_cfg(f"{mod}:run"))
    assert err.value.errors == [f"target.path: {mod}:run must be an async function"]


def test_missing_attribute(make_module: Any) -> None:
    mod = make_module("x = 1\n")
    with pytest.raises(SuiteError) as err:
        build_target(python_cfg(f"{mod}:run"))
    assert err.value.errors == [f"target.path: {mod} has no attribute run"]


def test_missing_module() -> None:
    with pytest.raises(SuiteError) as err:
        build_target(python_cfg("cg_no_such_module_xyz:run"))
    assert err.value.errors == [
        "target.path: cannot import cg_no_such_module_xyz: "
        "ModuleNotFoundError: No module named 'cg_no_such_module_xyz'"
    ]


def test_module_that_raises_on_import_is_wrapped(make_module: Any) -> None:
    mod = make_module("raise RuntimeError('boom at import')\n")
    with pytest.raises(SuiteError) as err:
        build_target(python_cfg(f"{mod}:run"))
    assert err.value.errors == [f"target.path: cannot import {mod}: RuntimeError: boom at import"]


def test_module_with_syntax_error_is_wrapped(make_module: Any) -> None:
    mod = make_module("def broken(:\n")
    with pytest.raises(SuiteError) as err:
        build_target(python_cfg(f"{mod}:run"))
    assert err.value.errors[0].startswith(f"target.path: cannot import {mod}: SyntaxError: ")


# --- HttpTarget ---------------------------------------------------------------


@respx.mock
async def test_http_200_posts_case_and_parses_output() -> None:
    route = respx.post(URL).mock(
        return_value=httpx.Response(200, json={"text": "done", "output_tokens": 7})
    )
    target = build_target(http_cfg({"X-Team": "evals"}))
    out = await target.run({"q": "hi"}, case_id="case-01")
    assert out == Output(text="done", output_tokens=7)
    request = route.calls.last.request
    assert request.headers["X-Team"] == "evals"
    assert httpx.Response(200, content=request.content).json() == {
        "case_id": "case-01",
        "input": {"q": "hi"},
    }
    await target.aclose()


@respx.mock
async def test_http_429_retry_after_then_success() -> None:
    respx.post(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(200, json={"text": "ok"}),
        ]
    )
    target = HttpTarget(URL, {})
    with pytest.raises(HttpStatusRetryable) as err:
        await target.run({})
    assert err.value.status == 429 and err.value.retry_after == 3.0
    assert (await target.run({})).text == "ok"
    await target.aclose()


@respx.mock
async def test_http_429_retry_after_is_honoured_by_retry_loop() -> None:
    respx.post(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(200, json={"text": "ok"}),
        ]
    )
    waits: list[float] = []

    async def sleep(seconds: float) -> None:
        waits.append(seconds)

    target = HttpTarget(URL, {})
    out, attempts = await with_retries(lambda: target.run({}), RetryConfig(attempts=3), sleep)
    assert out.text == "ok" and attempts == 2 and waits == [3.0]
    await target.aclose()


@respx.mock
async def test_http_429_date_retry_after_is_none() -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(429, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})
    )
    target = HttpTarget(URL, {})
    with pytest.raises(HttpStatusRetryable) as err:
        await target.run({})
    assert err.value.retry_after is None
    await target.aclose()


@respx.mock
async def test_http_500_is_retried_until_exhausted() -> None:
    route = respx.post(URL).mock(return_value=httpx.Response(500, text="oops"))
    target = HttpTarget(URL, {})
    cfg = RetryConfig(attempts=3, backoff_s=[0.0])
    with pytest.raises(RetriesExhausted) as err:
        await with_retries(lambda: target.run({}), cfg, no_sleep)
    assert err.value.attempts == 3 and route.call_count == 3
    assert isinstance(err.value.last, HttpStatusRetryable) and err.value.last.retry_after is None
    await target.aclose()


@respx.mock
async def test_http_400_is_not_retried() -> None:
    route = respx.post(URL).mock(return_value=httpx.Response(400, text="bad input"))
    target = HttpTarget(URL, {})
    with pytest.raises(RuntimeError, match="HTTP 400: bad input") as err:
        await with_retries(lambda: target.run({}), RetryConfig(attempts=3), no_sleep)
    assert route.call_count == 1
    assert getattr(err.value, "casegate_attempts", None) == 1
    await target.aclose()


@respx.mock
async def test_http_2xx_bad_body_is_an_error() -> None:
    respx.post(URL).mock(return_value=httpx.Response(200, text="not json"))
    target = HttpTarget(URL, {})
    with pytest.raises(ValidationError):
        await target.run({})
    await target.aclose()


def test_http_env_header_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CG_TEST_TOKEN", "s3cret")
    target = build_target(http_cfg({"Authorization": "Bearer ${CG_TEST_TOKEN}", "X-Plain": "a"}))
    assert isinstance(target, HttpTarget)
    assert target.headers == {"Authorization": "Bearer s3cret", "X-Plain": "a"}


def test_http_missing_env_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CG_TEST_MISSING", raising=False)
    with pytest.raises(SuiteError) as err:
        build_target(http_cfg({"Authorization": "Bearer ${CG_TEST_MISSING}"}))
    assert err.value.errors == [
        "target.headers.Authorization: environment variable CG_TEST_MISSING is not set"
    ]


async def test_http_client_is_lazy_and_closed() -> None:
    target = build_target(http_cfg())
    assert isinstance(target, HttpTarget)
    assert target._client is None
    await target.aclose()  # closing a target that never ran is a no-op
    assert target._client is None
    with respx.mock:
        respx.post(URL).mock(return_value=httpx.Response(200, json={"text": "ok"}))
        await target.run({})
    client = target._client
    assert client is not None and client.timeout.read == 60.0
    await target.aclose()
    assert client.is_closed and target._client is None
