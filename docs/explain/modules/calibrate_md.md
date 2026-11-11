# calibrate_md (`src/casegate/calibrate_md.py`, 78 lines)

**30 seconds:** This module turns a `Calibration` into the cells and the Markdown that people read. The terminal tables and `--format md` use the same cell helpers, so they always show the same values. It was split out of `calibrate.py` on 2026-11-11 to keep that file under the 250-line limit (SPEC §1b).

**2 minutes:** `headline_parts` gives the three headline values: agreement via `fmt_rate`, kappa with 2 decimals or `undefined`, and `n` (`src/casegate/calibrate_md.py:21-23` `headline_parts`). `confusion_rows` gives the 2 x 2 table rows from the short confusion keys (`src/casegate/calibrate_md.py:26-31` `confusion_rows`). `disagreement_cells` gives one disagreement row; every free-text cell goes through `md_cell` with the 120-char limit (`src/casegate/calibrate_md.py:34-44` `disagreement_cells`). `unmatched_cells` gives the line, case, repeat and scorer of a label that joined to no score (`src/casegate/calibrate_md.py:47-48` `unmatched_cells`). `render_calibration_md` puts these parts together: the title, the bold agreement, one note block per note, the confusion table, then two `<details>` blocks (`src/casegate/calibrate_md.py:55-78` `render_calibration_md`). `console.render_calibration` calls the same four helpers for the rich tables (`src/casegate/console.py:216-233` `render_calibration`). `calibrate.py` re-exports `render_calibration_md` (`src/casegate/calibrate.py:17`), so `cli.py` and the tests import it from the old place.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/calibrate_md.py:15-16` | `Calibration`, `Disagreement` and `LabelRow` are imported only for type checks | `calibrate.py` imports this module at the top; a runtime import back would be a circular import |
| `src/casegate/calibrate_md.py:34-35` | `markdown=False` for the terminal | the terminal does not need the Markdown escapes; the comparison flips do the same (SPEC §9) |
| `src/casegate/calibrate_md.py:42-43` | judge reason and note go through `md_cell` | both are free text; `md_cell` escapes `\|`, `<` and `@`, so a reason cannot break the table or notify someone in a PR comment |
| `src/casegate/calibrate_md.py:65-70` | the disagreements block is `<details open>` | the disagreements are the point of calibration, so they show without a click |
| `src/casegate/calibrate_md.py:71-76` | the unmatched block is closed | unmatched rows are a typo check, not the result |

## Trade-off
The helpers could stay in `calibrate.py` with only `render_calibration_md` moved. That leaves `calibrate_md.py` to import the helpers back from `calibrate.py`, which imports `calibrate_md.py`: a circular import. Moving all the rendering here, with type-only imports of the models, removes the cycle. The cost is one more file, and `console.py` imports from two modules (`src/casegate/console.py:21-27`).

## Failure modes
A changed cell or layout breaks the golden file (`tests/test_calibrate.py:42` `test_golden_md`, `tests/golden/calibrate.md`). The terminal output with the same helpers is checked in plain mode (`tests/test_calibrate.py:242` `test_render_calibration_plain`). Kappa `undefined` and the note block come from a one-class run (`tests/test_calibrate.py:75` `test_kappa_undefined_with_one_class`). The CLI `--format md` path is covered by `tests/test_calibrate.py:251` `test_cli_formats_and_exit_codes`.

## What I would change
Give the confusion keys a `Literal` type, so a typo in `confusion_rows` fails mypy, not a test. Cost: a small change to the `Calibration` model and its JSON schema.

## 10-minute version
Data in: one `Calibration` from `calibrate()` (`src/casegate/calibrate.py:142-180` `calibrate`). Data out: one Markdown string that ends in a newline, or lists of string cells for the terminal. The module does no joins and no math; it only formats. The number formats come from `fmt.py`, one place for every number format (SPEC §9), and the table rows come from `report.md_row`. The `<summary>` lines and the blank lines around each table follow SPEC §12, because GitHub renders a table inside `<details>` only with a blank line before it.
