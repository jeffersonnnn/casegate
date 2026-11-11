# targets (`src/casegate/targets/__init__.py`, 72 lines)

**30 seconds:** The one seam between casegate and the system under test. The `Target` protocol has two methods, `run` and `aclose`, so the runner treats a Python function and an HTTP service the same. `build_target` checks the config and turns every problem into a `SuiteError` line.

**2 minutes:** The protocol is at `src/casegate/targets/__init__.py:26-29` `Target`. `build_target` at `src/casegate/targets/__init__.py:32-36` `build_target` picks the adapter from `cfg.type`. For a Python target, `_resolve_function` at `src/casegate/targets/__init__.py:39-53` `_resolve_function` imports the module, finds the attribute and requires an async function. Any import fault, even `SystemExit`, becomes one line (`src/casegate/targets/__init__.py:43-47`). For an HTTP target, `_expand_headers` at `src/casegate/targets/__init__.py:56-72` `_expand_headers` replaces `${NAME}` with the environment value and lists every missing variable.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/targets/__init__.py:26-29` | a Protocol, not a base class | a user's target needs no casegate import to fit |
| `src/casegate/targets/__init__.py:43` | catches `Exception` and `SystemExit` at import | a user module can fail in any way; the loader must still list it |
| `src/casegate/targets/__init__.py:51-52` | rejects a sync function | the runner awaits every call; a sync call would block the event loop |
| `src/casegate/targets/__init__.py:57` | headers expand `${NAME}` once | secrets stay out of `suite.yaml` |

## Trade-off
A plugin system (entry points) would allow more adapter types. Two built-in adapters cover in-process and any-language services, and a reader can see both in under 100 lines. A new kind of target can still be wrapped as a Python function.

## Failure modes
A missing module, a missing attribute, a sync function and a module that raises at import each give one `target.path:` line (`tests/test_targets.py:106` `test_sync_function_rejected`, `tests/test_targets.py:120` `test_missing_module`, `tests/test_targets.py:129` `test_module_that_raises_on_import_is_wrapped`). A missing header variable is proved by `tests/test_targets.py:249` `test_http_missing_env_header`.

## What I would change
Check that a Python target accepts one positional argument with `inspect.signature`, so a wrong signature is a load error, not a run error. Cost: about 5 lines and one test.

## 10-minute version
`build_target` does no network I/O, so the loader can call it only to validate (`src/casegate/loader.py:146`). The runner calls it again and owns the result, so it also closes it (`src/casegate/runner.py:83-99`). Tests pass their own `ScriptedTarget` through `run_suite(target=...)`, and the runner then does not close it.
