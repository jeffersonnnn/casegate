"""The Markdown report of one run (`results/latest.md`, `casegate report`), SPEC §9.

A person who opens a run should see the headline number first and the worst cases with a
concrete failing scorer and reason next, not 75 raw repeats. The per-case cells (status,
pass count, failing scorer) are defined here once, and the terminal table reuses them.
"""

from __future__ import annotations

from casegate.fmt import ERROR_LIMIT, REASON_LIMIT, fmt_cache, fmt_money, fmt_rate, fmt_ts, md_cell
from casegate.models import CaseResult, Run
from casegate.stats import case_status

STATUS_WORD = {"pass": "✓ pass", "fail": "✗ fail", "error": "⚠ error"}
WORST_LIMIT = 10


def md_row(cells: list[str]) -> str:
    """One table row; an empty cell renders as `| |`, the form GitHub shows as blank."""
    return "|" + "|".join(f" {c} " if c else " " for c in cells) + "|"


def worst_key(case: CaseResult) -> tuple[bool, float, float, str]:
    """Report order (SPEC §9): pass rate up (None last), then mean score up, then id."""
    rate = case.pass_rate
    return (rate is None, rate or 0.0, case.mean_score or 0.0, case.id)


def pass_cell(case: CaseResult) -> str:
    passes = sum(r.status == "pass" for r in case.repeats)
    errors = sum(r.status == "error" for r in case.repeats)
    text = f"{passes}/{len(case.repeats)}"
    return text + (f" ({errors} errors)" if errors else "")


def mean_cell(case: CaseResult) -> str:
    return "—" if case.mean_score is None else f"{case.mean_score:.2f}"


def first_failure(case: CaseResult) -> tuple[str, str]:
    """(failing scorer cell, raw reason) from the first repeat that did not pass."""
    for rep in case.repeats:
        if rep.status == "error":
            return "⚠ error", rep.error or ""
        if rep.status == "fail":
            for s in rep.scores:
                if not s.passed:
                    return f"{s.scorer} {s.value:.2f} < {s.threshold:.2f}", s.reason
    return "", ""


def failing_scorer_cell(case: CaseResult) -> str:
    return first_failure(case)[0]


def _needs_attention(case: CaseResult) -> bool:
    return case.pass_rate is None or case.pass_rate < 1 or case_status(case) == "error"


def _header(run: Run) -> str:
    s = run.summary
    bold = f"**pass rate {fmt_rate(s.pass_rate)}**"
    if s.pass_rate is not None:
        bold += f" ± {fmt_rate(s.pass_rate_std)}"
    parts = [
        bold,
        f"{s.n_cases} cases × {run.repeat} repeats",  # noqa: RUF001 (SPEC §9 wants the sign)
        f"errors {s.n_error_repeats}",
        f"cost {fmt_money(s.cost_usd)}",
        f"target {run.target_version} ({run.target_model})",
    ]
    if run.judge_model is not None:
        parts.append(f"judge {run.judge_model}")
    parts += [run.git_sha[:7] if run.git_sha else "nogit", fmt_ts(run.finished_at)]
    return " · ".join(parts)


def _summary(run: Run) -> list[str]:
    s = run.summary
    rows = [
        ("pass rate", fmt_rate(s.pass_rate)),
        ("std across repeats", fmt_rate(s.pass_rate_std)),
        ("scored cases", f"{s.n_scored_cases}/{s.n_cases}"),
        ("error repeats", f"{s.n_error_repeats}/{s.n_repeats_total}"),
        ("tokens in / out", f"{s.input_tokens:,} / {s.output_tokens:,}"),
        ("cost this run", fmt_money(s.cost_usd)),
        ("cost full", fmt_money(s.cost_usd_full)),
        ("cache", fmt_cache(s)),
        ("duration", f"{s.duration_s:.1f} s"),
    ]
    return ["## Summary", "", "| metric | value |", "|---|--:|", *(md_row(list(r)) for r in rows)]


def _by_tag(run: Run) -> list[str]:
    lines = ["## Pass rate by tag", "", "| tag | cases | pass rate |", "|---|--:|--:|"]
    for tag in sorted(run.summary.by_tag):
        n = sum(tag in c.tags for c in run.cases)
        lines.append(
            md_row([md_cell(tag, REASON_LIMIT), str(n), fmt_rate(run.summary.by_tag[tag])])
        )
    return lines


def _worst(run: Run) -> list[str]:
    worst = sorted((c for c in run.cases if _needs_attention(c)), key=worst_key)[:WORST_LIMIT]
    if not worst:
        return ["## Worst cases", "", "✓ every case passed every repeat."]
    lines = [
        "## Worst cases",
        "",
        "| status | case | pass | mean | failing scorer | reason |",
        "|---|---|--:|--:|---|---|",
    ]
    for case in worst:
        scorer, reason = first_failure(case)
        cells = [
            STATUS_WORD[case_status(case)],
            md_cell(case.id, REASON_LIMIT),
            pass_cell(case),
            mean_cell(case),
            md_cell(scorer, REASON_LIMIT),
            md_cell(reason, REASON_LIMIT),
        ]
        lines.append(md_row(cells))
    return lines


def _errors(run: Run) -> list[str]:
    rows = [
        md_row([md_cell(c.id, REASON_LIMIT), str(r.repeat), md_cell(r.error or "", ERROR_LIMIT)])
        for c in run.cases
        for r in c.repeats
        if r.status == "error"
    ]
    if not rows:
        return []
    return ["## Errors", "", "| case | repeat | error |", "|---|--:|---|", *rows]


def render_markdown(run: Run) -> str:
    sections = [
        [f"# casegate · {run.suite}", "", _header(run)],
        _summary(run),
        _by_tag(run) if run.summary.by_tag else [],
        _worst(run),
        _errors(run),
        [f"<sub>casegate {run.casegate_version} · schema 1</sub>"],
    ]
    return "\n\n".join("\n".join(s) for s in sections if s) + "\n"
