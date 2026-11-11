# loader (`src/casegate/loader.py`, 161 lines)

**30 seconds:** The loader reads a suite directory into one `Suite` and a list of `Case` objects. It collects every problem as one line and raises them together as a `SuiteError`, so the CLI exits 2 with the full list before any paid call.

**2 minutes:** `load_suite` at `src/casegate/loader.py:26-53` `load_suite` reads `suite.yaml` first (`src/casegate/loader.py:56-68` `_read_suite_yaml`); without it there is nothing to check against, so that is the one early raise. It sets `root` itself (`src/casegate/loader.py:31`), so an author cannot point it elsewhere. A failed `Suite` validation does not stop the load: the cases are still read with the raw glob (`src/casegate/loader.py:39-41`). `_load_cases` at `src/casegate/loader.py:76-107` `_load_cases` reads each file in sorted order, splits multi-document YAML, validates each document as a `Case`, checks duplicate ids, checks scorer types against `REGISTRY`, and calls `build_scorers` only when every type is known (`src/casegate/loader.py:94-105`). `_check_target` at `src/casegate/loader.py:139-148` `_check_target` builds the target once with no I/O. The tag filter runs last (`src/casegate/loader.py:46-49`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/loader.py:39-41` | cases load even when the suite is invalid | the author sees every error in one run |
| `src/casegate/loader.py:94-99` | unknown scorer types are found here, with file and case index | the error points at the file the author must edit; `build_scorers` would only know the case id |
| `src/casegate/loader.py:115-116` | files sort by path relative to the root | the case order is the same on every machine |
| `src/casegate/loader.py:125-126` | empty YAML documents are skipped, but keep their index | a trailing `---` is not a case, and error indexes still match the file |
| `src/casegate/loader.py:141-144` | the current folder goes first on `sys.path` | `tests.fixtures.suite_fake.target:run` resolves like `python -m` from the repo root |
| `src/casegate/loader.py:159-161` | YAML errors fold to one line | the CLI prints one error per line |

## Trade-off
Fail fast on the first error is simpler. Collecting errors costs a list passed through each helper, but a suite with 15 cases and 4 mistakes is fixed in one edit, not four runs. The cost is that later checks must handle partial data (for example `suite is None`).

## Failure modes
A missing `suite.yaml` or a YAML syntax error stops at once with one line (`tests/test_loader.py:120` `test_suite_yaml_not_found`, `tests/test_loader.py:124` `test_suite_yaml_cannot_parse`). A missing `target.version` is a field error (`tests/test_loader.py:136` `test_suite_missing_version_and_model`) and the CLI exits 2 (`tests/test_cli.py:120` `test_run_missing_target_version_exits_2`). An unknown type (in M1 this was `llm_judge`) skips `build_scorers` (`tests/test_loader.py:213` `test_unknown_scorer_type_skips_build_scorers`). Every error kind in one raise is proved by `tests/test_loader.py:386` `test_all_error_kinds_in_one_raise`.

## What I would change
Add the line number inside the YAML file to each case error, not only the document index. Cost: a YAML loader that keeps marks (`yaml.compose`), about 30 lines.

## 10-minute version
The loader validates; it does not run. It builds scorers and the target once and throws them away; the runner builds them again (`src/casegate/runner.py:72`, `src/casegate/runner.py:84`). That is cheap because neither does I/O. `resolve_names` writes scorer names back into the case config, so the second build gives the same names (`src/casegate/scorers/__init__.py:47-67` `resolve_names`). Inputs: a directory. Outputs: `(Suite, list[Case])` or a `SuiteError` whose `errors` list the CLI prints (`src/casegate/cli.py:149-150`).
