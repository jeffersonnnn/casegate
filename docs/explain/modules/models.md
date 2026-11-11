# models (`src/casegate/models.py`, 182 lines)

**30 seconds:** The shapes that every other module agrees on: the suite config, a case, a target output, a score and the run result. A run is written to JSON and read back later by compare, gate and calibrate, so the models reject unknown fields and must round-trip exactly.

**2 minutes:** `_Strict` at `src/casegate/models.py:19-20` `_Strict` sets `extra="forbid"` once, and almost every model inherits it. `Output` at `src/casegate/models.py:35-43` `Output` is what a target returns: text, tool calls, citations, final state, tokens, cost and latency. `Score` at `src/casegate/models.py:46-54` `Score` is one scorer's verdict with its threshold and reason. `ScorerConfig` at `src/casegate/models.py:57-62` `ScorerConfig` is the one model that allows extra keys, because each scorer validates its own params. `TargetConfig` at `src/casegate/models.py:74-90` `TargetConfig` checks that a python target has a `module:function` path and an http target has a URL. `Suite` at `src/casegate/models.py:110-119` `Suite` holds the defaults (concurrency 8, threshold 0.7, 4 tries). The result side nests `RepeatResult` in `CaseResult` in `Run`, with `RunSummary` for the totals (`src/casegate/models.py:125-182` `Run`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/models.py:19-20` | `extra="forbid"` on a shared base | a typo in a case file or a run file fails loudly, not silently |
| `src/casegate/models.py:42` | `cost_usd: float \| None` | None means "unknown price", which must never be summed as 0 |
| `src/casegate/models.py:79` | `version` is required on the target | it is part of every output cache key (`docs/adr/0005-two-caches.md`) |
| `src/casegate/models.py:83-90` | the validator raises only `ValueError` | pydantic wraps it in `ValidationError`, which the loader collects with the other errors |
| `src/casegate/models.py:122` | `Status = Literal["pass", "fail", "error"]` | error is a third state, not a fail (`docs/adr/0003-errors-are-not-failures.md`) |
| `src/casegate/models.py:134-136` | `cost_usd_full` beside `cost_usd` | the report can show what the cache saved |
| `src/casegate/models.py:169` | `schema_version: Literal[1]` | an old casegate refuses a newer run file instead of misreading it |

## Trade-off
Dataclasses or TypedDicts have no dependency. pydantic gives validation with clear error paths, JSON round-trip and a JSON schema for free. The cost is a heavy dependency and pydantic-specific rules (for example, only `ValueError` inside validators).

## Failure modes
A field added to `Run` without a default breaks every old baseline file. `tests/test_models.py:81` `test_run_round_trip` proves a full run survives dump and load. `tests/test_models.py:108` `test_extra_fields_rejected` and `tests/test_models.py:113` `test_run_extra_field_rejected` prove unknown fields fail. `tests/test_models.py:136` `test_target_python_path_required` and `tests/test_models.py:144` `test_target_http_url_required` guard the target checks. `tests/test_models.py:151` `test_suite_defaults` pins the defaults from SPEC §2.

## What I would change
Split config models (Suite, TargetConfig, JudgeConfig) from result models (Run and below) into two files when the file nears 250 lines. Cost: one more import path to learn.

## 10-minute version
`pass_rate` and `mean_score` are `float | None` because a case whose repeats all errored has no score. `RunSummary.pass_rate_std` and `per_repeat_pass_rate` carry the run-to-run variance that the gate tolerance comes from (`docs/adr/0006-gate-tolerance-from-measured-variance.md`). `JudgeConfig.samples` allows 1 to 9 (`src/casegate/models.py:100` `samples`); odd numbers give a clean median. The loader (M1) fills `Case.source_file` and `Suite.root`, so error messages can name the file.
