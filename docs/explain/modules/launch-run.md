# film scene 2: the run (`launch/film/compositions/run.html`, 117 lines)

**30 seconds:** Film seconds 8.5 to 18.5. It shows `casegate run evals --repeat 5` on the regression: 15 case ticks grow one by one, two turn red, and the pass rate lands at 0.853 against 0.973. It turns "the agent got worse" into one measured number.

**2 minutes:** The command line and the HUD show the real suite, case count, repeats, target and judge (`launch/film/compositions/run.html:39-40`). The script holds the 15 cases of `docs/assets/demo-pr-regression/casegate-run.json` in order, each with its tick height `8 + round(36 × mean_score)` and a flip flag (`launch/film/compositions/run.html:57-63`). The ticks are drawn at 5× scale, 0.2 s apart from 0.9 s (`launch/film/compositions/run.html:64-71`). Two call-outs sit over the flipped ticks with leader lines (`launch/film/compositions/run.html:73-82`). Each tick grows with an 8% stretch, then settles (`launch/film/compositions/run.html:87-92`). A case label follows the growing tick, as a function of time only (`launch/film/compositions/run.html:94-101`). At 4.4 s the two flipped ticks turn red and the call-outs draw (`launch/film/compositions/run.html:103-105`). The numbers land from 5.4 s: 0.973, the arrow, 0.853 with a squash, then −0.120 and the limit 0.08 (`launch/film/compositions/run.html:107-113`). A horizontal whip ends the scene (`launch/film/compositions/run.html:115`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `launch/film/compositions/run.html:57-63` | `CASES` with heights and flips | the same rule as the site tick row (`docs/DESIGN.md` §8), so the film and the site show the same ticks |
| `launch/film/compositions/run.html:64` | `T0 = 0.9`, `STEP = 0.2` | the tick sounds in `launch/film/index.html:29-43` use the same times (8.5 + 0.9 + 0.2k) |
| `launch/film/compositions/run.html:97-101` | the label is set in `onUpdate` from `proxy.t` | a seek to any frame gives the same label; a counter would break on a seek |
| `launch/film/compositions/run.html:103` | the flips turn red last | DESIGN §4: fail colour arrives after the row is complete |

## Trade-off
Hard-coded heights, not a fetch of the run JSON. The scene must render the same on every seek with no network for data. The cost: if the demo run file changes, the array must be edited by hand.

## Failure modes
The heights are copied by hand from `casegate.compare` output on the demo pair; no test compares them with `docs/assets/demo-pr-regression/casegate-run.json`. The call-out text "0/5" and "1/5" comes from `casegate gate` on the same pair (launch/SPEC.md table).

## What I would change
Generate the `CASES` array with the same `uv run python -c` command the site uses (`site/index.html:33-41`), and diff it in the real-world-test. Cost: one more command to keep.

## 10-minute version
Values on screen and their source: pass rate 0.973 → 0.853, −0.120, limit 0.08 (`docs/assets/demo-pr-regression/casegate-run.json` `summary.pass_rate`, `docs/assets/demo-pr-regression/baseline.json` `summary.pass_rate`, `evals/tolerance.json` `max_drop`). The telemetry "run 21f0f61" is the commit in the run file. The scene comes in from below to match the whip of the diff scene, and leaves to the left so the gate scene can come in from the right (`launch/film/compositions/gate.html:169`).
