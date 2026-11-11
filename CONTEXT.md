# casegate — glossary

Definitions only. No implementation detail. The spec is `SPEC.md`.

## Language

**Case**:
One input, its expected outcome and the scorers that judge it. A case has a unique id and zero or more tags.
_Avoid_: test, example, sample

**Suite**:
A directory of cases with shared defaults (the target, the concurrency, the judge model, the pass threshold).
_Avoid_: dataset, benchmark

**Target**:
The system under test, seen through an adapter that takes a case input and returns an Output.
_Avoid_: model, agent (an agent is one kind of system a target can wrap)

**Target version**:
A string that names one build of the target. A change to it makes cached outputs stale.

**Output**:
What a target returns for one case input: final text, tool calls, citations, reported state, tokens, cost and latency.
_Avoid_: response, completion

**Tool call**:
One call that the target made to a tool, with its name and arguments, in the order it happened.

**Trajectory**:
The ordered list of tool calls in one Output.

**State**:
The key-value facts that the target reports about its world after a case (for example, an order status).

**Scorer**:
A function that takes a case and an Output and returns a Score.
_Avoid_: metric, grader, evaluator

**Score**:
The result of one scorer on one Output: a value from 0 to 1, passed or not, a reason, and its cost.

**Threshold**:
The lowest score value that counts as passed for a scorer.

**Judge**:
A model that a scorer calls to grade an Output against a rubric. The judge is a different model from the target where possible.
_Avoid_: grader model, evaluator LLM

**Rubric**:
The plain-language rule that the judge grades an Output against.

**Repeat**:
One of N runs of the same case in one run. A case pass rate is the fraction of its repeats that passed.

**Case status**:
One of `pass`, `fail` or `error`. A case passes when every scorer passes. `error` means the target or a scorer could not finish after retries; it is not a fail.

**Pass rate**:
For a case: the fraction of its repeats that passed. For a suite: the mean of the case pass rates, with error cases left out.

**Run**:
The results of one suite at one commit, saved as one JSON file.

**Baseline**:
A committed run that later runs are compared with.

**Comparison**:
The difference between a baseline and a run: the pass-rate delta and the cases that flipped.

**Flip**:
A case that changed from pass to fail (a regression) or from fail to pass (a fix) between the baseline and a run.

**Gate**:
The check that fails a build when the pass rate drops more than the allowed amount, when too many cases error, or when a must-pass case does not pass.

**Must-pass tag**:
A tag that marks cases which must pass in every repeat for the gate to pass.

**Max drop**:
The largest fall in suite pass rate, from baseline to run, that the gate allows.

**Judge sample**:
One of k judge calls on the same Output; with k > 1 the judge score is the median and the spread is reported.

**Tolerance**:
The measured max drop: 2 times the standard deviation of the baseline suite pass rate across repeats, rounded up to the next 0.01, and at least 0.02.

**Full cost**:
What a run would have cost with nothing cached. The run's own cost counts every cache hit as 0; both are reported.

**Human label**:
A person's pass or fail verdict on one scorer result, used to calibrate the judge.

**Calibration**:
The comparison of judge verdicts with human labels, reported as agreement and Cohen's kappa.

**Agreement**:
The fraction of labelled results where the judge and the person gave the same verdict.

## Relationships

- A **Suite** holds many **Cases** and names one **Target**.
- A **Case** lists one or more **Scorers**; each gives one **Score** per **Repeat**.
- A **Run** holds every **Score** for every **Case** and **Repeat**.
- A **Comparison** takes one **Baseline** and one **Run**; the **Gate** reads the **Comparison**.
- **Calibration** joins **Human labels** to the **Scores** of one **Run**.

## Flagged ambiguities

- "pass threshold" in the original brief meant the default **Threshold** for each scorer, not a suite-level weighted score. Resolved: a case passes only when every scorer passes.
- "error" vs "fail": resolved as different **Case statuses**. Error cases leave the pass-rate denominator and are counted by the **Gate** on their own.
