# scorers/state_match (`src/casegate/scorers/state_match.py`, 104 lines)

**30 seconds:** The `state_match` scorer: the world after the case must be in the expected state. A reply can say "refunded" when the order is not. This scorer reads the state the target reports and checks each expected path with a matcher.

**2 minutes:** `resolve_state` at `src/casegate/scorers/state_match.py:57-65` `resolve_state` takes `state` from the params, else `expected.state`, and needs at least one path. `split_path` at `src/casegate/scorers/state_match.py:32-41` `split_path` turns `orders["a.b"].status` into segments, or None when the path is malformed. `lookup` at `src/casegate/scorers/state_match.py:44-54` `lookup` walks dicts by key and lists by index, and returns a sentinel when the path does not resolve. `score` at `src/casegate/scorers/state_match.py:85-104` `score` checks each path with `parse(spec, allow_list=True)`, so `all_amounts_lte` is allowed here. The value is the fraction of matching paths, and the reason lists each mismatch as `path: expected X, got Y`.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/state_match.py:21` | the path grammar allows `["quoted.key"]` | state keys can hold dots, like an order id |
| `src/casegate/scorers/state_match.py:24` | a private `_MISSING` sentinel | a state value of `None` is different from an absent path |
| `src/casegate/scorers/state_match.py:76-77` | a malformed path fails at load | the author fixes it before a paid run |
| `src/casegate/scorers/state_match.py:101-103` | a missing path renders as `<missing>` and is a fail, not an error | the target ran; it did not reach the expected state |

## Trade-off
JSONPath is a standard, but it adds a dependency and filter syntax that a reader must learn. Dots plus quoted keys plus list indexes cover the toy store state.

## Failure modes
`tests/scorers/test_state_match.py:38` `test_mismatch_and_missing_reason_in_expected_order`, `tests/scorers/test_state_match.py:71` `test_split_path`, `tests/scorers/test_state_match.py:78` `test_load_errors`. The fake suite's `tools-state-04` case passes with `state: {done: true}` in the real CLI run (`tests/test_cli.py:35` `test_run_suite_fake_repeat_3`).

## What I would change
Allow a wildcard segment (`orders.*.status`) for "every order". Cost: the lookup returns many values and the matcher rule needs "all" or "any".

## 10-minute version
`split_path` runs in both `check` and `score`; `score` raises only if a scorer was built without `check` (`src/casegate/scorers/state_match.py:92-94`). The toy agent (M2) reports `refund_attempts` as a list of `{amount}` items, which `all_amounts_lte` reads (`src/casegate/scorers/matchers.py:97-100` `_all_amounts_lte`).
