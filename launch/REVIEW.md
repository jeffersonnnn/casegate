# REVIEW: launch videos (M5, 2026-11-12)

## Delivered (measured with ffprobe and ffmpeg ebur128 on the files in `~/Desktop/casegate-launch-assets/`)

| File | Canvas | fps | Frames | format.duration | Video | Audio | Loudness | True peak |
|---|---|---|---|---|---|---|---|---|
| `launch-film.mp4` | 1920×1080 | 30 | 1350 | 45.000000 s | H.264 High, yuv420p | AAC LC 48 kHz stereo | −14.2 LUFS | −1.0 dBTP |
| `launch-cut.mp4` | 1080×1920 | 30 | 600 | 20.000000 s | H.264 High, yuv420p | AAC LC 48 kHz stereo | −13.1 LUFS | −1.1 dBTP |

Both files decode to the end with no error (`ffmpeg -v error -f null`).

## Sync (measured on the delivered files: the largest sample in the window)

| Video | Arm-drop frame | Thud peak | Δ | PASSED frame | Click peak |
|---|---|---|---|---|---|
| film | 619 (20.633 s) | 20.6336 s = frame 619.01 | 0 frames | 880 (29.333 s) | 29.3450 s = frame 880.35 |
| cut | 75 (2.500 s) | 2.5006 s = frame 75.02 | 0 frames | 351 (11.700 s) | 11.7116 s = frame 351.35 |

The arm-drop frame is the first frame where `angleAt` puts the arm at or below DOWN (cycle frame 82, −0.1545 rad, the overshoot). The tick onsets measure one frame after each tick starts to grow (film 9.425 s for the tick at 9.400 s, and so on). The sound was measured, not heard.

## Frames looked at (from the delivered MP4s)

Film frames 0, 337, 618, 619, 675, 879, 880, 1012, 1200, 1349. Cut frames 0, 75, 150, 300, 350, 351, 450, 599. Frame 879 shows the arm red and BLOCKED; frame 880 shows the arm green and PASSED fading in, so the click, the colour and the text land together.

## Creative calls

- Storyline A ("Lab instrument", `STORYLINES.md`). Cut: B (a GitHub PR page take; reads as a mock-up) and C (numbers slam on the beat; does not show what the gate does).
- The sticky comment is rebuilt in HTML at about 1.6× from the real text (`casegate-comment.md`, and `pr-comment-passed.png` transcribed), not the 828 px PNG upscaled: the PNG goes soft at 1080p. The diff, run header, tick row, numbers and site hero copy are the real ones.
- The green tick row after the fix uses `baseline.json` heights; the push-2 run JSON is not in the repo. No number is attached to it.

## Lasseter's principles, and where each is used

| Principle | Use |
|---|---|
| Squash and stretch | The comment card squashes 3% on landing, then springs back; "worse." and "0.853" squash on contact; each tick stretches 8–10% past its height, then settles. |
| Anticipation | The arm lifts +0.12 rad before it drops (`angleAt`, DESIGN §4); "worse." rises before it drops in. |
| Staging | For the drop the mark is alone, centred and 1.35× large; the comment only enters after the hit. One signal colour at a time: red until frame 880, then green. |
| Straight ahead and pose to pose | The arm is pose to pose (up, anticipation, drop, hold, lift) from `angleAt`; the tick row is straight ahead, one tick after the other. |
| Follow through and overlapping action | The arm overshoots DOWN and settles; the mark starts to move left while the comment is still entering; the state label trails the mark by 2 frames. |
| Slow in and slow out | Arrivals use `expo.out`/`power3.out`; camera moves use `power2.inOut`; exits use `power3.in` and are faster than entrances; the lift is ease-in-out (`angleAt`). |
| Arcs | The arm swings on its hub; the mark travels to the left on an arc (x eases both ways while y rises 90 px and settles). |
| Timing | Ticks 0.2 s apart in the first run and 0.1 s apart in the re-run; a bar line of the 124 BPM bed sits on the drop; holds ≥ 2 s on every claim and ≥ 3 s on the end card. |
| Exaggeration | Ticks at 5× scale; the music cuts out for one bar under the thud; the bed is low-passed while the agent is "worse" and opens to full band on PASSED. |
| Secondary action | The state label (`✓ pass` / `✗ blocked`) changes with the arm colour; the mark turns in on Y as it lands on the end card; corner telemetry. |
| Appeal | Only DESIGN tokens and IBM Plex; the real 3D mark; a clean lockup with the site's `uv add casegate` chip. |

## Warnings kept on purpose (`npx hyperframes check`: ok = true for both)

- `line_unread` on the comment card: it is a document, not one line; the beat holds the headline (≥ 2.9 s) and the flips (≥ 3 s) with highlight sweeps.
- `text_below_floor`: the card's table and footer (18–24 px at 1080p) and the corner telemetry. The key lines (verdict, "Pass rate fell 12.0 points (limit 8.0).", the numbers) are 28 px or larger.
- `negative_z_index`: the highlight bars sit under their text inside an isolated stacking context; they render (checked in frames).
- Cut `container_overflow` on `#c-mark`: the canvas runs off the top on purpose; the mark itself stays in frame.

## Weakest shot and what to change with more time

The film's end card has no motion after 40.6 s (a still hold, as planned). With more time: a rerender of the comment at retina scale from GitHub itself, and a second take of the tick sound so the repeats differ.

## Rebuild

`bash launch/make_assets.sh`, then `npx hyperframes render -o <new file> --quality delivery` inside `launch/film` and `launch/cut`. Never overwrite a delivered file.
