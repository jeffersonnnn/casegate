# scorers/contains (`src/casegate/scorers/contains.py`, 105 lines)

**30 seconds:** The `contains` and `not_contains` scorers: required and banned phrases in the reply. They share one file because they read the same way and use the same normalisation. A `contains` item can be a group of synonyms, and any one is enough.

**2 minutes:** `resolve_items` at `src/casegate/scorers/contains.py:34-52` `resolve_items` takes `items` from the params, else from `expected.answer_contains` or `expected.answer_not_contains`, and rejects empty lists and empty groups. `ContainsScorer.score` at `src/casegate/scorers/contains.py:70-84` `score` checks each item; a group passes when any member is in the reply (`src/casegate/scorers/contains.py:78-81`). The value is the fraction of items found, and the reason lists the missing ones. `NotContainsScorer.score` at `src/casegate/scorers/contains.py:96-105` `score` gives 0 when any banned phrase is found and names them.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/contains.py:24` | an item is a string or a list of strings | "refund" or "refunded" are both fine; the case should not fail on wording |
| `src/casegate/scorers/contains.py:82` | the value is a fraction | with a lowered threshold, 3 of 4 phrases can pass, and the reason still lists the missing one |
| `src/casegate/scorers/contains.py:104` | `not_contains` is all or nothing | one banned phrase is enough to fail |

## Trade-off
Regex items would be more exact, but YAML authors get them wrong. Plain substrings after normalisation are easy to write and read; `json_schema`, `state_match` and the judge cover stricter checks.

## Failure modes
`tests/scorers/test_contains.py:21` `test_contains_fraction_and_any_of_group_reason`, `tests/scorers/test_contains.py:34` `test_contains_below_one_passes_with_lower_threshold_but_keeps_missing_reason`, `tests/scorers/test_contains.py:49` `test_not_contains_pass_and_fail_reason_in_config_order`. The fake suite's `fail-contains-02` case fails on purpose with `missing: "missing-word"` (`tests/fixtures/suite_fake/cases/02-fail-contains-02.yaml:1`).

## What I would change
Match on word boundaries, so "refund" does not match inside "nonrefundable". Cost: a regex per item and a choice about punctuation.

## 10-minute version
Substring matching after normalisation means a banned word inside a longer word still counts. That is safe for `not_contains` (it fails closed) and loose for `contains` (it can pass on a longer word).
