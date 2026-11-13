# SPEC: casegate launch videos (M5)

Source of every rule: repo `SPEC.md`, `BUILD.md` M5, `docs/DESIGN.md` §1–§4. Storyline A in `STORYLINES.md`.

## Deliverables

| File | Canvas | Length | Project |
|---|---|---|---|
| `~/Desktop/casegate-launch-assets/launch-film.mp4` | 1920×1080, 30 fps | 45.0 s ±0.1 | `launch/film/` |
| `~/Desktop/casegate-launch-assets/launch-cut.mp4` | 1080×1920, 30 fps | 20.0 s ±0.1 | `launch/cut/` |

Both: H.264 yuv420p, AAC 48 kHz stereo, no voiceover, loudness −14 LUFS ±1, true peak ≤ −1 dBTP.

## Approved figures (each traced to a file)

| On screen | Source |
|---|---|
| diff of `examples/toy_agent/store.py`, commit "refactor: return money as integer cents from get_order" | `git show a62cf60` |
| "468 passed", lint passed | FACTS §9 ("All 468 unit tests and lint passed on it") |
| PR #1 | FACTS §9 |
| suite `toy-refund-agent`, 15 cases, repeats 5, target `toy-agent@6-cents`, judge `claude-sonnet-5-5` | `docs/assets/demo-pr-regression/casegate-run.json` |
| tick heights `8 + round(36 × mean_score)` (× 5 in the film, × 3 in the cut), flips `refund-within-cap-01` (0/5), `refund-partial-02` (1/5), `tool_trajectory` | `casegate.compare` on the demo pair (DESIGN §8) |
| pass rate 0.973 → 0.853, −0.120, limit 0.08 | demo pair, `docs/assets/term-gate.txt` |
| BLOCKED comment text | `docs/assets/demo-pr-regression/casegate-comment.md` |
| PASSED comment text (0.973 / 0.973 / 0.000, 3/3, $0.19, +$0.0053, toy-agent@7, "edited") | `docs/assets/pr-comment-passed.png` (transcribed) |
| fix commit "fix: return money in dollars from get_order again", `toy-agent@7` | `git show e4d3575`, FACTS §9 |
| "Block the pull request that makes your agent worse.", `uv add casegate` | `site/index.html` hero |

The green tick row after the fix uses the baseline heights (`docs/assets/demo-pr-regression/baseline.json`): the push-2 run JSON is not committed. It shows no number.

## Logo cycle at 30 fps

`assets/mark3d.js` is the `scripts/render_mark.html` scene with its `angleAt(t)` copied verbatim. A scene never plays the cycle free-running: it maps its frame `sf` to a cycle frame `cf`, and renders `angleAt(cf / 30)`.

| Video | Up and anticipation | Drop (first frame at or under DOWN = cycle frame 82) | Hold blocked | Lift (cycle frames 125–155) | PASSED colour (cycle frame 141) |
|---|---|---|---|---|---|
| film (gate scene starts at film frame 555) | `cf = sf + 18` | film frame **619** (20.633 s) | `cf = 90` from sf 72 | `cf = sf − 184` | film frame **880** (29.333 s) |
| cut | `cf = sf + 7` | frame **75** (2.500 s) | `cf = 90` from sf 83 | `cf = sf − 210` | frame **351** (11.700 s) |

## Sound sync

| Event | Picture frame | Sound placement (file peak from `hyperframes audio`) |
|---|---|---|
| thud on the arm drop | film 619, cut 75 | `thud.mp3` peak 0.073 s lands on the drop frame (start = t − 0.073) |
| bright click on PASSED | film 880, cut 351 | `click.mp3` peak 0.073 s lands one frame after (start = t + 1/30 − 0.073) |
| tick on each case tick | each tick's grow start | `tick.mp3` peak 0.076 s lands one frame after |
| bed: bar line on the drop; music out for one bar; full band from PASSED | | `make_assets.sh` |

## Shots, film (45 s)

| t (s) | Shot |
|---|---|
| 0.0–8.5 | `diff`: frame 0 = the real diff; `+` lines wipe in 0.4–1.6; "A small refactor."; check row "✓ unit tests 468 passed ✓ lint" at 3.0; "The agent got worse." at 5.4 ("worse" in `fail`); vertical whip out 8.2 |
| 8.5–18.5 | `run`: run header and HUD; 15 ticks grow 0.2 s apart from 9.4, each with a tick; the two flips turn `fail` last (12.9) with call-outs; pass rate 0.973 → 0.853, −0.120, limit 0.08 at 14.0; whip out 18.2 |
| 18.5–33.0 | `gate`: the mark alone, centred; anticipation; drop on 619 + thud; mark moves left on an arc; BLOCKED comment enters right; comment scrolls to the flips; push 2 chip at 26.8, ticks re-run 27.1–28.5; lift; PASSED on 880 + click, "edited"; hold |
| 33.0–37.0 | claim: "Block the pull request that makes your agent worse." |
| 37.0–45.0 | end card: mark (pass pose) turns in, `casegate` wipes in, `$ uv add casegate`, tick row; hold ≥ 3 s |

## BANNED

Floating cards in a void, glow, particles, every element fading up, a docked logo, breathing loops on titles, invented UI, any number not in the table above, synthesised tones, the 25 fps GIF frames.
