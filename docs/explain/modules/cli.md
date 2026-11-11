# cli (`src/casegate/cli.py`, 250 lines)

**30 seconds:** The `casegate` command. Each command is a thin wrapper over the library: it parses options, calls one library function, prints through `console.py` and maps errors to exit codes (2 = bad input, 130 = Ctrl-C). M2 adds the cache, the judge, `results/latest.md`, `compare`, `gate` and the Markdown `report`.

**2 minutes:** `app` at `src/casegate/cli.py:30` `app` is the typer app; a bare `casegate` prints help. `--version` is eager, so `_version` prints and exits before any sub-command is parsed (`src/casegate/cli.py:35-51` `_version`). `run` at `src/casegate/cli.py:114-163` `run` loads the suite, warns when the judge model equals the target model (`src/casegate/cli.py:131-134`), and runs `_run_with_judge` under a progress bar (`src/casegate/cli.py:135-148`). `_run_with_judge` builds a judge only when a case needs one, a `FakeJudge` with `--fake-judge`, and always closes it (`src/casegate/cli.py:82-111` `_run_with_judge`). The cache is `Cache()` unless `--no-cache` (`src/casegate/cli.py:144`). It writes the run JSON, then `results/latest.md`, then prints the table (`src/casegate/cli.py:156-161`). `compare` prints text, Markdown or JSON and always exits 0 (`src/casegate/cli.py:166-182` `compare_cmd`). `gate` resolves the must-pass tags, runs the checks, writes the comment, and exits 0 or 1 (`src/casegate/cli.py:185-207` `gate_cmd`). `report` prints a saved run as Markdown or its summary as JSON (`src/casegate/cli.py:236-250` `report`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/cli.py:65-70` | a bad run file is exit 2 | a missing or wrong-schema file is bad input, not a regression |
| `src/casegate/cli.py:94-97` | the judge is built only when needed | a deterministic suite needs no API key |
| `src/casegate/cli.py:126` | `run` exits 0 even when cases fail | `run` measures; the gate decides |
| `src/casegate/cli.py:149-152` | `SuiteError` is exit 2, Ctrl-C is exit 130 with no file | a half run must not look like a full run |
| `src/casegate/cli.py:156-160` | the files are written before the table prints | the run is saved even if rendering fails |
| `src/casegate/cli.py:202` | the comment is the only file `gate` writes | bad input exits 2 before it, so no stale comment is posted |
| `src/casegate/cli.py:207` | exit 0 or 1 from `result.passed` | CI reads the exit code, not the text |
| `src/casegate/cli.py:210-233` `calibrate_cmd` | `calibrate` joins labels to a run; `--template` prints a CSV to fill in (M3) | calibration never gates: exit 0, or 2 on a bad run file, a bad CSV or a missing `--labels` |
| `src/casegate/cli.py:15` | `console` is imported as `term` | the M3 command had to fit in the 250-line limit; this file is now exactly 250 lines |

## Trade-off
argparse has no dependency. typer gives typed options and help text from the signatures, which keeps each command short. The cost is one dependency.

## Failure modes
`tests/test_cli.py:29` `test_version` guards the version line. `tests/test_cli.py:35` `test_run_suite_fake_repeat_3` runs the real CLI on the fake suite and checks the SPEC §17 values. A cold then warm cache (`tests/test_cli.py:69` `test_run_cache_cold_then_warm`). A missing target version is exit 2 (`tests/test_cli.py:120` `test_run_missing_target_version_exits_2`). A judge with no key is exit 2 (`tests/test_cli.py:185` `test_run_judge_without_key_exits_2`). Gate exits 0, 1 and 2 (`tests/test_cli.py:242` `test_gate_exit_0_on_pass`, `tests/test_cli.py:251` `test_gate_exit_1_on_regression`, `tests/test_cli.py:264` `test_gate_exit_2_on_bad_input`). Ctrl-C (`tests/test_cli.py:302` `test_run_ctrl_c_exits_130_and_writes_nothing`).

## What I would change
`results/latest.md` is always written in the working folder, also when `--out` points elsewhere (`src/casegate/cli.py:32`). Two runs in parallel overwrite each other's `latest.md`. Fix: write it next to the run JSON. Cost: one line and a docs change in SPEC §9.

## 10-minute version
The default output name holds the UTC start time and the first 7 chars of the git sha, or `nogit` (`src/casegate/cli.py:73-75` `_default_out`), so result files sort by time and name their commit (`tests/test_cli.py:109` `test_run_default_out_path`). When the judge equals the target, the run file records `judge_same_as_target` in its filters (`src/casegate/cli.py:154-155`). `--fake-judge` and `--record-svg` are hidden flags for tests and the video assets.
