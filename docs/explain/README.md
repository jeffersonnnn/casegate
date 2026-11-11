# casegate explain kit

This kit makes you able to explain casegate from memory, at 30 seconds, 2 minutes and 10 minutes, and to defend every decision and number. It is written from the code and checked by `python scripts/check_explain.py`. Skill: `/walkthrough` (`refresh`, `tour`, `drill`, `pitch`, `status`).

## Reading order

1. `00-pitch.md`: the three pitches.
2. `06-diagrams.md`: draw the architecture once by hand.
3. `01-tour.md`: one real `casegate run` + `gate`, stop by stop.
4. `modules/`: one page per source file (filled as each milestone ships).
5. `02-decisions.md`: every ADR as an interview answer.
6. `03-numbers.md`: every number, its source and how to reproduce it.
7. `04-failures.md`: failure stories.
8. `05-drill.md`: the question bank.

## Study plan

| When | Session |
|---|---|
| After M0 and M1 | `/walkthrough tour` on the stops marked M0/M1 |
| After M2 (day 2, the core ships) | `/walkthrough tour`, then `/walkthrough pitch` |
| Day after M2 | `/walkthrough drill` (decisions) |
| After M3 | `/walkthrough drill` (numbers, CI gate, calibration) |
| Then every 2 to 3 days until interviews | `/walkthrough drill` (weak spots first) |

## Readability check

Filled by each milestone's Explain stage.

| Rule | Check |
|---|---|
| Each source module starts with a 3-5 line docstring that says why it exists | M3: pass. M3 fix: `calibrate_md` 5 lines ("the Markdown and the terminal tables must show the same values"). New in M3: `calibrate` 4 lines ("A judge score is only worth gating on if people would give the same verdict"). Changed in M3: `cli` 4, `console` 4 (unchanged docstrings, both still true). The YAML files `action.yml`, `eval-gate.yml` and `release.yml` have no docstring form; `action.yml` has a one-line `description`, the workflows have none. Counted with `ast.get_docstring`. M2: pass for every module with code, 1 exception. All 30 modules in `src/casegate/` have 3 or 4 non-blank docstring lines (counted with `ast.get_docstring`), and each says why the module exists. New or rewritten in M2: `cache` 4, `judge` 4, `judge_openai` 4, `report` 4, `compare` 4, `gate` 4, `scorers/llm_judge` 4, `scorers/citation_support` 4, `examples/toy_agent/agent` 4, `examples/toy_agent/store` 4. Exception: `examples/__init__.py` and `examples/toy_agent/__init__.py` are empty package markers with no docstring (0 lines). (M1 result: pass, 24 modules.) |
| No source file is longer than 250 lines (the agent loop: 200) | M3 fix (2026-11-11): pass. The renderers moved to `src/casegate/calibrate_md.py` (78 lines); `calibrate.py` is now 197, `cli.py` 250, `console.py` 233. Before the fix: 1 fail. `src/casegate/calibrate.py` is 258 lines, 8 over the limit: it was 250 when built, and the review fixes for CSV injection (`_inert`, `FORMULA_START`) and non-UTF-8 input added the rest. Fix: move the renderers (`headline_parts` to `render_calibration_md`) to their own module; not done, because the Explain stage does not change code. At the limit: `cli.py` 250 (the `calibrate` command, +29; the next command must go to its own module). Pass: `console.py` 233, `action.yml` 155, `eval-gate.yml` 82, `release.yml` 57. M2: pass. Longest: `examples/toy_agent/store.py` 226, `cli.py` 221, `judge.py` 217, `compare.py` 209, `runner.py` 194, `console.py` 188, `gate.py` 187, `models.py` 182, `scorers/llm_judge.py` 178. The agent loop `examples/toy_agent/agent.py` is 168, under its 200 limit. Watch: `cli.py` is 29 lines under the limit; M3 adds `calibrate`, so move the `gate` and `compare` commands into their own module if it passes 250. `runner.py` did not grow in M2 (194). |
| Comments say why, not what | M3 fix (2026-11-11): pass. The confusion-key comment now gives a reason (`src/casegate/calibrate.py:59-60`, short keys keep the JSON compact). In `examples/toy_agent/store.py`, the item-shape comment is removed and the order-key comment says why (`examples/toy_agent/store.py:63`, the model sends the id as a string and the case state paths use it). Before the fix: 1 fail. All 13 comments in the files M3 built or changed were read: 8 in `calibrate.py`, 2 new in `console.py`, 0 new in `cli.py`, 3 in `eval-gate.yml` (the 10 `# vX.Y.Z` pin tags in the YAML files are not counted). Fail: the old confusion-key comment (`# jp_hp, jp_hf, jf_hp, jf_hf: judge pass or fail, then human`) only gave the key legend, not a reason. Nearest to "what" but kept: `src/casegate/calibrate.py:35` (defines what `line` counts, as SPEC §12 does) and `src/casegate/calibrate.py:190` (`# the csv default is \r\n`, the reason for the argument). Fix for the fail: a `Literal` key type, or a reason ("keys stay short for the JSON"); not done. The 2 M2 fails in `examples/toy_agent/store.py` are still open. M2: 2 fail. All 60 comments (counted with `tokenize`) in the 14 files M2 built or changed were read. Two only state a data shape, not a reason: the old `store.py` comments `# [{"sku", "qty", "unit_price"}]` and `# keys are str order ids ("1042")`. Nearest to "what" but kept: `src/casegate/scorers/llm_judge.py:60` (`# as if nothing were cached`, defines the field's meaning). The M1 note at `cli.py` about `--no-cache` having no effect is gone. Fix for the 2 fails: a typed `Item` dict and a reason ("str keys match the case state paths"); not done, because the Explain stage does not change code. |
