# launch cut root (`launch/cut/index.html`, 61 lines)

**30 seconds:** The root HyperFrames composition of the 20 s vertical cut (1080 × 1920). It holds one scene and the sound cues for it. Like the film root, it is where picture time and sound time meet.

**2 minutes:** The header says why the cut exists (a second deliverable that keeps only the gate moment) and why the thud and click sit on frames 75 and 351 (`launch/cut/index.html:2-7`). The root sets 20 s, 30 fps, 1080 × 1920 (`launch/cut/index.html:20`). The scene `cut` fills all 20 s on track 1 (`launch/cut/index.html:21`). The bed plays on track 10 (`launch/cut/index.html:23`). The thud starts at 2.447 s for the drop frame 75, and the click at 11.66 s for the PASSED frame 351 (`launch/cut/index.html:24-25`). Fifteen ticks for the first run and fifteen for the re-run, 0.1 s apart, on tracks 11 and 12 in turn (`launch/cut/index.html:26-55`). The root timeline is empty (`launch/cut/index.html:57-60`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `launch/cut/index.html:24` | thud at 2.447 s | the peak lands on frame 75 (2.500 s); measured 2.5006 s (launch/REVIEW.md "Sync") |
| `launch/cut/index.html:25` | click at 11.66 s | 11.7 + 1/30 − 0.073: the peak lands one frame after PASSED |
| `launch/cut/index.html:26-55` | 0.18 s tick clips, two tracks in turn | ticks 0.1 s apart never overlap on one track |

## Trade-off
A separate project, not a crop of the film. A vertical frame needs its own layout: the mark on top, the comment below, the tick row at the bottom. A crop of the 16:9 film would cut the comment in half.

## Failure modes
The thud start is 0.02 s later than the launch/SPEC.md formula (t − 0.073 = 2.427 s), as in the film; the measured sync is 0 frames off, so the SPEC formula is out of date. The `hyperframes check` on the cut gives one layout warning, `container_overflow` on `#c-mark`, on purpose: the canvas runs off the top, the mark stays in frame (launch/REVIEW.md "Warnings kept on purpose").

## What I would change
The same as the film: generate the tick lines from the scene constants. Cost: one build step.

## 10-minute version
Measured: 1080 × 1920, 30 fps, 600 frames, `format.duration` 20.000000 s, −13.1 LUFS, true peak −1.1 dBTP, no decode error (`docs/assets/runs/launch-assets-m5.json`).
