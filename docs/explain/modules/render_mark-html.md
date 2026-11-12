# render_mark harness (`scripts/render_mark.html`, 82 lines)

**30 seconds:** The page that holds the 3D logo scene for offline renders. It is the site scene with no animation loop and no pointer input, so one call renders one exact pose. `scripts/render_mark.py` drives it.

**2 minutes:** The page reads the size and the background from the URL (`scripts/render_mark.html:13-16`). It has two palettes, dark and light (`scripts/render_mark.html:19-22`). It loads three.js 0.160.0 from jsDelivr and asks for a WebGL context with `preserveDrawingBuffer` (`scripts/render_mark.html:25-28`). The scene is two extruded rounded bars and a hub cylinder, three lights and one camera (`scripts/render_mark.html:36-52`). `angleAt` is the logo cycle from `docs/DESIGN.md` §4: hold up, anticipation, drop and settle, hold down, rise (`scripts/render_mark.html:57-64` `angleAt`). `window.renderAt(t, palette, sway)` sets the arm angle, the colours and the Y turn, then renders at once (`scripts/render_mark.html:65-76` `renderAt`). `window.glOk` tells the driver if the scene is ready (`scripts/render_mark.html:77-79`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `scripts/render_mark.html:27-28` | `preserveDrawingBuffer: true` | the screenshot reads the canvas after the render call returns; without it the buffer can already be clear |
| `scripts/render_mark.html:33` | `setPixelRatio(1)` | the PNG size must equal `--size`, not the screen density |
| `scripts/render_mark.html:21` | light fail colour `#C8312F` | DESIGN §3 gives no light fail colour; the light banner's fail tick colour keeps one palette |
| `scripts/render_mark.html:72` | `g.rotation.y = -0.35 + sway term` | the M4 pose is fixed; M5 adds a small sway with the same cycle length |

## Trade-off
The scene code is a copy of the site scene, not a shared module. A shared ES module would remove the copy but the site has no build step and the harness must also run from `file://`. Two copies are the price of no build step.

## Failure modes
Three.js fails to load: `glOk` is `false` and the driver exits 1. An unknown palette throws (`scripts/render_mark.html:67`), and the driver reports it as a page error. No test: the M4 build checked the PNGs by eye, and frame 90 of a 25 fps series showed the red fail arm as the cycle says.

## What I would change
Move the scene into one `mark-scene.js` file that the site, the harness and the M5 film all import. Cost: the site then needs the file served next to it, and `file://` module loading needs a local server.

## 10-minute version
The cycle is 5.2 s. The arm is up for the first 38 %, lifts 0.12 rad as anticipation, drops with a cubic ease and a small settle wobble, holds down until 80 %, then rises. The fail colour starts once the drop is 35 % done (`scripts/render_mark.html:61`), so the colour change reads as the result of the drop. The same function sits in `site/assets/mark.js:45-55` `angleAt`.
