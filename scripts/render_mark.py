"""Render the casegate 3D mark to PNG through scripts/render_mark.html (docs/DESIGN.md §3).

The icons and banner frames must match the live site logo, so they come from the same scene.
Needs Playwright Chromium with SwiftShader WebGL from a scratch venv (not a project dependency).
Quote '#' colours in the shell: an unquoted #0B0F0E starts a comment (FACTS §7).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HTML = Path(__file__).resolve().parent / "render_mark.html"
CHROMIUM_ARGS = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
GL_CHECK = """() => {
  const c = document.querySelector('canvas');
  return window.glOk === true && !!c && !!(c.getContext('webgl2') || c.getContext('webgl'));
}"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render the casegate 3D mark to PNG.")
    p.add_argument("--size", type=int, required=True, help="output width and height in px")
    p.add_argument("--t", type=float, default=0.0, help="cycle time in seconds (ignored with --frames)")
    p.add_argument("--palette", choices=["dark", "light"], required=True)
    p.add_argument("--bg", required=True, help="transparent or #RRGGBB (quote it in the shell)")
    p.add_argument("--sway", action="store_true", help="add the loop sway on Y (off unless given)")
    p.add_argument("--frames", type=int, help="render N frames; --out is then a directory")
    p.add_argument("--fps", type=float, help="frames per second for --frames")
    p.add_argument("--out", required=True, help="PNG file, or a directory with --frames")
    a = p.parse_args(argv)
    if a.bg != "transparent" and not re.fullmatch(r"#[0-9A-Fa-f]{6}", a.bg):
        p.error(f"--bg must be transparent or #RRGGBB, got {a.bg!r}")
    if (a.frames is None) != (a.fps is None):
        p.error("--frames and --fps go together")
    if a.frames is not None and (a.frames < 1 or a.fps <= 0):
        p.error("--frames must be >= 1 and --fps > 0")
    return a


def main(argv: list[str] | None = None) -> int:
    a = parse_args(argv)
    transparent = a.bg == "transparent"
    bg_param = "transparent" if transparent else a.bg[1:]
    url = f"{HTML.as_uri()}?size={a.size}&bg={bg_param}"

    if a.frames is not None:
        out_dir = Path(a.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        jobs = [(k / a.fps, out_dir / f"frame_{k:03d}.png") for k in range(a.frames)]
    else:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        jobs = [(a.t, Path(a.out))]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=CHROMIUM_ARGS)
        page = browser.new_page(viewport={"width": a.size, "height": a.size}, device_scale_factor=1)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url)
        page.wait_for_function("() => window.glOk !== undefined", timeout=30_000)
        if not page.evaluate(GL_CHECK):
            print(f"error: no WebGL context in {HTML.name} {errors}", file=sys.stderr)
            browser.close()
            return 1
        canvas = page.locator("canvas")
        for t, path in jobs:
            page.evaluate("([t, p, s]) => window.renderAt(t, p, s)", [t, a.palette, a.sway])
            if not page.evaluate(GL_CHECK):
                print(f"error: WebGL context lost before {path}", file=sys.stderr)
                browser.close()
                return 1
            canvas.screenshot(path=str(path), omit_background=transparent)
        browser.close()
        if errors:
            print(f"error: page errors: {errors}", file=sys.stderr)
            return 1
    print(f"wrote {len(jobs)} file(s) to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
