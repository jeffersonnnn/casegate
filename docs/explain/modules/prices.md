# prices (`src/casegate/prices.py`, 50 lines)

**30 seconds:** Turns token counts into dollars, so every run reports what it cost. The table is a dated snapshot, a user can correct it with `CASEGATE_PRICES`, and an unknown model gives None, never 0.

**2 minutes:** `PRICES` at `src/casegate/prices.py:15-21` `PRICES` maps a model id to (input, output) USD per 1M tokens, dated by `PRICES_AS_OF` (`src/casegate/prices.py:14` `PRICES_AS_OF`). `price_table` at `src/casegate/prices.py:36-42` `price_table` copies the table and merges a JSON override file named by `CASEGATE_PRICES`, read on each call so tests can set the variable. `_load_overrides` at `src/casegate/prices.py:24-33` `_load_overrides` rejects anything that is not an object of `[input, output]` pairs. `cost` at `src/casegate/prices.py:45-50` `cost` returns None for an unknown model, else the dollar amount.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/prices.py:14` | `PRICES_AS_OF = "2026-11-03"` | prices change; the report can say how old they are |
| `src/casegate/prices.py:19-20` | two OpenAI prices marked UNVERIFIED | honest: they were not checked against the provider page |
| `src/casegate/prices.py:39-41` | env override merged over the table | a user fixes a price without a release |
| `src/casegate/prices.py:47-48` | unknown model returns None | a run with a missing price shows "cost unknown", not "free" |

## Trade-off
A live price API would always be current but adds a network call and a failure mode to every run. A static dated table is offline and deterministic, at the cost of going stale.

## Failure modes
A stale or missing price gives a wrong or unknown cost. `tests/test_prices.py:14` `test_table_matches_facts` pins the table to FACTS.md §4.4. `tests/test_prices.py:27` `test_unknown_model_is_none_not_zero` proves None. `tests/test_prices.py:31` `test_env_override_merges` and `tests/test_prices.py:42` `test_bad_override_raises` guard the override file.

## What I would change
Verify the two OpenAI prices (planned at M2) or remove them. Cost: one check against the provider page.

## 10-minute version
Cache hits cost 0 in `Score.cost_usd` and `RepeatResult.cost_usd`, but `cost_usd_full` still uses this table, so the report can show both. Prompt-cache discounts are not modelled; the cost is an upper bound for cached prompts.
