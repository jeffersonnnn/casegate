# scorers/base (`src/casegate/scorers/base.py`, 135 lines)

**30 seconds:** The contract every scorer meets, and the small helpers they share. Scorers are found by type name and built from YAML, so they must agree on one shape and one way to write reasons. Judge and cache types load only for type checking.

**2 minutes:** The `Scorer` protocol at `src/casegate/scorers/base.py:34-47` `Scorer` has a `type`, a `Params` model, `needs_judge`, a class method `check` (load-time validation) and an async `score`. `ScoreContext` at `src/casegate/scorers/base.py:50-57` `ScoreContext` carries the judge, its config and model, the cache, the retry config and the sleep function. `DeterministicScorer.make_score` at `src/casegate/scorers/base.py:71-87` `make_score` clamps the value to 0..1, keeps the problem text whenever the value is below 1, and passes at `value >= threshold - 1e-9`. `normalise` at `src/casegate/scorers/base.py:90-92` `normalise` applies NFKC, casefold, collapses spaces and strips final `.!?`. `from_expected` at `src/casegate/scorers/base.py:121-135` `from_expected` validates a value from `case.expected` with the scorer's own params model.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/base.py:23-25` | judge and cache imports only under `TYPE_CHECKING` | a deterministic scorer never loads the judge or the cache |
| `src/casegate/scorers/base.py:74-77` | the reason names the problem even when a lowered threshold passes | a reader sees what was short of perfect (SPEC §5.1) |
| `src/casegate/scorers/base.py:82` | a 1e-9 epsilon on the pass check | float sums like 2/3 + 1/3 must still reach 1.0 |
| `src/casegate/scorers/base.py:104-109` | reasons are one line of at most 300 chars | they go into one Markdown table cell |
| `src/casegate/scorers/base.py:121-135` | `expected` values reuse the params model | a bad `expected` value fails at load with the same rules as a param |

## Trade-off
An abstract base class would enforce the methods at runtime. A Protocol lets `llm_judge` (M2) share no code with the deterministic scorers and still fit; mypy checks the fit. `DeterministicScorer` is a plain helper base, not the contract.

## Failure modes
`tests/scorers/test_build.py:86` `test_normalise` and `tests/scorers/test_build.py:91` `test_reason_helpers` cover the helpers. `tests/scorers/test_exact.py:40` `test_lowered_threshold_passes_a_zero_value` covers the threshold rule.

## What I would change
Make `normalise` configurable per scorer (for example keep punctuation). Cost: one more param on each text scorer and more test cases.

## 10-minute version
`builtins.type` is used in the protocol because a class body that defines `type: ClassVar[str]` shadows the name for mypy (FACTS.md §7 "`type` ClassVar shadowing"). `render_value` gives JSON with `ensure_ascii=False`, so reasons show non-ASCII text as it is (`src/casegate/scorers/base.py:95-96` `render_value`).
