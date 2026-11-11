"""Golden Markdown report (SPEC §9) and the fixture runs it is built from."""

from pathlib import Path

import pytest

from casegate.fmt import MINUS, fmt_delta, fmt_delta_money, fmt_money, md_cell
from casegate.models import Run
from casegate.report import render_markdown
from tests.conftest import assert_golden
from tests.fixtures.runs import make_runs

RUNS = Path(__file__).parent / "fixtures" / "runs"


def load(name: str) -> Run:
    return Run.model_validate_json((RUNS / f"{name}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ["baseline", "regressed", "fixed"])
def test_committed_fixtures_match_make_runs(name: str) -> None:
    # A hand edit of a fixture JSON would make the goldens test data that make_runs never wrote.
    assert (RUNS / f"{name}.json").read_text(encoding="utf-8") == make_runs.render(name)


def test_fixture_shape_follows_spec_17() -> None:
    base, reg = load("baseline"), load("regressed")
    assert len(base.cases) == 15 and base.repeat == 5
    assert base.git_sha == "a" * 40 and reg.git_sha == "b" * 40
    over_cap = next(c for c in reg.cases if c.id == "refund-over-cap-adv")
    assert sum(r.status == "pass" for r in over_cap.repeats) == 2
    names = [s.scorer for s in over_cap.repeats[0].scores]
    assert names == ["no-over-cap-attempt", "attempts-within-cap", "llm_judge"]
    errors = [r for c in reg.cases for r in c.repeats if r.status == "error"]
    assert len(errors) == 1 and errors[0].output is None
    assert errors[0].error == "RuntimeError: fixture error"
    rep = base.cases[0].repeats[2]
    assert rep.output is not None and rep.output.text == "reply refund-within-cap-01 r2"
    judge = next(s for s in rep.scores if s.type == "llm_judge")
    assert (judge.threshold, judge.reason) == (0.7, "fixture judge refund-within-cap-01 r2")


def test_report_golden() -> None:
    assert_golden("report.md", render_markdown(load("regressed")))


def test_report_all_pass_unknown_cost_no_judge_no_tags() -> None:
    run = load("baseline")
    cases = [c.model_copy(update={"tags": []}) for c in run.cases if c.pass_rate == 1.0]
    summary = run.summary.model_copy(update={"by_tag": {}, "cost_usd": None})
    run = run.model_copy(
        update={"cases": cases, "summary": summary, "judge_model": None, "git_sha": None}
    )
    text = render_markdown(run)
    assert "✓ every case passed every repeat." in text
    assert "## Pass rate by tag" not in text and "## Errors" not in text
    assert "· cost unknown ·" in text and "judge" not in text.splitlines()[2]
    assert "· nogit ·" in text and text.endswith("schema 1</sub>\n")


def test_report_without_pass_rate_drops_the_std() -> None:
    run = load("baseline")
    run = run.model_copy(update={"summary": run.summary.model_copy(update={"pass_rate": None})})
    assert render_markdown(run).splitlines()[2].startswith("**pass rate —** · 15 cases")


def test_fmt_cases_used_by_reports() -> None:
    assert fmt_money(0) == "$0.00"
    assert fmt_money(0.0042) == "$0.0042"
    assert fmt_money(-0.02) == MINUS + "$0.02"
    assert fmt_money(None) == "unknown"
    assert fmt_delta(-0.1062) == MINUS + "0.106" and fmt_delta(0.0004) == "0.000"
    assert fmt_delta_money(0.27, 0.25) == MINUS + "$0.02"
    assert md_cell("a|b\nc", 120) == "a\\|b c"
    assert md_cell("x" * 130, 120) == "x" * 119 + "…"
