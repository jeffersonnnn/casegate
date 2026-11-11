# judge_openai (`src/casegate/judge_openai.py`, 98 lines)

**30 seconds:** The judge adapter for any OpenAI-compatible `/chat/completions` endpoint: OpenAI, OpenRouter or a local server. It uses plain httpx and JSON-schema output, so the anthropic SDK stays an optional extra. It lives apart from `judge.py` only to keep each file short (SPEC §1b).

**2 minutes:** `OpenAICompatJudge` at `src/casegate/judge_openai.py:22-39` `OpenAICompatJudge` reads the key from the named variable, else `OPENAI_API_KEY`, and fails with a `SuiteError` when it is missing (`src/casegate/judge_openai.py:29-32`). The base URL comes from `base_url_env`, else OpenAI (`src/casegate/judge_openai.py:34-35`). `_post` sends the schema as a strict `json_schema` response format with `additionalProperties: false` (`src/casegate/judge_openai.py:41-58` `_post`). It sends `temperature: 0` while the endpoint accepts it. `grade` at `src/casegate/judge_openai.py:60-87` `grade` resends once without temperature when a 400 names it, and remembers that for the life of the client (`src/casegate/judge_openai.py:64-67`). A 429 or 5xx becomes `HttpStatusRetryable` with the `retry-after` seconds (`src/casegate/judge_openai.py:69-70`). Other statuses, bad JSON, a refusal or a verdict that does not match the schema are a `JudgeError` (`src/casegate/judge_openai.py:71-84`). The cost comes from the usage counts and the price table (`src/casegate/judge_openai.py:85-87`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/judge_openai.py:39` | `_send_temperature` starts True | temperature 0 helps where it is accepted (ADR 0004) |
| `src/casegate/judge_openai.py:64-67` | one resend without temperature, not a retry | some models reject the field; this is the same grade, so it must not count as an attempt |
| `src/casegate/judge_openai.py:69-70` | 429 and 5xx are retryable | the shared retry loop handles them like target errors |
| `src/casegate/judge_openai.py:78-80` | a refusal or no content is a `JudgeError` | an empty verdict must not become a 0 score |

## Trade-off
The official openai SDK would parse responses for us. httpx is already a dependency (the HTTP target uses it), so this adapter adds no new package. The cost: we parse the response shape ourselves.

## Failure modes
The request shape and result are pinned (`tests/test_judge.py:177` `test_openai_request_shape_and_result`). The temperature fallback happens once and is remembered (`tests/test_judge.py:216` `test_openai_temperature_rejected_falls_back_once_and_remembers`). Another 400 is an error with no fallback (`tests/test_judge.py:233` `test_openai_other_400_is_judge_error_without_fallback`). 429 and 5xx are retryable (`tests/test_judge.py:246` `test_openai_429_and_5xx_are_retryable`). Bad content is a `JudgeError` (`tests/test_judge.py:268` `test_openai_bad_content_is_judge_error`).

## What I would change
Detect the temperature rejection from the error code, not from the word "temperature" in the body text. Cost: a table of error codes per provider, which differ; the text check is simpler and works on the providers seen so far.

## 10-minute version
The M2 live runs used only the Anthropic adapter; this adapter is tested with a stubbed httpx client, not against a live endpoint. Its `provider` is `openai`, which goes into the judge cache key, and effort is left out of that key for it (`src/casegate/judge.py:108`). The adapter closes only a client it built (`src/casegate/judge_openai.py:89-91` `aclose`).
