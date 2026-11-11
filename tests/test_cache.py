"""The disk cache on its own, and the runner reading and writing it across two runs."""

import builtins
import hashlib
import json
from pathlib import Path
from typing import Any, ClassVar

import pytest
from pydantic import BaseModel, ConfigDict

from casegate.cache import Cache, canonical_json, key
from casegate.models import (
    Case,
    Output,
    RetryConfig,
    Score,
    ScorerConfig,
    Suite,
    TargetConfig,
)
from casegate.runner import run_suite
from casegate.scorers import REGISTRY, ScoreContext

KEY = {"v": 1, "input": {"q": "é"}, "repeat": 0}


def test_key_is_sha256_of_canonical_json_and_order_free() -> None:
    expected = hashlib.sha256('{"input":{"q":"é"},"repeat":0,"v":1}'.encode()).hexdigest()
    assert key(KEY) == expected
    assert key({"repeat": 0, "v": 1, "input": {"q": "é"}}) == expected
    assert key({**KEY, "repeat": 1}) != expected
    assert canonical_json({"p": Path("x")}) == '{"p":"x"}'  # default=str


def test_root_from_env_then_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CASEGATE_CACHE_DIR", str(tmp_path / "env"))
    assert Cache().root == tmp_path / "env"
    monkeypatch.delenv("CASEGATE_CACHE_DIR")
    monkeypatch.chdir(tmp_path)
    assert Cache().root == tmp_path / ".casegate" / "cache"
    assert Cache(tmp_path / "given").root == tmp_path / "given"


def test_put_get_round_trip_and_file_layout(tmp_path: Path) -> None:
    cache = Cache(tmp_path)
    assert cache.get("outputs", KEY) is None
    cache.put("outputs", KEY, {"output": {"text": "hé"}})
    k = key(KEY)
    path = tmp_path / "outputs" / k[:2] / f"{k}.json"
    assert path.is_file()
    assert [p.name for p in path.parent.iterdir()] == [path.name]  # no temp file left
    assert cache.get("outputs", KEY) == {"output": {"text": "hé"}}
    assert cache.get("judge", KEY) is None  # namespaces never share entries
    assert cache.lookups == {"outputs": 2, "judge": 1}
    assert cache.hits == {"outputs": 1, "judge": 0}


@pytest.mark.parametrize("content", [b"{not json", b"[1, 2]", b"\xff\xfe"])
def test_corrupt_file_is_a_miss_and_is_overwritten(tmp_path: Path, content: bytes) -> None:
    cache = Cache(tmp_path)
    path = cache.path("judge", KEY)
    path.parent.mkdir(parents=True)
    path.write_bytes(content)
    assert cache.get("judge", KEY) is None
    assert (cache.hits["judge"], cache.lookups["judge"]) == (0, 1)
    cache.put("judge", KEY, {"parsed": {"score": 1}})
    assert cache.get("judge", KEY) == {"parsed": {"score": 1}}


def test_validate_failure_is_a_miss_without_a_hit(tmp_path: Path) -> None:
    cache = Cache(tmp_path)
    cache.put("outputs", KEY, {"output": {"txt": "wrong shape"}})
    got = cache.get("outputs", KEY, validate=lambda v: Output.model_validate(v["output"]))
    assert got is None
    missing_key = cache.get("outputs", KEY, validate=lambda v: v["absent"])
    assert missing_key is None
    assert (cache.hits["outputs"], cache.lookups["outputs"]) == (0, 2)
    good = cache.get("outputs", KEY, validate=lambda v: v["output"])
    assert good is not None and cache.hits["outputs"] == 1


def test_failed_write_leaves_no_temp_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(src: Any, dst: Any) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("casegate.cache.os.replace", fail)
    cache = Cache(tmp_path)
    with pytest.raises(OSError, match="disk full"):
        cache.put("outputs", KEY, {"output": {"text": "x"}})
    assert list(cache.path("outputs", KEY).parent.iterdir()) == []


# --- the runner with a real disk cache ---------------------------------------------------


class CountingTarget:
    def __init__(self, output: Output) -> None:
        self.output = output
        self.calls = 0

    async def run(self, case_input: dict[str, Any], *, case_id: str = "") -> Output:
        self.calls += 1
        return self.output

    async def aclose(self) -> None:
        return None


class _NoParams(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JudgeCacheScorer:
    """Stands in for a judge scorer: one judge-cache lookup per score, priced like a call."""

    type: ClassVar[str] = "judge_cache_probe"
    Params: ClassVar[builtins.type[BaseModel]] = _NoParams
    needs_judge: ClassVar[bool] = False

    def __init__(self, name: str, threshold: float, params: BaseModel) -> None:
        self.name, self.threshold, self.params = name, threshold, params

    @classmethod
    def check(cls, case: Case, params: BaseModel, suite_root: Path) -> list[str]:
        return []

    async def score(self, case: Case, output: Output, ctx: ScoreContext) -> Score:
        assert ctx.cache is not None
        k = {"v": 1, "text": output.text}
        hit = ctx.cache.get("judge", k, validate=lambda v: float(v["cost_usd"]))
        if hit is None:
            ctx.cache.put("judge", k, {"cost_usd": 0.01, "input_tokens": 5, "output_tokens": 2})
        return Score(
            scorer=self.name,
            type=self.type,
            value=1.0,
            passed=True,
            threshold=0.7,
            reason="r",
            cost_usd=0.0 if hit else 0.01,
            details={"cost_usd_full": 0.01, "input_tokens": 5, "output_tokens": 2},
        )


def make_suite(tmp_path: Path, version: str = "t@1") -> Suite:
    target = TargetConfig(type="python", path="tests.x:run", version=version, model="m")
    return Suite(name="s", target=target, retries=RetryConfig(attempts=1), root=str(tmp_path))


def make_case() -> Case:
    return Case(
        id="a",
        input={"q": "a"},
        expected={"answer": "OK"},
        scorers=[ScorerConfig(type="exact"), ScorerConfig(type="judge_cache_probe")],
        source_file="cases/a.yaml",
    )


async def test_second_run_is_all_hits_and_costs_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(REGISTRY, "judge_cache_probe", JudgeCacheScorer)  # type: ignore[arg-type]
    out = Output(text="OK", cost_usd=0.02, input_tokens=10, output_tokens=3, latency_ms=9)
    suite = make_suite(tmp_path)
    runs = []
    for _ in range(2):
        target = CountingTarget(out)
        cache = Cache(tmp_path / "cache")  # a fresh object: hits come from disk, not memory
        runs.append(
            await run_suite(suite, [make_case()], repeat=3, cache=cache, judge=None, target=target)
        )
        calls = target.calls
    cold, warm = runs
    assert calls == 0  # the warm run never called the target
    s = cold.summary
    assert (s.cache_output_hits, s.cache_output_total) == (0, 3)
    assert (s.cache_judge_hits, s.cache_judge_total) == (2, 3)  # 3 repeats share one judge key
    assert s.cost_usd == pytest.approx(3 * 0.02 + 0.01)
    assert s.cost_usd_full == pytest.approx(3 * (0.02 + 0.01))
    w = warm.summary
    assert (w.cache_output_hits, w.cache_output_total) == (3, 3)
    assert (w.cache_judge_hits, w.cache_judge_total) == (3, 3)
    assert w.cost_usd == 0.0
    assert w.cost_usd_full == pytest.approx(s.cost_usd_full)
    assert (w.input_tokens, w.output_tokens) == (s.input_tokens, s.output_tokens) == (45, 15)
    for rep in warm.cases[0].repeats:
        assert (rep.cached, rep.attempts, rep.status) == (True, 0, "pass")
        assert rep.output == out  # the stored Output comes back unchanged
    assert [r.repeat for r in warm.cases[0].repeats] == [0, 1, 2]


async def test_version_bump_misses_and_bad_entry_is_rewritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(REGISTRY, "judge_cache_probe", JudgeCacheScorer)  # type: ignore[arg-type]
    out = Output(text="OK", cost_usd=0.02)
    cache = Cache(tmp_path / "cache")
    await run_suite(
        make_suite(tmp_path), [make_case()], cache=cache, judge=None, target=CountingTarget(out)
    )

    bumped = CountingTarget(out)
    await run_suite(
        make_suite(tmp_path, "t@2"),
        [make_case()],
        cache=Cache(tmp_path / "cache"),
        judge=None,
        target=bumped,
    )
    assert bumped.calls == 1  # a new target version makes the stored output stale

    path = cache.path(
        "outputs",
        {"v": 1, "input": {"q": "a"}, "target_version": "t@1", "target_model": "m", "repeat": 0},
    )
    path.write_text(json.dumps({"output": {"text": 5}}), encoding="utf-8")
    again = CountingTarget(out)
    run = await run_suite(
        make_suite(tmp_path),
        [make_case()],
        cache=Cache(tmp_path / "cache"),
        judge=None,
        target=again,
    )
    assert again.calls == 1 and run.summary.cache_output_hits == 0
    assert json.loads(path.read_text(encoding="utf-8"))["output"]["text"] == "OK"


async def test_target_error_is_not_cached(tmp_path: Path) -> None:
    class Failing(CountingTarget):
        async def run(self, case_input: dict[str, Any], *, case_id: str = "") -> Output:
            self.calls += 1
            raise ValueError("boom")

    cache = Cache(tmp_path / "cache")
    case = make_case()
    case.scorers = [ScorerConfig(type="exact")]
    run = await run_suite(
        make_suite(tmp_path), [case], cache=cache, judge=None, target=Failing(Output(text=""))
    )
    assert run.cases[0].repeats[0].status == "error"
    assert not (tmp_path / "cache" / "outputs").exists()
