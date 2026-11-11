# citation_support (`src/casegate/scorers/citation_support.py`, 90 lines)

**30 seconds:** The `citation_support` scorer checks that each cited passage supports the claim that cites it. A reply can cite [P1] for a sentence that P1 never says. The judge sees each citation alone, with only the claim and the passage, so one bad citation is named in the reason and not hidden in an overall grade (SPEC §5.6).

**2 minutes:** The system prompt is short and strict: supported means the passage states or directly implies the claim (`src/casegate/scorers/citation_support.py:21-24` `CITATION_SYSTEM`). `citation_prompt` puts the claim and the passage in tagged blocks (`src/casegate/scorers/citation_support.py:33-38` `citation_prompt`). `score` at `src/casegate/scorers/citation_support.py:49-84` `score` first fails with no judge call when there are fewer citations than `min_citations` (`src/casegate/scorers/citation_support.py:52-55`). Then it grades each citation k times (`src/casegate/scorers/citation_support.py:59-74`). A citation is supported when more than half of the votes say so; a tie is unsupported (`src/casegate/scorers/citation_support.py:75`). The value is the fraction of supported citations (`src/casegate/scorers/citation_support.py:78`). On a fail, the reason names the first unsupported source id with the judge's reasoning (`src/casegate/scorers/citation_support.py:81-83`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/citation_support.py:29` | `min_citations` defaults to 1 | a policy answer with no citation is a fail, not a free pass |
| `src/casegate/scorers/citation_support.py:52-55` | too few citations fails before any judge call | a sure fail costs nothing |
| `src/casegate/scorers/citation_support.py:75` | a tie is unsupported | when the judge is unsure, the citation does not count |
| `src/casegate/scorers/citation_support.py:81-83` | the reason names the source id | a reviewer sees which citation broke without opening the run JSON |

## Trade-off
One judge call on the whole reply would cost less. One call per citation costs more (4 to 6 calls for a policy answer in the baseline) but gives a per-citation verdict and a clear reason. The judge never sees the rest of the reply, so it cannot be talked into "supported" by the context.

## Failure modes
The prompt is exact and the system text is fixed (`tests/scorers/test_citation_support.py:76` `test_prompt_is_exact_and_system_is_fixed`). The fail reason names the first unsupported citation (`tests/scorers/test_citation_support.py:106` `test_fail_reason_names_the_first_unsupported_citation`). Majority vote and the tie rule (`tests/scorers/test_citation_support.py:125` `test_majority_of_samples_and_tie_is_unsupported`). Too few citations fails without a call (`tests/scorers/test_citation_support.py:141` `test_too_few_citations_fails_without_a_judge_call`). The cache serves a second run (`tests/scorers/test_citation_support.py:162` `test_cache_serves_the_second_run`).

## What I would change
The claim is the whole sentence that holds the marker (`examples/toy_agent/agent.py:88-110` `extract_citations`). A sentence with two markers then gives two citations with the same two-part claim, and each is graded against one passage. That is the cause of every baseline fail (`04-failures.md`). I would give the judge all the passages a sentence cites in one call, or split the claim at each marker. Cost: a new prompt (all grades re-run once) and a rule for which part of the sentence each marker covers.

## 10-minute version
The claim, quote and source id come from the target's `Output.citations`; casegate does not extract them. The toy agent builds them from `[Pn]` markers. The citation key has no repeat index, so the same claim and passage in two repeats share one grade, even on a fresh cache (`modules/cache.md`). Baseline (toy-agent@5): by tag `citations` 0.9 (`evals/baseline.json` `summary.by_tag.citations`), with case pass rates 0.8, 1.0, 1.0 and 0.8 for `policy-window-10` to `policy-giftcard-13`. On toy-agent@2 it was 0.5, with 0.8, 0.2, 0.6 and 0.4 (`docs/assets/runs/baseline-toy-agent@2.json`).
