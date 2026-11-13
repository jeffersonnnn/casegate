# launch asset script (`launch/make_assets.sh`, 42 lines)

**30 seconds:** The shell script that builds the two music beds with ffmpeg and copies the shared fonts, sounds and mark scene into both HyperFrames projects. It exists because the beds are cut to the same frames as the picture, and because the repo does not commit `.wav` copies inside the projects.

**2 minutes:** The header says how to run it and what it writes (`launch/make_assets.sh:2-4`). `SRC` is the one CC0 track (`launch/make_assets.sh:7`). The function `bed` takes a source offset, a length, the drop time, the PASSED time and an output file (`launch/make_assets.sh:12-25` `bed`). It trims the track and splits it in two. Branch one is low-passed at 700 Hz twice, with a volume curve: it rises until the drop, cuts to silence for one bar of 1.9355 s, comes back low-passed, and fades out at PASSED (`launch/make_assets.sh:17`). Branch two is the full band, silent until PASSED, then up in 0.03 s (`launch/make_assets.sh:18`). The mix gets a 2 s fade out and a limiter (`launch/make_assets.sh:23`). The film bed starts 0.683 s into the track and the cut bed 36.235 s in, so a bar line falls on the drop frame (`launch/make_assets.sh:27-30`). Then the loop copies fonts, `mark3d.js` and the three sound effects into each project (`launch/make_assets.sh:32-37`), and the beds go in as `assets/audio/bed.wav` (`launch/make_assets.sh:40-41`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `launch/make_assets.sh:14` | `bar=1.9355` | one bar at 124 BPM (4 × 60 / 124 s): the music is out for exactly one bar under the thud |
| `launch/make_assets.sh:17` | the low-pass volume curve | the regression sounds muffled; the drop leaves the thud alone (exaggeration, launch/REVIEW.md) |
| `launch/make_assets.sh:18` | the full-band branch opens at PASSED | the sound opens up on the same frame as the green arm and the click |
| `launch/make_assets.sh:27-30` | source offsets 0.683 and 36.235 | a bar line of the track sits on the drop frame (619 in the film, 75 in the cut) |
| `launch/make_assets.sh:38-41` | the beds are copied, not committed in the projects | `.gitignore` ignores `launch/**/*.wav` outside `launch/audio/`, so the script recreates the copies |

## Trade-off
A script with fixed times, not a sound edit in HyperFrames. HyperFrames can mix tracks, but a filter that changes at an exact time is easier to check in ffmpeg, and the times sit next to the frames they serve. The cost: the times are written twice, here and in the compositions.

## Failure modes
Change a drop frame in a composition and forget this script, and the bar line and the low-pass change land on the wrong frame. Nothing checks that link; the sync was measured on the delivered files (launch/REVIEW.md "Sync"). The script needs `ffmpeg` and `python3` on the path and stops on the first error (`set -euo pipefail`).

## What I would change
Read the drop and PASSED times from one JSON file that the compositions also read. Cost: the compositions would need a fetch or a build step.

## 10-minute version
Measured loudness of the delivered files: film −14.2 LUFS, cut −13.1 LUFS, true peak −1.0 and −1.1 dBTP (`docs/assets/runs/launch-assets-m5.json`). The limiter is set to 0.79 (about −2 dBFS) before the encoder (`launch/make_assets.sh:23`). The sources and licences are in `launch/CREDITS.md`.
