"""CLI end to end through typer's CliRunner: run, report, compare, gate and their exit codes."""

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from casegate import __version__
from casegate.cli import app
from casegate.models import Run
from casegate.report import render_markdown
from tests.fixtures.suite_fake import target as fake_target

SUITE = Path(__file__).parent / "fixtures" / "suite_fake"
RUNS = Path(__file__).parent / "fixtures" / "runs"
runner = CliRunner()


@pytest.fixture(autouse=True)
def _fresh_target(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # The fake target fails its first retry_once call per process; every run starts fresh.
    monkeypatch.setattr(fake_target, "_retried", False)
    # results/latest.md and the cache land in the test's own folder, never in the repo.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CASEGATE_CACHE_DIR", str(tmp_path / "cache"))


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"{__version__}\n"


def test_run_suite_fake_repeat_3(tmp_path: Path) -> None:
    # --no-cache keeps attempts exact: cases 01 and 02 share one input, so with a cache one
    # case's repeat can read the other's output inside the same cold run (SPEC §8 key).
    out = tmp_path / "run.json"
    args = ["run", str(SUITE), "--repeat", "3", "--out", str(out), "--no-cache", "--plain"]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    run = Run.model_validate_json(out.read_text(encoding="utf-8"))

    # SPEC §17 expected values for suite_fake with --repeat 3.
    assert [c.id for c in run.cases] == [
        "pass-exact-01",
        "fail-contains-02",
        "retry-once-03",
        "tools-state-04",
    ]
    assert [c.pass_rate for c in run.cases] == [1.0, 0.0, 1.0, 1.0]
    assert run.summary.pass_rate == 0.75
    assert run.summary.pass_rate_std == 0.0
    assert run.summary.n_error_repeats == 0
    attempts = [r.attempts for c in run.cases for r in c.repeats]
    assert attempts.count(2) == 1 and attempts.count(1) == len(attempts) - 1
    assert run.repeat == 3 and run.summary.n_repeats_total == 12
    assert run.filters == {"must_pass_tags": ["core"]}
    assert Run.model_validate_json(run.model_dump_json()) == run

    assert "suite suite-fake  cases 4  repeats 3  concurrency 4" in result.output
    assert "pass rate 0.750 ± 0.000  errors 0  cost $0.00  cache off" in result.output
    assert f"wrote {out}" in result.output
    assert "\x1b[" not in result.output  # plain mode: no ANSI codes
    latest = tmp_path / "results" / "latest.md"
    assert latest.read_text(encoding="utf-8") == render_markdown(run)


def test_run_cache_cold_then_warm(tmp_path: Path) -> None:
    out = tmp_path / "run.json"
    args = ["run", str(SUITE), "--repeat", "3", "--out", str(out), "--plain"]
    cold = runner.invoke(app, args)
    assert cold.exit_code == 0, cold.output
    run = Run.model_validate_json(out.read_text(encoding="utf-8"))
    assert run.summary.pass_rate == 0.75
    assert run.summary.cache_output_total == 12
    assert "cache " in cold.output and "/12 outputs" in cold.output

    # A second run in the same cache dir reads every output from the cache.
    warm = runner.invoke(app, args)
    assert warm.exit_code == 0, warm.output
    assert "cache 12/12 outputs" in warm.output
    run = Run.model_validate_json(out.read_text(encoding="utf-8"))
    assert run.summary.pass_rate == 0.75
    assert all(r.cached and r.attempts == 0 for c in run.cases for r in c.repeats)


def test_run_no_cache_tag_and_concurrency(tmp_path: Path) -> None:
    out = tmp_path / "run.json"
    args = [
        "run",
        str(SUITE),
        "--tag",
        "core",
        "--concurrency",
        "2",
        "--no-cache",
        "--out",
        str(out),
    ]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    run = Run.model_validate_json(out.read_text(encoding="utf-8"))
    assert [c.id for c in run.cases] == ["pass-exact-01", "fail-contains-02"]
    assert run.filters == {"must_pass_tags": ["core"], "tags": ["core"]}
    assert "concurrency 2" in result.output and "cache off" in result.output


def test_run_default_out_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_SHA", "abcdef1234567890")
    result = runner.invoke(app, ["run", str(SUITE)])
    assert result.exit_code == 0, result.output
    files = list((tmp_path / "results").glob("*.json"))
    assert len(files) == 1
    assert files[0].name.endswith("-abcdef1.json")
    assert len(files[0].name) == len("20261111T090000Z-abcdef1.json")


def test_run_missing_target_version_exits_2(tmp_path: Path) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(SUITE, suite)
    text = (suite / "suite.yaml").read_text(encoding="utf-8")
    (suite / "suite.yaml").write_text(text.replace("  version: fake@1\n", ""), encoding="utf-8")
    result = runner.invoke(app, ["run", str(suite), "--out", str(tmp_path / "r.json")])
    assert result.exit_code == 2
    assert "target.version" in result.output
    assert not (tmp_path / "r.json").exists()


def test_run_bad_repeat_is_rejected() -> None:
    result = runner.invoke(app, ["run", str(SUITE), "--repeat", "21"])
    assert result.exit_code == 2


def test_report_json(tmp_path: Path) -> None:
    out = tmp_path / "run.json"
    assert runner.invoke(app, ["run", str(SUITE), "--out", str(out)]).exit_code == 0
    result = runner.invoke(app, ["report", str(out), "--format", "json"])
    assert result.exit_code == 0, result.output
    run = Run.model_validate_json(out.read_text(encoding="utf-8"))
    assert result.output == run.summary.model_dump_json(indent=2) + "\n"

    dest = tmp_path / "summary.json"
    result = runner.invoke(app, ["report", str(out), "--format", "json", "--out", str(dest)])
    assert result.exit_code == 0
    assert dest.read_text(encoding="utf-8") == run.summary.model_dump_json(indent=2) + "\n"


def test_report_errors_exit_2(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    assert runner.invoke(app, ["report", str(missing), "--format", "json"]).exit_code == 2
    assert runner.invoke(app, ["report", str(missing), "--format", "xml"]).exit_code == 2
    assert runner.invoke(app, ["report", str(missing)]).exit_code == 2


def test_report_md() -> None:
    result = runner.invoke(app, ["report", str(RUNS / "regressed.json")])
    assert result.exit_code == 0, result.output
    run = Run.model_validate_json((RUNS / "regressed.json").read_text(encoding="utf-8"))
    assert result.output == render_markdown(run)


def _judge_suite(tmp_path: Path) -> Path:
    suite = tmp_path / "judged"
    shutil.copytree(SUITE, suite)
    case = suite / "cases" / "01-pass-exact-01.yaml"
    text = case.read_text(encoding="utf-8") + "  - type: llm_judge\n    rubric: Says OK.\n"
    case.write_text(text, encoding="utf-8")
    return suite


def test_run_fake_judge(tmp_path: Path) -> None:
    out = tmp_path / "run.json"
    args = ["run", str(_judge_suite(tmp_path)), "--fake-judge", "--out", str(out)]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    run = Run.model_validate_json(out.read_text(encoding="utf-8"))
    assert run.judge_model == "claude-sonnet-5-5"
    assert [s.type for s in run.cases[0].repeats[0].scores] == ["exact", "llm_judge"]
    assert run.cases[0].pass_rate == 1.0
    assert "judge_same_as_target" not in run.filters


def test_run_judge_without_key_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = tmp_path / "run.json"
    result = runner.invoke(app, ["run", str(_judge_suite(tmp_path)), "--out", str(out)])
    assert result.exit_code == 2
    assert "ANTHROPIC_API_KEY is not set" in result.output
    assert not out.exists()


def test_run_warns_when_judge_equals_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CASEGATE_JUDGE_MODEL", "none")  # the fake target's model
    out = tmp_path / "run.json"
    args = ["run", str(_judge_suite(tmp_path)), "--fake-judge", "--out", str(out)]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "judge model equals target model; scores may be biased" in result.output
    run = Run.model_validate_json(out.read_text(encoding="utf-8"))
    assert run.filters["judge_same_as_target"] is True


def test_run_record_svg(tmp_path: Path) -> None:
    svg = tmp_path / "run.svg"
    args = ["run", str(SUITE), "--out", str(tmp_path / "r.json"), "--record-svg", str(svg)]
    assert runner.invoke(app, args).exit_code == 0
    assert svg.read_text(encoding="utf-8").lstrip().startswith("<svg")


def test_compare_formats() -> None:
    base, reg = str(RUNS / "baseline.json"), str(RUNS / "regressed.json")
    text = runner.invoke(app, ["compare", base, reg, "--plain"])
    assert text.exit_code == 0, text.output
    assert "Flipped pass → fail (3)" in text.output
    md = runner.invoke(app, ["compare", base, reg, "--format", "md"])
    assert md.exit_code == 0 and "| metric | baseline | run | delta |" in md.output
    js = runner.invoke(app, ["compare", base, reg, "--format", "json"])
    assert js.exit_code == 0 and '"flips_pass_to_fail"' in js.output
    assert runner.invoke(app, ["compare", base, "missing.json"]).exit_code == 2
    assert runner.invoke(app, ["compare", base, reg, "--format", "xml"]).exit_code == 2


def _gate_args(run_name: str, *extra: str) -> list[str]:
    return [
        "gate",
        "--baseline",
        str(RUNS / "baseline.json"),
        "--run",
        str(RUNS / run_name),
        "--max-drop",
        "0.05",
        "--must-pass-tag",
        "adversarial",
        *extra,
    ]


def test_gate_exit_0_on_pass(tmp_path: Path) -> None:
    comment = tmp_path / "comment.md"
    result = runner.invoke(app, _gate_args("fixed.json", "--comment-out", str(comment), "--plain"))
    assert result.exit_code == 0, result.output
    assert result.output.rstrip().endswith("✓ PASSED  exit 0")
    golden = Path(__file__).parent / "golden" / "gate_pass.md"
    assert comment.read_text(encoding="utf-8") == golden.read_text(encoding="utf-8")


def test_gate_exit_1_on_regression(tmp_path: Path) -> None:
    comment = tmp_path / "comment.md"
    result = runner.invoke(app, _gate_args("regressed.json", "--comment-out", str(comment)))
    assert result.exit_code == 1, result.output
    assert result.output.rstrip().endswith("✗ BLOCKED  exit 1")
    golden = Path(__file__).parent / "golden" / "gate_fail.md"
    assert comment.read_text(encoding="utf-8") == golden.read_text(encoding="utf-8")

    md = runner.invoke(app, _gate_args("regressed.json", "--format", "md"))
    assert md.exit_code == 1
    assert md.output == golden.read_text(encoding="utf-8")


def test_gate_exit_2_on_bad_input(tmp_path: Path) -> None:
    comment = tmp_path / "comment.md"
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not json", encoding="utf-8")
    other_schema = tmp_path / "v2.json"
    data = (RUNS / "fixed.json").read_text(encoding="utf-8")
    other_schema.write_text(data.replace('"schema_version": 1', '"schema_version": 2'), "utf-8")
    not_utf8 = tmp_path / "latin1.json"
    not_utf8.write_bytes(b"\xff\xfe{}")
    for run_file in (tmp_path / "missing.json", bad_json, other_schema, not_utf8):
        args = ["gate", "--baseline", str(RUNS / "baseline.json"), "--run", str(run_file)]
        result = runner.invoke(app, [*args, "--comment-out", str(comment)])
        assert result.exit_code == 2, (run_file, result.output)
    assert '"schema_version": 1' in data
    assert not comment.exists()  # SPEC §11: no comment file on exit 2


def test_gate_uses_run_must_pass_tags_when_none_given() -> None:
    args = ["gate", "--baseline", str(RUNS / "baseline.json"), "--run", str(RUNS / "fixed.json")]
    result = runner.invoke(app, [*args, "--max-drop", "0.05", "--plain"])
    run = Run.model_validate_json((RUNS / "fixed.json").read_text(encoding="utf-8"))
    for tag in run.filters.get("must_pass_tags", []):
        assert f"must_pass:{tag}" in result.output


def test_gate_appends_to_step_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    first = runner.invoke(app, _gate_args("fixed.json"))
    second = runner.invoke(app, _gate_args("regressed.json"))
    assert (first.exit_code, second.exit_code) == (0, 1)
    golden = Path(__file__).parent / "golden"
    expected = (golden / "gate_pass.md").read_text(encoding="utf-8") + (
        golden / "gate_fail.md"
    ).read_text(encoding="utf-8")
    assert summary.read_text(encoding="utf-8") == expected


def test_run_ctrl_c_exits_130_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import casegate.cli as cli

    async def interrupted(*_a: object, **_k: object) -> Run:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "run_suite", interrupted)
    result = runner.invoke(app, ["run", str(SUITE), "--out", str(tmp_path / "r.json")])
    assert result.exit_code == 130
    assert not (tmp_path / "r.json").exists()


def test_render_run_shows_the_worst_20_and_error_cells() -> None:
    import io

    from rich.console import Console

    from casegate.console import make_console, render_run
    from casegate.models import Case, RepeatResult, Score, ScorerConfig
    from casegate.runner import aggregate

    def case(i: int) -> Case:
        return Case(id=f"c{i:02d}", input={}, scorers=[ScorerConfig(type="exact")], source_file="x")

    def score(v: float) -> Score:
        return Score(
            scorer="exact", type="exact", value=v, passed=v == 1, threshold=1.0, reason="r"
        )

    def ok(k: int) -> RepeatResult:
        return RepeatResult(repeat=k, status="pass", scores=[score(1.0)])

    def err(k: int) -> RepeatResult:
        return RepeatResult(repeat=k, status="error", error="RuntimeError: x")

    results = [(case(i), [ok(0), ok(1)]) for i in range(21)]
    results[5] = (case(5), [err(0), err(1)])  # pass rate None: sorts last, so it is cut
    fail = RepeatResult(repeat=1, status="fail", scores=[score(0.0)])
    results[7] = (case(7), [err(0), fail])  # 0/2 with an error first
    results[9] = (case(9), [ok(0), fail])  # partial 1/2
    cases, summary = aggregate(results, repeat=2, duration_s=0.1)
    run = Run(
        casegate_version="0.1.0",
        suite="s",
        suite_path="s",
        started_at="2026-11-11T09:00:00Z",  # type: ignore[arg-type]
        finished_at="2026-11-11T09:00:01Z",  # type: ignore[arg-type]
        git_sha=None,
        target_version="t@1",
        target_model="none",
        judge_model=None,
        repeat=2,
        cases=cases,
        summary=summary,
    )
    console = Console(file=io.StringIO(), width=100, no_color=True, force_terminal=False)
    render_run(console, run, concurrency=8, out_path="results/run.json")
    text = console.file.getvalue()  # type: ignore[attr-defined]
    lines = text.splitlines()
    assert lines[0] == "suite s  cases 21  repeats 2  concurrency 8  target t@1 (none)  judge none"
    rows = [line.split() for line in lines if line.strip().startswith(("✓", "✗", "⚠"))]
    assert [r[2] for r in rows[:2]] == ["c07", "c09"]  # worst first (SPEC §9 order)
    assert rows[0][3:] == ["0/2", "(1", "errors)", "0.00", "⚠", "error"]
    assert rows[1][3:] == ["1/2", "0.50", "exact", "0.00", "<", "1.00"]
    assert len(rows) == 20 and "c05" not in text and "… 1 more" in text
    assert lines[-2] == "pass rate 0.925 ± 0.071  errors 3  cost $0.00  cache off"
    assert lines[-1] == "wrote results/run.json"
    assert make_console(plain=True).no_color
