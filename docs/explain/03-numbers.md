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
| Judge agreement and kappa | [TBD: not measured in M3; needs `evals/labels.csv` with 40 human labels (OPEN-5, a human step), then the command writes `evals/calibration.json`] | evals/calibration.json | `casegate calibrate --labels evals/labels.csv --run evals/baseline.json --format json` | 40 labels | one labeller |
| Runtime at concurrency 8 | 51.5 s | evals/baseline.json | field `summary.duration_s` = 51.51832654100144 | 15 × 5 | one local run on a laptop; network-bound |
| One-repeat re-run on a warm cache (M3 real-world-test) | pass rate 0.933, 15/15 outputs and 16/16 judge cached, cost $0.00 this run, $0.04 full | docs/assets/runs/rerun-repeat1-m3-toy-agent@5.md (archived copy of results/latest.md) | header line "pass rate 0.933", Summary rows "cache", "cost this run", "cost full"; `casegate run evals --repeat 1` twice with the same `CASEGATE_CACHE_DIR` | 15 × 1 | one repeat: one flip moves the rate 0.067; the run file of the cold first run was not kept |
| Size of the library | 3,974 lines in 31 files | src/casegate | `python -c "import glob; fs=glob.glob('src/casegate/**/*.py', recursive=True); print(len(fs), sum(len(open(f).read().splitlines()) for f in fs))"` after M3 | all of `src/casegate/` | counts blank lines, docstrings and comments; the toy agent in `examples/` is not counted; no measured comparison with promptfoo or deepeval |
| Terminal recording for the site (M4) | pass rate 1.000, 0 errors, cost $0.043, cache 0/15 outputs and 0/18 judge, 14.5 s | docs/assets/runs/term-run-toy-agent@5.json (archived copy of results/20261112T102254Z-6f5d06b.json) | `casegate run evals --repeat 1 --plain` with `.env` loaded, M4 site task; fields `summary.pass_rate` = 1.0, `summary.n_error_repeats`, `summary.cost_usd` = 0.0430238, `summary.cache_output_hits`/`cache_output_total`, `summary.cache_judge_hits`/`cache_judge_total`, `summary.duration_s` = 14.494952916997136 | 15 × 1 | one repeat on a cold cache; shown in `docs/assets/term-run.txt` |
| Demo PR gate, push 1 (shown in `term-gate.txt` and on the site) | pass rate 0.973 to 0.853 (drop 0.120, limit 0.08), std 0.056, 0 error repeats, cost $0.196 | docs/assets/demo-pr-regression/casegate-run.json | fields `summary.pass_rate` = 0.8533333333333334, `summary.pass_rate_std` = 0.05577733510227169, `summary.n_error_repeats`, `summary.cost_usd` = 0.19617489999999999; baseline `summary.pass_rate` = 0.9733333333333333 from `docs/assets/demo-pr-regression/baseline.json` | 15 × 5 | `toy-agent@6-cents`, a code regression on purpose; 2 flips and `refund-over-cap-adv` 4/5 come from `casegate gate` on this pair |
| Site accessibility, Lighthouse 12.8.2 (M4) | 100 on mobile and on desktop | docs/assets/runs/lighthouse-local-mobile-m4.json | field `categories.accessibility.score` = 1 in the mobile file and in `docs/assets/runs/lighthouse-local-desktop-m4.json`; `--only-categories=accessibility` against `http://127.0.0.1:8765/` | 1 page, 2 form factors | a local server, not the deployed URL: Pages is not on yet (M4 human step) |
| Light banner contrast on `#F4F7F5` | text 17.88:1, grey 4.99:1, fail 4.95:1, arm 3.83:1 (graphic) | scripts/contrast.py | `python3 scripts/contrast.py` (exit 0), rows "light §7"; the same values are in `docs/DESIGN.md` §7 | 5 light pairs | computed, not measured on a screen; the grey holds only at opacity 1 |
| Dark palette contrast (lowest pairs) | fail on surface 5.86:1, muted on surface 6.61:1; text on bg 16.00:1 | scripts/contrast.py | `python3 scripts/contrast.py`, rows "dark §1" | 10 dark pairs | every dark text pair is at least 4.5:1 |
| Launch film, measured (M5) | 1920 × 1080, 30 fps, 1350 frames, 45.000000 s, H.264 High yuv420p, AAC LC 48 kHz stereo, no decode error | docs/assets/runs/launch-assets-m5.json | `files."launch-film.mp4".probe` (ffprobe `format.duration`, `streams[].width/height/r_frame_rate/nb_frames`) and `decode_errors` = "" (`ffmpeg -v error -f null`); commands in the file's `commands` | 1 file | target 45.0 s ±0.1 (BUILD.md M5); the file lives in `~/Desktop/casegate-launch-assets/`, not in git |
| Launch cut, measured (M5) | 1080 × 1920, 30 fps, 600 frames, 20.000000 s, H.264 High yuv420p, AAC LC 48 kHz stereo, no decode error | docs/assets/runs/launch-assets-m5.json | `files."launch-cut.mp4".probe`, `decode_errors` | 1 file | target 20.0 s ±0.1 |
| Launch video loudness | film −14.2 LUFS, true peak −1.0 dBTP; cut −13.1 LUFS, true peak −1.1 dBTP | docs/assets/runs/launch-assets-m5.json | fields `integrated_lufs`, `true_peak_dbfs` per file (`ffmpeg -af ebur128=peak=true`, Summary I and Peak) | 2 files | target −14 LUFS ±1 and ≤ −1 dBTP (launch/SPEC.md); the cut is 0.1 LU inside the upper bound |
| Sound sync on the arm drop | 0 frames: film thud peak 20.6336 s = frame 619.01, cut 2.5006 s = frame 75.02 | launch/REVIEW.md | table "Sync": the largest sample in the window, on the delivered files | 2 drops | measured, not heard; the click lands one frame after PASSED on purpose (frame 880.35, 351.35) |
| Logo and X banner stills (M5) | logo PNG 1000 × 1000; logo GIF 1000 × 1000, 130 frames at 25 fps, loops forever, 956,615 bytes; banner PNG 4500 × 1500; banner GIF 4500 × 1500, 130 frames at 25 fps, loops forever, 924,747 bytes | docs/assets/runs/launch-assets-m5.json | `pixelWidth`/`pixelHeight` (sips), `probe.streams[0]` (ffprobe), `netscape_loop_count` = 0, `bytes` | 4 files | 130 frames at 25 fps = one 5.2 s cycle; each GIF under the 15 MB limit (BUILD.md M5) |

## Reproduce

```bash
set -a; . ./.env; set +a
CASEGATE_CACHE_DIR=$(mktemp -d) casegate run evals --repeat 5 --out /tmp/cg-baseline.json   # about $0.19
casegate report /tmp/cg-baseline.json --format json   # the summary fields above
casegate gate --baseline evals/baseline.json --run evals/baseline.json; echo $?   # 0
```

M4 checks:

```bash
python3 scripts/contrast.py; echo $?   # the contrast rows, 0
uv run casegate gate --baseline docs/assets/demo-pr-regression/baseline.json --run docs/assets/demo-pr-regression/casegate-run.json --max-drop 0.08 --plain; echo $?   # 1, term-gate.txt
npx lighthouse@12 <url> --only-categories=accessibility --output=json --chrome-flags="--headless=new"   # docs/DESIGN.md §8
```

M5 checks (the launch files are in `~/Desktop/casegate-launch-assets/`):

```bash
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate,nb_frames -of json ~/Desktop/casegate-launch-assets/launch-film.mp4
ffmpeg -nostats -i ~/Desktop/casegate-launch-assets/launch-film.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12   # I and Peak
sips -g pixelWidth -g pixelHeight ~/Desktop/casegate-launch-assets/logo-1000.png
```

A new run gives new values, because the target and the judge are not deterministic. The numbers above are from the committed `evals/baseline.json`.
