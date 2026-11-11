# scorers (`src/casegate/scorers/__init__.py`, 100 lines)

**30 seconds:** The scorer registry and `build_scorers`, the one function that turns a case's scorer YAML into scorer objects. The loader and the runner both use it, so names, thresholds and validation follow one rule set. Every problem in a case is collected and raised together.

**2 minutes:** `REGISTRY` at `src/casegate/scorers/__init__.py:33-42` `REGISTRY` maps each type name to its class; from M2 it holds 8 types, with `llm_judge` and `citation_support` as the two that need a judge (`src/casegate/scorers/__init__.py:40-41`). `build_scorers` at `src/casegate/scorers/__init__.py:74-100` `build_scorers` first rejects unknown types with a `SuiteError`, never a `KeyError` (`src/casegate/scorers/__init__.py:76-79`). `resolve_names` at `src/casegate/scorers/__init__.py:51-71` `resolve_names` names unnamed scorers per type (`exact`, `exact#2`) and reports duplicates. For each scorer it picks the threshold: the scorer's own, else 1.0 for a deterministic type, else the suite threshold (`src/casegate/scorers/__init__.py:85-88`). It validates the params with the class's pydantic model, then runs the class's `check`, and adds the prefix `case <id> scorer <name>: ` to each line (`src/casegate/scorers/__init__.py:84-95`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/__init__.py:76-79` | unknown types are checked first | a bad type is a clear load error, never a `KeyError` crash |
| `src/casegate/scorers/__init__.py:60-63` | names are written back into the config | a second build (loader, then runner) gives the same names |
| `src/casegate/scorers/__init__.py:87-88` | deterministic scorers default to threshold 1.0; judge scorers to the suite threshold | a partial `contains` match is a fail unless the author lowers it; a judge grade is graded on a scale |
| `src/casegate/scorers/__init__.py:84` | one prefix added here, not in each scorer | every scorer error reads the same way |

## Trade-off
Scorers could register themselves with a decorator. An explicit dict is visible in one place and mypy checks it (FACTS.md §7 "nested params class"). Adding a type means one import and one line here.

## Failure modes
`tests/scorers/test_build.py:18` `test_registry_holds_all_eight_types`, `tests/scorers/test_build.py:23` `test_unknown_type_raises_suite_error_before_anything_else`, `tests/scorers/test_build.py:35` `test_names_are_numbered_per_type_and_written_back`, `tests/scorers/test_build.py:50` `test_duplicate_names`, `tests/scorers/test_build.py:59` `test_thresholds`, `tests/scorers/test_build.py:68` `test_all_errors_are_collected`.

## What I would change
Make `resolve_names` return new configs instead of writing into `cfg.name`. Cost: callers must use the returned list; the write-back is a hidden side effect that a reader can miss.

## 10-minute version
The unknown-type line lists every known type, sorted (`src/casegate/scorers/__init__.py:47-48` `unknown_type_line`). The test checks the 8 names and that exactly the two judge types have `needs_judge` (`tests/scorers/test_build.py:18-21`). The CLI reads `needs_judge` from the registry to decide whether to build a judge at all (`src/casegate/cli.py:78-79` `_needs_judge`). Params come from the scorer YAML's extra keys (`cfg.model_extra`), so a typo in a param name is a load error through `extra="forbid"` on each params model.
