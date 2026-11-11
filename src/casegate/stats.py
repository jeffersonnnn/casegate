"""Turn per-repeat results into case pass rates and one run summary (SPEC §2 rules).

The pass-rate maths (errors left out of the denominator, std across repeats, unknown
costs kept unknown) decides what the gate sees, so it lives in pure functions that tests
call on hand-made results. The runner re-exports `aggregate` as `runner.aggregate`.
"""

from __future__ import annotations

import statistics
from collections.abc import Iterable

from casegate.models import Case, CaseResult, RepeatResult, RunSummary, Score, Status


def sum_costs(terms: Iterable[float | None]) -> float | None:
    """Sum costs; one unknown term makes the total unknown, never a silent 0."""
    total = 0.0
    for t in terms:
        if t is None:
            return None
        total += t
    return total


def case_status(case: CaseResult) -> Status:
    """One word per case for reports (SPEC §2 rule 10): a flaky fail outranks an error."""
    if case.pass_rate is None:
        return "error"
    if case.pass_rate < 1:
        return "fail"
    return "error" if any(r.status == "error" for r in case.repeats) else "pass"


def aggregate(
    results: list[tuple[Case, list[RepeatResult]]],
    *,
    repeat: int,
    duration_s: float,
    cache_hits: dict[str, int] | None = None,
    cache_lookups: dict[str, int] | None = None,
) -> tuple[list[CaseResult], RunSummary]:
    cases: list[CaseResult] = []
    for case, reps in results:
        scored = [r for r in reps if r.status != "error"]  # errors leave the denominator
        rate = sum(r.status == "pass" for r in scored) / len(scored) if scored else None
        means = [statistics.fmean(s.value for s in r.scores) for r in scored if r.scores]
        cases.append(
            CaseResult(
                id=case.id,
                tags=case.tags,
                repeats=reps,
                pass_rate=rate,
                mean_score=statistics.fmean(means) if means else None,
                variance=None if rate is None else rate * (1 - rate),
            )
        )

    per_repeat: list[float | None] = []
    for k in range(repeat):
        passed = [
            r.status == "pass"
            for c in cases
            for r in c.repeats
            if r.repeat == k and r.status != "error"
        ]
        per_repeat.append(sum(passed) / len(passed) if passed else None)
    rates = [c.pass_rate for c in cases if c.pass_rate is not None]
    scored_k = [r for r in per_repeat if r is not None]

    by_tag: dict[str, float | None] = {}
    for tag in sorted({t for c in cases for t in c.tags}):
        tagged = [c.pass_rate for c in cases if tag in c.tags and c.pass_rate is not None]
        by_tag[tag] = statistics.fmean(tagged) if tagged else None

    all_reps = [r for c in cases for r in c.repeats]
    scores: list[Score] = [s for r in all_reps for s in r.scores]
    hits, lookups = cache_hits or {}, cache_lookups or {}
    summary = RunSummary(
        pass_rate=statistics.fmean(rates) if rates else None,
        pass_rate_std=statistics.stdev(scored_k) if len(scored_k) >= 2 else 0.0,
        per_repeat_pass_rate=per_repeat,
        n_cases=len(cases),
        n_scored_cases=len(rates),
        n_repeats_total=len(all_reps),
        n_error_repeats=sum(r.status == "error" for r in all_reps),
        by_tag=by_tag,
        input_tokens=sum(r.output.input_tokens for r in all_reps if r.output)
        + sum(int(s.details.get("input_tokens", 0)) for s in scores),
        output_tokens=sum(r.output.output_tokens for r in all_reps if r.output)
        + sum(int(s.details.get("output_tokens", 0)) for s in scores),
        cost_usd=sum_costs(r.cost_usd for r in all_reps),
        cost_usd_full=sum_costs(r.cost_usd_full for r in all_reps),
        cache_output_hits=hits.get("outputs", 0),
        cache_output_total=lookups.get("outputs", 0),
        cache_judge_hits=hits.get("judge", 0),
        cache_judge_total=lookups.get("judge", 0),
        duration_s=duration_s,
    )
    return cases, summary
