"""The baseline decides which cases must pass: removing the tag in a PR cannot skip the check.

A case with a must-pass tag in the BASELINE must pass in the run whether or not the run copy
still has the tag. A copy that lost the tag is reported as `<id> tag removed` and fails (§11).
"""

from casegate.gate import gate, render_gate_comment
from casegate.models import Run
from tests.test_report import load

ARGS = {"max_drop": 0.05, "must_pass_tags": ["adversarial"]}


def drop_tag(run: Run, *ids: str, tag: str = "adversarial") -> Run:
    cases = [
        c.model_copy(update={"tags": [t for t in c.tags if t != tag]}) if c.id in ids else c
        for c in run.cases
    ]
    return run.model_copy(update={"cases": cases})


def must_pass_check(baseline: Run, run: Run) -> tuple[bool, str]:
    check = gate(baseline, run, **ARGS).checks[-1]
    return check.passed, check.detail


def test_fixed_run_passes_with_every_tag_kept() -> None:
    assert must_pass_check(load("baseline"), load("fixed")) == (True, "must_pass:adversarial")


def test_passing_case_that_lost_the_tag_fails_as_tag_removed() -> None:
    run = drop_tag(load("fixed"), "refund-late-45d-adv")
    assert must_pass_check(load("baseline"), run) == (
        False,
        "must_pass:adversarial refund-late-45d-adv tag removed",
    )


def test_failing_case_cannot_hide_by_dropping_its_tag() -> None:
    run = drop_tag(load("regressed"), "refund-over-cap-adv")
    assert must_pass_check(load("baseline"), run) == (
        False,
        "must_pass:adversarial refund-over-cap-adv tag removed",
    )


def test_every_tag_removed_is_not_reported_as_no_cases() -> None:
    ids = ("refund-late-45d-adv", "refund-over-cap-adv", "injection-order-note-adv")
    passed, detail = must_pass_check(load("baseline"), drop_tag(load("fixed"), *ids))
    assert not passed
    assert detail == "must_pass:adversarial " + ", ".join(f"{i} tag removed" for i in ids)


def test_gate_comment_shows_tag_removed() -> None:
    base, run = load("baseline"), drop_tag(load("fixed"), "refund-late-45d-adv")
    result = gate(base, run, **ARGS)
    body = render_gate_comment(result, base, run, **ARGS)
    assert "✗ must_pass:adversarial refund-late-45d-adv tag removed" in body
    assert "BLOCKED" in body
