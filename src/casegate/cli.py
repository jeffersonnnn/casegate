"""Command-line entry point for casegate (the `casegate` script).

Each command is a thin wrapper over the library: it parses flags, calls one library
function, prints through console.py and maps errors to exit codes (2 = bad input,
130 = Ctrl-C). Keeping logic out of here means tests can call the library directly.
"""

import asyncio
import sys
from collections.abc import Callable
from pathlib import Path

import typer

from casegate import __version__
from casegate import console as term
from casegate.cache import Cache
from casegate.calibrate import calibrate, read_labels, render_calibration_md, write_template
from casegate.compare import compare, render_comparison_md
from casegate.console import make_console, progress, render_compare, render_gate, render_run
from casegate.errors import SuiteError
from casegate.gate import gate, render_gate_comment, resolve_must_pass_tags, write_comment
from casegate.judge import FakeJudge, JudgeClient, build_judge, resolve_judge_model
from casegate.loader import load_suite
from casegate.models import Case, Run, Suite
from casegate.report import render_markdown
from casegate.runner import ProgressEvent, run_suite
from casegate.scorers import REGISTRY

app = typer.Typer(no_args_is_help=True)
SAME_MODEL_WARNING = "judge model equals target model; scores may be biased"
LATEST_MD = Path("results") / "latest.md"


def _version(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version,
        is_eager=True,
        help="Print the version and exit.",
    ),
) -> None:
    """casegate: run eval suites and gate regressions in CI."""


def _fail(lines: list[str]) -> typer.Exit:
    for line in lines:
        typer.echo(line, err=True)
    return typer.Exit(2)


def _check_format(fmt: str, allowed: tuple[str, ...]) -> None:
    if fmt not in allowed:
        raise _fail([f"--format must be {' or '.join(allowed)}, got {fmt}"])


def _load_run(path: Path) -> Run:
    """Read a run JSON; a missing file, bad JSON or another schema_version is exit 2."""
    try:
        return Run.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:  # ValueError covers ValidationError and bad UTF-8
        raise _fail([f"{path}: cannot read run: {err}"]) from err


def _default_out(run: Run) -> Path:
    stamp = run.started_at.strftime("%Y%m%dT%H%M%SZ")
    return Path("results") / f"{stamp}-{run.git_sha[:7] if run.git_sha else 'nogit'}.json"


def _needs_judge(cases: list[Case]) -> bool:
    return any(REGISTRY[s.type].needs_judge for c in cases for s in c.scorers)


async def _run_with_judge(
    suite: Suite,
    cases: list[Case],
    *,
    judge_needed: bool,
    fake_judge: bool,
    repeat: int,
    concurrency: int | None,
    cache: Cache | None,
    on_event: Callable[[ProgressEvent], None],
    tags: list[str] | None,
) -> Run:
    # Build the judge only when a case grades with one, so a deterministic suite needs no key.
    judge: JudgeClient | None = None
    if judge_needed:
        judge = FakeJudge() if fake_judge else build_judge(suite.judge)
    try:
        return await run_suite(
            suite,
            cases,
            repeat=repeat,
            concurrency=concurrency,
            cache=cache,
            judge=judge,
            progress=on_event,
            tags=tags,
        )
    finally:
        if judge is not None:
            await judge.aclose()


@app.command()
def run(
    suite_dir: Path = typer.Argument(..., help="Directory that holds suite.yaml."),
    tag: list[str] | None = typer.Option(None, "--tag", help="Keep cases with this tag."),
    repeat: int = typer.Option(1, "--repeat", min=1, max=20),
    concurrency: int | None = typer.Option(None, "--concurrency", min=1, max=64),
    out: Path | None = typer.Option(None, "--out", help="Run JSON path."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache reads and writes."),
    plain: bool = typer.Option(False, "--plain", help="Plain text, no colour."),
    fake_judge: bool = typer.Option(False, "--fake-judge", hidden=True),
    record_svg: Path | None = typer.Option(None, "--record-svg", hidden=True),
) -> None:
    """Run a suite and write the run JSON. Exit 0 even when cases fail: the gate decides."""
    console = make_console(plain)
    console.record = record_svg is not None
    try:
        suite, cases = load_suite(suite_dir, tag)
        judge_needed = _needs_judge(cases)
        same_model = judge_needed and resolve_judge_model(suite.judge) == suite.target.model
        if same_model:
            typer.echo(SAME_MODEL_WARNING, err=True)
        with progress(console, len(cases) * repeat) as on_event:
            result = asyncio.run(
                _run_with_judge(
                    suite,
                    cases,
                    judge_needed=judge_needed,
                    fake_judge=fake_judge,
                    repeat=repeat,
                    concurrency=concurrency,
                    cache=None if no_cache else Cache(),
                    on_event=on_event,
                    tags=tag,
                )
            )
    except SuiteError as err:
        raise _fail(err.errors) from err
    except KeyboardInterrupt:
        raise typer.Exit(130) from None  # nothing is written for a cancelled run

    if same_model:
        result.filters["judge_same_as_target"] = True
    path = out or _default_out(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    LATEST_MD.parent.mkdir(parents=True, exist_ok=True)
    LATEST_MD.write_text(render_markdown(result), encoding="utf-8")
    render_run(console, result, concurrency=concurrency or suite.concurrency, out_path=str(path))
    if record_svg is not None:
        console.save_svg(str(record_svg), title="casegate run")


@app.command("compare")
def compare_cmd(
    baseline: Path = typer.Argument(..., help="The baseline run JSON."),
    run_file: Path = typer.Argument(..., help="The run JSON to compare with it."),
    fmt: str = typer.Option("text", "--format", help="text, md or json."),
    plain: bool = typer.Option(False, "--plain", help="Plain text, no colour."),
) -> None:
    """Compare a run with a baseline. Exit 0 always: only the gate blocks."""
    _check_format(fmt, ("text", "md", "json"))
    base, current = _load_run(baseline), _load_run(run_file)
    cmp = compare(base, current)
    if fmt == "md":
        typer.echo(render_comparison_md(cmp, base, current), nl=False)
    elif fmt == "json":
        typer.echo(cmp.model_dump_json(indent=2))
    else:
        render_compare(make_console(plain), cmp, base, current)


@app.command("gate")
def gate_cmd(
    baseline: Path = typer.Option(..., "--baseline", help="The baseline run JSON."),
    run_file: Path = typer.Option(..., "--run", help="The run JSON to gate."),
    max_drop: float = typer.Option(0.03, "--max-drop", min=0.0),
    max_errors: int = typer.Option(0, "--max-errors", min=0),
    must_pass_tag: list[str] | None = typer.Option(None, "--must-pass-tag"),
    comment_out: Path | None = typer.Option(None, "--comment-out", help="Write the comment."),
    fmt: str = typer.Option("text", "--format", help="text or md."),
    plain: bool = typer.Option(False, "--plain", help="Plain text, no colour."),
) -> None:
    """Exit 0 when every check passes, 1 when any fails, 2 on bad input (SPEC §11)."""
    _check_format(fmt, ("text", "md"))
    base, current = _load_run(baseline), _load_run(run_file)
    tags = resolve_must_pass_tags(current, must_pass_tag)
    result = gate(base, current, max_drop=max_drop, max_errors=max_errors, must_pass_tags=tags)
    body = render_gate_comment(result, base, current, max_drop=max_drop, must_pass_tags=tags)
    write_comment(body, comment_out)  # the only file write of `gate`; never reached on exit 2
    if fmt == "md":
        typer.echo(body, nl=False)
    else:
        render_gate(make_console(plain), result, base, current, max_drop, tags)
    raise typer.Exit(0 if result.passed else 1)


@app.command("calibrate")
def calibrate_cmd(
    run_file: Path = typer.Option(..., "--run", help="The run JSON the labels refer to."),
    labels: Path | None = typer.Option(None, "--labels", help="The human labels CSV."),
    template: bool = typer.Option(False, "--template", help="Print a labels CSV to fill in."),
    scorer: str | None = typer.Option(None, "--scorer", help="Only this scorer name."),
    fmt: str = typer.Option("text", "--format", help="text, md or json."),
    plain: bool = typer.Option(False, "--plain", help="Plain text, no colour."),
) -> None:
    """Join human labels to judge scores (SPEC §12). Never gates: exit 0, or 2 on bad input."""
    _check_format(fmt, ("text", "md", "json"))
    saved = _load_run(run_file)
    if template:
        return write_template(saved, sys.stdout, scorer=scorer)
    if labels is None:
        raise _fail(["--labels is required unless --template is given"])
    try:
        cal = calibrate(saved, read_labels(labels), scorer=scorer)
    except SuiteError as err:
        raise _fail(err.errors) from err
    if fmt == "text":
        return term.render_calibration(make_console(plain), cal)
    text = render_calibration_md(cal) if fmt == "md" else cal.model_dump_json(indent=2) + "\n"
    typer.echo(text, nl=False)


@app.command()
def report(
    run_file: Path = typer.Argument(..., help="A run JSON written by `casegate run`."),
    fmt: str = typer.Option("md", "--format", help="md or json."),
    out: Path | None = typer.Option(None, "--out", help="Write here instead of stdout."),
    plain: bool = typer.Option(False, "--plain", help="Plain text, no colour."),
) -> None:
    """Print a saved run as the Markdown report (md) or its summary (json)."""
    _check_format(fmt, ("md", "json"))
    saved = _load_run(run_file)
    text = render_markdown(saved) if fmt == "md" else saved.summary.model_dump_json(indent=2) + "\n"
    if out is None:
        typer.echo(text, nl=False)
    else:
        out.write_text(text, encoding="utf-8")
