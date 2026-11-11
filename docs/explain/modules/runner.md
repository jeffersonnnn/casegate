# runner (`src/casegate/runner.py`, 194 lines)

**30 seconds:** The runner runs every case of a suite N times against a target, scores each output and builds the `Run`. It is the one place where target calls, retries, the output cache, scorers and the concurrency limit meet. The pass-rate maths is in `stats.py`.

**2 minutes:** `run_suite` at `src/casegate/runner.py:58-130` `run_suite` builds the scorers per case (`src/casegate/runner.py:72`) and refuses to start when a scorer needs a judge and none is given (`src/casegate/runner.py:73-75`). It makes one semaphore of size C (`src/casegate/runner.py:82`) and one task per (case, repeat), all gathered at once (`src/casegate/runner.py:96`). Each task runs `_run_repeat` at `src/casegate/runner.py:133-194` `_run_repeat`: try the output cache, else call the target through `with_retries` (`src/casegate/runner.py:156-158`). A `RetriesExhausted` or any other exception becomes an `error` string with the try count (`src/casegate/runner.py:159-162`). Then each scorer runs in config order; a scorer exception stops scoring and keeps the scores so far (`src/casegate/runner.py:173-178`). The status is `error`, else `pass` when every scorer passed, else `fail` (`src/casegate/runner.py:180`). At the end the flat results are grouped per case and passed to `aggregate` (`src/casegate/runner.py:101-108`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/runner.py:81-82` | one semaphore for all tasks | C bounds all model work in flight, so a rate limit is not flooded |
| `src/casegate/runner.py:83-99` | closes the target only if it built it | a test's own target stays open for its asserts |
| `src/casegate/runner.py:140-146` | the output cache key has input, target version, model and repeat index | a new target version makes old outputs stale; the repeat index keeps N real samples (ADR 0005) |
| `src/casegate/runner.py:159-162` | target faults become `error`, not `fail` | an outage is not a regression (`docs/adr/0003-errors-are-not-failures.md`) |
| `src/casegate/runner.py:164-166` | latency is measured when the target gives 0 | a target need not time itself |
| `src/casegate/runner.py:180` | pass only when every scorer passes | a fail always names a scorer (`docs/adr/0002-case-passes-when-every-scorer-passes.md`) |
| `src/casegate/runner.py:183` | a cache hit costs 0 in `cost_usd` | the run's own cost is what was spent; `cost_usd_full` keeps the no-cache cost |

## Trade-off
A worker pool (a queue and C workers) uses less memory than one task per (case, repeat). `gather` plus a semaphore is shorter and easy to read; for 15 × 5 tasks the memory does not matter. At 10 000 tasks a bounded queue would be better.

## Failure modes
`tests/test_runner.py:89` `test_pass_fail_error_statuses`, `tests/test_runner.py:110` `test_retry_then_success`, `tests/test_runner.py:120` `test_retries_exhausted_is_error`. The concurrency cap is observed as the max tasks in flight (`tests/test_runner.py:136` `test_concurrency_limit`). A scorer exception keeps earlier scores (`tests/test_runner.py:224` `test_scorer_exception_is_error_and_keeps_scores`). A missing judge stops the run (`tests/test_runner.py:247` `test_suite_needs_a_judge`).

## What I would change
Write each finished repeat to disk as it completes, so a crash or Ctrl-C keeps partial results. Cost: a JSON-lines side file and a merge step, about 40 lines.

## 10-minute version
`gather` keeps input order, so `flat[i * repeat : (i + 1) * repeat]` is case i's repeats (`src/casegate/runner.py:101`). Progress events fire as each task ends, in finish order (`src/casegate/runner.py:91-92`). `git_sha` reads `GITHUB_SHA` first, then `git rev-parse HEAD`, and gives None outside a repo (`src/casegate/runner.py:44-55` `git_sha`). `filters` records the must-pass tags and any `--tag` filter, so the gate later knows what the run covered (`src/casegate/runner.py:109-111`). From M2 the CLI passes `Cache()` unless `--no-cache` (`src/casegate/cli.py:144`), and a judge only when a case needs one (`src/casegate/cli.py:94-97`).
