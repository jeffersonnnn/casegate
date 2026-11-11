"""Console goldens (SPEC §14, §17): plain text through a 100-column console with no colour."""

import io

from rich.console import Console

from casegate.compare import compare
from casegate.console import render_compare, render_gate, render_run
from casegate.gate import gate
from tests.conftest import assert_golden
from tests.test_report import load


def plain() -> Console:
    return Console(file=io.StringIO(), width=100, no_color=True, force_terminal=False)


def text(console: Console) -> str:
    return console.file.getvalue()  # type: ignore[attr-defined]


def test_run_plain_golden() -> None:
    console = plain()
    render_run(console, load("baseline"), concurrency=8, out_path="results/run.json")
    assert_golden("run_plain.txt", text(console))


def test_gate_plain_golden() -> None:
    base, reg = load("baseline"), load("regressed")
    console = plain()
    result = gate(base, reg, max_drop=0.05, must_pass_tags=["adversarial"])
    render_gate(console, result, base, reg, 0.05, ["adversarial"])
    out = text(console)
    assert_golden("gate_plain.txt", out)
    assert "\x1b[" not in out and out.splitlines()[-1] == "✗ BLOCKED  exit 1"


def test_gate_plain_passed_shows_no_flip_tables() -> None:
    base, fixed = load("baseline"), load("fixed")
    console = plain()
    result = gate(base, fixed, max_drop=0.05, must_pass_tags=["adversarial"])
    render_gate(console, result, base, fixed, 0.05, ["adversarial"])
    out = text(console)
    assert "Flipped" not in out and "✓ pass  must_pass:adversarial" in out
    assert out.splitlines()[-1] == "✓ PASSED  exit 0"


def test_compare_plain_lists_and_flips() -> None:
    base, reg = load("baseline"), load("regressed")
    run = reg.model_copy(update={"cases": reg.cases[1:]})
    console = plain()
    render_compare(console, compare(base, run), base, run)
    out = text(console)
    assert out.startswith("⚠ target version changed: toy-agent@1 → toy-agent@2\n")
    assert "Flipped pass → fail (2)" in out and "fixture fail attempts-within-cap" in out
    assert out.splitlines()[-1] == "Removed refund-within-cap-01"
