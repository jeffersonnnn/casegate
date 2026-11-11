"""Comparison and gate rules, the gate comment goldens, truncation and write_comment (§10, §11)."""

from pathlib import Path

import pytest

from casegate.compare import Flip, compare, render_comparison_md
from casegate.gate import (
    BODY_LIMIT,
    MARKER,
    gate,
    render_gate_comment,
    resolve_must_pass_tags,
    write_comment,
)
from casegate.models import CaseResult, RepeatResult, Run
from tests.conftest import assert_golden
from tests.test_report import load

ARGS = {"max_drop": 0.05, "must_pass_tags": ["adversarial"]}


def comment(baseline: Run, run: Run) -> str:
    return render_gate_comment(gate(baseline, run, **ARGS), baseline, run, **ARGS)


def with_cases(run: Run, cases: list[CaseResult]) -> Run:
    return run.model_copy(update={"cases": cases})


def test_gate_fail_golden() -> None:
    assert_golden("gate_fail.md", comment(load("baseline"), load("regressed")))


def test_gate_pass_golden() -> None:
    assert_golden("gate_pass.md", comment(load("baseline"), load("fixed")))


def test_comparison_golden() -> None:
    base, reg = load("baseline"), load("regressed")
    assert_golden("compare.md", render_comparison_md(compare(base, reg), base, reg))


def test_compare_regressed() -> None:
    cmp = compare(load("baseline"), load("regressed"))
    ids = [f.id for f in cmp.flips_pass_to_fail]
    assert ids == ["refund-within-cap-01", "refund-over-cap-adv", "policy-window-10"]
    assert cmp.flips_pass_to_fail[1] == Flip(
        id="refund-over-cap-adv",
        scorer="attempts-within-cap",
        reason="fixture fail attempts-within-cap",
    )
    assert cmp.flips_fail_to_pass == [] and cmp.added == [] and cmp.removed == []
    assert cmp.warnings == ["target version changed: toy-agent@1 → toy-agent@2"]
    assert [d.id for d in cmp.deltas] == ids  # -0.8 first, then the -0.6 tie in suite order
    assert cmp.deltas[0].delta == pytest.approx(-0.8)
    assert (cmp.baseline_error_repeats, cmp.run_error_repeats) == (0, 1)


def test_compare_error_lists_added_removed_and_warnings() -> None:
    base, reg = load("baseline"), load("regressed")
    err = [RepeatResult(repeat=k, status="error", error="E: x") for k in range(5)]
    all_error = reg.cases[1].model_copy(update={"repeats": err, "pass_rate": None})
    renamed = reg.cases[2].model_copy(update={"id": "new-case"})
    run = with_cases(reg, [reg.cases[0], all_error, renamed, *reg.cases[3:]])
    run = run.model_copy(update={"repeat": 3, "judge_model": None})
    cmp = compare(base, run)
    assert cmp.changed_to_error == ["refund-partial-02"]
    assert cmp.added == ["new-case"] and cmp.removed == ["refund-already-done-03"]
    assert cmp.warnings[1:] == [
        "judge model changed: claude-sonnet-5-5 → none",
        "repeat changed: 5 → 3",
    ]
    back = compare(run, base)
    assert back.changed_from_error == ["refund-partial-02"]
    md = render_comparison_md(cmp, base, run)
    assert "**Errors** ⚠ refund-partial-02\n\n**Added** new-case\n\n**Removed**" in md
    assert "**Recovered from error** refund-partial-02" in render_comparison_md(back, run, base)


def test_fail_to_pass_flip_and_error_flip_reason() -> None:
    base, reg = load("baseline"), load("regressed")
    cmp = compare(reg, base)
    assert cmp.flips_fail_to_pass[0].id == "refund-within-cap-01"
    assert cmp.flips_fail_to_pass[0].scorer is None
    case = base.cases[0]
    reps = [RepeatResult(repeat=0, status="error", error="RuntimeError: boom")] + [
        RepeatResult(repeat=k, status="fail") for k in range(1, 5)
    ]
    run = with_cases(base, [case.model_copy(update={"repeats": reps, "pass_rate": 0.0})])
    flip = compare(base, run).flips_pass_to_fail[0]
    assert (flip.scorer, flip.reason) == ("⚠ error", "RuntimeError: boom")
    assert "| refund-within-cap-01 | — | — |" in render_comparison_md(cmp, reg, base)


def test_gate_checks_on_regressed() -> None:
    res = gate(load("baseline"), load("regressed"), **ARGS)
    assert not res.passed
    assert [c.detail for c in res.checks] == [
        "scored",
        "max_drop 0.133 > 0.05",
        "max_errors 1 > 0",
        "must_pass:adversarial refund-over-cap-adv 2/5",
    ]


def test_gate_against_itself_passes_unchanged() -> None:
    base = load("baseline")
    res = gate(base, base, **ARGS)
    assert res.passed and res.checks[1].detail == "max_drop 0.000 ≤ 0.05"
    assert "Pass rate unchanged (limit 5.0)." in comment(base, base)


def test_gate_no_pass_rate_and_missing_tag_cases() -> None:
    base, reg = load("baseline"), load("regressed")
    none_rate = reg.model_copy(
        update={"summary": reg.summary.model_copy(update={"pass_rate": None})}
    )
    res = gate(base, none_rate, max_drop=0.05, must_pass_tags=["nope"])
    assert [(c.passed, c.detail) for c in res.checks] == [
        (False, "no scored cases"),
        (True, "max_drop skipped (no pass rate)"),
        (False, "max_errors 1 > 0"),
        (False, "must_pass:nope no cases have this tag"),
    ]
    assert "No scored cases in the run." in render_gate_comment(
        res, base, none_rate, max_drop=0.05, must_pass_tags=["nope"]
    )
    no_base = base.model_copy(
        update={"summary": base.summary.model_copy(update={"pass_rate": None})}
    )
    body = render_gate_comment(gate(no_base, base, **ARGS), no_base, base, **ARGS)
    assert "No scored cases in the baseline." in body
    dropped = with_cases(base, [c for c in base.cases if c.id != "refund-late-45d-adv"])
    check = gate(base, dropped, **ARGS).checks[-1]
    assert check.detail == "must_pass:adversarial refund-late-45d-adv missing"


def test_gate_max_drop_boundary_and_errors_allowed() -> None:
    base, reg = load("baseline"), load("regressed")
    assert base.summary.pass_rate is not None and reg.summary.pass_rate is not None
    drop = base.summary.pass_rate - reg.summary.pass_rate
    res = gate(base, reg, max_drop=drop, max_errors=1, must_pass_tags=[])
    assert [c.passed for c in res.checks] == [True, True, True]
    assert "must-pass" not in render_gate_comment(res, base, reg, max_drop=drop, must_pass_tags=[])


def test_gate_comment_truncates_at_60000() -> None:
    base = load("baseline")
    cmp = compare(base, base)
    long = "r" * 200
    p2f = [Flip(id=f"case-{i:04d}", scorer="llm_judge", reason=long) for i in range(400)]
    f2p = [Flip(id=f"back-{i:04d}", scorer=None, reason=None) for i in range(300)]
    cmp = cmp.model_copy(update={"flips_pass_to_fail": p2f, "flips_fail_to_pass": f2p})
    res = gate(base, base, **ARGS).model_copy(update={"comparison": cmp})
    body = render_gate_comment(res, base, base, **ARGS)
    assert len(body) <= BODY_LIMIT and body.startswith(MARKER)
    assert "Flipped pass → fail (400)" in body and "Flipped fail → pass (300)" in body
    assert "| … 300 more | | |" in body  # fail → pass is emptied first
    kept = body.count("| case-")
    assert "| … " + str(400 - kept) + " more | | |" in body
    one_more = p2f[kept]
    row = f"| {one_more.id} | llm_judge | {'r' * 119}… |\n"
    assert len(body) + len(row) > BODY_LIMIT  # no room for one more row
    assert body.rstrip("\n").endswith("baseline std 0.082</sub>")


def test_resolve_must_pass_tags() -> None:
    run = load("regressed")
    assert resolve_must_pass_tags(run, None) == ["adversarial"]
    assert resolve_must_pass_tags(run, []) == ["adversarial"]
    assert resolve_must_pass_tags(run, ["core", "x"]) == ["core", "x"]
    assert resolve_must_pass_tags(run.model_copy(update={"filters": {}}), None) == []


def test_write_comment_file_and_step_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "comment.md"
    out.write_text("old", encoding="utf-8")
    write_comment("first\n", out)
    assert out.read_text(encoding="utf-8") == "first\n"  # overwritten
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    write_comment("one ✓\n", None)
    write_comment("two ✗\n", out)
    assert summary.read_text(encoding="utf-8") == "one ✓\ntwo ✗\n"  # appended
    assert out.read_text(encoding="utf-8") == "two ✗\n"


def test_max_drop_fails_closed_on_nan_pass_rate() -> None:
    base, run = load("baseline"), load("fixed")
    bad = run.model_copy(
        update={"summary": run.summary.model_copy(update={"pass_rate": float("nan")})}
    )
    check = next(c for c in gate(base, bad, **ARGS).checks if c.name == "max_drop")
    assert not check.passed
