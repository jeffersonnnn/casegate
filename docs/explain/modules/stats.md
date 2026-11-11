# stats (`src/casegate/stats.py`, 100 lines)

**30 seconds:** Pure functions that turn per-repeat results into case pass rates and one run summary. The maths decides what the gate sees, so it is kept apart from the async runner and tested on hand-made results. The runner re-exports `aggregate` as `runner.aggregate`.

**2 minutes:** `aggregate` at `src/casegate/stats.py:35-100` `aggregate` first builds one `CaseResult` per case. Error repeats leave the denominator (`src/casegate/stats.py:45`), so the case pass rate is passes over scored repeats, or None when every repeat errored (`src/casegate/stats.py:46`). The case variance is `p(1-p)` (`src/casegate/stats.py:55`). Then it computes the suite pass rate of each repeat index (`src/casegate/stats.py:59-67`). The suite pass rate is the mean of the case pass rates, and `pass_rate_std` is the sample std of the per-repeat rates, or 0.0 with fewer than two (`src/casegate/stats.py:80-81`). Tokens and costs add up target and scorer terms. `sum_costs` at `src/casegate/stats.py:16-23` `sum_costs` makes the total None when any term is None.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/stats.py:45` | errors leave the denominator | an outage cannot look like a regression (`docs/adr/0003-errors-are-not-failures.md`) |
| `src/casegate/stats.py:59-67` | one suite pass rate per repeat index | the spread across repeats is the run-to-run noise the gate tolerance needs (`docs/adr/0006-gate-tolerance-from-measured-variance.md`) |
| `src/casegate/stats.py:81` | `stdev` needs two values, else 0.0 | one repeat has no measured spread |
| `src/casegate/stats.py:16-23` | one unknown cost makes the total unknown | a missing price must never show as $0 |
| `src/casegate/stats.py:26-32` | `case_status`: a flaky fail outranks an error | the report shows the real problem first (SPEC §2 rule 10) |

## Trade-off
A pooled pass rate (all passes over all scored repeats) weights a case with more scored repeats more. The mean of case pass rates gives each case equal weight, which is what a suite author expects. The cost: a case with 1 scored repeat of 5 counts as much as a case with 5.

## Failure modes
`tests/test_runner.py:311` `test_aggregate_maths` checks the rates and std by hand. `tests/test_runner.py:336` `test_aggregate_single_repeat_std_is_zero_and_all_error_rate_none` covers one repeat and an all-error case. `tests/test_runner.py:342` `test_case_status_error_when_all_scored_pass_but_one_errored` covers the status rule. `tests/test_runner.py:385` `test_unknown_target_cost_makes_repeat_cost_unknown` covers None costs.

## What I would change
Report a confidence interval for the suite pass rate (for example a bootstrap over cases), not only the std across repeats. Cost: more code and a harder number to explain; PLAN.md keeps statistical tests out of scope.

## 10-minute version
`statistics.stdev` is the sample std (n-1), so 5 repeats give a slightly larger std than the population formula, which makes the tolerance a little safer. The SPEC §17 fake suite gives per-repeat rates of 0.75 three times, so the std is 0.0; the CLI test pins this (`tests/test_cli.py:35` `test_run_suite_fake_repeat_3`). `by_tag` is the mean case pass rate per tag, with None when every tagged case errored (`src/casegate/stats.py:71-74`).
