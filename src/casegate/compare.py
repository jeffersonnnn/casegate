"""Compare a run with a baseline: the pass-rate delta and the cases that flipped (SPEC §10).

A pass-rate number alone does not tell a reviewer what broke. The comparison names each
case that changed verdict, with the scorer and reason that failed, and warns when the two
runs are not like for like (another target version, judge model or repeat count).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from casegate.fmt import (
    REASON_LIMIT,
    fmt_delta,
    fmt_delta_int,
    fmt_delta_money,
    fmt_money,
    fmt_rate,
    md_cell,
)
from casegate.models import CaseResult, Run
from casegate.report import md_row

Verdict = Literal["pass", "fail", "error"]
DELTA_LIMIT = 10


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Flip(_Strict):
    id: str
    scorer: str | None
    reason: str | None


class Delta(_Strict):
    id: str
    baseline: float
    run: float
    delta: float


class Comparison(_Strict):
    flips_pass_to_fail: list[Flip]
    flips_fail_to_pass: list[Flip]
    changed_to_error: list[str]
    changed_from_error: list[str]
    added: list[str]
    removed: list[str]
    deltas: list[Delta]
    pass_rate_delta: float | None
    cost_delta: float | None
    baseline_error_repeats: int
    run_error_repeats: int
    warnings: list[str]


def verdict(case: CaseResult) -> Verdict:
    """A flip needs one verdict per case: majority of scored repeats, error when none scored."""
    if case.pass_rate is None:
        return "error"
    return "pass" if case.pass_rate >= 0.5 else "fail"


def _regression(case: CaseResult) -> Flip:
    for rep in case.repeats:
        if rep.status == "error":
            return Flip(id=case.id, scorer="⚠ error", reason=rep.error or "")
        if rep.status == "fail":
            failed = next((s for s in rep.scores if not s.passed), None)
            if failed is not None:
                return Flip(id=case.id, scorer=failed.scorer, reason=failed.reason)
    return Flip(id=case.id, scorer=None, reason=None)


def _minus(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else a - b


def compare(baseline: Run, run: Run) -> Comparison:
    base = {c.id: c for c in baseline.cases}
    now = {c.id: c for c in run.cases}
    p2f: list[Flip] = []
    f2p: list[Flip] = []
    to_err: list[str] = []
    from_err: list[str] = []
    ranked: list[tuple[float, int, Delta]] = []
    for index, case in enumerate(run.cases):
        old = base.get(case.id)
        if old is None:
            continue
        a, b = verdict(old), verdict(case)
        if a == "pass" and b == "fail":
            p2f.append(_regression(case))
        elif a == "fail" and b == "pass":
            f2p.append(Flip(id=case.id, scorer=None, reason=None))
        elif b == "error" and a != "error":
            to_err.append(case.id)
        elif a == "error" and b != "error":
            from_err.append(case.id)
        if old.pass_rate is not None and case.pass_rate is not None:
            d = case.pass_rate - old.pass_rate
            if abs(d) > 1e-9:
                ranked.append(
                    (
                        -abs(d),
                        index,
                        Delta(id=case.id, baseline=old.pass_rate, run=case.pass_rate, delta=d),
                    )
                )
    warnings = []
    pairs = [
        ("target version", baseline.target_version, run.target_version),
        ("judge model", baseline.judge_model, run.judge_model),
        ("repeat", baseline.repeat, run.repeat),
    ]
    for label, a_val, b_val in pairs:
        if a_val != b_val:
            warnings.append(f"{label} changed: {a_val or 'none'} → {b_val or 'none'}")
    return Comparison(
        flips_pass_to_fail=p2f,
        flips_fail_to_pass=f2p,
        changed_to_error=to_err,
        changed_from_error=from_err,
        added=[c.id for c in run.cases if c.id not in base],
        removed=[c.id for c in baseline.cases if c.id not in now],
        deltas=[d for _, _, d in sorted(ranked, key=lambda t: (t[0], t[1]))[:DELTA_LIMIT]],
        pass_rate_delta=_minus(run.summary.pass_rate, baseline.summary.pass_rate),
        cost_delta=_minus(run.summary.cost_usd, baseline.summary.cost_usd),
        baseline_error_repeats=baseline.summary.n_error_repeats,
        run_error_repeats=run.summary.n_error_repeats,
        warnings=warnings,
    )


def metric_rows(
    cmp: Comparison, baseline: Run, run: Run, extra: list[list[str]] | None = None
) -> list[list[str]]:
    """metric | baseline | run | delta rows; `extra` (gate must-pass rows) go after std."""
    b, r = baseline.summary, run.summary
    return [
        ["pass rate", fmt_rate(b.pass_rate), fmt_rate(r.pass_rate), fmt_delta(cmp.pass_rate_delta)],
        ["std across repeats", fmt_rate(b.pass_rate_std), fmt_rate(r.pass_rate_std), ""],
        *(extra or []),
        [
            "error repeats",
            str(b.n_error_repeats),
            str(r.n_error_repeats),
            fmt_delta_int(r.n_error_repeats - b.n_error_repeats),
        ],
        [
            "cost",
            fmt_money(b.cost_usd),
            fmt_money(r.cost_usd),
            fmt_delta_money(b.cost_usd, r.cost_usd),
        ],
    ]


def metric_table_md(rows: list[list[str]]) -> str:
    head = ["| metric | baseline | run | delta |", "|---|--:|--:|--:|"]
    return "\n".join(head + [md_row(row) for row in rows])


def flip_cells(flip: Flip, *, markdown: bool = True) -> list[str]:
    """The case, scorer and reason cells; the terminal passes markdown=False (SPEC §9)."""
    reason = "—" if flip.reason is None else md_cell(flip.reason, REASON_LIMIT, markdown=markdown)
    return [flip.id, flip.scorer or "—", reason]


def flips_md(cmp: Comparison, keep_p2f: int | None = None, keep_f2p: int | None = None) -> str:
    """The two flips <details> blocks; `keep_*` cut a table and end it with `… N more`.

    An empty direction holds the line `_none_` in place of a header-only table (SPEC §11).
    """
    blocks = []
    tables = [
        ("<details open>", "Flipped pass → fail", cmp.flips_pass_to_fail, keep_p2f),
        ("<details>", "Flipped fail → pass", cmp.flips_fail_to_pass, keep_f2p),
    ]
    for tag, title, flips, keep in tables:
        kept = flips if keep is None else flips[:keep]
        rows = [md_row(flip_cells(f)) for f in kept]
        if len(kept) < len(flips):
            rows.append(md_row([f"… {len(flips) - len(kept)} more", "", ""]))
        table = (
            ["| case | failing scorer | reason |", "|---|---|---|", *rows] if flips else ["_none_"]
        )
        summary = f"{tag}<summary>{title} ({len(flips)})</summary>"
        blocks.append("\n".join([summary, "", *table, "", "</details>"]))
    return "\n".join(blocks)


def list_lines(cmp: Comparison) -> list[tuple[str, str]]:
    """(label, text) for each non-empty list, in the §10 order; errors keep the ⚠ glyph."""
    lists = [
        ("Errors", "⚠ ", cmp.changed_to_error),
        ("Recovered from error", "", cmp.changed_from_error),
        ("Added", "", cmp.added),
        ("Removed", "", cmp.removed),
    ]
    return [(label, glyph + ", ".join(ids)) for label, glyph, ids in lists if ids]


def list_lines_md(cmp: Comparison) -> list[str]:
    return [f"**{label}** {text}" for label, text in list_lines(cmp)]


def render_comparison_md(cmp: Comparison, baseline: Run, run: Run) -> str:
    parts = [metric_table_md(metric_rows(cmp, baseline, run)), flips_md(cmp), *list_lines_md(cmp)]
    return "\n\n".join(parts) + "\n"
