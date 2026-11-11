# compare (`src/casegate/compare.py`, 209 lines)

**30 seconds:** Compares a run with a baseline: the pass-rate delta and the cases that flipped (SPEC §10). A pass-rate number alone does not tell a reviewer what broke. The comparison names each flipped case with the scorer and reason that failed, and warns when the two runs are not like for like.

**2 minutes:** `compare` at `src/casegate/compare.py:84-137` `compare` indexes both runs by case id. For each case in both, `verdict` gives one word: `error` when no repeat was scored, else `pass` when the pass rate is at least 0.5, else `fail` (`src/casegate/compare.py:62-66` `verdict`). A pass to fail is a regression, and `_regression` finds the first failing scorer and reason in the run (`src/casegate/compare.py:69-77` `_regression`). Fail to pass, to error and from error go in their own lists (`src/casegate/compare.py:96-104`). Any change in a case pass rate becomes a `Delta`, and the 10 largest are kept (`src/casegate/compare.py:105-114`, `src/casegate/compare.py:131`). A changed target version, judge model or repeat count adds a warning (`src/casegate/compare.py:115-123`). Added and removed case ids, the pass-rate delta, the cost delta and both error counts complete the `Comparison` (`src/casegate/compare.py:47-59` `Comparison`). The helpers `metric_rows`, `flips_md` and `list_lines` build the table and lists that the gate comment and the terminal share (`src/casegate/compare.py:140-205`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/compare.py:62-66` | majority verdict per case | with 5 repeats, a 3/5 to 2/5 change is a flip; 5/5 to 4/5 is only a delta |
| `src/casegate/compare.py:69-77` | the flip carries the failing scorer and reason | the reviewer sees why, in the comment, without the JSON |
| `src/casegate/compare.py:115-123` | like-for-like warnings | a judge change can move scores with no agent change; the reader must know |
| `src/casegate/compare.py:131` | sort by size of delta, then input order | the order is stable, so goldens stay fixed |

## Trade-off
A per-case statistical test (for example a paired test over repeats) would say which flips are real. A majority rule and a list of deltas are simple to explain and to check by hand; the noise is handled at the suite level by the gate tolerance (`docs/adr/0006-gate-tolerance-from-measured-variance.md`).

## Failure modes
The Markdown matches its golden (`tests/test_compare_gate.py:39` `test_comparison_golden`). The regressed fixture gives the expected flips (`tests/test_compare_gate.py:44` `test_compare_regressed`). Error lists, added, removed and warnings (`tests/test_compare_gate.py:60` `test_compare_error_lists_added_removed_and_warnings`). A fail-to-pass flip and an error flip reason (`tests/test_compare_gate.py:81` `test_fail_to_pass_flip_and_error_flip_reason`). `casegate compare` always exits 0, because only the gate blocks (`src/casegate/cli.py:166-182` `compare_cmd`).

## What I would change
Show per-case deltas only when they are larger than that case's own noise in the baseline. Cost: the baseline must keep per-case variance, which it already can compute from its repeats.

## 10-minute version
`compare` reads only `Run` files, so a baseline made months ago still compares as long as `schema_version` matches. A case pass rate of None (all repeats errored) is left out of the deltas. `pass_rate_delta` is None when either run has no pass rate. The cost delta uses `cost_usd`, the cost of this run, so a cached run shows a large saving; the full cost is in each run's own summary.
