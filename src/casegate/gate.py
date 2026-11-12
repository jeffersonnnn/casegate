"""The CI gate: decide pass or block from a comparison, and write the PR comment (SPEC §11).

Every rule runs and reports, even after one fails, so a blocked pull request shows all of
its problems at once. The comment is one Markdown body with a fixed marker, so CI can find
and edit the same comment on every push instead of adding a new one.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from casegate.compare import (
    Comparison,
    compare,
    flip_cells,
    flips_md,
    list_lines_md,
    metric_rows,
    metric_table_md,
)
from casegate.fmt import fmt_delta_int, fmt_signed3
from casegate.models import CaseResult, Run

MARKER = "<!-- casegate-gate -->"
BODY_LIMIT = 60_000


class GateCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    passed: bool
    detail: str


class GateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passed: bool
    checks: list[GateCheck]
    comparison: Comparison


def resolve_must_pass_tags(run: Run, cli_tags: list[str] | None) -> list[str]:
    """CLI tags win; else the RUN file's tags (never the baseline's, which a PR cannot set)."""
    if cli_tags:
        return list(cli_tags)
    return [str(t) for t in run.filters.get("must_pass_tags", [])]


def _all_passed(case: CaseResult) -> bool:
    return all(r.status == "pass" for r in case.repeats)


def _must_pass(baseline: Run, run: Run, tag: str) -> GateCheck:
    name = f"must_pass:{tag}"
    tagged = [c for c in run.cases if tag in c.tags]
    by_id = {c.id: c for c in run.cases}
    base_ids = [c.id for c in baseline.cases if tag in c.tags]
    missing = [i for i in base_ids if i not in by_id]
    # The baseline decides which cases must pass: a PR that drops the tag still fails here.
    untagged = [i for i in base_ids if i in by_id and tag not in by_id[i].tags]
    if not tagged and not missing and not untagged:
        return GateCheck(name=name, passed=False, detail=f"{name} no cases have this tag")
    bad = [
        f"{c.id} {sum(r.status == 'pass' for r in c.repeats)}/{len(c.repeats)}"
        for c in tagged
        if not _all_passed(c)
    ]
    bad += [f"{i} tag removed" for i in untagged] + [f"{i} missing" for i in missing]
    if not bad:
        return GateCheck(name=name, passed=True, detail=name)
    return GateCheck(name=name, passed=False, detail=f"{name} {', '.join(bad)}")


def gate(
    baseline: Run,
    run: Run,
    *,
    max_drop: float = 0.03,
    max_errors: int = 0,
    must_pass_tags: list[str],
) -> GateResult:
    b, r = baseline.summary.pass_rate, run.summary.pass_rate
    checks = [
        GateCheck(
            name="scored",
            passed=r is not None,
            detail="scored" if r is not None else "no scored cases",
        )
    ]
    if b is None or r is None:  # the scored check already decides this run
        checks.append(
            GateCheck(name="max_drop", passed=True, detail="max_drop skipped (no pass rate)")
        )
    else:
        drop = b - r
        ok = drop <= max_drop + 1e-9  # a NaN pass rate in a run file fails, never passes
        sign = "≤" if ok else ">"
        detail = f"max_drop {fmt_signed3(drop)} {sign} {max_drop:.2f}"
        checks.append(GateCheck(name="max_drop", passed=ok, detail=detail))
    n = run.summary.n_error_repeats
    ok = n <= max_errors
    checks.append(
        GateCheck(
            name="max_errors", passed=ok, detail=f"max_errors {n} {'≤' if ok else '>'} {max_errors}"
        )
    )
    checks += [_must_pass(baseline, run, tag) for tag in must_pass_tags]
    return GateResult(
        passed=all(c.passed for c in checks), checks=checks, comparison=compare(baseline, run)
    )


def headline(baseline: Run, run: Run, max_drop: float) -> str:
    b, r = baseline.summary.pass_rate, run.summary.pass_rate
    if r is None:
        return "No scored cases in the run."
    if b is None:
        return "No scored cases in the baseline."
    d = r - b
    pts = round(abs(d) * 100, 1)
    limit = f"{max_drop * 100:.1f}"
    if pts == 0:  # §9 zero rule: a rounded zero is "unchanged", never "fell 0.0"
        return f"Pass rate unchanged (limit {limit})."
    return f"Pass rate {'fell' if d < 0 else 'rose'} {pts:.1f} points (limit {limit})."


def must_pass_rows(baseline: Run, run: Run, tags: list[str]) -> list[list[str]]:
    rows = []
    for tag in tags:
        counts = []
        for side in (baseline, run):
            tagged = [c for c in side.cases if tag in c.tags]
            counts.append((sum(_all_passed(c) for c in tagged), len(tagged)))
        (bp, bn), (rp, rn) = counts
        rows.append([f"must-pass ({tag})", f"{bp}/{bn}", f"{rp}/{rn}", fmt_delta_int(rp - bp)])
    return rows


def check_glyph(check: GateCheck) -> str:
    return "✓" if check.passed else "✗"


def render_gate_comment(
    result: GateResult, baseline: Run, run: Run, *, max_drop: float, must_pass_tags: list[str]
) -> str:
    cmp = result.comparison
    verdict = "✓ casegate gate: PASSED" if result.passed else "✗ casegate gate: BLOCKED"
    rows = metric_rows(cmp, baseline, run, must_pass_rows(baseline, run, must_pass_tags))
    checks = " · ".join(f"{check_glyph(c)} {c.detail}" for c in result.checks)
    sha = [x.git_sha[:7] if x.git_sha else x.target_version for x in (baseline, run)]
    footer = (
        f"<sub>baseline {sha[0]} · run {sha[1]} · casegate {run.casegate_version}"
        f" · max-drop {max_drop:.2f} · baseline std {baseline.summary.pass_rate_std:.3f}</sub>"
    )
    head = [f"{MARKER}\n### {verdict}\n{headline(baseline, run, max_drop)}"]
    head += [f"> [!WARNING]\n> {w}" for w in cmp.warnings]
    head += [metric_table_md(rows), f"**Checks** {checks}"]
    tail = [*list_lines_md(cmp), footer]

    def build(keep_p2f: int, keep_f2p: int) -> str:
        return "\n\n".join([*head, flips_md(cmp, keep_p2f, keep_f2p), *tail]) + "\n"

    p2f, f2p = cmp.flips_pass_to_fail, cmp.flips_fail_to_pass
    keep_p, keep_f = len(p2f), len(f2p)
    body = build(keep_p, keep_f)
    while len(body) > BODY_LIMIT and (keep_p or keep_f):
        # Drop rows from the end (fail → pass first) until the cut rows cover the excess,
        # then render again: the `… N more` row may need one more row to go.
        excess = len(body) - BODY_LIMIT
        while excess > 0 and (keep_p or keep_f):
            if keep_f:
                keep_f -= 1
                excess -= len(" | ".join(flip_cells(f2p[keep_f]))) + 5
            else:
                keep_p -= 1
                excess -= len(" | ".join(flip_cells(p2f[keep_p]))) + 5
        body = build(keep_p, keep_f)
    return body


def write_comment(body: str, comment_out: Path | None) -> None:
    """Write the comment file (overwrite) and append to the GitHub job summary when set."""
    if comment_out is not None:
        comment_out.write_text(body, encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(body)
