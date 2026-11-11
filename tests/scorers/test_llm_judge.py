"""The llm_judge scorer: params, thresholds, median of samples, reasons, costs and the cache."""

import asyncio
from pathlib import Path
from typing import Any

import pytest

from casegate.cache import Cache
from casegate.errors import JudgeError, SuiteError
from casegate.judge import FakeJudge, JudgeResult, Verdict
from casegate.models import Case, JudgeConfig, Output, RetryConfig, Score
from casegate.scorers import REGISTRY, ScoreContext, build_scorers
from casegate.scorers.llm_judge import JUDGE_SYSTEM, LlmJudgeScorer
from tests.scorers._util import make_case, make_suite

RUBRIC = "The reply confirms the refund amount."


async def no_sleep(_: float) -> None:
    return None


def judge_ctx(judge: Any, cache: Cache | None = None, samples: int = 1) -> ScoreContext:
    cfg = JudgeConfig(samples=samples)
    return ScoreContext(judge, cfg, "judge-m", cache, RetryConfig(backoff_s=[0.0]), no_sleep)


def verdicts(*scores: float) -> list[Verdict]:
    return [Verdict(reasoning=f"r{s}", score=s) for s in scores]


def run(
    scorer: dict[str, Any],
    ctx: ScoreContext,
    output: Output | None = None,
    case: Case | None = None,
) -> Score:
    case = case or make_case([scorer])
    (built,) = build_scorers(case, make_suite())
    return asyncio.run(built.score(case, output or Output(text="Refunded $39."), ctx))


def test_registered_as_a_judge_scorer() -> None:
    assert REGISTRY["llm_judge"] is LlmJudgeScorer
    assert LlmJudgeScorer.needs_judge is True


def test_rubric_is_required_and_params_are_checked() -> None:
    case = make_case([{"type": "llm_judge"}, {"type": "llm_judge", "rubric": "r", "samples": 10}])
    with pytest.raises(SuiteError) as exc:
        build_scorers(case, make_suite())
    assert exc.value.errors == [
        "case c1 scorer llm_judge: rubric: Field required",
        "case c1 scorer llm_judge#2: samples: Input should be less than or equal to 9",
    ]
    bad_part = make_case([{"type": "llm_judge", "rubric": "r", "include": ["tone"]}])
    with pytest.raises(SuiteError, match=r"include\.0"):
        build_scorers(bad_part, make_suite())


def test_threshold_defaults_to_the_suite_threshold() -> None:
    case = make_case(
        [
            {"type": "llm_judge", "rubric": "r"},
            {"type": "llm_judge", "rubric": "r", "threshold": 0.9},
        ]
    )
    built = build_scorers(case, make_suite(threshold=0.6))
    assert [s.threshold for s in built] == [0.6, 0.9]


def test_one_sample_pass_and_fail_use_the_judge_reasoning() -> None:
    ok = run({"type": "llm_judge", "rubric": RUBRIC}, judge_ctx(FakeJudge(verdicts(0.7))))
    assert (ok.passed, ok.value, ok.reason, ok.threshold) == (True, 0.7, "r0.7", 0.7)
    bad = run({"type": "llm_judge", "rubric": RUBRIC}, judge_ctx(FakeJudge(verdicts(0.5))))
    assert (bad.passed, bad.reason, bad.type, bad.scorer) == (
        False,
        "r0.5",
        "llm_judge",
        "llm_judge",
    )


def test_median_of_samples_reason_closest_to_median_and_details() -> None:
    judge = FakeJudge(verdicts(0.2, 0.9, 0.8))
    s = run({"type": "llm_judge", "rubric": RUBRIC}, judge_ctx(judge, samples=3))
    assert s.value == 0.8 and s.reason == "r0.8"
    assert s.details == {
        "samples": [0.2, 0.9, 0.8],
        "spread": pytest.approx(0.7),
        "judge_model": "judge-m",
        "cost_usd_full": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "calls": 3,
        "cached_calls": 0,
        "judge_attempts": 3,
    }
    assert judge.calls == 3 and s.cost_usd == 0.0


def test_even_samples_take_the_mean_median_and_first_closest_reason() -> None:
    # Median of (0.2, 0.6) is 0.4; both are 0.2 away, so the first sample's reason is kept.
    s = run(
        {"type": "llm_judge", "rubric": "r", "samples": 2}, judge_ctx(FakeJudge(verdicts(0.2, 0.6)))
    )
    assert s.value == pytest.approx(0.4) and s.reason == "r0.2"


def test_param_samples_override_the_suite_samples() -> None:
    judge = FakeJudge(verdicts(1.0))
    s = run({"type": "llm_judge", "rubric": "r", "samples": 1}, judge_ctx(judge, samples=5))
    assert judge.calls == 1 and s.details["calls"] == 1


def test_scores_are_clamped() -> None:
    s = run(
        {"type": "llm_judge", "rubric": "r", "samples": 2},
        judge_ctx(FakeJudge(verdicts(1.7, -0.3))),
    )
    assert s.details["samples"] == [1.0, 0.0] and s.value == 0.5


def test_reason_is_one_line_and_cut_at_300_chars() -> None:
    v = Verdict(reasoning="line one\nline two " + "x" * 400, score=1.0)
    s = run({"type": "llm_judge", "rubric": "r"}, judge_ctx(FakeJudge([v])))
    assert "\n" not in s.reason and len(s.reason) == 300 and s.reason.endswith("…")


def test_no_judge_is_an_error() -> None:
    ctx = judge_ctx(None)
    with pytest.raises(JudgeError, match="no judge configured"):
        run({"type": "llm_judge", "rubric": "r"}, ctx)


class PricedJudge:
    provider = "anthropic"

    def __init__(self, costs: list[float | None]) -> None:
        self.costs = costs
        self.calls = 0

    async def grade(self, *, system: str, prompt: str, schema: Any, model: str) -> Any:
        c = self.costs[self.calls]
        self.calls += 1
        return JudgeResult(Verdict(reasoning="r", score=1.0), 100, 10, c)

    async def aclose(self) -> None:
        return None


def test_costs_and_tokens_are_summed() -> None:
    judge = PricedJudge([0.001, 0.002, 0.003])
    s = run({"type": "llm_judge", "rubric": "r", "samples": 3}, judge_ctx(judge))
    assert s.cost_usd == pytest.approx(0.006)
    assert s.details["cost_usd_full"] == pytest.approx(0.006)
    assert (s.details["input_tokens"], s.details["output_tokens"]) == (300, 30)


def test_one_unknown_cost_makes_the_sum_unknown() -> None:
    s = run(
        {"type": "llm_judge", "rubric": "r", "samples": 2}, judge_ctx(PricedJudge([0.001, None]))
    )
    assert s.cost_usd is None and s.details["cost_usd_full"] is None


def test_cache_hit_costs_nothing_this_run_but_keeps_full_cost(tmp_path: Path) -> None:
    cache = Cache(tmp_path)
    scorer = {"type": "llm_judge", "rubric": "r", "samples": 2}
    first = run(scorer, judge_ctx(PricedJudge([0.001, 0.002]), cache))
    judge = PricedJudge([])
    second = run(scorer, judge_ctx(judge, cache))
    assert judge.calls == 0
    assert first.cost_usd == pytest.approx(0.003) and second.cost_usd == 0.0
    assert second.details["cost_usd_full"] == pytest.approx(0.003)
    assert (second.details["cached_calls"], second.details["judge_attempts"]) == (2, 0)
    assert second.details["input_tokens"] == 200  # original counts, also on a hit


def test_rubric_change_regrades(tmp_path: Path) -> None:
    cache = Cache(tmp_path)
    run({"type": "llm_judge", "rubric": "a"}, judge_ctx(FakeJudge(), cache))
    judge = FakeJudge()
    s = run({"type": "llm_judge", "rubric": "b"}, judge_ctx(judge, cache))
    assert judge.calls == 1 and s.details["cached_calls"] == 0


def test_judge_gets_the_fixed_system_prompt_and_model() -> None:
    judge = FakeJudge()
    run({"type": "llm_judge", "rubric": RUBRIC}, judge_ctx(judge))
    system, prompt, model = judge.requests[0]
    assert system == JUDGE_SYSTEM and model == "judge-m"
    assert prompt.startswith(f"RUBRIC:\n{RUBRIC}\n\nCONVERSATION:\n")
