# Pitch

## 30 seconds

casegate is a small Python library, CLI and GitHub Action for LLM evals. It runs labelled cases against any LLM system, scores both the answer and the tool calls, compares the run with a committed baseline, and fails the pull request when quality drops. One measured result: the example suite passes at 0.973 ± 0.037 over 5 repeats (`evals/baseline.json` `summary.pass_rate`, `summary.pass_rate_std`). What I learned: an LLM judge is not deterministic, so the gate tolerance must come from measured variance.

## 2 minutes

- **Problem:** a prompt or model change can make an agent worse, and nobody sees it until users do. Final-answer checks miss agents that say the right words but call the wrong tools.
- **What it does:** you write cases in YAML (input, expected tools, expected state, expected text). casegate runs them against your system through a Python or HTTP adapter, with concurrency, retries and caching.
- **How:** seven scorers, from exact match to tool-trajectory matching to an LLM judge with a strict rubric. A case passes only when every scorer passes. Runs are saved as JSON; `compare` lists the cases that flipped; `gate` exits 1 on a drop larger than the tolerance or on any failed must-pass case, and the Action posts one sticky comment on the pull request.
- **Result:** on 15 cases × 5 repeats the pass rate is 0.973 with a std of 0.037, so the gate tolerance is 0.08; one cold run costs $0.19 and a cached re-run costs $0.00 (`evals/baseline.json` `summary`, `evals/tolerance.json` `max_drop`, FACTS.md §8). Judge agreement and kappa: [TBD: `evals/calibration.json`, needs 40 human labels, OPEN-5].
- **What I learned:** in the first real test the judge gave 0.8 to a reply that only offered a conditional refund (FACTS.md §4.2). That is why the judge prompt is strict and why calibration against human labels is part of the tool.

## 10 minutes

1. **Architecture (2 min):** draw the diagram in `06-diagrams.md`: cases in, the runner with two caches, the run JSON, then the three readers of a run: report, compare and gate, calibrate.
2. **One request (4 min):** walk `01-tour.md`, stops 1 to 14 for `casegate run` and `gate`, then stops 15 and 16 for CI: the sticky comment edited in place (`action.yml:128-146`) and the baseline read from the base branch (`.github/workflows/eval-gate.yml:51-56`).
3. **Trajectory over final answer (1 min):** an agent can say the right words without the lookup; `tool_trajectory` and `state_match` catch it (`05-drill.md` question 25).
4. **Tolerance from variance (1 min):** the std across 5 repeats is 0.037, so `max_drop` is 0.08, not a picked 0.03 (`evals/baseline.json` `summary.pass_rate_std`, `evals/tolerance.json` `max_drop`).
5. **The judge disagreement (1 min):** the judge passed a hedged reply (FACTS.md §4.2); the prompt fix, and `calibrate` to measure agreement with a person (`01-tour.md` stop 17). The real kappa is [TBD: `evals/calibration.json`, OPEN-5].
6. **Limits (1 min):** no deterministic judge, a tolerance and not a statistical test, one labeller, and a same-repo PR can edit its own workflow (README Limitations).

## Resume bullets (fill only with measured numbers)

- Wrote an open-source eval harness (YAML cases, 7 scorers including an LLM judge and tool-trajectory matching, baseline comparison) that gates pull requests on a regression threshold measured from run-to-run variance (max drop 0.08, `evals/tolerance.json`).
- Calibrated the LLM judge against [TBD: n from evals/calibration.json] human labels, reaching [TBD: agreement and kappa] agreement, and reported run-to-run variance across 5 repeats (`evals/baseline.json` `repeat`).
- Used it across [TBD: number of projects] projects to track [TBD: total cases] labelled cases.
