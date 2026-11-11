# 0006 Set the gate tolerance from measured run-to-run variance

Status: accepted (2026-11-11)

## Context
The toy suite has 15 cases. With 1 repeat, one flipped case moves the pass rate by 6.7 points, so the brief's `--max-drop 0.03` fails on any single flip, including noise. Options: keep 0.03 with repeats, set the tolerance from data, or add a statistical test.

## Decision
CI runs the suite with `--repeat 5`. The tolerance is measured: run the baseline 5 times, take the standard deviation of the suite pass rate, and set `--max-drop` to 2 times that value (rounded up to the next 0.01). README states the number and the method. Must-pass cases must pass in every repeat.

## Why
It answers "how did you choose the tolerance?" with a measured number, and it needs no extra statistics code.

## Consequences
The tolerance must be re-measured when the suite or the target changes a lot. A statistical test stays out of scope.

## Amendment (2026-11-11, SPEC §16.3)
The tolerance has a floor of 0.02: max_drop = max(0.02, ceil(round(2*std*100, 6))/100). A std of 0 must not give a zero tolerance.
