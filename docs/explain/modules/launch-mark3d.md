# launch mark scene (`launch/shared/mark3d.js`, 65 lines)

**30 seconds:** The 3D barrier-arm logo for the two launch videos. It is a copy of the render harness scene (`scripts/render_mark.html`), with the same `angleAt(t)` pose function. The videos never let the logo cycle run on its own clock: each scene picks the pose for its own frame, so the arm drop lands on an exact frame.

**2 minutes:** The constants `UP`, `DOWN` and `CYC` (5.2 s) and the easing function come first (`launch/shared/mark3d.js:7-8`). `angleAt` is copied verbatim from the harness and returns the arm angle and a flag that says "fail colour" (`launch/shared/mark3d.js:10-20` `angleAt`). three.js 0.160.0 loads once, from jsDelivr (`launch/shared/mark3d.js:22-24` `loadThree`). `create` builds the renderer with `preserveDrawingBuffer`, so the frame stays in the canvas for the capture, and a pixel ratio of 1, so the canvas size is the output size (`launch/shared/mark3d.js:26-31` `create`). The camera, the three lights, the extruded bars and the hub match DESIGN §3 (`launch/shared/mark3d.js:32-50`). `render(cycleSeconds, rotY)` sets the arm angle and colour from `angleAt`, turns the group on Y, renders once and returns the state, so the caller can set the state label from the same value (`launch/shared/mark3d.js:53-61` `render`). The module puts `CasegateMark` on `window` (`launch/shared/mark3d.js:64`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `launch/shared/mark3d.js:3-4` | the header rule: no free-running cycle, no 25 fps GIF frames | the arm drop must land on one known frame for the thud (launch/SPEC.md "Logo cycle at 30 fps") |
| `launch/shared/mark3d.js:10-20` | `angleAt` copied verbatim | the logo in the videos must move exactly as on the site and in the GIFs (`docs/DESIGN.md` §4) |
| `launch/shared/mark3d.js:28-31` | `preserveDrawingBuffer`, pixel ratio 1 | HyperFrames captures the canvas after the call returns; without the buffer the frame can be blank |
| `launch/shared/mark3d.js:52-53` | `render` takes cycle seconds, not scene seconds | the caller maps its frame to a cycle frame; the scene never guesses the time |
| `launch/shared/mark3d.js:60` | `render` returns `st` | the "✓ pass" / "✗ blocked" label and the arm colour change on the same frame |

## Trade-off
A third copy of the scene (the site has `site/assets/mark.js`, the harness has `scripts/render_mark.html`). One shared module would remove the copies, but the harness runs from `file://` and the site must stay static. The copy is small and `angleAt` is marked verbatim, so a diff shows any drift.

## Failure modes
No network: the three.js import fails, `buildReady` rejects and the render stops; there is no fallback in a video, on purpose. The usage line in the header names the two arguments `render` takes and its `{ a, f }` result (`launch/shared/mark3d.js:5`, `launch/shared/mark3d.js:53`); the scale is set on the wrapper by GSAP, not by `render`. Before the 2026-11-12 comment fix, the usage line said `render(cycleSeconds, rotY, scale)`. No test guards the copy; the check was by eye on frames 618, 619, 879 and 880 (launch/REVIEW.md "Frames looked at").

## What I would change
Fix the stale usage line. Then make `angleAt` one file that the harness, the site and the videos all import. Cost: a local server for the harness and one more file on the site.

## 10-minute version
`make_assets.sh` copies this file into `launch/film/assets/` and `launch/cut/assets/` (`launch/make_assets.sh:32-37`), because each HyperFrames project serves only its own folder. The gate scene and the cut call `create` with 760 and 900 px (`launch/film/compositions/gate.html:159`, `launch/cut/compositions/cut.html:110`). The arm-drop frame is the first cycle frame at or below `DOWN`: cycle frame 82, with the overshoot (launch/REVIEW.md "Sync").
