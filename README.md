# casegate

A small Python library and CLI that runs labelled cases against any LLM system, scores them, compares the run with a baseline and fails the build on regression.

> **Work in progress (2026-11-11).** The core works: `casegate run`, `compare`, `gate` and `report`, with an LLM judge and a measured baseline (milestones M0-M2). The GitHub Action, judge calibration and the PyPI release come next (M3). This README is still the builder's entry point; M3 replaces it with the public README described in `SPEC.md` §19.

## Reading order

1. `README.md` (this file): premise, status, layout.
2. `SPEC.md`: the authoritative implementation spec. Wins on any conflict.
3. `BUILD.md`: milestones M0–M5, done-criteria, human-only steps, cost.
4. `CONTEXT.md`: the glossary. Use these words in code and docs.
5. `FACTS.md`: observed facts: versions, prices, API behaviour, CI pins, OPEN items.
6. `docs/DESIGN.md`: the look (tokens, type, logo, motion, terminal theme, site).
7. `docs/adr/` (index in `DECISIONS.md`): the hard-to-reverse decisions.
8. `PLAN.md`: the why, scope and architecture in one page.
9. `workflows/README.md`: how to run each milestone's pre-written workflow.

## Status

| Item | State |
|---|---|
| Design grilled to settled | done (4 rounds, 2026-11-11) |
| Load-bearing API behaviour observed | done (FACTS §4) |
| Doc set | written |
| UI direction | A "Lab instrument" chosen from 3 live options |
| Cold-build audit | round 1: 105 findings, 100 applied, 5 settled later by the user; round 2: 101 findings, 100 applied, 1 settled later by the user (one demo PR, two pushes); round 3: 21 findings, all applied (`docs/audit/README.md`) |
| M0–M2 | done (core, judge, gate, toy agent, baseline) |
| M3–M5 | not started |

## Results (draft, M2, measured 2026-11-11)

Numbers come from `evals/baseline.json` and `evals/tolerance.json` (SPEC §19b). M3 moves them into the public README.

| Item | Value | Source |
|---|---|---|
| Example suite pass rate, mean of 5 repeats | 0.973 (15 cases, toy-agent@5, `claude-haiku-5-5`, judge `claude-sonnet-5-5`) | `evals/baseline.json` `summary.pass_rate` |
| Std across repeats | 0.037 | `summary.pass_rate_std` |
| Gate tolerance | `max_drop` 0.08 = `max(0.02, ceil(round(2*std*100, 6))/100)` | `evals/tolerance.json` |
| Cost of one full run (15 × 5) | $0.19 | `summary.cost_usd_full` |

The toy-agent@5 prompt fix (one policy claim per cited sentence) replaced the toy-agent@2 baseline (pass rate 0.867, std 0.067, `max_drop` 0.14; `docs/assets/runs/baseline-toy-agent@2.json`). See FACTS.md §8.

## Repository layout (now)

```
README.md PLAN.md SPEC.md BUILD.md CONTEXT.md FACTS.md DECISIONS.md .env.example .gitignore
docs/adr/0001..0008-*.md
docs/DESIGN.md
docs/design/options/   build.py, option-a/b/c.html, index.html (live design options)
docs/research/         github-actions-and-pypi.md, design-references.md
docs/audit/            round1.json, round2.json, round3.json (cold-build audit findings) + README.md (what was applied)
scripts/derisk_claude.py   Phase 2 observation script (real API calls)
workflows/             m0..m5 workflow scripts + README (run order)
```

The target layout after the build is in `SPEC.md` §1.

## Environment

Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`. Load it with `set -a; . ./.env; set +a`. The repo is its own git repo; never run git from the home folder.
