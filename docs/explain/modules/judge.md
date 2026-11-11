# judge (`src/casegate/judge.py`, 217 lines)

**30 seconds:** The judge seam: the one path a scorer takes to ask a model for a grade. Two adapters (Anthropic here, OpenAI-compatible in `judge_openai.py`) and a scripted fake sit behind one protocol. `cached_grade` puts the judge cache and the retry loop in front of all of them, so every grade is keyed, retried and costed the same way (`docs/adr/0004-judge-client-two-adapters.md`).

**2 minutes:** The two verdict types are `Verdict` (reasoning, score) and `CitationVerdict` (reasoning, supported), both with `extra="forbid"` (`src/casegate/judge.py:28-37` `CitationVerdict`). `JudgeClient` at `src/casegate/judge.py:48-55` `JudgeClient` is a Protocol with a `provider` string, `grade(system, prompt, schema, model)` and `aclose`. `build_judge` picks the adapter from the suite's `judge.provider` (`src/casegate/judge.py:58-63` `build_judge`). `resolve_judge_model` lets an environment variable override the suite's model (`src/casegate/judge.py:66-67` `resolve_judge_model`). `cached_grade` at `src/casegate/judge.py:85-134` `cached_grade` builds the key from the whole request (`src/casegate/judge.py:100-111`), returns a valid cache entry with 0 attempts (`src/casegate/judge.py:112-120`), else calls the judge through `with_retries` (`src/casegate/judge.py:121-125`) and stores the result (`src/casegate/judge.py:126-133`). `AnthropicJudge` calls `messages.parse` with a schema and an effort level, and no sampling fields (`src/casegate/judge.py:161-168`). `FakeJudge` gives scripted verdicts and costs nothing (`src/casegate/judge.py:183-214` `FakeJudge`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/judge.py:100-111` | the key holds system, prompt, schema, provider, model, effort, max_tokens and sample | a new rubric, model, provider or effort must re-grade (ADR 0005 amendment) |
| `src/casegate/judge.py:108` | effort is in the key only for Anthropic | the OpenAI adapter ignores effort, so it must not split the cache |
| `src/casegate/judge.py:70-82` | `_check_entry` validates the verdict and the counts | an old entry without `cost_usd` is a fresh grade, not an `error` repeat |
| `src/casegate/judge.py:150-153` | the key variable must be set, by name | the SDK must not fall back to another variable and bill the wrong account |
| `src/casegate/judge.py:155` | `max_retries=0` on the SDK client | casegate's retry layer owns retries and counts the attempts |
| `src/casegate/judge.py:161-168` | no `temperature`, `top_p` or `top_k` | the API returns 400 on any of them (FACTS.md §4.3, ADR 0004 amendment) |
| `src/casegate/judge.py:170-171` | a refusal or `max_tokens` stop is a `JudgeError` | a partial verdict must never become a score |
| `src/casegate/judge.py:188` | the fake has provider `fake` | its grades sit in their own cache keys and never serve a real run |

## Trade-off
litellm would give many providers at once. A small protocol with two adapters is easy to read in one sitting and controls the request shape, which matters because the Anthropic API rejects sampling fields (`docs/adr/0004-judge-client-two-adapters.md`). The cost: a new provider needs a new adapter of about 60 to 100 lines.

## Failure modes
The request shape has no sampling field (`tests/test_judge.py:94` `test_anthropic_request_shape_has_no_sampling_fields`). No verdict is a `JudgeError` (`tests/test_judge.py:124` `test_anthropic_no_verdict_is_judge_error`). A missing key names the variable (`tests/test_judge.py:130` `test_anthropic_missing_key_names_the_variable`). A miss then a hit keeps the original token counts (`tests/test_judge.py:383` `test_cached_grade_miss_then_hit_keeps_original_usage`). Each part of the request changes the key (`tests/test_judge.py:398` `test_cached_grade_key_is_the_whole_request`). Retries are counted (`tests/test_judge.py:428` `test_cached_grade_retries_and_counts_attempts`). An entry without a cost is a miss (`tests/test_judge.py:461` `test_cached_grade_entry_without_cost_is_a_miss`).

## What I would change
Send judge calls through the Message Batches API for CI runs, at half the price. Cost: a poll loop and a second code path; a run then takes minutes, not seconds.

## 10-minute version
The judge call runs inside the runner's semaphore slot of its (case, repeat) task, so C bounds target and judge calls together (`src/casegate/runner.py:81-82`). `cached_grade` returns `(result, hit, attempts)`; the scorer sums these in a `JudgeTally` (`src/casegate/scorers/llm_judge.py:55-87` `JudgeTally`). The cost of a hit is 0 in this run but keeps its original value in the full cost, so a re-run shows both "$0.00 this run" and what it would cost cold. `build_judge` imports `judge_openai` on demand, because that module imports this one back (`src/casegate/judge.py:61`).
