# scorers/matchers (`src/casegate/scorers/matchers.py`, 133 lines)

**30 seconds:** A small matcher language, so a case can say "an amount at most 39" instead of one exact value. Tool arguments and reported state share it. Matchers parse at load time, so a bad matcher is a load error, not a silent fail in a paid run.

**2 minutes:** `parse` at `src/casegate/scorers/matchers.py:107-133` `parse` treats any value that is not a dict of matcher keys as a plain value. A matcher dict must use one of the valid key sets (`src/casegate/scorers/matchers.py:18-30`), so `{gte, lte}` is fine but `{regex, lte}` is not. Each key's value is checked, and a regex is compiled once. `all_amounts_lte` is allowed only when the caller says `allow_list=True` (`src/casegate/scorers/matchers.py:114-115`). `Matcher.match` at `src/casegate/scorers/matchers.py:71-91` `match` returns False for an absent value, uses `equal` for plain values, and applies the one matcher rule otherwise. `equal` at `src/casegate/scorers/matchers.py:42-54` `equal` compares numbers with a tolerance and never coerces types.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/matchers.py:37-39` | `bool` is not a number | `True` is an `int` in Python, but it is not an amount |
| `src/casegate/scorers/matchers.py:44-45` | bools compare only with bools | `True == 1` must not match |
| `src/casegate/scorers/matchers.py:52-53` | strings never equal numbers | `"1042"` is not order `1042`; a type change in the target is a real change |
| `src/casegate/scorers/matchers.py:97-100` | `all_amounts_lte`: every item's `amount` is at most the limit | it checks every refund attempt, not only the last one |
| `src/casegate/scorers/matchers.py:103-104` | a dict with any non-matcher key is a plain value | `{status: "open"}` stays an exact value, not a bad matcher |

## Trade-off
JSONPath or a full expression language would be more powerful. Seven keys cover the cases in the suite, and each rule is a few lines to explain. The cost is that a new check needs a code change.

## Failure modes
`tests/scorers/test_matchers.py:37` `test_match` covers each rule; `tests/scorers/test_matchers.py:42` `test_absent_value_never_matches`; `tests/scorers/test_matchers.py:58` `test_all_amounts_lte`; `tests/scorers/test_matchers.py:90` `test_parse_errors` covers every SPEC §3.3 message.

## What I would change
Add a `not` wrapper, so a case can say "status is not refunded". Cost: one recursive rule and its key-set entries.

## 10-minute version
`Matcher.render` gives compact JSON (`{"lte":39}`) for matchers and normal JSON for plain values, so a reason shows exactly what the case asked for (`src/casegate/scorers/matchers.py:93-94` `render`). Regex uses `search`, not `fullmatch`, so an author anchors with `^...$` when they need it.
