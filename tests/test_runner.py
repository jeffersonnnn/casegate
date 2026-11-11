"""Runner flow with a scripted target, and the aggregation maths on hand-made results."""

import asyncio
import builtins
import statistics
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

import pytest
from pydantic import BaseModel, ConfigDict

from casegate.errors import RetriesExhausted, RetryableError, SuiteError
from casegate.models import (
    Case,
    Output,
    RepeatResult,
    RetryConfig,
    Score,
    ScorerConfig,
    Suite,
    TargetConfig,
)
from casegate.runner import ProgressEvent, aggregate, case_status, git_sha, run_suite
from casegate.scorers import REGISTRY

Step = Output | BaseException | Callable[[], Output]


class ScriptedTarget:
    """A fake target: each case id has a script of outputs or exceptions, one per call."""

    def __init__(self, script: dict[str, list[Step]], delay: float = 0.0) -> None:
        self.script = {k: list(v) for k, v in script.items()}
        self.delay = delay
        self.calls: list[str] = []
        self.in_flight = 0
        self.max_in_flight = 0
        self.closed = False

    async def run(self, case_input: dict[str, Any], *, case_id: str = "") -> Output:
        self.calls.append(case_id)
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            steps = self.script[case_id]
            step = steps.pop(0) if len(steps) > 1 else steps[0]  # the last step repeats
            if isinstance(step, BaseException):
                raise step
            return step() if callable(step) else step
        finally:
            self.in_flight -= 1

    async def aclose(self) -> None:
        self.closed = True


class FakeSleep:
    def __init__(self) -> None:
        self.waits: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.waits.append(seconds)


def make_suite(tmp_path: Path, **kw: Any) -> Suite:
    target = TargetConfig(type="python", path="tests.x:run", version="t@1", model="none")
    retries = RetryConfig(attempts=3, backoff_s=[0.5])
    return Suite(name="s", target=target, retries=retries, root=str(tmp_path), **kw)


def exact_case(case_id: str, answer: str = "OK", tags: list[str] | None = None) -> Case:
    return Case(
        id=case_id,
        tags=tags or [],
        input={"q": case_id},
        expected={"answer": answer},
        scorers=[ScorerConfig(type="exact")],
        source_file="cases/x.yaml",
    )


async def run(suite: Suite, cases: list[Case], target: ScriptedTarget, **kw: Any) -> Any:
    sleep = kw.pop("sleep", FakeSleep())
    return await run_suite(suite, cases, cache=None, judge=None, target=target, sleep=sleep, **kw)


async def test_pass_fail_error_statuses(tmp_path: Path) -> None:
    target = ScriptedTarget(
        {"a": [Output(text="OK")], "b": [Output(text="nope")], "c": [ValueError("boom")]}
    )
    cases = [exact_case("a"), exact_case("b"), exact_case("c")]
    result = await run(make_suite(tmp_path), cases, target)
    a, b, c = result.cases
    assert [r.status for r in (a.repeats[0], b.repeats[0], c.repeats[0])] == [
        "pass",
        "fail",
        "error",
    ]
    assert c.repeats[0].error == "ValueError: boom"
    assert c.repeats[0].attempts == 1  # not retryable: one try only
    assert c.repeats[0].output is None and c.pass_rate is None
    assert b.repeats[0].scores[0].scorer == "exact"
    assert result.summary.pass_rate == 0.5
    assert result.summary.n_error_repeats == 1
    assert not target.closed  # an injected target is never closed by the runner


async def test_retry_then_success(tmp_path: Path) -> None:
    sleep = FakeSleep()
    target = ScriptedTarget({"a": [RetryableError("busy", retry_after=2), Output(text="OK")]})
    result = await run(make_suite(tmp_path), [exact_case("a")], target, sleep=sleep)
    rep = result.cases[0].repeats[0]
    assert (rep.status, rep.attempts, rep.cached) == ("pass", 2, False)
    assert sleep.waits == [2]
    assert rep.output is not None and rep.output.latency_ms >= 0


async def test_retries_exhausted_is_error(tmp_path: Path) -> None:
    target = ScriptedTarget({"a": [RetryableError("busy", retry_after=0)]})
    result = await run(make_suite(tmp_path), [exact_case("a")], target)
    rep = result.cases[0].repeats[0]
    assert rep.status == "error"
    assert rep.attempts == 3
    assert rep.error == "RetryableError: busy"
    assert target.calls == ["a", "a", "a"]


async def test_non_retryable_after_a_retry_counts_both_tries(tmp_path: Path) -> None:
    target = ScriptedTarget({"a": [RetryableError("busy", retry_after=0), KeyError("k")]})
    result = await run(make_suite(tmp_path), [exact_case("a")], target)
    assert result.cases[0].repeats[0].attempts == 2


async def test_concurrency_limit(tmp_path: Path) -> None:
    cases = [exact_case(f"c{i}") for i in range(10)]
    target = ScriptedTarget({c.id: [Output(text="OK")] for c in cases}, delay=0.01)
    await run(make_suite(tmp_path, concurrency=8), cases, target, concurrency=2)
    assert target.max_in_flight == 2


async def test_suite_concurrency_is_the_default(tmp_path: Path) -> None:
    cases = [exact_case(f"c{i}") for i in range(6)]
    target = ScriptedTarget({c.id: [Output(text="OK")] for c in cases}, delay=0.01)
    await run(make_suite(tmp_path, concurrency=3), cases, target)
    assert target.max_in_flight == 3


async def test_repeats_progress_and_order(tmp_path: Path) -> None:
    events: list[ProgressEvent] = []
    target = ScriptedTarget(
        {"a": [Output(text="OK")], "b": [Output(text="OK"), Output(text="x"), Output(text="OK")]}
    )
    cases = [exact_case("a"), exact_case("b")]
    result = await run(make_suite(tmp_path), cases, target, repeat=3, progress=events.append)
    assert [c.id for c in result.cases] == ["a", "b"]
    assert [r.repeat for r in result.cases[1].repeats] == [0, 1, 2]
    assert len(events) == 6 and all(not e.cached for e in events)
    assert result.repeat == 3
    assert result.summary.n_repeats_total == 6


async def test_run_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_SHA", "f" * 40)
    target = ScriptedTarget({"a": [Output(text="OK", cost_usd=0.01, input_tokens=5)]})
    suite = make_suite(tmp_path, must_pass_tags=["core"])
    result = await run(suite, [exact_case("a")], target, tags=["core"])
    assert result.git_sha == "f" * 40
    assert result.filters == {"must_pass_tags": ["core"], "tags": ["core"]}
    assert (result.target_version, result.target_model, result.judge_model) == ("t@1", "none", None)
    assert result.summary.cost_usd == pytest.approx(0.01)
    assert result.summary.input_tokens == 5
    assert result.finished_at >= result.started_at


async def test_runner_builds_and_closes_its_own_target(tmp_path: Path) -> None:
    tc = TargetConfig(
        type="python", path="tests.fixtures.suite_fake.target:run", version="f@1", model="none"
    )
    suite = Suite(name="s", target=tc, root=str(tmp_path))
    case = exact_case("a")
    case.input = {"reply": "OK"}
    result = await run_suite(suite, [case], cache=None, judge=None)
    assert result.cases[0].pass_rate == 1.0


class _NoParams(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BoomScorer:
    type: ClassVar[str] = "boom"
    Params: ClassVar[builtins.type[BaseModel]] = _NoParams
    needs_judge: ClassVar[bool] = False
    error: ClassVar[BaseException] = RuntimeError("bad")

    def __init__(self, name: str, threshold: float, params: BaseModel) -> None:
        self.name, self.threshold, self.params = name, threshold, params

    @classmethod
    def check(cls, case: Case, params: BaseModel, suite_root: Path) -> list[str]:
        return []

    async def score(self, case: Case, output: Output, ctx: Any) -> Score:
        raise self.error


class JudgeNeedingScorer(BoomScorer):
    type: ClassVar[str] = "needs_judge"
    needs_judge: ClassVar[bool] = True


def boom_case(case_id: str) -> Case:
    return Case(
        id=case_id,
        input={},
        expected={"answer": "OK"},
        scorers=[ScorerConfig(type="exact"), ScorerConfig(type="boom")],
        source_file="cases/x.yaml",
    )


async def test_scorer_exception_is_error_and_keeps_scores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(REGISTRY, "boom", BoomScorer)  # type: ignore[arg-type]
    target = ScriptedTarget({"a": [Output(text="OK")]})
    result = await run(make_suite(tmp_path), [boom_case("a")], target)
    rep = result.cases[0].repeats[0]
    assert rep.status == "error"
    assert rep.error == "scorer boom: RuntimeError: bad"
    assert [s.scorer for s in rep.scores] == ["exact"]
    assert rep.output is not None


async def test_scorer_retries_exhausted_formats_last(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(REGISTRY, "boom", BoomScorer)  # type: ignore[arg-type]
    monkeypatch.setattr(BoomScorer, "error", RetriesExhausted(TimeoutError("slow"), 4))
    target = ScriptedTarget({"a": [Output(text="OK")]})
    result = await run(make_suite(tmp_path), [boom_case("a")], target)
    assert result.cases[0].repeats[0].error == "scorer boom: TimeoutError: slow"


async def test_suite_needs_a_judge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(REGISTRY, "needs_judge", JudgeNeedingScorer)  # type: ignore[arg-type]
    case = Case(
        id="a", input={}, scorers=[ScorerConfig(type="needs_judge")], source_file="cases/x.yaml"
    )
    with pytest.raises(SuiteError, match="suite needs a judge"):
        await run(make_suite(tmp_path), [case], ScriptedTarget({}))


class DictCache:
    """A minimal in-memory stand-in for the M2 Cache, to cover the runner's cache path."""

    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}
        self.hits = {"outputs": 0, "judge": 0}
        self.lookups = {"outputs": 0, "judge": 0}

    def get(self, ns: str, key_obj: dict[str, Any], validate: Any = None) -> Any:
        self.lookups[ns] += 1
        value = self.store.get(repr((ns, key_obj)))
        if value is not None:
            if validate is not None:
                validate(value)
            self.hits[ns] += 1
        return value

    def put(self, ns: str, key_obj: dict[str, Any], value: dict[str, Any]) -> None:
        self.store[repr((ns, key_obj))] = value


async def test_cache_hit_path(tmp_path: Path) -> None:
    cache = DictCache()
    suite = make_suite(tmp_path)
    out = Output(text="OK", cost_usd=0.02, latency_ms=7)
    for _ in range(2):
        target = ScriptedTarget({"a": [out]})
        result = await run_suite(
            suite,
            [exact_case("a")],
            cache=cache,
            judge=None,
            target=target,  # type: ignore[arg-type]
        )
    rep = result.cases[0].repeats[0]
    assert (rep.cached, rep.attempts, rep.cost_usd) == (True, 0, 0.0)
    assert rep.cost_usd_full == pytest.approx(0.02)
    assert rep.output is not None and rep.output.latency_ms == 7  # stored Output unchanged
    assert (result.summary.cache_output_hits, result.summary.cache_output_total) == (1, 2)


def rep(k: int, status: str, values: list[float] | None = None, **kw: Any) -> RepeatResult:
    scores = [
        Score(scorer=f"s{i}", type="exact", value=v, passed=v >= 1, threshold=1.0, reason="r")
        for i, v in enumerate(values or [])
    ]
    return RepeatResult(repeat=k, status=status, scores=scores, **kw)  # type: ignore[arg-type]


def case(case_id: str, tags: list[str]) -> Case:
    return Case(
        id=case_id, tags=tags, input={}, scorers=[ScorerConfig(type="exact")], source_file="x"
    )


def test_aggregate_maths() -> None:
    results = [
        (case("a", ["t1"]), [rep(0, "pass", [1.0]), rep(1, "pass", [1.0]), rep(2, "fail", [0.0])]),
        (case("b", ["t1", "t2"]), [rep(0, "fail", [0.5]), rep(1, "error"), rep(2, "pass", [1.0])]),
        (case("c", ["t3"]), [rep(0, "error"), rep(1, "error"), rep(2, "error")]),
    ]
    cases, s = aggregate(results, repeat=3, duration_s=1.5)
    a, b, c = cases
    assert a.pass_rate == pytest.approx(2 / 3)
    assert a.variance == pytest.approx(2 / 9)
    assert a.mean_score == pytest.approx(2 / 3)
    assert b.pass_rate == 0.5 and b.mean_score == pytest.approx(0.75)
    assert c.pass_rate is None and c.variance is None and c.mean_score is None
    assert s.per_repeat_pass_rate == [0.5, 1.0, 0.5]
    assert s.pass_rate_std == pytest.approx(statistics.stdev([0.5, 1.0, 0.5]))
    assert s.pass_rate == pytest.approx((2 / 3 + 0.5) / 2)
    assert (s.n_cases, s.n_scored_cases, s.n_repeats_total, s.n_error_repeats) == (3, 2, 9, 4)
    assert list(s.by_tag) == ["t1", "t2", "t3"]
    assert s.by_tag["t1"] == pytest.approx((2 / 3 + 0.5) / 2)
    assert s.by_tag["t2"] == 0.5 and s.by_tag["t3"] is None
    assert (s.cache_output_hits, s.cache_output_total) == (0, 0)
    assert s.duration_s == 1.5
    assert [case_status(x) for x in cases] == ["fail", "fail", "error"]


def test_aggregate_single_repeat_std_is_zero_and_all_error_rate_none() -> None:
    _, s = aggregate([(case("a", []), [rep(0, "error")])], repeat=1, duration_s=0.0)
    assert s.pass_rate is None and s.pass_rate_std == 0.0
    assert s.per_repeat_pass_rate == [None]


def test_case_status_error_when_all_scored_pass_but_one_errored() -> None:
    cases, _ = aggregate(
        [(case("a", []), [rep(0, "pass", [1.0]), rep(1, "error")])], repeat=2, duration_s=0
    )
    assert case_status(cases[0]) == "error"
    cases, _ = aggregate([(case("a", []), [rep(0, "pass", [1.0])])], repeat=1, duration_s=0)
    assert case_status(cases[0]) == "pass"


def test_aggregate_costs_tokens_and_cache_counters() -> None:
    judge = Score(
        scorer="j",
        type="llm_judge",
        value=1.0,
        passed=True,
        threshold=0.7,
        reason="r",
        cost_usd=0.0,
        details={"cost_usd_full": 0.03, "input_tokens": 100, "output_tokens": 10},
    )
    r0 = RepeatResult(
        repeat=0,
        status="pass",
        scores=[judge],
        output=Output(text="x", input_tokens=7, output_tokens=3),
        cost_usd=0.01,
        cost_usd_full=0.04,
    )
    r1 = RepeatResult(repeat=1, status="error", cost_usd=None, cost_usd_full=0.02)
    _, s = aggregate(
        [(case("a", []), [r0, r1])],
        repeat=2,
        duration_s=0,
        cache_hits={"outputs": 1, "judge": 2},
        cache_lookups={"outputs": 2, "judge": 3},
    )
    assert (s.input_tokens, s.output_tokens) == (107, 13)
    assert s.cost_usd is None  # one unknown term makes the sum unknown
    assert s.cost_usd_full == pytest.approx(0.06)
    assert (s.cache_output_hits, s.cache_output_total) == (1, 2)
    assert (s.cache_judge_hits, s.cache_judge_total) == (2, 3)


async def test_unknown_target_cost_makes_repeat_cost_unknown(tmp_path: Path) -> None:
    target = ScriptedTarget({"a": [Output(text="OK", cost_usd=None)]})
    result = await run(make_suite(tmp_path), [exact_case("a")], target)
    rep0 = result.cases[0].repeats[0]
    assert rep0.cost_usd is None and rep0.cost_usd_full is None
    assert result.summary.cost_usd is None


def test_git_sha_without_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.chdir(tmp_path)  # not a git repo: rev-parse fails, so no sha
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    assert git_sha() is None


def test_git_sha_missing_git(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    def missing(*_a: Any, **_k: Any) -> Any:
        raise FileNotFoundError("git")

    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.setattr(subprocess, "run", missing)
    assert git_sha() is None


def test_git_sha_from_git(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    def fake_run(*_a: Any, **_k: Any) -> Any:
        return subprocess.CompletedProcess(["git"], 0, stdout="abc123\n", stderr="")

    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert git_sha() == "abc123"
