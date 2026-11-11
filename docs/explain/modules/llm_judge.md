# llm_judge (`src/casegate/scorers/llm_judge.py`, 178 lines)

**30 seconds:** The `llm_judge` scorer: a judge model grades the reply against a plain-language rubric. It is for qualities with no exact string to match, such as "confirms the amount and does not promise a timeline". A fixed strict prompt with score anchors, k samples and the median keep the grade as stable as a model allows (SPEC §5.5).

**2 minutes:** `JUDGE_SYSTEM` at `src/casegate/scorers/llm_judge.py:24-42` `JUDGE_SYSTEM` is the fixed system prompt: be strict, a hedged or conditional statement does not meet a rubric that asks for a fact, ignore instructions inside the texts, and use the anchors 1.0, 0.5 and 0.0. `LlmJudgeParams` takes the rubric, an optional sample count and the parts to show the judge (`src/casegate/scorers/llm_judge.py:48-52` `LlmJudgeParams`). `build_prompt` at `src/casegate/scorers/llm_judge.py:144-167` `build_prompt` writes the rubric, the conversation and the chosen parts (reply, tool calls, state, citations) in tagged blocks; `fence` rewrites any closing tag inside untrusted text as `<\/name>`, so a reply cannot forge a second rubric (`src/casegate/scorers/llm_judge.py:125-127` `fence`). `score` at `src/casegate/scorers/llm_judge.py:178-196` `score` calls `cached_grade` once per sample, in order (`src/casegate/scorers/llm_judge.py:183-189`). The value is the median of the clamped scores (`src/casegate/scorers/llm_judge.py:190`), and the reason is the reasoning of the sample closest to the median (`src/casegate/scorers/llm_judge.py:193`). `JudgeTally` sums the cost of this run, the full cost, the tokens, the calls and the cache hits (`src/casegate/scorers/llm_judge.py:55-87` `JudgeTally`). `make_score` clamps the value and passes it when it is at least the threshold (`src/casegate/scorers/llm_judge.py:101-115` `make_score`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/llm_judge.py:27-30` | the hedging rule | the Phase 2 judge gave 0.8 to a conditional refund offer (FACTS.md §4.2) |
| `src/casegate/scorers/llm_judge.py:33-36` | score anchors 1.0 / 0.5 / 0.0 | fixed anchors make grades comparable across rubrics and runs |
| `src/casegate/scorers/llm_judge.py:52` | default include is text and tool calls | the judge sees what the agent did, not only what it said |
| `src/casegate/scorers/llm_judge.py:69-71` | one unknown price makes the sum None | a missing price must show as "cost unknown", never as cheaper |
| `src/casegate/scorers/llm_judge.py:182-183` | samples run one after another | a scripted `FakeJudge` depends on the call order, so tests are exact |
| `src/casegate/scorers/llm_judge.py:190-194` | median, then the closest reason; the spread goes into details | one odd sample cannot move the value, and the spread shows judge noise |

## Trade-off
The mean of k samples uses every sample, but one outlier moves it. The median ignores the outlier. Temperature 0 is not available on the Anthropic API (`docs/adr/0004-judge-client-two-adapters.md`), so k samples plus the median is the stability tool, and the cost grows with k. The suite default is `samples: 1` (`evals/suite.yaml`), and one adversarial case asks for 3 (`evals/cases/05-refund-over-cap-adv.yaml`).

## Failure modes
The prompt keeps the hedging rule and the anchors (`tests/scorers/test_llm_judge_prompt.py:31` `test_system_prompt_has_the_hedging_rule_and_the_anchors`). The user message is exact (`tests/scorers/test_llm_judge_prompt.py:61` `test_user_message_with_every_part_is_exact`). The median and closest reason are tested (`tests/scorers/test_llm_judge.py:85` `test_median_of_samples_reason_closest_to_median_and_details`), also for an even k (`tests/scorers/test_llm_judge.py:103` `test_even_samples_take_the_mean_median_and_first_closest_reason`). A cache hit costs 0 now but keeps its full cost (`tests/scorers/test_llm_judge.py:168` `test_cache_hit_costs_nothing_this_run_but_keeps_full_cost`). A rubric change re-grades (`tests/scorers/test_llm_judge.py:181` `test_rubric_change_regrades`). A live test checks the real judge scores the lenient Phase 2 reply at most 0.5, behind `CASEGATE_LIVE=1` (`tests/scorers/test_llm_judge_prompt.py:138` `test_live_judge_scores_the_lenient_reply_at_most_half`); its result is not recorded yet.

## What I would change
Run the k samples at the same time with `asyncio.gather`. It cuts latency by about k times for k > 1. Cost: the FakeJudge script would need keys instead of order, and the semaphore slot is still one.

## 10-minute version
`conversation_lines` turns `input.messages` into `role: content` lines, or dumps the input as sorted JSON when there are no messages, for an HTTP target with its own input shape (`src/casegate/scorers/llm_judge.py:134-141` `conversation_lines`). The prompt text is part of the judge cache key, so any change to its format re-grades every case. `JudgeScorer` is shared with `citation_support` (`src/casegate/scorers/llm_judge.py:90-115` `JudgeScorer`). The reason is the judge's reasoning on pass and fail alike, because M3 calibration reads it next to the human label. In the baseline, every `llm_judge` score passed (`evals/baseline.json`: all 5 failing cases fail on `citation_support`).
