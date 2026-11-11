"""Terminal output for the CLI: colour on a terminal, the same words as plain text elsewhere.

CI logs, pipes and NO_COLOR users get plain text with no ANSI codes; a person at a terminal
gets the "Lab instrument" theme (docs/DESIGN.md §5). Both modes share one renderer, so the
words, glyphs and numbers never differ between them and the goldens test both.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from rich import box
from rich.console import Console, JustifyMethod
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from casegate.calibrate import Calibration
from casegate.calibrate_md import (
    confusion_rows,
    disagreement_cells,
    headline_parts,
    unmatched_cells,
)
from casegate.compare import Comparison, flip_cells, list_lines, metric_rows
from casegate.fmt import fmt_cache, fmt_money, fmt_rate
from casegate.gate import GateResult, check_glyph, headline, must_pass_rows
from casegate.models import CaseResult, Run
from casegate.report import failing_scorer_cell, mean_cell, pass_cell, worst_key
from casegate.runner import ProgressEvent, case_status

LABEL, VALUE, MUTED = "#8FA39A", "#E3ECE7", "#8FA39A"
GREEN, RED, YELLOW, TRACK = "#3DDC84", "#FF5D5D", "#E8C547", "#2A3430"
STATUS_TEXT = {"pass": ("✓ pass", GREEN), "fail": ("✗ fail", RED), "error": ("⚠ error", YELLOW)}
MAX_ROWS = 20
NUMERIC_COLUMNS = {"human pass", "human fail", "repeat", "judge value", "line"}


def make_console(plain: bool) -> Console:
    rich_mode = not plain and sys.stdout.isatty() and "NO_COLOR" not in os.environ
    if rich_mode:
        return Console(highlight=False)
    return Console(no_color=True, force_terminal=False, highlight=False)


@contextmanager
def progress(console: Console, total: int) -> Iterator[Callable[[ProgressEvent], None]]:
    """A progress bar on a terminal; in plain mode a no-op callback (prints nothing)."""
    bar = Progress(
        TextColumn("[#8FA39A]cases"),
        BarColumn(complete_style=GREEN, finished_style=GREEN, style=TRACK),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,  # the final table replaces the bar, so logs keep only the result
        disable=not console.is_terminal or console.no_color,
    )
    with bar:
        task = bar.add_task("run", total=total)
        yield lambda _event: bar.advance(task)


def _pass_style(case: CaseResult) -> str:
    passes = sum(r.status == "pass" for r in case.repeats)
    if passes == len(case.repeats):
        return GREEN
    return RED if passes == 0 else VALUE  # partial is plain text; the scorer column says why


def render_run(console: Console, run: Run, *, concurrency: int, out_path: str) -> None:
    header = Text()
    pairs = [
        ("suite", run.suite),
        ("cases", str(run.summary.n_cases)),
        ("repeats", str(run.repeat)),
        ("concurrency", str(concurrency)),
        ("target", f"{run.target_version} ({run.target_model})"),
        ("judge", run.judge_model or "none"),
    ]
    for i, (label, value) in enumerate(pairs):
        header.append(("  " if i else "") + label + " ", style=LABEL)
        header.append(value, style=VALUE)
    console.print(header, soft_wrap=True)

    cases = run.cases
    if len(cases) > MAX_ROWS:
        cases = sorted(cases, key=worst_key)[:MAX_ROWS]
    table = Table(box=box.SIMPLE_HEAD, header_style=f"bold {VALUE}")
    columns: list[tuple[str, JustifyMethod]] = [
        ("status", "left"),
        ("case", "left"),
        ("pass", "right"),
        ("mean", "right"),
        ("failing scorer", "left"),
    ]
    for name, justify in columns:
        table.add_column(name, justify=justify)
    for case in cases:
        word, colour = STATUS_TEXT[case_status(case)]
        table.add_row(
            Text(word, style=colour),
            Text(case.id),
            Text(pass_cell(case), style=_pass_style(case)),
            Text(mean_cell(case)),
            Text(failing_scorer_cell(case)),
        )
    console.print(table)
    if len(run.cases) > MAX_ROWS:
        console.print(Text(f"… {len(run.cases) - MAX_ROWS} more", style=MUTED))

    s = run.summary
    rate = f"pass rate {fmt_rate(s.pass_rate)}"
    if s.pass_rate is not None:
        rate += f" ± {fmt_rate(s.pass_rate_std)}"
    line = f"{rate}  errors {s.n_error_repeats}  cost {fmt_money(s.cost_usd)}  {fmt_cache(s)}"
    console.print(Text(line), soft_wrap=True)
    console.print(Text(f"wrote {out_path}", style=MUTED), soft_wrap=True)


def _metric_table(rows: list[list[str]]) -> Table:
    table = Table(box=box.SIMPLE_HEAD, header_style=f"bold {VALUE}")
    table.add_column("metric")
    for name in ("baseline", "run", "delta"):
        table.add_column(name, justify="right")
    for row in rows:
        table.add_row(*(Text(cell) for cell in row))
    return table


def _flips_tables(console: Console, cmp: Comparison) -> None:
    """One table per flip direction, shown only when it has rows."""
    for title, flips in (
        ("Flipped pass → fail", cmp.flips_pass_to_fail),
        ("Flipped fail → pass", cmp.flips_fail_to_pass),
    ):
        if not flips:
            continue
        table = Table(
            title=f"{title} ({len(flips)})",
            box=box.SIMPLE_HEAD,
            header_style=f"bold {VALUE}",
            title_justify="left",
            title_style=VALUE,
        )
        for name in ("case", "failing scorer", "reason"):
            table.add_column(name)
        for flip in flips:
            table.add_row(*(Text(cell) for cell in flip_cells(flip, markdown=False)))
        console.print(table)


def _warnings(console: Console, cmp: Comparison) -> None:
    for w in cmp.warnings:
        console.print(Text(f"⚠ {w}", style=YELLOW), soft_wrap=True)


def _list_lines(console: Console, cmp: Comparison) -> None:
    for label, text in list_lines(cmp):
        console.print(Text(f"{label} {text}"), soft_wrap=True)


def render_compare(console: Console, cmp: Comparison, baseline: Run, run: Run) -> None:
    _warnings(console, cmp)
    console.print(_metric_table(metric_rows(cmp, baseline, run)))
    _flips_tables(console, cmp)
    _list_lines(console, cmp)


def render_gate(
    console: Console,
    result: GateResult,
    baseline: Run,
    run: Run,
    max_drop: float,
    must_pass_tags: list[str],
) -> None:
    cmp = result.comparison
    console.print(Text(headline(baseline, run, max_drop)), soft_wrap=True)
    _warnings(console, cmp)
    rows = metric_rows(cmp, baseline, run, must_pass_rows(baseline, run, must_pass_tags))
    console.print(_metric_table(rows))
    console.print()
    for check in result.checks:
        word = f"{check_glyph(check)} {'pass' if check.passed else 'fail'}"
        line = Text(word, style=GREEN if check.passed else RED)
        line.append(f"  {check.detail}")
        console.print(line, soft_wrap=True)
    _flips_tables(console, cmp)
    _list_lines(console, cmp)
    if result.passed:
        console.print(Text("✓ PASSED  exit 0", style=f"bold {GREEN}"))
    else:
        console.print(Text("✗ BLOCKED  exit 1", style=f"bold {RED}"))


def _titled_table(title: str, columns: list[str], rows: list[list[str]]) -> Table:
    table = Table(
        title=title,
        box=box.SIMPLE_HEAD,
        header_style=f"bold {VALUE}",
        title_justify="left",
        title_style=VALUE,
    )
    for i, name in enumerate(columns):
        # The id column never wraps, so a case id stays whole and searchable in CI logs.
        justify: JustifyMethod = "right" if name in NUMERIC_COLUMNS else "left"
        table.add_column(name, justify=justify, no_wrap=i == 0)
    for row in rows:
        table.add_row(*(Text(cell) for cell in row))
    return table


def render_calibration(console: Console, cal: Calibration) -> None:
    line = Text()
    for i, (label, value) in enumerate(headline_parts(cal)):
        line.append(("  " if i else "") + label + " ", style=LABEL)
        line.append(value, style=VALUE)
    console.print(line, soft_wrap=True)
    for note in cal.notes:
        console.print(Text(f"⚠ {note}", style=YELLOW), soft_wrap=True)
    console.print(_titled_table("", ["", "human pass", "human fail"], confusion_rows(cal)))
    # Empty tables are left out, as in the comparison: the counts in the title say enough.
    head = ["case", "repeat", "scorer", "judge value", "human", "judge reason", "note"]
    rows = [disagreement_cells(d, markdown=False) for d in cal.disagreements]
    if rows:
        console.print(_titled_table(f"Disagreements ({len(rows)})", head, rows))
    unmatched = [unmatched_cells(r) for r in cal.unmatched]
    if unmatched:
        cols = ["line", "case", "repeat", "scorer"]
        console.print(_titled_table(f"Unmatched rows ({len(unmatched)})", cols, unmatched))
