# targets/python (`src/casegate/targets/python.py`, 35 lines)

**30 seconds:** A target that calls an async Python function in the same process. It is the shortest path from "I have an agent function" to an eval: no server and no serialisation. A timeout bounds each call.

**2 minutes:** `PythonTarget.run` at `src/casegate/targets/python.py:25-32` `run` awaits the function under `asyncio.wait_for` with the config timeout, default 120 s (`src/casegate/targets/python.py:15`). An `Output` passes through unchanged; a dict is validated into an `Output` (`src/casegate/targets/python.py:30-31`); any other type raises `TypeError`. `aclose` does nothing, because there is no client to close (`src/casegate/targets/python.py:34-35`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/targets/python.py:26-27` | `wait_for` with a timeout | one hung case cannot stall the run; `TimeoutError` is retryable |
| `src/casegate/targets/python.py:30-31` | a dict is accepted | a user target can return plain JSON-like data with no casegate import |
| `src/casegate/targets/python.py:32` | other types raise `TypeError` | a wrong return type is a target bug, so it is an error, not a retry |

## Trade-off
Running the target in a subprocess would isolate crashes and global state. In-process is faster and needs no protocol, but a target that changes global state can affect the next case. A target must keep its state per call to stay safe under concurrency.

## Failure modes
A timeout is proved by `tests/test_targets.py:88` `test_python_timeout`. A bad dict raises a pydantic `ValidationError`, which is not retried (`tests/test_targets.py:72` `test_python_bad_dict_raises_validation_error`). Another type is proved by `tests/test_targets.py:80` `test_python_other_return_type_raises`.

## What I would change
Pass `case_id` to the function too, so a target can log it. Cost: a change to the target function signature, which breaks existing targets unless it is optional.

## 10-minute version
`asyncio.wait_for` cancels the task on timeout. A target that ignores cancellation (a blocking sync call inside an async function) is not stopped. The retry loop counts each timeout as one try (`src/casegate/retry.py:62-88` `with_retries`).
