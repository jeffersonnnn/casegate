# Credits and licences: launch videos (M5)

Every sound, font and library in `launch-film.mp4` and `launch-cut.mp4`. No voiceover. No generated audio.

## Music bed (one track, used in both videos)

| Item | Value |
|---|---|
| Title | Circuit Synthwave Alt |
| Creator | Doctor_Dreamchip (https://freesound.org/people/Doctor_Dreamchip) |
| Source | https://freesound.org/people/Doctor_Dreamchip/sounds/460358 (found through the Openverse audio API, id `3d3cbc70-3e75-476e-bd50-6b6d5157c06d`, the media-use skill's free source) |
| File | `launch/audio/circuit-synthwave-alt.mp3` (Freesound HQ preview, 116.1 s, 124 BPM; sha256 `d170dc8a…5c51`) |
| Licence | CC0 1.0 Universal (public domain dedication), https://creativecommons.org/publicdomain/zero/1.0/ . No attribution required; credited here for transparency. |
| Edit | `launch/make_assets.sh`: film = 45 s from 0.683 s, cut = 20 s from 36.235 s; low-pass 700 Hz until the drop, out for one bar after the drop, low-pass until PASSED, full band after; 2 s fade out; limiter at −2 dBFS. Output `launch/audio/bed-film.wav`, `bed-cut.wav`. |

## Sound effects

All three come from the media-use skill's bundled offline library (`~/.claude/skills/media-use/audio/assets/sfx/`). Its `CREDITS.md` says the files come from Pixabay under the Pixabay Content License (https://pixabay.com/service/license-summary/): free for commercial and non-commercial use, modification allowed, no attribution required.

| Cue | Our file | Library file | sha256 (first 8) | Placement |
|---|---|---|---|---|
| tick on each case tick | `launch/audio/tick.mp3` | `key-press.mp3` | `bcc892df` | peak (0.076 s into the file) one frame after each tick starts to grow: film 30 ticks, cut 30 ticks |
| low thud when the arm drops on BLOCKED | `launch/audio/thud.mp3` | `impact-bass-1.mp3` | `634d5eda` | peak (0.073 s) on the arm-drop frame: film frame 619, cut frame 75 |
| bright click on PASSED | `launch/audio/click.mp3` | `click.mp3` | `075e17bd` | peak (0.073 s) one frame after the PASSED frame: film frame 880, cut frame 351 |

## Fonts

IBM Plex Sans Condensed (700), IBM Plex Sans (400, 500) and IBM Plex Mono: SIL Open Font License 1.1, by IBM. The woff2 files in `launch/shared/fonts/` were downloaded from Google Fonts (latin subset). HyperFrames also embeds its own cached copy of IBM Plex Mono from Google Fonts at render time.

## Code and libraries

- three.js 0.160.0 (MIT), loaded from `https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js`, as in DESIGN §3.
- GSAP 3.15.0 (GreenSock standard licence, free to use), loaded by HyperFrames.
- HyperFrames CLI 0.9.38 (the render engine).

## Content shown on screen

All on-screen artefacts are this repo's own: the `store.py` diffs (`git show a62cf60`, `e4d3575`), the run files in `docs/assets/demo-pr-regression/`, the PR comment text (`casegate-comment.md`, `pr-comment-passed.png`), the logo scene (`scripts/render_mark.html`) and the site hero copy (`site/index.html`).

Publish note: CC0 and the Pixabay licence need no credit line in the post.
