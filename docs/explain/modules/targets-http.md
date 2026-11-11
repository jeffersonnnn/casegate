# targets/http (`src/casegate/targets/http.py`, 54 lines)

**30 seconds:** A target that POSTs each case to an HTTP service. It lets a team eval an agent written in any language, or a deployed one. The status code decides retries: 429 and 5xx are passing faults, other 4xx are bugs.

**2 minutes:** `HttpTarget.run` at `src/casegate/targets/http.py:27-39` `run` opens an `httpx.AsyncClient` on the first call (`src/casegate/targets/http.py:28-29`). It posts `{"case_id", "input"}` with the expanded headers. A 429 or 5xx raises `HttpStatusRetryable` with the `retry-after` seconds (`src/casegate/targets/http.py:34-35`). Another non-2xx raises `RuntimeError` with the first 200 chars of the body. A 2xx body is parsed as an `Output` (`src/casegate/targets/http.py:39`). `_retry_after_seconds` at `src/casegate/targets/http.py:47-54` `_retry_after_seconds` reads seconds and gives None for an HTTP date.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/targets/http.py:28-29` | the client opens on the first call | building the target to validate it costs nothing and leaves nothing to close |
| `src/casegate/targets/http.py:34-35` | 429 and 5xx raise a retryable error | rate limits and overload pass; a retry is the right answer |
| `src/casegate/targets/http.py:36-37` | other 4xx raise `RuntimeError` | a 400 is a bug; a retry only wastes time |
| `src/casegate/targets/http.py:38-39` | a malformed body is not retried | the same bad body would come back |
| `src/casegate/targets/http.py:53-54` | an HTTP date gives None | the retry loop falls back to backoff; date parsing is not worth the code |

## Trade-off
`requests` is simpler but blocks the event loop. `httpx` is async and `respx` mocks it in tests. One shared client per target reuses connections across cases.

## Failure modes
`tests/test_targets.py:164` `test_http_429_retry_after_then_success`, `tests/test_targets.py:211` `test_http_500_is_retried_until_exhausted`, `tests/test_targets.py:223` `test_http_400_is_not_retried`, `tests/test_targets.py:234` `test_http_2xx_bad_body_is_an_error`. The lazy client and its close are proved by `tests/test_targets.py:258` `test_http_client_is_lazy_and_closed`.

## What I would change
Read the HTTP-date form of `retry-after` too, with `email.utils.parsedate_to_datetime`. Cost: about 6 lines; few APIs send dates.

## 10-minute version
The request body is fixed: `case_id` and `input`. The response must be an `Output` JSON with no extra fields (`src/casegate/models.py:19-20` `_Strict`), so a service that adds a field fails loudly. The timeout is per request (default 60 s, `src/casegate/targets/http.py:17`).
