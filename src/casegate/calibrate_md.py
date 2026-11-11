"""Calibration rendering, kept apart from the join and the metrics (SPEC §12).

The Markdown and the terminal tables must show the same values, so the cell helpers live
here once and both `render_calibration_md` and `console.render_calibration` use them. The
split also keeps `calibrate.py` under the 250-line limit (SPEC §1b).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from casegate.fmt import REASON_LIMIT, fmt_rate, md_cell
from casegate.report import md_row

if TYPE_CHECKING:
    from casegate.calibrate import Calibration, Disagreement, LabelRow

DISAGREE_HEAD = "| case | repeat | scorer | judge value | human | judge reason | note |"


def headline_parts(cal: Calibration) -> list[tuple[str, str]]:
    kappa = "undefined" if cal.kappa is None else f"{cal.kappa:.2f}"
    return [("agreement", fmt_rate(cal.agreement)), ("kappa", kappa), ("n", str(cal.n))]


def confusion_rows(cal: Calibration) -> list[list[str]]:
    c = cal.confusion
    return [
        ["judge pass", str(c["jp_hp"]), str(c["jp_hf"])],
        ["judge fail", str(c["jf_hp"]), str(c["jf_hf"])],
    ]


def disagreement_cells(d: Disagreement, *, markdown: bool = True) -> list[str]:
    """The terminal passes markdown=False, as for the comparison flips (SPEC §9)."""
    return [
        d.case_id,
        str(d.repeat),
        d.scorer,
        f"{d.judge_value:.2f}",
        "✓ pass" if d.human_pass else "✗ fail",
        md_cell(d.judge_reason, REASON_LIMIT, markdown=markdown),
        md_cell(d.note, REASON_LIMIT, markdown=markdown),
    ]


def unmatched_cells(row: LabelRow) -> list[str]:
    return [str(row.line), row.case_id, str(row.repeat), row.scorer]


def _details(tag: str, title: str, head: list[str], rows: list[str]) -> str:
    return "\n".join([f"{tag}<summary>{title}</summary>", "", *head, *rows, "", "</details>"])


def render_calibration_md(cal: Calibration) -> str:
    (_, agreement), *rest = headline_parts(cal)
    parts = [
        "## casegate calibrate",
        f"**agreement {agreement}** · " + " · ".join(f"{k} {v}" for k, v in rest),
        *(f"> [!NOTE]\n> {note}" for note in cal.notes),
        "\n".join(
            ["| | human pass | human fail |", "|---|--:|--:|"]
            + [md_row(r) for r in confusion_rows(cal)]
        ),
        _details(
            "<details open>",
            f"Disagreements ({len(cal.disagreements)})",
            [DISAGREE_HEAD, "|---|--:|---|--:|---|---|---|"],
            [md_row(disagreement_cells(d)) for d in cal.disagreements],
        ),
        _details(
            "<details>",
            f"Unmatched rows ({len(cal.unmatched)})",
            ["| line | case | repeat | scorer |", "|--:|---|--:|---|"],
            [md_row([md_cell(c, REASON_LIMIT) for c in unmatched_cells(r)]) for r in cal.unmatched],
        ),
    ]
    return "\n\n".join(parts) + "\n"
