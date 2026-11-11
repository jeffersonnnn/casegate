"""Judge calibration: how often the LLM judge agrees with a person (SPEC §12).

A judge score is only worth gating on if people would give the same verdict. This module
joins human pass/fail labels (a CSV) to the judge scores of one run and reports agreement
and Cohen's kappa, plus every disagreement, so a lenient or strict judge is visible.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import TextIO

from pydantic import BaseModel, ConfigDict

from casegate.calibrate_md import render_calibration_md as render_calibration_md
from casegate.errors import SuiteError
from casegate.models import RepeatResult, Run, Score

COLUMNS = ("case_id", "repeat", "scorer", "human_pass", "note")
HELPER_COLUMNS = ("judge_value", "judge_passed", "judge_reason", "reply_excerpt")
JUDGE_TYPES = frozenset({"llm_judge", "citation_support"})
TRUE_WORDS, FALSE_WORDS = {"1", "true", "yes"}, {"0", "false", "no"}
EXCERPT_LIMIT = 200
# A spreadsheet runs a cell that starts with one of these as a formula (CSV injection).
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LabelRow(_Strict):
    line: int  # csv line number of the row: header = 1, first data row = 2
    case_id: str
    repeat: int
    scorer: str
    human_pass: bool | None
    note: str = ""


class Disagreement(_Strict):
    case_id: str
    repeat: int
    scorer: str
    judge_value: float
    judge_passed: bool
    human_pass: bool
    judge_reason: str
    note: str


class Calibration(_Strict):
    n: int
    agreement: float | None
    kappa: float | None
    notes: list[str]
    # Short keys (judge then human: jp_hp = judge pass, human pass) keep the JSON output compact.
    confusion: dict[str, int]
    disagreements: list[Disagreement]
    unmatched: list[LabelRow]


def _parse_row(raw: dict[str, str | None], line: int) -> LabelRow:
    """One CSV row to a LabelRow; ValueError carries the message for a bad repeat or verdict."""
    cell = {c: (raw.get(c) or "") for c in COLUMNS}
    try:
        repeat = int(cell["repeat"].strip())
    except ValueError:
        raise ValueError(f"repeat must be an int, got {cell['repeat']!r}") from None
    word = cell["human_pass"].strip().lower()
    if word and word not in TRUE_WORDS | FALSE_WORDS:
        raise ValueError(f"invalid human_pass {cell['human_pass']!r} (use 1/0/true/false/yes/no)")
    human = None if not word else word in TRUE_WORDS
    case_id, name, note = cell["case_id"].strip(), cell["scorer"].strip(), cell["note"]
    return LabelRow(
        line=line, case_id=case_id, repeat=repeat, scorer=name, human_pass=human, note=note
    )


def read_labels(path: Path) -> list[LabelRow]:
    """Parse the labels CSV; every input error names its line and exits 2 via SuiteError."""
    rows: list[LabelRow] = []
    errors: list[str] = []
    try:
        # utf-8-sig drops the byte-order mark that spreadsheet apps put before the header.
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                raise SuiteError([f"{path.name}: missing column {c}" for c in missing])
            for raw in reader:
                try:
                    rows.append(_parse_row(raw, reader.line_num))
                except ValueError as err:
                    errors.append(f"{path.name}:{reader.line_num}: {err}")
    except (OSError, UnicodeDecodeError, csv.Error) as err:
        # A CSV saved by a spreadsheet as cp1252 is bad input (exit 2), not a crash (exit 1).
        raise SuiteError(f"{path.name}: cannot read labels: {err}") from err
    if errors:
        raise SuiteError(errors)
    _check_duplicates(path.name, rows)
    return rows


def _check_duplicates(name: str, rows: list[LabelRow]) -> None:
    # Empty human_pass rows count too: two rows for one result is a mistake either way.
    first: dict[tuple[str, int, str], int] = {}
    errors = []
    for row in rows:
        key = (row.case_id, row.repeat, row.scorer)
        if key in first:
            errors.append(f"{name}:{row.line}: duplicate row {key} (first on line {first[key]})")
        first.setdefault(key, row.line)
    if errors:
        raise SuiteError(errors)


def _keep(score: Score, scorer: str | None) -> bool:
    """Without --scorer only judge scores count; --scorer NAME picks one name of any type."""
    return score.type in JUDGE_TYPES if scorer is None else score.scorer == scorer


def _scores(run: Run, scorer: str | None) -> list[tuple[str, RepeatResult, Score]]:
    """Every kept score in run order, error repeats included (their judge scores are real)."""
    kept = [(c.id, rep, s) for c in run.cases for rep in c.repeats for s in rep.scores]
    return [t for t in kept if _keep(t[2], scorer)]


def _kappa(pairs: list[tuple[bool, bool]], po: float) -> float | None:
    """Cohen's kappa for two raters and two classes; None when chance agreement is 1."""
    n = len(pairs)
    p_j1 = sum(j for j, _ in pairs) / n
    p_h1 = sum(h for _, h in pairs) / n
    pe = p_j1 * p_h1 + (1 - p_j1) * (1 - p_h1)
    if math.isclose(pe, 1.0):
        return None
    return (po - pe) / (1 - pe)


def calibrate(run: Run, labels: list[LabelRow], *, scorer: str | None = None) -> Calibration:
    index = {(cid, rep.repeat, s.scorer): s for cid, rep, s in _scores(run, scorer)}
    pairs: list[tuple[bool, bool]] = []
    disagreements: list[Disagreement] = []
    unmatched: list[LabelRow] = []
    for row in labels:
        if row.human_pass is None:
            continue  # not labelled yet: skipped, not unmatched
        score = index.get((row.case_id, row.repeat, row.scorer))
        if score is None:
            unmatched.append(row)
            continue
        pairs.append((score.passed, row.human_pass))
        if score.passed != row.human_pass:
            disagreements.append(
                Disagreement(
                    **row.model_dump(include={"case_id", "repeat", "scorer", "human_pass", "note"}),
                    judge_value=score.value,
                    judge_passed=score.passed,
                    judge_reason=score.reason,
                )
            )
    agreement = sum(j == h for j, h in pairs) / len(pairs) if pairs else None
    kappa = None if agreement is None else _kappa(pairs, agreement)
    note = "kappa undefined: one class only" if pairs else "no labelled rows"
    confusion = {
        f"j{'p' if j else 'f'}_h{'p' if h else 'f'}": sum(p == (j, h) for p in pairs)
        for j in (True, False)
        for h in (True, False)
    }
    return Calibration(
        n=len(pairs),
        agreement=agreement,
        kappa=kappa,
        notes=[note] if kappa is None else [],
        confusion=confusion,
        disagreements=disagreements,
        unmatched=unmatched,
    )


def _inert(text: str) -> str:
    """Agent and judge text is untrusted: a leading quote stops a spreadsheet formula."""
    return "'" + text if text.startswith(FORMULA_START) else text


def write_template(run: Run, out: TextIO, *, scorer: str | None = None) -> None:
    """One row per kept score, human_pass empty; the helper columns are ignored on read."""
    writer = csv.writer(out, lineterminator="\n")  # the csv default is \r\n
    writer.writerow([*COLUMNS, *HELPER_COLUMNS])
    for case_id, rep, s in _scores(run, scorer):
        text = rep.output.text if rep.output is not None else ""
        excerpt = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
        verdict = 1 if s.passed else 0
        row = [case_id, rep.repeat, s.scorer, "", "", f"{s.value:.3f}", verdict, _inert(s.reason)]
        writer.writerow([*row, _inert(excerpt[:EXCERPT_LIMIT])])
