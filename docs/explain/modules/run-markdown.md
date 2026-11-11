# report (`src/casegate/report.py`, 149 lines)

This is the module page for `report.py` (file name `run-markdown.md`).

**30 seconds:** The Markdown view of one run: `results/latest.md` after each `casegate run`, and `casegate report`. A person who opens a run sees the headline number first, then the worst cases with a concrete failing scorer and reason, not 75 raw repeats. The per-case cells are defined here once, and the terminal table reuses them.

**2 minutes:** `render_markdown` at `src/casegate/report.py:140-149` `render_markdown` joins six sections and drops the empty ones. `_header` writes one line: bold pass rate with ± std, cases × repeats, errors, cost, target, judge, sha and time (`src/casegate/report.py:60-75` `_header`). `_summary` is a metric table, with "cost this run" and "cost full" side by side (`src/casegate/report.py:78-91` `_summary`). `_by_tag` gives the pass rate per tag (`src/casegate/report.py:94-101` `_by_tag`). `_worst` keeps only cases that need attention and sorts them by `worst_key`, at most 10 (`src/casegate/report.py:104-125` `_worst`). Each row has a status word, the pass count, the mean score, the failing scorer as `name value < threshold`, and the reason from `first_failure` (`src/casegate/report.py:40-49` `first_failure`). `_errors` lists every error repeat with its message (`src/casegate/report.py:128-137` `_errors`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/report.py:14` | status words with glyphs | status stays readable with no colour (`docs/adr/0007-design-direction-lab-instrument.md`) |
| `src/casegate/report.py:18-20` | an empty cell renders as a single space | GitHub shows it as blank, and the goldens stay stable |
| `src/casegate/report.py:23-26` | worst first: pass rate up, None last, then mean score, then id | the order is total, so the output never changes between equal runs |
| `src/casegate/report.py:56-57` | a case needs attention below 1.0 or on error | a clean run says "every case passed" instead of a long table |
| `src/casegate/report.py:86-87` | both costs are shown | a cached re-run shows $0.00 and still says what a cold run costs |

## Trade-off
An HTML page could show charts. Markdown renders in a GitHub PR, a job summary and a terminal pager with no server. The cost: no interaction, so detail stays in the run JSON.

## Failure modes
The output matches its golden file (`tests/test_report.py:43` `test_report_golden`). An all-pass run with unknown cost, no judge and no tags (`tests/test_report.py:47` `test_report_all_pass_unknown_cost_no_judge_no_tags`). A run with no pass rate drops the ± std (`tests/test_report.py:61` `test_report_without_pass_rate_drops_the_std`). Real output: `results/latest.md` after the M2 re-run check shows pass rate 0.973 and two worst cases, both on `citation_support`.

## What I would change
Add a "judge spread" column for cases with k > 1 samples, so judge noise is visible next to the verdict. Cost: one column and a golden update.

## 10-minute version
`pass_cell`, `mean_cell`, `failing_scorer_cell` and `worst_key` are imported by `console.py` (`src/casegate/console.py:25`), so the terminal and the Markdown never disagree on a cell. The CLI writes `results/latest.md` after the run JSON (`src/casegate/cli.py:153-157`). Cells pass through `md_cell` in `fmt.py`, which escapes pipes and cuts long text. `md_row` is also used by `compare.py` and `gate.py`.
