"""Judge clients and cached_grade: request shapes, errors, the fake judge and the judge cache."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
import respx
from pydantic import BaseModel

from casegate.cache import Cache
from casegate.errors import HttpStatusRetryable, JudgeError, RetriesExhausted, SuiteError
from casegate.judge import (
    AnthropicJudge,
    CitationVerdict,
    FakeJudge,
    JudgeResult,
    Verdict,
    build_judge,
    cached_grade,
    resolve_judge_model,
)
from casegate.judge_openai import OpenAICompatJudge
from casegate.models import JudgeConfig, RetryConfig
from casegate.prices import cost
from casegate.scorers.base import ScoreContext

URL = "https://judge.test/v1/chat/completions"
SAMPLING = {"temperature", "top_p", "top_k"}


async def no_sleep(_: float) -> None:
    return None


def ctx(judge: Any, cache: Cache | None = None, **cfg: Any) -> ScoreContext:
    retry = RetryConfig(attempts=3, backoff_s=[0.0])
    return ScoreContext(judge, JudgeConfig(**cfg), "judge-m", cache, retry, no_sleep)


# --- models and helpers --------------------------------------------------------------------


def test_verdicts_forbid_extra_fields() -> None:
    with pytest.raises(ValueError):
        Verdict.model_validate({"reasoning": "r", "score": 1, "x": 1})
    with pytest.raises(ValueError):
        CitationVerdict.model_validate({"reasoning": "r", "supported": True, "x": 1})


def test_resolve_judge_model_env_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = JudgeConfig(model="m-file", model_env="CG_TEST_JUDGE")
    monkeypatch.delenv("CG_TEST_JUDGE", raising=False)
    assert resolve_judge_model(cfg) == "m-file"
    monkeypatch.setenv("CG_TEST_JUDGE", "")
    assert resolve_judge_model(cfg) == "m-file"
    monkeypatch.setenv("CG_TEST_JUDGE", "m-env")
    assert resolve_judge_model(cfg) == "m-env"


async def test_build_judge_picks_the_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    a = build_judge(JudgeConfig(provider="anthropic"))
    o = build_judge(JudgeConfig(provider="openai"))
    assert (type(a), a.provider) == (AnthropicJudge, "anthropic")
    assert (type(o), o.provider) == (OpenAICompatJudge, "openai")
    await a.aclose()
    await o.aclose()


# --- AnthropicJudge ------------------------------------------------------------------------


class StubMessages:
    def __init__(self, resp: Any) -> None:
        self.resp = resp
        self.kwargs: dict[str, Any] = {}

    async def parse(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        return self.resp


def stub_client(parsed: Any, stop_reason: str = "end_turn") -> Any:
    usage = SimpleNamespace(input_tokens=529, output_tokens=101)
    resp = SimpleNamespace(parsed_output=parsed, stop_reason=stop_reason, usage=usage)
    return SimpleNamespace(messages=StubMessages(resp))


async def test_anthropic_request_shape_has_no_sampling_fields() -> None:
    client = stub_client(Verdict(reasoning="ok", score=0.9))
    judge = AnthropicJudge(JudgeConfig(effort="high", max_tokens=900), client=client)
    res = await judge.grade(system="S", prompt="P", schema=Verdict, model="claude-sonnet-5-5")
    kw = client.messages.kwargs
    assert kw == {
        "model": "claude-sonnet-5-5",
        "max_tokens": 900,
        "system": "S",
        "messages": [{"role": "user", "content": "P"}],
        "output_format": Verdict,
        "output_config": {"effort": "high"},
    }
    assert not SAMPLING & kw.keys()
    assert res.parsed == Verdict(reasoning="ok", score=0.9)
    assert (res.input_tokens, res.output_tokens) == (529, 101)
    assert res.cost_usd == pytest.approx(cost("claude-sonnet-5-5", 529, 101))
    await judge.aclose()  # an injected client is not closed (the stub has no close)


async def test_anthropic_unknown_model_cost_is_none() -> None:
    judge = AnthropicJudge(JudgeConfig(), client=stub_client(Verdict(reasoning="r", score=1)))
    res = await judge.grade(system="S", prompt="P", schema=Verdict, model="no-such-model")
    assert res.cost_usd is None


@pytest.mark.parametrize(
    ("parsed", "stop"),
    [(None, "end_turn"), (Verdict(reasoning="r", score=1), "refusal"), (None, "max_tokens")],
)
async def test_anthropic_no_verdict_is_judge_error(parsed: Any, stop: str) -> None:
    judge = AnthropicJudge(JudgeConfig(), client=stub_client(parsed, stop))
    with pytest.raises(JudgeError, match=stop):
        await judge.grade(system="S", prompt="P", schema=Verdict, model="m")


def test_anthropic_missing_key_names_the_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SuiteError, match=r"^ANTHROPIC_API_KEY is not set$"):
        AnthropicJudge(JudgeConfig())
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("CG_JUDGE_KEY", "")
    with pytest.raises(SuiteError, match=r"^CG_JUDGE_KEY is not set$"):
        AnthropicJudge(JudgeConfig(api_key_env="CG_JUDGE_KEY"))


def test_anthropic_missing_sdk_is_suite_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "anthropic", None)  # makes `import anthropic` fail
    with pytest.raises(SuiteError, match=r"pip install 'casegate\[anthropic\]'"):
        AnthropicJudge(JudgeConfig())


async def test_anthropic_builds_and_closes_its_own_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CG_JUDGE_KEY", "sk-test")
    judge = AnthropicJudge(JudgeConfig(api_key_env="CG_JUDGE_KEY"))
    client = judge._client
    assert client.api_key == "sk-test" and client.max_retries == 0
    await judge.aclose()
    assert client.is_closed()


# --- OpenAICompatJudge ---------------------------------------------------------------------


@pytest.fixture
def oa_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
    monkeypatch.setenv("CASEGATE_JUDGE_BASE_URL", "https://judge.test/v1/")


def ok_body(content: Any, refusal: Any = None) -> dict[str, Any]:
    message = {"content": content, "refusal": refusal}
    return {
        "choices": [{"message": message}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 5},
    }


def verdict_json(score: float = 0.5) -> str:
    return json.dumps({"reasoning": "fine", "score": score})


@respx.mock
async def test_openai_request_shape_and_result(oa_env: None) -> None:
    route = respx.post(URL).respond(200, json=ok_body(verdict_json(0.5)))
    judge = OpenAICompatJudge(JudgeConfig(provider="openai", max_tokens=321))
    res = await judge.grade(system="S", prompt="P", schema=Verdict, model="gpt-4.1-mini")
    req = route.calls.last.request
    body = json.loads(req.content)
    assert req.headers["authorization"] == "Bearer sk-oa"
    assert body["model"] == "gpt-4.1-mini"
    assert body["messages"] == [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "P"},
    ]
    assert body["max_tokens"] == 321 and body["temperature"] == 0
    fmt = body["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["name"] == "Verdict" and fmt["json_schema"]["strict"] is True
    assert fmt["json_schema"]["schema"]["additionalProperties"] is False
    assert set(fmt["json_schema"]["schema"]["properties"]) == {"reasoning", "score"}
    assert "effort" not in body
    assert res.parsed == Verdict(reasoning="fine", score=0.5)
    assert (res.input_tokens, res.output_tokens) == (50, 5)
    assert res.cost_usd == pytest.approx(cost("gpt-4.1-mini", 50, 5))
    await judge.aclose()


@respx.mock
async def test_openai_default_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
    monkeypatch.delenv("CASEGATE_JUDGE_BASE_URL", raising=False)
    route = respx.post("https://api.openai.com/v1/chat/completions").respond(
        200, json=ok_body(verdict_json())
    )
    judge = OpenAICompatJudge(JudgeConfig(provider="openai"))
    await judge.grade(system="S", prompt="P", schema=Verdict, model="m")
    assert route.called
    await judge.aclose()


@respx.mock
async def test_openai_temperature_rejected_falls_back_once_and_remembers(oa_env: None) -> None:
    route = respx.post(URL).mock(
        side_effect=[
            httpx.Response(400, text='{"error": "Unsupported parameter: Temperature"}'),
            httpx.Response(200, json=ok_body(verdict_json())),
            httpx.Response(200, json=ok_body(verdict_json())),
        ]
    )
    judge = OpenAICompatJudge(JudgeConfig(provider="openai"))
    await judge.grade(system="S", prompt="P", schema=Verdict, model="m")
    await judge.grade(system="S", prompt="P", schema=Verdict, model="m")
    sent = [json.loads(c.request.content) for c in route.calls]
    assert ["temperature" in b for b in sent] == [True, False, False]
    await judge.aclose()


@respx.mock
async def test_openai_other_400_is_judge_error_without_fallback(oa_env: None) -> None:
    route = respx.post(URL).respond(400, text="bad model")
    judge = OpenAICompatJudge(JudgeConfig(provider="openai"))
    with pytest.raises(JudgeError, match=r"^HTTP 400: bad model$"):
        await judge.grade(system="S", prompt="P", schema=Verdict, model="m")
    assert route.call_count == 1
    await judge.aclose()


@respx.mock
@pytest.mark.parametrize(
    ("status", "headers", "after"), [(429, {"Retry-After": "7"}, 7.0), (503, {}, None)]
)
async def test_openai_429_and_5xx_are_retryable(
    oa_env: None, status: int, headers: dict[str, str], after: float | None
) -> None:
    respx.post(URL).respond(status, headers=headers, text="busy")
    judge = OpenAICompatJudge(JudgeConfig(provider="openai"))
    with pytest.raises(HttpStatusRetryable) as exc:
        await judge.grade(system="S", prompt="P", schema=Verdict, model="m")
    assert (exc.value.status, exc.value.retry_after) == (status, after)
    await judge.aclose()


@respx.mock
@pytest.mark.parametrize(
    ("body", "match"),
    [
        (ok_body(None), "no verdict"),
        (ok_body(None, refusal="I will not"), "I will not"),
        (ok_body('{"reasoning": "r"}'), "does not match Verdict"),
        (ok_body("not json"), "does not match Verdict"),
        ({"choices": []}, "unexpected response"),
    ],
)
async def test_openai_bad_content_is_judge_error(
    oa_env: None, body: dict[str, Any], match: str
) -> None:
    respx.post(URL).respond(200, json=body)
    judge = OpenAICompatJudge(JudgeConfig(provider="openai"))
    with pytest.raises(JudgeError, match=match):
        await judge.grade(system="S", prompt="P", schema=Verdict, model="m")
    await judge.aclose()


def test_openai_missing_key_is_suite_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SuiteError, match=r"^OPENAI_API_KEY is not set$"):
        OpenAICompatJudge(JudgeConfig(provider="openai"))


async def test_openai_closes_only_its_own_client(oa_env: None) -> None:
    given = httpx.AsyncClient()
    await OpenAICompatJudge(JudgeConfig(provider="openai"), client=given).aclose()
    assert not given.is_closed
    await given.aclose()
    own = OpenAICompatJudge(JudgeConfig(provider="openai"))
    await own.aclose()
    assert own._client.is_closed


# --- FakeJudge -----------------------------------------------------------------------------


async def test_fake_judge_defaults_and_records_requests() -> None:
    judge = FakeJudge()
    v = await judge.grade(system="S", prompt="P", schema=Verdict, model="m")
    c = await judge.grade(system="S2", prompt="P2", schema=CitationVerdict, model="m2")
    assert v.parsed == Verdict(reasoning="fake", score=1.0)
    assert c.parsed == CitationVerdict(reasoning="fake", supported=True)
    assert (v.input_tokens, v.output_tokens, v.cost_usd) == (0, 0, 0.0)
    assert judge.provider == "fake" and judge.calls == 2
    assert judge.requests == [("S", "P", "m"), ("S2", "P2", "m2")]

    class Other(BaseModel):
        x: int

    with pytest.raises(JudgeError, match="no default for Other"):
        await judge.grade(system="S", prompt="P", schema=Other, model="m")
    await judge.aclose()


async def test_fake_judge_list_script_in_order_then_exhausted() -> None:
    judge = FakeJudge([Verdict(reasoning="a", score=0.1), Verdict(reasoning="b", score=0.2)])
    got = [(await judge.grade(system="", prompt="", schema=Verdict, model="m")).parsed.reasoning]
    got.append(
        (await judge.grade(system="", prompt="", schema=Verdict, model="m")).parsed.reasoning
    )
    assert got == ["a", "b"]
    with pytest.raises(JudgeError, match=r"^FakeJudge script exhausted$"):
        await judge.grade(system="", prompt="", schema=Verdict, model="m")


async def test_fake_judge_callable_and_wrong_type() -> None:
    seen: list[tuple[str, str, type[BaseModel]]] = []

    def script(system: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
        seen.append((system, prompt, schema))
        return Verdict(reasoning=prompt, score=0.4)

    judge = FakeJudge(script)
    res = await judge.grade(system="S", prompt="P", schema=Verdict, model="m")
    assert res.parsed.reasoning == "P" and seen == [("S", "P", Verdict)]
    with pytest.raises(JudgeError, match="expected CitationVerdict"):
        await judge.grade(system="S", prompt="P", schema=CitationVerdict, model="m")


# --- cached_grade --------------------------------------------------------------------------


async def test_cached_grade_without_a_judge_is_judge_error() -> None:
    with pytest.raises(JudgeError, match=r"^no judge configured$"):
        await cached_grade(
            ctx(None), kind="llm_judge", system="", prompt="", schema=Verdict, sample=0
        )
    no_model = ctx(FakeJudge())
    no_model.judge_model = None
    with pytest.raises(JudgeError, match=r"^no judge configured$"):
        await cached_grade(
            no_model, kind="llm_judge", system="", prompt="", schema=Verdict, sample=0
        )


async def test_cached_grade_without_cache_always_calls_the_judge() -> None:
    judge = FakeJudge()
    c = ctx(judge)
    for _ in range(2):
        _, hit, attempts = await cached_grade(
            c, kind="llm_judge", system="S", prompt="P", schema=Verdict, sample=0
        )
        assert (hit, attempts) == (False, 1)
    assert judge.calls == 2 and judge.requests[0] == ("S", "P", "judge-m")


class CostlyJudge:
    """A judge with a real-looking cost, to see what the cache stores and returns."""

    provider = "anthropic"

    def __init__(self) -> None:
        self.calls = 0

    async def grade(self, *, system: str, prompt: str, schema: Any, model: str) -> Any:
        self.calls += 1
        return JudgeResult(Verdict(reasoning="r", score=0.75), 500, 100, 0.002)

    async def aclose(self) -> None:
        return None


async def test_cached_grade_miss_then_hit_keeps_original_usage(tmp_path: Path) -> None:
    judge, cache = CostlyJudge(), Cache(tmp_path)
    c = ctx(judge, cache)
    first = await cached_grade(
        c, kind="llm_judge", system="S", prompt="P", schema=Verdict, sample=0
    )
    second = await cached_grade(
        c, kind="llm_judge", system="S", prompt="P", schema=Verdict, sample=0
    )
    assert first[1:] == (False, 1) and second[1:] == (True, 0)
    assert second[0] == JudgeResult(Verdict(reasoning="r", score=0.75), 500, 100, 0.002)
    assert judge.calls == 1
    assert (cache.hits["judge"], cache.lookups["judge"]) == (1, 2)


async def test_cached_grade_key_is_the_whole_request(tmp_path: Path) -> None:
    judge, cache = CostlyJudge(), Cache(tmp_path)
    base = {"kind": "llm_judge", "system": "S", "prompt": "P", "schema": Verdict, "sample": 0}
    await cached_grade(ctx(judge, cache), **base)
    variants = [
        (ctx(judge, cache), {**base, "prompt": "P2"}),
        (ctx(judge, cache), {**base, "system": "S2"}),
        (ctx(judge, cache), {**base, "sample": 1}),
        (ctx(judge, cache), {**base, "kind": "citation"}),
        (ctx(judge, cache, effort="high"), base),
        (ctx(judge, cache, max_tokens=10), base),
        (ctx(FakeJudge(), cache), base),  # another provider never reuses a real grade
    ]
    for c, kwargs in variants:
        _, hit, _ = await cached_grade(c, **kwargs)
        assert not hit, kwargs
    other_model = ctx(judge, cache)
    other_model.judge_model = "judge-other"
    assert not (await cached_grade(other_model, **base))[1]
    assert (await cached_grade(ctx(judge, cache), **base))[1]


async def test_cached_grade_effort_is_ignored_for_non_anthropic(tmp_path: Path) -> None:
    cache = Cache(tmp_path)
    base = {"kind": "llm_judge", "system": "S", "prompt": "P", "schema": Verdict, "sample": 0}
    await cached_grade(ctx(FakeJudge(), cache, effort="low"), **base)
    _, hit, _ = await cached_grade(ctx(FakeJudge(), cache, effort="high"), **base)
    assert hit


async def test_cached_grade_retries_and_counts_attempts() -> None:
    calls = 0

    def flaky(system: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise HttpStatusRetryable(529)
        return Verdict(reasoning="r", score=1.0)

    res, hit, attempts = await cached_grade(
        ctx(FakeJudge(flaky)), kind="llm_judge", system="", prompt="", schema=Verdict, sample=0
    )
    assert (hit, attempts, res.parsed.score) == (False, 2, 1.0)


async def test_cached_grade_retries_exhausted_and_judge_error_not_retried() -> None:
    def busy(system: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
        raise HttpStatusRetryable(503)

    with pytest.raises(RetriesExhausted) as exc:
        await cached_grade(
            ctx(FakeJudge(busy)), kind="llm_judge", system="", prompt="", schema=Verdict, sample=0
        )
    assert exc.value.attempts == 3
    judge = FakeJudge([])
    with pytest.raises(JudgeError):
        await cached_grade(
            ctx(judge), kind="llm_judge", system="", prompt="", schema=Verdict, sample=0
        )
    assert judge.calls == 1


async def test_cached_grade_entry_without_cost_is_a_miss(tmp_path: Path) -> None:
    # A damaged or old entry must be re-graded, never raise KeyError inside the scorer.
    judge, cache = CostlyJudge(), Cache(tmp_path)
    c = ctx(judge, cache)
    await cached_grade(c, kind="llm_judge", system="S", prompt="P", schema=Verdict, sample=0)
    (entry,) = list((tmp_path / "judge").rglob("*.json"))
    stored = json.loads(entry.read_text(encoding="utf-8"))
    del stored["cost_usd"]
    entry.write_text(json.dumps(stored), encoding="utf-8")
    result, hit, attempts = await cached_grade(
        c, kind="llm_judge", system="S", prompt="P", schema=Verdict, sample=0
    )
    assert (hit, attempts, result.cost_usd, judge.calls) == (False, 1, 0.002, 2)
