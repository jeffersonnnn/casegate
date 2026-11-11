# DESIGN — casegate

Direction: **A "Lab instrument"** (ADR 0007). Rejected: B "Traffic gate" (hazard stripes compete with the red/green status signal) and C "Paper report" (light theme fights the dark terminal the videos use). The live options stay in `docs/design/options/` (`python3 build.py`, serve the folder, open `index.html`); option A's file is the visual reference for every asset.

Feel words: dark, quiet, precise, one signal. Ornament is limited to hairline grids, crosshair ticks and small monospace telemetry.

References (techniques only, never assets; full list with URLs in `docs/research/design-references.md`):
- ZIRKA Interceptor (Awwwards SOTD 2026-11-09): small monospace telemetry in the corners, hairline circles.
- DeepBook (SOTD 2026-11-03): a field of grey ticks with a few ticks in one accent colour → the case tick row.
- Charm VHS: studied for terminal framing only; not used (§5).
- Ghostty: the logo drawn in a terminal frame in two tones.
- Astral uv docs: short output lines, each with a number and a unit.

---

## 1. Colour tokens

| Token | Hex | Use | Contrast on bg | Contrast on surface |
|---|---|---|---:|---:|
| `bg` | `#0B0F0E` | page, terminal, video background | — | — |
| `surface` | `#141A18` | panels, code blocks, cards | — | — |
| `text` | `#E3ECE7` | body text, logo post and hub | 16.00:1 | 14.63:1 |
| `muted` | `#8FA39A` | labels, secondary text, grey ticks | 7.23:1 | 6.61:1 |
| `pass` | `#3DDC84` | pass status, the logo arm when up, primary accent | 10.81:1 | 9.88:1 |
| `fail` | `#FF5D5D` | fail status, regressions, the logo arm when down | 6.41:1 | 5.86:1 |
| `warn` | `#E8C547` | `error` status only (ADR 0003) | 11.49:1 | 10.51:1 |
| `line` | `rgba(227,236,231,0.12)` | hairlines, grid | decorative | decorative |

Rules:
- One signal colour at a time. Links and focus rings use `text` with an underline or `pass`; the research palette's cyan accent is dropped.
- Status never by colour alone: always a glyph and a word: `✓ pass`, `✗ fail`, `⚠ error`.
- Contrast was computed with the WCAG 2.x formula (`docs/research/design-references.md` §4). Every text pair is ≥ 4.5:1; every status colour on bg/surface is ≥ 4.5:1.

## 2. Type

| Role | Family | Weights | Source |
|---|---|---|---|
| Display | IBM Plex Sans Condensed | 500, 700 | Google Fonts (OFL) |
| Body | IBM Plex Sans | 400, 500 | Google Fonts (OFL) |
| Mono | IBM Plex Mono | 400, 500 | Google Fonts (OFL) |

Scale (site): h1 `clamp(40px, 6.2vw, 76px)` / 1.02, h2 `clamp(28px, 3.4vw, 40px)` / 1.1, lede 19px (17px on phones), body 16px / 1.6, mono labels 11–13px with 0.04–0.12em tracking and uppercase. Terminal and video type: IBM Plex Mono.

## 3. Logo

Concept: a barrier arm that is also a check mark. A short leg and a long arm meet at a hub (the pivot). Arm up = check = pass (arm in `pass`). Arm down = barrier closed = blocked (arm in `fail`).

- **Flat SVG** (`site/assets/mark.svg`, also inline in the site): viewBox `0 0 64 64`; leg `M12 33 L25 45` stroke `text`; arm `M25 45 L54 17` stroke `pass`; stroke width 6 (7 for ≥ 128 px), round caps; hub circle `cx=25 cy=45 r=4.5` fill `text`. A `mark-fail.svg` variant has the arm `M25 45 L56 47` in `fail`.
- **3D mark** (three.js r160 via `https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js`): two rounded bars made with `ExtrudeGeometry` (depth 0.42, bevel thickness 0.08, bevel size 0.06, 6 bevel segments); leg length 1.35 at 135°; arm length 3.1 on a pivot group; hub cylinder r 0.34; materials `MeshStandardMaterial` (post/hub `text`, metalness 0.35, roughness 0.35; arm `pass`/`fail`, metalness 0.25, roughness 0.3); hemisphere light + key light (3,4,6) + rim light (−4,−2,−3); camera fov 30 at (0, 0.3, 12.5). Arm angles: up `π/4.1`, down `−0.12`. Reference implementation: `docs/design/options/build.py` (the `<script type="module">` block).
- **Render harness** (M4 writes it, M5 reuses it; both files are committed and `scripts/` is outside ruff and mypy): `scripts/render_mark.html` is the `build.py` scene with no rAF loop and no pointer input. It exposes `window.glOk: boolean` and `window.renderAt(t: number, palette: "dark" | "light", sway: boolean)`, which sets `pivot.rotation.z` and the arm colour from the §4 `angleAt(t)`, sets `g.rotation.y = -0.35 + (sway ? 0.08 * sin(2π t / 5.2) : 0)`, and calls `renderer.render` synchronously. `scripts/render_mark.py` drives it with Playwright (installed in a scratch venv, not in the project deps): args `--size N --t SECONDS --palette dark|light --bg transparent|#RRGGBB [--sway] --out FILE`; sway is off unless `--sway` is given (single renders and M4 renders never pass it). With `--frames N --fps F`, `--out` is a directory, frame k is `renderAt(k/F, palette, sway)` saved as `frame_%03d.png`, and `--t` is ignored. Quote the `#` colour in every shell command (`--bg '#0B0F0E'`): an unquoted `#0B0F0E` starts a shell comment (FACTS §7). Palettes: dark = post/hub `text` `#E3ECE7`, arm `pass`/`fail`; light = post/hub `#0B0F0E`, arm `#1A8F4E`.
- **Renders** (M4): from the same three.js scene (through the harness), rendered with Playwright Chromium launched with args `["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]` (headless Chromium often has no WebGL without them); assert the canvas has a WebGL context before each screenshot. Render pose: `pivot.rotation.z = π/4.1`, group position `(-0.7, -0.9, 0)`, group `rotation.y = -0.35`, `rotation.x = 0`, no sway; renderer `alpha: true`, screenshot with `omitBackground`. From 3D: `site/assets/mark-512.png`, `mark-192.png` (transparent, dark palette), `mark-512-light.png` (same pose and alpha, light palette: post/hub `#0B0F0E`, arm `#1A8F4E`, contrast 3.83:1 on `#F4F7F5`, ≥ 3:1 for graphics; the dark post `#E3ECE7` would be 1.12:1 there, FACTS §7) and `apple-touch-icon.png` (180, on bg `#0B0F0E`, not transparent: iOS fills transparency with black). `favicon-32.png` is rasterised from the flat SVG at stroke 6 (a 3D render is not legible at 32 px). `favicon.svg` = flat SVG. The nav mark uses the flat SVG.
- The live 3D canvas is used only on the site's landing hero, loaded with a dynamic `import()`; nothing else loads three.js.

## 4. Motion

The logo cycle (5.2 s loop, pose to pose): hold up/pass (38%) → anticipation lift +0.12 rad (6%) → drop with cubic ease-out and a small settle bounce, colour switches to `fail` a third of the way down (10%) → hold blocked (26%) → lift back with ease-in-out, colour back to `pass` halfway (20%). A slow idle sway on Y (±0.08 rad, 0.6 rad/s) plus pointer parallax (±0.25 rad) on the live site. `angleAt(t)` is the function of that name in `docs/design/options/build.py`: it returns the arm angle `a` and the fail flag `f` for time `t` (seconds, mod 5.2); every render, GIF and video re-times the cycle from it.

Loop assets (GIFs, video loops): 25 fps (GIF delay 4 cs), 130 frames = exactly one 5.2 s cycle; sway = `0.08·sin(2π·t/5.2)` so the loop is seamless; no pointer parallax. (At 30 fps the GIF delay cannot be 3.33 cs, and the site's 0.6 rad/s sway has a 10.47 s period, so neither loops cleanly.)

Site rules:
- Sections rise in on first view (16 px translate + opacity, 400 ms, ease-out, staggered 60 ms).
- The tick row in the hero animates once on load: ticks grow from 0 to their height left to right over 900 ms; flipped ticks turn `fail` last.
- Pause the render loop when the tab is hidden (`document.hidden`) or the canvas is off screen (`IntersectionObserver`).
- `prefers-reduced-motion: reduce`: no loop, no sway, no rise-in; the logo holds the pass pose.
- No WebGL (or the three.js import fails): the flat SVG shows in the stage. The page is fully readable with JavaScript off.

## 5. Terminal theme (`console.py`, rich)

| Element | Rich style |
|---|---|
| Header labels (`suite`, `cases`, ...) | `#8FA39A` |
| Header values | `#E3ECE7` |
| Progress bar complete / remaining | `#3DDC84` / `#2A3430` |
| Table header | `bold #E3ECE7`, no box lines except a single `line` rule under the header (`box.SIMPLE_HEAD`) |
| `✓ pass` / `k/N` all passed | `#3DDC84` |
| `✗ fail` / `0/N` | `#FF5D5D` |
| partial `k/N` | `#E8C547` is NOT used for partial; partial uses `#E3ECE7` with the failing scorer shown |
| `⚠ error` | `#E8C547` |
| Muted notes (`wrote ...`, `… 10 more`) | `#8FA39A` |
| Gate verdict | `bold #3DDC84 ✓ PASSED` or `bold #FF5D5D ✗ BLOCKED` |

Layout follows the mood of the "terminal · casegate run" and "casegate gate" panels in `docs/design/options/option-a.html`. **option-a.html shows the mood only; text, numbers and formats come from SPEC §9–§14** (for example the gate console is SPEC §11 "Gate console", with U+2212 minus and `limit 5.0`). Plain mode (`--plain`, not a TTY, or `NO_COLOR`) prints the same words and glyphs with no ANSI codes.

Recording: use copied text. In M4, load `.env` first, then run:
- `uv run casegate run evals --repeat 1 --plain > docs/assets/term-run.txt` (usually a warm cache, cost ≈ $0; `.casegate/cache` is gitignored and the M3 demo PR may have bumped `target.version`, so if `summary.cache_output_hits < cache_output_total` the run spends real money: M4 budget for this step ≤ $0.10). Plain mode prints no progress bar (SPEC §14).
- `uv run casegate gate --baseline docs/assets/demo-pr-regression/baseline.json --run docs/assets/demo-pr-regression/casegate-run.json --max-drop "$(jq -r .max_drop evals/tolerance.json)" --plain > docs/assets/term-gate.txt; test $? -eq 1` (exit 1 = BLOCKED is expected; any other exit code stops the task). The baseline is the base-branch file the demo PR gate used (§8), and `--max-drop` is the measured value, so the panel matches the real PR comment.

Paste both HTML-escaped into `<pre>` with token colour spans: `✓` and the word after it → `pass`; `✗` and the word after it → `fail`; `⚠ error` → `warn`; header labels (`suite`, `cases`, `repeats`, `concurrency`, `target`, `judge`) and the `wrote` line → `muted`; everything else → `text`. VHS is out of scope; the videos rebuild the terminal as HTML from the same `.txt` files.

## 6. Markdown surfaces (report, PR comment, job summary, README)

GitHub strips styles, classes and ids. Allowed and used: tables, `<details open>`, `<summary>`, `<sub>`, `<picture>` with `prefers-color-scheme` sources, hidden comments (the `<!-- casegate-gate -->` marker), alerts (`> [!WARNING]`), emoji-free Unicode glyphs ✓ ✗ ⚠ → ±.

Conventions:
- Headline first: verdict glyph + word + one sentence with the number ("Pass rate fell 10.6 points (limit 5.0).").
- Numbers right-aligned (`--:`), 3 decimals for rates, `−` (U+2212) for negative deltas.
- One table per idea; long lists inside `<details>`.
- Footer in `<sub>` with versions and shas.

## 7. README banner

`docs/assets/banner-dark.png` and `banner-light.png` are screenshots of `site/banner.html`: a 1280×320 page that links `assets/site.css` (§8) and adds only its own layout rules in a `<style>` block, the hero mark render `site/assets/mark-512.png` (pass pose) on the right, "casegate" in Plex Mono 500 plus the one-line description on the left, and the tick row (§8) along the bottom. Taken with Playwright at `deviceScaleFactor: 2`, so the PNG pixels are 2560×640; the README shows them with `width="1280"`. The banner is made after the logo and the site (M4 runs logo → site → banner).

Theme switch: `site/banner.html` reads `?theme=light|dark` (default dark); for light it sets the light tokens below on `:root` and swaps the img src to `assets/mark-512-light.png`. Screenshot `banner.html?theme=dark` → `banner-dark.png` and `banner.html?theme=light` → `banner-light.png`.

X header mode (M5 uses it): `site/banner.html` also reads `?size=x`. With `size=x` (viewport 1500×500), the page lays out for the X header: "casegate", the one-line description and the tick row sit inside CSS x 500–960, y 100–333 (device x 1500–2880, y 300–1000 at DPR 3). The mark `<img>` is removed (`display:none`), so CSS x 967–1267, y 100–400 stays empty for the composited mark. CSS x 0–500, y 333–500 stays empty for the profile photo. The M4 banner agent implements this mode and screenshots `banner.html?theme=dark&size=x` once to check it.

Light variant: bg `#F4F7F5`, text `#0B0F0E`, post/hub material `#0B0F0E`, arm `#1A8F4E`, grey ticks `#5E6E67`, fail ticks `#C8312F`, hairlines `rgba(11,15,14,0.12)`. The M4 banner task writes `scripts/contrast.py` (WCAG 2.x relative luminance) and records each ratio here (text pairs ≥ 4.5:1). Used via `<picture>` with `prefers-color-scheme`.

## 8. Site (`site/`, GitHub Pages, M4)

One page, built from `docs/design/options/option-a.html` with real content:
- Nav: mark + `casegate`, links How it works, The gate, GitHub (phone: GitHub only).
- Hero: eyebrow `Evals · CI gate · Python`; h1 "Block the pull request that makes your agent **worse**." (the word in `fail`); lede; install chip `uv add casegate` (the copy button copies exactly that text) with copy button; tick row; HUD telemetry with real numbers (suite, target version, repeats, judge, pass rate ± std from `evals/baseline.json`; tolerance from `evals/tolerance.json`); 3D stage.
- The stage is `<div class="stage" id="stage" role="img" aria-label="casegate logo: a barrier arm that lifts on pass and drops on fail">`; the canvas and the fallback SVG inside it get `aria-hidden="true"`. The live state text (`#state`) sits outside the `role="img"` element. (axe flags `aria-label` on a plain div, which would block Lighthouse 100.)
- Tick row: the cases of `evals/baseline.json` in order, 15 ticks, width 6 px, gap 6 px; height = `8 + round(36 × mean_score)` px (mean_score None: 8 px, class `warn`); class `f` when the case id is in `compare(docs/assets/demo-pr-regression/baseline.json, docs/assets/demo-pr-regression/casegate-run.json).flips_pass_to_fail` (the base-branch baseline the demo PR gate used, so the ticks match the PR screenshot beside them); no `p` class. When a case is both flipped and has mean_score None, `warn` wins over `f`. Tick CSS: `.ticks{gap:6px} .ticks i{width:6px} .ticks i.warn{background:var(--warn);opacity:1}`.
- Computed values: the site has no build step, so M4 computes every number once with one `uv run python -c` command that loads the files with `Run.model_validate_json` and `casegate.compare.compare` (and `casegate.fmt`), then writes the values into `index.html`. The exact command sits in an HTML comment at the top of the hero. The M4 real-world-test runs the command again and diffs the values against the page. HUD lines: `suite <run.suite> · target <target_version>` / `repeats <repeat> · judge <judge_model>` / `pass <fmt_rate(pass_rate)> ± <fmt_rate(pass_rate_std)>` / `tolerance <max_drop:.2f>`. HUD numbers come from `evals/baseline.json` and `evals/tolerance.json`; the tick flips and `term-gate.txt` come from the `docs/assets/demo-pr-regression/` pair.
- Section "Seven scorers. One verdict.": the real `casegate run` and `casegate gate` output from `docs/assets/term-run.txt` and `term-gate.txt` (§5 Recording).
- Section "The pull request knows before you merge.": `docs/assets/pr-comment-blocked.png` and `pr-comment-passed.png` from the M3 demo PR (the same comment before and after push 2).
- Three cards: trajectory, judge calibration (`n <n> · agreement <fmt_rate(agreement)> · kappa <kappa:.2f>`, None → `—`, from `evals/calibration.json`), variance (std from `evals/baseline.json`).
- Footer: MIT, repo link, version = `casegate.__version__` read at M4 build time; it must equal the PyPI release from M3.
- No build step: static HTML + `site/assets/`. All site CSS lives in `site/assets/site.css`; `index.html` and `banner.html` link it with `<link rel="stylesheet" href="assets/site.css">`. Every image the site uses is copied into `site/assets/`; the site never links `../docs` (Pages uploads only `site/`). Fonts from Google Fonts; three.js from jsDelivr (pinned 0.160.0).
- `.github/workflows/pages.yml`: on push to `main` with paths `[site/**, .github/workflows/pages.yml]`, and `workflow_dispatch`; `permissions: {contents: read, pages: write, id-token: write}`; `concurrency: {group: pages}`; one job `deploy` with `environment: {name: github-pages, url: ${{ steps.deployment.outputs.page_url }}}`; steps checkout (FACTS §5 pin), `actions/configure-pages`, `actions/upload-pages-artifact` with `path: site`, `actions/deploy-pages` with `id: deployment`. Pin all three by the SHAs in FACTS §5 (observed 2026-11-11); at M4, re-check each with `gh api repos/actions/<name>/releases/latest` and update FACTS §5 if a newer release exists. Enable Pages with `gh api -X POST repos/jeffersonnnn/casegate/pages -f build_type=workflow` (user yes), then run `gh workflow run pages.yml --repo jeffersonnnn/casegate` once (the first push happened before Pages existed, so nothing deployed). URL: `https://jeffersonnnn.github.io/casegate/`.
- Lighthouse command: `npx lighthouse@12 <url> --only-categories=accessibility --output=json --chrome-flags="--headless=new"`.

## 9. Layout and phone rules

- Max content width 1160 px, side gutter 24 px (16 px under 400 px).
- Breakpoint 760 px: hero becomes one column with the 3D stage first (max 300 px), panels and cards stack, nav keeps only GitHub, HUD hidden.
- No horizontal scroll at 360 px (code panels scroll inside themselves).
- Tap targets ≥ 44 px (nav links have 14 px vertical padding; the copy button gets 10 px padding + min-height).
- Lighthouse accessibility target 100 on the site.

## 10. Copy tone

Short, factual, numeric. One fact per line, with a unit. Verbs first in instructions. No hype words ("revolutionary", "blazing"). The product is "casegate" in lower case everywhere, including sentence starts in headings.

## 11. Verify checklist (M4 real-world-test)

- Screenshots at 1280 and 390 px of the site, the README (GitHub render), the PR comments.
- Lighthouse accessibility 100 on the site.
- Contrast check of every token pair in §1 and the light banner palette (`scripts/contrast.py`).
- No console errors.
- Layering: the canvas never covers text; the HUD never overlaps the eyebrow or h1 at any width from 360 to 1920.
- The logo never overlaps the headline at any width.
- `prefers-reduced-motion` holds still; WebGL off shows the SVG.
