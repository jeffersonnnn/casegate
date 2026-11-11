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
| Each source module starts with a 3-5 line docstring that says why it exists | M2: pass for every module with code, 1 exception. All 30 modules in `src/casegate/` have 3 or 4 non-blank docstring lines (counted with `ast.get_docstring`), and each says why the module exists. New or rewritten in M2: `cache` 4, `judge` 4, `judge_openai` 4, `report` 4, `compare` 4, `gate` 4, `scorers/llm_judge` 4, `scorers/citation_support` 4, `examples/toy_agent/agent` 4, `examples/toy_agent/store` 4. Exception: `examples/__init__.py` and `examples/toy_agent/__init__.py` are empty package markers with no docstring (0 lines). (M1 result: pass, 24 modules.) |
| No source file is longer than 250 lines (the agent loop: 200) | M2: pass. Longest: `examples/toy_agent/store.py` 226, `cli.py` 221, `judge.py` 217, `compare.py` 209, `runner.py` 194, `console.py` 188, `gate.py` 187, `models.py` 182, `scorers/llm_judge.py` 178. The agent loop `examples/toy_agent/agent.py` is 168, under its 200 limit. Watch: `cli.py` is 29 lines under the limit; M3 adds `calibrate`, so move the `gate` and `compare` commands into their own module if it passes 250. `runner.py` did not grow in M2 (194). |
| Comments say why, not what | M2: 2 fail. All 60 comments (counted with `tokenize`) in the 14 files M2 built or changed were read. Two only state a data shape, not a reason: `examples/toy_agent/store.py:46` (`# [{"sku", "qty", "unit_price"}]`) and `examples/toy_agent/store.py:63` (`# keys are str order ids ("1042")`). Nearest to "what" but kept: `src/casegate/scorers/llm_judge.py:60` (`# as if nothing were cached`, defines the field's meaning). The M1 note at `cli.py` about `--no-cache` having no effect is gone. Fix for the 2 fails: a typed `Item` dict and a reason ("str keys match the case state paths"); not done, because the Explain stage does not change code. |
