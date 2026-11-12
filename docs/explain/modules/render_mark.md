# render_mark (`scripts/render_mark.py`, 86 lines)

**30 seconds:** The script that turns the 3D logo into PNG files. It opens the render harness in headless Chromium, renders one pose or a series of frames, and saves each canvas as a PNG. M4 uses it for the logo renders; M5 reuses it for the logo loop frames (`docs/DESIGN.md` §3).

**2 minutes:** The arguments are size, time, palette, background, an optional sway and an optional frame series (`scripts/render_mark.py:24-41` `parse_args`). A background must be `transparent` or `#RRGGBB`, and `--frames` and `--fps` must come together (`scripts/render_mark.py:35-40`). The page URL carries the size and the background without the `#` (`scripts/render_mark.py:46-48`). One pose is one job; a frame series is one job per frame at time `k / fps` (`scripts/render_mark.py:50-56`). Chromium starts with SwiftShader flags (`scripts/render_mark.py:17` `CHROMIUM_ARGS`), and the page must report a WebGL context before any screenshot (`scripts/render_mark.py:64-68`). Each job calls `window.renderAt` and checks the context again before it saves (`scripts/render_mark.py:70-76`). Any page error makes the script exit 1 (`scripts/render_mark.py:78-80`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `scripts/render_mark.py:17` | `--use-angle=swiftshader`, `--enable-unsafe-swiftshader` | headless Chromium often has no WebGL without them (`docs/DESIGN.md` §3) |
| `scripts/render_mark.py:18-21` | `GL_CHECK` reads `window.glOk` and the canvas context | a blank PNG from a failed context looks like a valid file; the check turns it into exit 1 |
| `scripts/render_mark.py:35-36` | reject a `--bg` with no `#` | an unquoted `#0B0F0E` in the shell starts a comment, so the value arrives empty or wrong (FACTS.md §7) |
| `scripts/render_mark.py:53` | frame k renders at `k / fps` | each frame is a pure function of time, so a frame series is repeatable and has no timer drift |
| `scripts/render_mark.py:76` | `omit_background=transparent` | the logo PNGs need real alpha; a dark fill would show on light pages |

## Trade-off
Playwright is not a project dependency; the script runs from a scratch venv (`scripts/render_mark.py:1-5`). The project stays small and its CI does not download a browser. The cost: a new contributor must install Playwright by hand to make a render.

## Failure modes
No WebGL: exit 1 with the page errors. Context lost in a long frame series: exit 1 before the bad frame is saved. No network: three.js comes from jsDelivr, so the page sets `glOk = false` and the script exits 1. There is no test file: `scripts/` is outside ruff, mypy and pytest (`docs/DESIGN.md` §3). The M4 build checked it by eye on a contact sheet and with a 130-frame series at 25 fps.

## What I would change
Vendor three.js 0.160.0 into `scripts/`, so a render works offline and the CDN cannot change the output. Cost: about 1 MB in the repo.

## 10-minute version
The script holds no scene code; all geometry, light and the pose cycle live in `scripts/render_mark.html` (see `render_mark-html.md`). The viewport equals the output size and the device scale factor is 1, so a 512 render is exactly 512 × 512 pixels (`scripts/render_mark.py:60`). In frame mode, `--t` is ignored and the files are `frame_000.png` and up (`scripts/render_mark.py:53`). M4 renders never pass `--sway`; M5 loops can.
