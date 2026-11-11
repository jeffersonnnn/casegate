# Pitch

## 30 seconds

casegate is a small Python library, CLI and GitHub Action for LLM evals. It runs labelled cases against any LLM system, scores both the answer and the tool calls, compares the run with a committed baseline, and fails the pull request when quality drops. One measured result: the example suite passes at 0.973 ± 0.037 over 5 repeats (`evals/baseline.json` `summary.pass_rate`, `summary.pass_rate_std`). What I learned: an LLM judge is not deterministic, so the gate tolerance must come from measured variance.

## 2 minutes

- **Problem:** a prompt or model change can make an agent worse, and nobody sees it until users do. Final-answer checks miss agents that say the right words but call the wrong tools.
- **What it does:** you write cases in YAML (input, expected tools, expected state, expected text). casegate runs them against your system through a Python or HTTP adapter, with concurrency, retries and caching.
- **How:** seven scorers, from exact match to tool-trajectory matching to an LLM judge with a strict rubric. A case passes only when every scorer passes. Runs are saved as JSON; `compare` lists the cases that flipped; `gate` exits 1 on a drop larger than the tolerance or on any failed must-pass case, and the Action posts one sticky comment on the pull request.
- **Result:** on 15 cases × 5 repeats the pass rate is 0.973 with a std of 0.037, so the gate tolerance is 0.08; one cold run costs $0.19 and a cached re-run costs $0.00 (`evals/baseline.json` `summary`, `evals/tolerance.json` `max_drop`, FACTS.md §8). Judge agreement and kappa: [TBD: M3, evals/calibration.json].
- **What I learned:** in the first real test the judge gave 0.8 to a reply that only offered a conditional refund (FACTS.md §4.2). That is why the judge prompt is strict and why calibration against human labels is part of the tool.

## 10 minutes

[PLANNED: M3: walk the architecture diagram in 06-diagrams.md, then the tour in 01-tour.md, then the three talking points: trajectory over final answer, tolerance from variance, the judge disagreement.]

## Resume bullets (fill only with measured numbers)

- Wrote an open-source eval harness (YAML cases, 7 scorers including an LLM judge and tool-trajectory matching, baseline comparison) that gates pull requests on a regression threshold measured from run-to-run variance (max drop 0.08, `evals/tolerance.json`).
- Calibrated the LLM judge against [TBD: n from evals/calibration.json] human labels, reaching [TBD: agreement and kappa] agreement, and reported run-to-run variance across 5 repeats (`evals/baseline.json` `repeat`).
- Used it across [TBD: number of projects] projects to track [TBD: total cases] labelled cases.
