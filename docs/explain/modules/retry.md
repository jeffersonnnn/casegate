# retry (`src/casegate/retry.py`, 88 lines)

**30 seconds:** One shared retry wrapper for target and judge calls. It decides which errors are worth another try and how long to wait, so the runner and the judge count tries the same way, and tests replace the sleep instead of waiting.

**2 minutes:** `is_retryable` at `src/casegate/retry.py:27-44` `is_retryable` says yes to timeouts, transport faults, `RetryableError`, and the Anthropic SDK's rate-limit, connection and 5xx errors, including 529 (overloaded). `retry_after` at `src/casegate/retry.py:47-59` `retry_after` reads the server's wait hint, first from a `retry_after` attribute, then from the `retry-after` header; an HTTP date gives None and falls back to backoff. `with_retries` at `src/casegate/retry.py:62-88` `with_retries` calls the function in a loop. A non-retryable error passes through unchanged, tagged with the try count (`src/casegate/retry.py:75-78`). After the last try it raises `RetriesExhausted` (`src/casegate/retry.py:79-80`). Else it waits the server's hint capped at `max_retry_after_s`, or the backoff step plus up to 25% jitter (`src/casegate/retry.py:81-87`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/retry.py:18-22` | anthropic import is optional | the core installs without the anthropic extra |
| `src/casegate/retry.py:41-43` | 529 checked by status code | 529 has no own SDK class |
| `src/casegate/retry.py:62-68` | `sleep` and `jitter` are parameters | tests run the backoff in zero time and check the exact waits |
| `src/casegate/retry.py:74` | catches `Exception`, not `BaseException` | a cancelled task (`CancelledError`) stops at once and is never retried |
| `src/casegate/retry.py:77` | `casegate_attempts` set on the error | the runner records the try count even for a non-retryable error |
| `src/casegate/retry.py:83` | wait = min(hint, cap) | a server that asks for 120 s cannot stall the whole run |

## Trade-off
tenacity or backoff are tested libraries. A 27-line loop is easy to read in an interview, returns the try count the run file needs, and has no dependency. The cost is owning the edge cases, which the tests cover.

## Failure modes
A wrong classification either retries a real bug (wasted spend) or gives up on a passing rate limit (a false error). `tests/test_retry.py:43` `test_backoff_sequence` proves waits of 1, 2, 4. `tests/test_retry.py:92` `test_retries_exhausted_keeps_last_error` proves the last error is kept. `tests/test_retry.py:114` `test_non_retryable_after_a_retry_counts_both_tries` proves the try count. `tests/test_retry.py:124` `test_cancellation_is_not_retried` proves cancellation. `tests/test_retry.py:175` `test_anthropic_status_errors` covers 429, 5xx, 529, 400 and 404. `tests/test_retry.py:191` `test_anthropic_retry_after_header_is_capped` proves the 30 s cap.

## What I would change
Add a total time budget per call, not only a try count, so a slow server cannot use 4 full timeouts. Cost: one more config field and a clock in the tests.

## 10-minute version
The default config is 4 tries with backoff 1, 2, 4 s and a 30 s cap on server hints (`src/casegate/models.py:104-107` `RetryConfig`). Jitter spreads retries from parallel cases, which share one rate limit. The runner (M1) wraps each target call in `with_retries`, and the judge (M2) wraps each judge call, so `RepeatResult.attempts` means the same thing for both.
