# scorers/exact (`src/casegate/scorers/exact.py`, 60 lines)

**30 seconds:** The `exact` scorer: the reply must equal one of the expected answers. It is the strictest and cheapest check, for short fixed replies. Normalisation is on by default, so case, spacing and a final full stop do not decide a pass.

**2 minutes:** `resolve_answers` at `src/casegate/scorers/exact.py:26-40` `resolve_answers` takes `answer` from the params, else from `expected.answer`; params win, with no merge. A string becomes a one-item list, and an empty list is a load error. `ExactScorer.score` at `src/casegate/scorers/exact.py:51-60` `score` applies `normalise` (or `str` when `normalise: false`) to both sides and gives 1.0 when any answer matches. The fail reason lists the answers and the first 80 chars of the reply (`src/casegate/scorers/exact.py:59`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/exact.py:28-29` | params override `expected.answer` | one case can hold an answer for several scorers and still override one |
| `src/casegate/scorers/exact.py:37` | one answer or a list of answers | a short reply often has several accepted forms |
| `src/casegate/scorers/exact.py:59` | the reply is cut to 80 chars before rendering | a long reply would fill the reason cell |

## Trade-off
Fuzzy matching (edit distance) accepts near misses, but its threshold is hard to explain and hides real changes. `exact` stays binary; `contains` and the judge cover looser checks.

## Failure modes
`tests/scorers/test_exact.py:20` `test_any_of_list_and_fail_reason`, `tests/scorers/test_exact.py:31` `test_normalise_false_is_case_sensitive`, `tests/scorers/test_exact.py:51` `test_expected_answer_wrong_type_gives_one_line_per_union_member`.

## What I would change
Show a short diff in the reason instead of the full expected and actual text. Cost: about 10 lines with `difflib`.

## 10-minute version
`check` and `score` share `resolve_answers`, so a case that loads can always score (`src/casegate/scorers/exact.py:48-49`). `score` raises `ValueError` only when it is built without `check`; the runner turns that into an `error` (`src/casegate/runner.py:176-178`).
