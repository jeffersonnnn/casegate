# 0008 The PR gate reads the baseline from the base branch

Status: accepted (2026-11-11, cold-build audit round 1, user decision)

## Context
`eval-gate.yml` gated a PR against `evals/baseline.json` from the PR head. A regression PR could lower the baseline in the same diff and pass its own gate.

## Decision
On `pull_request`, the workflow reads `evals/baseline.json` from `origin/<base_ref>` and passes that file to the gate. A PR that changes `evals/baseline.json` fails unless it carries the label `baseline-update`.

## Why
The gate must compare a PR with what is already merged, or it proves nothing.

## Consequences
Baseline updates are explicit, reviewed PRs with a label (the BUILD runbook already makes them from a main-branch artifact). The workflow needs `fetch-depth: 0`.
