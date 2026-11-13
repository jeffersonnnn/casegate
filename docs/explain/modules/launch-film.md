# launch film root (`launch/film/index.html`, 64 lines)

**30 seconds:** The root HyperFrames composition of the 45 s launch film. It places the three scenes on one track and every sound on its own frame. It holds no animation itself: the timing of picture and sound meets here.

**2 minutes:** The header comment says why the file exists (it places the scenes and the audio, so timing and sound sync live in one place) and why the thud and click sit on frames 619 and 880 (`launch/film/index.html:2-8`). The root div sets 45 s, 30 fps and 1920 × 1080 (`launch/film/index.html:21`). The three scenes are sub-compositions on track 1: `diff` 0 to 8.5 s, `run` 8.5 to 18.5 s and `gate` 18.5 to 45 s, which also holds the claim and the end card (`launch/film/index.html:22-24`). The bed plays for all 45 s on track 10 (`launch/film/index.html:26`). The thud and the click share track 13 (`launch/film/index.html:27-28`). Thirty tick clips follow: 15 for the first run at 0.2 s steps and 15 for the re-run after push 2 at 0.1 s steps, on tracks 11 and 12 in turn (`launch/film/index.html:29-58`). The root timeline is empty and paused, because each scene registers its own (`launch/film/index.html:60-63`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `launch/film/index.html:27` | thud starts at 20.58 s | its peak must land on the arm-drop frame 619 (20.633 s) |
| `launch/film/index.html:28` | click starts at 29.294 s | peak 0.073 s into the file lands one frame after PASSED frame 880 (29.333 + 1/30 − 0.073) |
| `launch/film/index.html:29` | first tick at 9.357 s | the first tick grows at 9.4 s; the peak (0.076 s) lands one frame after (9.4 + 1/30 − 0.076) |
| `launch/film/index.html:44-58` | 0.18 s tick clips on tracks 11 and 12 in turn | at 0.1 s steps the same track then has a gap of 0.2 s, so no two ticks overlap on one track (see 04-failures.md) |

## Trade-off
Thirty `<audio>` elements written out, not a loop in a script. HyperFrames reads clip timing from the DOM, so a loop would need a build step; written out, every start time is visible and checkable against launch/SPEC.md.

## Failure modes
The thud start does not follow the formula in launch/SPEC.md ("start = t − 0.073" gives 20.560 s); the file says 20.58 s, 0.02 s later. The measured result on the delivered file is still 0 frames off: thud peak 20.6336 s = frame 619.01 (launch/REVIEW.md "Sync"). So the code is right by measurement and the SPEC formula is out of date. The first `hyperframes check` gave 13 `duplicate_audio_track` warnings for 0.4 s tick clips; the final check gives none (04-failures.md).

## What I would change
Generate the tick lines from the scene constants (`T0`, `STEP`) with a small script, so the sound cannot drift from the picture. Cost: one more build step before render.

## 10-minute version
Measured on the delivered file: 1920 × 1080, 30 fps, 1350 frames, `format.duration` 45.000000 s, H.264 High yuv420p, AAC LC 48 kHz stereo, decodes to the end with no error (`docs/assets/runs/launch-assets-m5.json`). Rebuild: `bash launch/make_assets.sh`, then `npx hyperframes render` in `launch/film` (launch/REVIEW.md "Rebuild").
