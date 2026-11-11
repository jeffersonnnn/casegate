"""Build the fixed run files that the report, compare, gate and console goldens read.

Run it from the repo root with `uv run python tests/fixtures/runs/make_runs.py`. Each run is
made with `runner.aggregate()` from one pass-count table, so the summary always equals the
case data (SPEC §17). Scorer names, Output text and the error repeat follow SPEC §17 exactly,
because M3 calibration joins labels to these runs on them.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from casegate.models import Case, Output, RepeatResult, Run, Score, ScorerConfig
from casegate.runner import aggregate

HERE = Path(__file__).parent
REPEAT = 5
JUDGE_TYPES = {"llm_judge", "citation_support"}
OUTPUT_COST, JUDGE_COST = 0.0024, 0.0012

# id, tags, scorers as (resolved name, type), passes out of 5 in baseline / regressed / fixed,
# the scorer that fails in a failed repeat, and the run where one repeat is an error (or None).
# Every case has the scorers of SPEC §16.2; the counts are made up but fixed.
# fmt: off
CASES: list[tuple[str, list[str], list[tuple[str, str]], tuple[int, int, int], str]] = [
    ("refund-within-cap-01", ["refund", "tools"],
     [("tool_trajectory", "tool_trajectory"), ("state_match", "state_match"),
      ("llm_judge", "llm_judge")], (5, 1, 5), "tool_trajectory"),
    ("refund-partial-02", ["refund", "tools"],
     [("tool_trajectory", "tool_trajectory"), ("state_match", "state_match")],
     (5, 5, 5), "state_match"),
    ("refund-already-done-03", ["refund"],
     [("tool_trajectory", "tool_trajectory"), ("contains", "contains")], (4, 4, 4), "contains"),
    ("refund-late-45d-adv", ["refund", "adversarial"],
     [("tool_trajectory", "tool_trajectory"), ("llm_judge", "llm_judge")],
     (5, 5, 5), "llm_judge"),
    ("refund-over-cap-adv", ["refund", "adversarial"],
     [("no-over-cap-attempt", "state_match"), ("attempts-within-cap", "state_match"),
      ("llm_judge", "llm_judge")], (5, 2, 5), "attempts-within-cap"),
    ("injection-order-note-adv", ["security", "adversarial"],
     [("tool_trajectory", "tool_trajectory"), ("not_contains", "not_contains"),
      ("state_match", "state_match")], (5, 5, 5), "not_contains"),
    ("order-status-07", ["status"],
     [("tool_trajectory", "tool_trajectory"), ("contains", "contains")], (5, 4, 5), "contains"),
    ("unknown-order-08", ["status"],
     [("tool_trajectory", "tool_trajectory"), ("llm_judge", "llm_judge")],
     (4, 4, 4), "llm_judge"),
    ("escalate-request-09", ["escalation"],
     [("tool_trajectory", "tool_trajectory"), ("state_match", "state_match")],
     (5, 5, 5), "tool_trajectory"),
    ("policy-window-10", ["policy", "citations"],
     [("tool_trajectory", "tool_trajectory"), ("contains", "contains"),
      ("citation_support", "citation_support")], (5, 2, 5), "citation_support"),
    ("policy-timeline-11", ["policy", "citations"],
     [("citation_support", "citation_support"), ("llm_judge", "llm_judge")],
     (3, 3, 4), "llm_judge"),
    ("policy-method-12", ["policy", "citations"],
     [("contains", "contains"), ("citation_support", "citation_support")],
     (5, 5, 5), "citation_support"),
    ("policy-giftcard-13", ["policy", "citations"],
     [("tool_trajectory", "tool_trajectory"), ("contains", "contains"),
      ("citation_support", "citation_support")], (4, 4, 5), "contains"),
    ("json-summary-14", ["format"], [("json_schema", "json_schema")], (5, 5, 5), "json_schema"),
    ("exact-ok-15", ["format"], [("exact", "exact")], (5, 5, 5), "exact"),
]
# fmt: on
ERROR_CASE = "order-status-07"  # regressed only: its one non-pass repeat is an error, not a fail

RUNS = {  # name: (column in CASES, git sha, target version, started_at)
    "baseline": (0, "a" * 40, "toy-agent@1", datetime(2026, 11, 10, 12, 0, tzinfo=UTC)),
    "regressed": (1, "b" * 40, "toy-agent@2", datetime(2026, 11, 11, 9, 0, tzinfo=UTC)),
    "fixed": (2, "c" * 40, "toy-agent@2", datetime(2026, 11, 11, 10, 0, tzinfo=UTC)),
}


def _score(case_id: str, k: int, name: str, type_: str, failed: bool) -> Score:
    judge = type_ in JUDGE_TYPES
    if judge:
        reason = f"fixture judge {case_id} r{k}"
    else:
        reason = f"fixture fail {name}" if failed else "ok"
    details = {}
    if judge:
        details = {
            "judge_model": "claude-sonnet-5-5",
            "cost_usd_full": JUDGE_COST,
            "input_tokens": 600,
            "output_tokens": 80,
            "calls": 1,
            "cached_calls": 0,
            "judge_attempts": 1,
        }
    return Score(
        scorer=name,
        type=type_,
        value=0.0 if failed else 1.0,
        passed=not failed,
        threshold=0.7 if judge else 1.0,
        reason=reason,
        cost_usd=JUDGE_COST if judge else 0.0,
        details=details,
    )


def _repeat(case_id: str, index: int, k: int, row: tuple, passes: int, err: bool) -> RepeatResult:
    _, _, scorers, _, fail_name = row
    # Spread the failing repeats over the repeat indices, so per-repeat pass rates vary.
    failing = {(index + j) % REPEAT for j in range(REPEAT - passes)}
    if err and k == min(failing):
        return RepeatResult(
            repeat=k,
            status="error",
            error="RuntimeError: fixture error",
            attempts=4,
            latency_ms=900,
            cost_usd=0.0,
            cost_usd_full=0.0,
        )
    failed = k in failing
    scores = [_score(case_id, k, n, t, failed and n == fail_name) for n, t in scorers]
    output = Output(
        text=f"reply {case_id} r{k}",
        input_tokens=1200,
        output_tokens=300,
        cost_usd=OUTPUT_COST,
        latency_ms=2000,
    )
    cost = OUTPUT_COST + sum(s.cost_usd or 0.0 for s in scores)
    return RepeatResult(
        repeat=k,
        status="fail" if failed else "pass",
        scores=scores,
        output=output,
        latency_ms=2400,
        cost_usd=cost,
        cost_usd_full=cost,
    )


def build_run(name: str) -> Run:
    column, sha, version, started = RUNS[name]
    results: list[tuple[Case, list[RepeatResult]]] = []
    for index, row in enumerate(CASES):
        case_id, tags, scorers = row[0], row[1], row[2]
        case = Case(
            id=case_id,
            tags=tags,
            input={"messages": [{"role": "user", "content": "x"}]},
            scorers=[ScorerConfig(type=t, name=n) for n, t in scorers],
            source_file=f"cases/{index + 1:02d}-{case_id}.yaml",
        )
        err = name == "regressed" and case_id == ERROR_CASE
        passes = row[3][column]
        results.append(
            (case, [_repeat(case_id, index, k, row, passes, err) for k in range(REPEAT)])
        )
    judge_calls = sum(t in JUDGE_TYPES for row in CASES for _, t in row[2]) * REPEAT
    # A cold cache: every lookup misses, so no repeat is marked cached.
    cases, summary = aggregate(
        results,
        repeat=REPEAT,
        duration_s=90.0,
        cache_hits={"outputs": 0, "judge": 0},
        cache_lookups={"outputs": len(CASES) * REPEAT, "judge": judge_calls},
    )
    return Run(
        casegate_version="0.1.0",
        suite="toy-refund-agent",
        suite_path="evals",
        started_at=started,
        finished_at=started.replace(minute=1, second=30),
        git_sha=sha,
        target_version=version,
        target_model="claude-haiku-5-5",
        judge_model="claude-sonnet-5-5",
        repeat=REPEAT,
        filters={"must_pass_tags": ["adversarial"]},
        cases=cases,
        summary=summary,
    )


def render(name: str) -> str:
    return build_run(name).model_dump_json(indent=2) + "\n"


def main() -> None:
    for name in RUNS:
        (HERE / f"{name}.json").write_text(render(name), encoding="utf-8")


if __name__ == "__main__":
    main()
