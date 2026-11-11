# console (`src/casegate/console.py`, 188 lines)

**30 seconds:** Terminal output for the CLI. A person at a terminal gets colour in the "Lab instrument" theme; CI logs, pipes and `NO_COLOR` users get plain text. Both modes share one renderer, so the words, glyphs and numbers are always the same, and the goldens test both.

**2 minutes:** `make_console` at `src/casegate/console.py:34-38` `make_console` gives colour only when `--plain` is off, stdout is a terminal and `NO_COLOR` is unset. `progress` at `src/casegate/console.py:41-55` `progress` shows a bar on a terminal and is off in plain mode; the bar is transient, so the final table replaces it. `render_run` at `src/casegate/console.py:65-112` `render_run` prints a header line, a table with status, case, pass count, mean score and failing scorer, then a summary line with pass rate ± std, errors, cost and cache, and the path written (`src/casegate/console.py:106-112`). `render_compare` prints warnings, the metric table, the flip tables and the lists (`src/casegate/console.py:157-161` `render_compare`). `render_gate` prints the headline, warnings, the metric table with must-pass rows, one line per check, the flips, and `✓ PASSED exit 0` or `✗ BLOCKED exit 1` (`src/casegate/console.py:164-188` `render_gate`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/console.py:28-30` | theme colours and the three status glyphs | the design tokens (`docs/adr/0007-design-direction-lab-instrument.md`); a glyph keeps the status readable with no colour |
| `src/casegate/console.py:25` | cells come from `report.py` | the terminal and the Markdown never disagree on a cell |
| `src/casegate/console.py:21-23` | rows and checks come from `compare.py` and `gate.py` | the comment and the terminal show the same numbers |
| `src/casegate/console.py:50` | the progress bar is transient | logs keep only the result |
| `src/casegate/console.py:80-82` | more than 20 cases: show the worst 20 | a big suite still fits one screen |
| `src/casegate/console.py:131-132` | an empty flip table is not printed | a passed gate shows no empty tables |

## Trade-off
Plain `print` is simpler, but colour and an aligned table make a 15-case run readable at a glance. rich is one dependency, and its `no_color` console gives the plain mode with the same code path.

## Failure modes
Plain goldens for run and gate (`tests/test_console.py:22` `test_run_plain_golden`, `tests/test_console.py:28` `test_gate_plain_golden`). A passed gate shows no flip tables (`tests/test_console.py:38` `test_gate_plain_passed_shows_no_flip_tables`). Compare lists and flips (`tests/test_console.py:48` `test_compare_plain_lists_and_flips`). The 20-row cut and error cells (`tests/test_cli.py:316` `test_render_run_shows_the_worst_20_and_error_cells`). No ANSI code in plain mode (`tests/test_cli.py:35` `test_run_suite_fake_repeat_3`).

## What I would change
Print a one-line progress count in plain mode every N cases, so a long CI run shows life. Cost: a few lines and a golden update.

## 10-minute version
M3 adds `render_calibration` here (FACTS.md §7 R3: a `TYPE_CHECKING` import of a missing module fails mypy, so it waits for `calibrate.py`). The summary line's `± std` is the `pass_rate_std` from `stats.aggregate` (`src/casegate/stats.py:81`). `--record-svg` saves the coloured output as an SVG for the README and the site (`src/casegate/cli.py:159-160`).
