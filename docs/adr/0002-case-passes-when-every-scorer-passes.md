# 0002 A case passes only when every scorer passes

Status: accepted (2026-11-11)

## Context
A case lists several scorers. The alternative was a weighted mean of scorer values compared with a suite threshold.

## Decision
A case repeat passes only when every one of its scorers passes. The case score is the mean of its scorer values and is for reports only. The suite `threshold` is the default threshold for any scorer without its own.

## Why
A failed case always has at least one concrete failed scorer with a reason. Weights hide a broken tool trajectory behind a good judge score.

## Consequences
Adding a scorer to a case can only make it harder to pass. Reports show the failing scorer first.

## Amendment (2026-11-11, SPEC §5.1)
"The suite threshold is the default for any scorer without its own" is narrowed: the suite `threshold` is the default only for judge scorers (`llm_judge`, `citation_support`). Deterministic scorers default to 1.0, so a `contains` scorer with 2 of 3 strings present fails unless the case sets a lower threshold.
