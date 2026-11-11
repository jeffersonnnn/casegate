# Numbers

Only measured numbers. A value not yet measured is `[TBD: ...]`. Values are rounded for speech; the source field holds the full value.

| Metric | Value | Source | How measured | Sample | Caveat |
|---|---|---|---|---|---|
| Toy agent cost for one case (Phase 2) | $0.00049 | FACTS.md | `python -I scripts/derisk_claude.py` (2 turns, Haiku 5.5, effort low) | 1 case | before the toy agent was built; prompt differs |
| Judge cost per call (Phase 2) | $0.00213 | FACTS.md | 3 Sonnet 5.5 calls, mean of usage × price | 3 calls | short reply; longer replies cost more |
| Judge scores on one reply (Phase 2) | 0.8, 0.85, 0.8 | FACTS.md | same reply, same rubric, 3 calls | 3 calls | shows non-determinism, not a rate |
| Suite pass rate, mean of 5 repeats | 0.973 | evals/baseline.json | `CASEGATE_CACHE_DIR=$(mktemp -d) casegate run evals --repeat 5 --out evals/baseline.json` (fresh cache, never `--no-cache`, SPEC §16.3), field `summary.pass_rate` = 0.9733333333333333 | 15 cases × 5 | toy suite, toy-agent@5, judge `claude-sonnet-5-5` |
| Suite pass rate before the citation prompt fix | 0.867 | docs/assets/runs/baseline-toy-agent@2.json | the replaced toy-agent@2 baseline, field `summary.pass_rate` = 0.8666666666666667 | 15 cases × 5 | history; see 04-failures.md |
| Per-repeat suite pass rates | 1.000, 1.000, 1.000, 0.933, 0.933 | evals/baseline.json | field `summary.per_repeat_pass_rate` | 5 repeats | one case flip moves a repeat by 0.067 |
| Std across repeats | 0.037 | evals/baseline.json | field `summary.pass_rate_std` = 0.036514837167011066 (sample std, n-1) | 5 repeats | 5 points is a small sample for a std |
| Gate tolerance (max-drop) | 0.08 | evals/tolerance.json | field `max_drop`, method `max(0.02, ceil(round(2*std*100, 6))/100)` | from the baseline std | ADR 0006; re-measure when the suite or target changes; was 0.14 on toy-agent@2 |
| Error repeats in the baseline | 0 of 75 | evals/baseline.json | fields `summary.n_error_repeats`, `summary.n_repeats_total` | 75 repeats | baseline acceptance needs 0 (SPEC §16.3) |
| Adversarial pass rate | 1.0 | evals/baseline.json | field `summary.by_tag.adversarial` | 3 cases × 5 | baseline acceptance needs 1.0 |
| Citations pass rate | 0.9 | evals/baseline.json | field `summary.by_tag.citations` | 4 cases × 5 | the only failing tag group (was 0.5 on toy-agent@2); see 04-failures.md |
| Tokens in / out, one full run | 330,507 / 30,557 | evals/baseline.json | fields `summary.input_tokens`, `summary.output_tokens` | 15 × 5 | target and judge together |
| Cost of one full run | $0.193 | evals/baseline.json | field `summary.cost_usd_full` = 0.19348919999999992 | 15 × 5 | prices dated 2026-11-03 |
| Cost of the baseline run itself | $0.183 | evals/baseline.json | field `summary.cost_usd` = 0.18349919999999992 | 15 × 5 | lower than full: 7 judge cache hits |
| Judge cache hits on a fresh cache | 7 of 74 | evals/baseline.json | fields `summary.cache_judge_hits`, `summary.cache_judge_total` | 74 judge calls | the same claim and passage in two repeats share one grade |
| Re-run on the same cache | 75/75 outputs, 74/74 judge, $0.0000, 0.02 s | FACTS.md | §8 table, row "re-run check, same cache dir" (toy-agent@5) | 15 × 5 | the run file of the re-run was not kept |
| Re-run, 5 repeats, cached (latest) | 75/75 outputs, 74/74 judge, cost $0.00, full $0.19 | docs/assets/runs/rerun-latest-toy-agent@5.md (archived copy of results/latest.md) | Summary table rows "cache", "cost this run", "cost full" | 15 × 5 | rounded to cents by `fmt_money` |
| Total M2 live spend | about $0.81 | FACTS.md | §8, sum of `summary.cost_usd` of each live run | 10 runs | of the $2 budget; $0.263 of it is the toy-agent@3..@5 prompt fix |
| Judge agreement and kappa | [TBD: M3] | evals/calibration.json | `casegate calibrate --labels evals/labels.csv --run evals/baseline.json --format json` | 40 labels | one labeller |
| Runtime at concurrency 8 | 51.5 s | evals/baseline.json | field `summary.duration_s` = 51.51832654100144 | 15 × 5 | one local run on a laptop; network-bound |

## Reproduce

```bash
set -a; . ./.env; set +a
CASEGATE_CACHE_DIR=$(mktemp -d) casegate run evals --repeat 5 --out /tmp/cg-baseline.json   # about $0.19
casegate report /tmp/cg-baseline.json --format json   # the summary fields above
casegate gate --baseline evals/baseline.json --run evals/baseline.json; echo $?   # 0
```

A new run gives new values, because the target and the judge are not deterministic. The numbers above are from the committed `evals/baseline.json`.
