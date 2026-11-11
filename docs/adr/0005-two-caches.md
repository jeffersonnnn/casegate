# 0005 Separate caches for target outputs and judge results

Status: accepted (2026-11-11)

## Context
The brief keys one disk cache on case content, target version and model name. A rubric edit would then re-run the target too, which costs money and adds noise.

## Decision
Keep two content-addressed caches under `.casegate/cache/`: `outputs/` keyed by case input, target version, target model and repeat index; `judge/` keyed by scorer config, the graded Output content and judge model. `--no-cache` skips reads and writes.

## Why
A rubric change re-grades the same outputs, so a judge change is measured apart from a target change.

## Consequences
The repeat index is in the output key, so `--repeat 5` makes 5 real target calls on the first run and 0 on a re-run.

## Amendment (2026-11-11, cold-build audit round 1)
The judge key is the full judge request (system prompt, user prompt, schema, provider, model, effort, max_tokens) plus the sample index, not "scorer config". A change of effort or provider for the same model name must re-grade, not reuse old grades. Exact key object: SPEC §8.
