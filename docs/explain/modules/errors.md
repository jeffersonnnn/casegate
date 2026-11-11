# errors (`src/casegate/errors.py`, 34 lines)

**30 seconds:** The error types that the loader, targets, judges and the retry loop share. They live in one small module with no imports, so a target can raise them without importing the runner, and the retry loop can classify a failure by its type alone.

**2 minutes:** `SuiteError` at `src/casegate/errors.py:8-12` `SuiteError` takes one message or a list and keeps them all in `.errors`, because validation collects every problem first and the CLI prints them at once. `JudgeError` at `src/casegate/errors.py:15` `JudgeError` marks a judge reply that cannot be used. `RetryableError` at `src/casegate/errors.py:18-21` `RetryableError` is how user code says "try again", with an optional `retry_after` hint. `HttpStatusRetryable` at `src/casegate/errors.py:24-27` `HttpStatusRetryable` is the HTTP target's version, which keeps the status code. `RetriesExhausted` at `src/casegate/errors.py:30-34` `RetriesExhausted` wraps the last error and the number of tries, so the report can say "failed after 4 tries: HttpStatusRetryable: HTTP 503".

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/errors.py:9-12` | normalises one string or a list into `.errors` | the user sees every suite problem in one run, not one per run |
| `src/casegate/errors.py:19-21` | stores `retry_after` as a keyword-only field | the retry loop reads the server's wait hint without parsing text |
| `src/casegate/errors.py:31-34` | keeps `last` and `attempts` | the runner records the try count in `RepeatResult.attempts` |

## Trade-off
One error class with a `kind` field would be shorter. Separate classes let `isinstance` decide retry and status (an error is not a fail, `docs/adr/0003-errors-are-not-failures.md`), and mypy checks each constructor.

## Failure modes
A wrong class choice changes behaviour: a target that raises `ValueError` for a busy server gets no retry. `tests/test_retry.py:92` `test_retries_exhausted_keeps_last_error` proves the message format and the `last`/`attempts` fields.

## What I would change
Give `JudgeError` a field for the raw reply, so a report can show what the judge sent. Cost: a larger run file.

## 10-minute version
The constructors match SPEC §7.3 exactly. `SuiteError` comes from the loader (M1), `JudgeError` from the judge (M2), `RetryableError` from user targets, `HttpStatusRetryable` from the HTTP target (M1), and `RetriesExhausted` only from `with_retries` (`src/casegate/retry.py:80` `RetriesExhausted`).
