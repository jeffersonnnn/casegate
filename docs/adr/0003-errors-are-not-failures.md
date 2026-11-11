# 0003 Errors leave the pass rate and have their own gate limit

Status: accepted (2026-11-11)

## Context
A case can error (timeout, rate limit, crash) after all retries. If errors count as fails, an API outage looks like a regression. If errors are ignored, an outage can pass the gate in silence.

## Decision
Error repeats are left out of the pass-rate denominator and reported on their own. `gate` has `--max-errors N` (default 0) and fails when the run has more than N error repeats. An error in a must-pass case fails the gate.

## Why
The pass rate measures quality only; the error count measures availability. Both are visible, and neither can hide the other.

## Consequences
A run where every case errors has no pass rate (`null`); `gate` fails it with the reason "no scored cases".
