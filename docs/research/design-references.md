# casegate design references

Collected 2026-11-11. Facts and references only. Nothing here is built.

Scope: the brand for `casegate` (terminal output, Markdown report, sticky PR comment, README banner, 3D barrier-arm logo, two launch videos). Three directions get prototypes:

| Id | Name | One-line brief |
|---|---|---|
| A | Lab instrument | Dark, quiet, one signal colour (green pass / red fail), monospace, thin lines, oscilloscope feel |
| B | Traffic gate | Bold, warm, amber and black hazard stripes like a barrier arm, heavy sans-serif |
| C | Paper report | Light background, serif headings, printed lab-report feel |

Rule for every reference below: take the technique, never the assets (no images, logos, fonts that are not open licence, copy or code).

---

## 1. Awwwards Site of the Day picks (2026-10-14 to 2026-11-11)

Source list: <https://www.awwwards.com/websites/sites_of_the_day/> (scraped 2026-11-11, page 1 covers Sep 11 to Nov 11, 2026). For each pick I read the Awwwards detail page (date, tags, listed colours) and looked at the Awwwards submission image. Motion notes come from the Awwwards tags, not from a full session on the live site; confirm motion in a browser before you copy timing.

| # | Site | SOTD date | Live URL | Awwwards page | Direction | Technique to take |
|---|---|---|---|---|---|---|
| 1 | ZIRKA Interceptor (Qream) | 2026-11-09 | <https://www.zrk.technology/> | <https://www.awwwards.com/sites/zirka-interceptor> | A | HUD telemetry layer: tiny monospace readouts (coordinates, status lines) in the corners, a thin crosshair "+" marker and hairline circles over a dark field. Big clean sans headline sits low-left. For casegate: print run metadata (suite, target version, repeats, seed) as a small mono telemetry block, and use crosshair ticks as the only ornament. Listed colours `#FC4F00`, `#000000`; tags Animation, 3D, Microinteractions. |
| 2 | DeepBook (HOLOGRAPHIK) | 2026-11-03 | <https://deepbook-v2-wip.webflow.io/> | <https://www.awwwards.com/sites/deepbook> | A | A field of thin vertical tick marks that form a wave, almost all grey, with a few ticks in one accent colour. This is the oscilloscope idea in one image: per-case ticks, grey when unchanged, signal colour only where a case flipped. Listed colours `#1E6EF3`, `#6A7681`; tags Clean, Graphic design, Data Visualization. |
| 3 | FORMAT (Obys) | 2026-10-19 | <https://format.obys.agency/> | <https://www.awwwards.com/sites/format> | B | Full-width blocky wordmark: the letters fill the whole viewport width and are cut from solid rectangles, with a thin rule of small meta text under them. For casegate: set `CASEGATE` edge to edge in a heavy, wide face as the banner and the video end card. Tags Experimental, Typography, Transitions; tech GSAP, Matter.js (physics, fits "arm drops" motion). |
| 4 | Unbelievably Crap (Liubomyr Ulytskyi) | 2026-10-29 | <https://www.unbelievablycrap.com/> | <https://www.awwwards.com/sites/unbelievably-crap> | B | Two solid diagonal bands in one hot colour cross the frame like tape, over a pale halftone; large rotated numerals ("0039") and corner bracket markers. For casegate: the barrier arm as one diagonal band across the frame, and a big rotated counter (pass rate or case count). Listed colours `#FF0000`, `#FFFFFF`; tags Experimental, Filters and Effects, Interaction Design. |
| 5 | Grids (Obys) | 2026-11-02 | <https://grids03.obys.agency/> | <https://www.awwwards.com/sites/grids-1> | C | An index laid out like a printed table of contents: numbered rows (16, 17, 18) with hairline rules, durations right-aligned, thick black bars as section breaks. This maps straight to the Markdown report: case id left, scorer middle, delta right, a heavy rule between suites. Listed colours `#000000`, `#ffffff`; tags Clean, Typography, Locomotive Scroll. |
| 6 | Signal-A Studio | 2026-10-18 | <https://signal-a.studio/> | <https://www.awwwards.com/sites/signal-a-studio> | C | One headline mixes a light condensed serif with a bold grotesk for the key words; the nav is small monospace labels on hairline underlines, plus a live clock and city line. For casegate: serif for the sentence, bold sans or mono only for the verdict word ("**REGRESSION**", "**PASS**"). Listed colours `#000000`, `#FFFFFF`; tags Clean, Minimal, Typography. |

Also seen and not picked (kept for later):

- MECHA (widelab.co), 2026-10-31, <https://www.awwwards.com/sites/mecha>: small serif tagline over a huge geometric industrial wordmark on cool grey `#E9EDEF`. A good C/B bridge if the team wants a serif heading with a mechanical logo.
- Creative Reference Library (Bimo Tri), 2026-11-10, <https://www.awwwards.com/sites/creative-reference-library>: numbered paragraphs "(1)", "(2)" and "/V.01 (2026)" version labels. Fits the report versioning of C.
- Overworld Audio, 2026-10-15, <https://www.awwwards.com/sites/overworld-audio>: dark `#13151f`, serif headline, letter-spaced small-caps nav. Too atmospheric for a CLI, but the quiet dark nav fits A.

---

## 2. Developer-tool references

| # | Reference | URL | What I observed | Technique to take |
|---|---|---|---|---|
| 1 | Charm VHS | <https://github.com/charmbracelet/vhs> | "Write terminal GIFs as code." A `.tape` file is a list of commands (`Output`, `Set FontSize`, `Set Theme`, `Type`, `Sleep`, `Enter`). Outputs GIF, MP4, WebM. MIT licence. | Script every terminal shot (README hero, launch videos) as a tape file in the repo. Shots become reproducible and re-render when the output format changes. Charm's other tools (Lip Gloss "terminal style and layout toolkit", Glamour "stylesheet-driven markdown renderer") are listed on <https://charm.land/>. |
| 2 | Ghostty | <https://ghostty.org/> | Hero is one macOS-style terminal window on near-black. Inside, an ASCII-art ghost is drawn in two tones: grey glyphs for the body, blue glyphs for the outline. One line of text and two outlined buttons below. | Render the barrier-arm logo as ASCII inside a terminal frame for the README and the video opening (direction A). Two tones only: muted body, signal colour for the edge. |
| 3 | Astral uv docs | <https://docs.astral.sh/uv/> | Built with MkDocs Material 9.7.6 (from the page `generator` meta). The hero benchmark chart ships as two images with `#only-light` and `#only-dark` URL fragments. Console blocks show a `$` prompt and real, terse output with timings: "Resolved 2 packages in 170ms", "Installed 2 packages in 1ms", "All checks passed!". | Keep output short, one fact per line, always with a number and a unit. Show one benchmark-style chart (for casegate: pass rate baseline vs run) in a light and a dark version. |
| 4 | Vercel Geist | <https://vercel.com/geist/introduction> | Design system with typefaces Geist Sans, Geist Mono, Geist Serif and Geist Pixel; foundations pages for Colors, Typography, Materials and a dedicated "Terminal" page; "high contrast and accessible color system". | Treat terminal output as a first-class foundation with its own tokens, same as web colours. Geist and Geist Mono are OFL on Google Fonts (see section 3), so they are usable. |
| 5 | Linear changelog | <https://linear.app/changelog> | Dated entries (latest: 2026-11-05 "Mobile Diffs", 2026-10-22 "More ways to run and share Loops", 2026-10-08 "Stacked pull requests"). Each entry: optional hero image, title, body, then grouped lists such as "Improvements" and "Fixes". | Report structure: one headline verdict, a short paragraph, then grouped lists ("Regressions", "Fixes", "Errors") in a fixed order. |

Tooling fact for the terminal surface (Rich, the library casegate uses): progress columns include `BarColumn`, `TextColumn`, `TimeElapsedColumn`, `TimeRemainingColumn`, `MofNCompleteColumn`, `SpinnerColumn` and custom `ProgressColumn` subclasses (<https://rich.readthedocs.io/en/stable/progress.html>). `Console(record=True)` with `save_svg` / `export_svg` / `save_html` exports what was printed (<https://rich.readthedocs.io/en/stable/console.html>). That gives a static SVG of the real summary table for the README, in the same palette as the terminal.

---

## 3. Fonts (all free, all SIL Open Font License)

Check method: every family returned HTTP 200 from the Google Fonts CSS API (`https://fonts.googleapis.com/css2?family=...`), and its `METADATA.pb` sits under `ofl/` in the official repo <https://github.com/google/fonts>. Specimen pages returned 200 except where noted.

| Direction | Role | Family | Why | URL |
|---|---|---|---|---|
| A | Display | IBM Plex Sans Condensed | Narrow, technical labels, like the face of an instrument | <https://fonts.google.com/specimen/IBM+Plex+Sans+Condensed> |
| A | Body | IBM Plex Sans | Same skeleton as the display and mono | <https://fonts.google.com/specimen/IBM+Plex+Sans> |
| A | Mono | IBM Plex Mono | Thin weights read well on dark | <https://fonts.google.com/specimen/IBM+Plex+Mono> |
| A | Alt set | Geist / Geist Mono (wght 100 to 900) | Closer to current dev-tool look | <https://fonts.google.com/specimen/Geist>, <https://fonts.google.com/specimen/Geist+Mono> |
| B | Display | Archivo (wght 100 to 900, wdth 62 to 125) | Black weight at 125 width gives the edge-to-edge FORMAT-style wordmark | <https://fonts.google.com/specimen/Archivo> |
| B | Body | Inter | Neutral, sturdy at small sizes next to a loud display | <https://fonts.google.com/specimen/Inter> |
| B | Mono | JetBrains Mono (wght 100 to 800) | Has heavy weights, so mono text can stay bold | <https://fonts.google.com/specimen/JetBrains+Mono> |
| B | Alt display | Big Shoulders Stencil (opsz 10 to 72, wght 100 to 900) | Stencil cuts look like road and barrier signage. Note: the family is now "Big Shoulders Stencil"; the old name "Big Shoulders Stencil Display" still works in the CSS API but its specimen URL returns 404 | <https://fonts.google.com/specimen/Big+Shoulders+Stencil> |
| C | Display | Source Serif 4 (opsz 8 to 60, wght 200 to 900) | Optical sizes give a true display cut for headings | <https://fonts.google.com/specimen/Source+Serif+4> |
| C | Body | Source Sans 3 | Same superfamily, reads as a printed report | <https://fonts.google.com/specimen/Source+Sans+3> |
| C | Mono | Source Code Pro | Completes the superfamily for case ids and numbers | <https://fonts.google.com/specimen/Source+Code+Pro> |
| C | Alt display | Newsreader (opsz 6 to 72, wght 200 to 800) | More editorial, warmer | <https://fonts.google.com/specimen/Newsreader> |

Note: fonts apply to the web page, the banner images and the videos only. The terminal uses the viewer's font, and GitHub uses its own fonts (see section 5).

---

## 4. Palettes and WCAG contrast

Script: WCAG 2.x relative luminance and contrast ratio, `(L1 + 0.05) / (L2 + 0.05)`. The script is short and kept below so the numbers can be re-run.

Targets: every text pair at least 4.5:1; every pass/fail on background at least 3:1. I also checked every pair on `surface` and checked pass/fail against 4.5:1 so they can be used as normal-size text.

Status mapping to the glossary (`CONTEXT.md`): `pass` token = case status `pass`; `fail` token = `fail` and regressions; `warn` token = `error` (target or scorer could not finish; not a fail, per ADR 0003).

### A Lab instrument (dark)

| Token | Hex |
|---|---|
| bg | `#0B0F0E` |
| surface | `#141A18` |
| text | `#E3ECE7` |
| muted | `#8FA39A` |
| pass | `#3DDC84` |
| fail | `#FF5D5D` |
| warn | `#E8C547` |
| accent | `#5CC8FF` (links and focus only; drop it if the "one signal colour" rule must be strict) |

| Pair | Ratio | Min | Result |
|---|---:|---:|---|
| text on bg | 16.00:1 | 4.5 | PASS |
| muted on bg | 7.23:1 | 4.5 | PASS |
| accent on bg | 10.25:1 | 4.5 | PASS |
| text on surface | 14.63:1 | 4.5 | PASS |
| muted on surface | 6.61:1 | 4.5 | PASS |
| pass on bg | 10.81:1 | 3.0 | PASS |
| fail on bg | 6.41:1 | 3.0 | PASS |
| warn on bg | 11.49:1 | 3.0 | PASS |
| pass on surface | 9.88:1 | 3.0 | PASS |
| fail on surface | 5.86:1 | 3.0 | PASS |
| warn on surface | 10.51:1 | 3.0 | PASS |

### B Traffic gate (warm black with amber)

| Token | Hex |
|---|---|
| bg | `#14110D` |
| surface | `#221C15` |
| text | `#FFF4E2` |
| muted | `#C4B49C` |
| pass | `#6BD68A` |
| fail | `#FF5A3C` |
| warn | `#FFB000` |
| accent | `#FFB000` (same as warn on purpose: in the traffic metaphor amber is the brand and the caution light; hazard stripes are `accent` and `bg` in alternation) |

| Pair | Ratio | Min | Result |
|---|---:|---:|---|
| text on bg | 17.29:1 | 4.5 | PASS |
| muted on bg | 9.28:1 | 4.5 | PASS |
| accent on bg | 10.27:1 | 4.5 | PASS |
| text on surface | 15.50:1 | 4.5 | PASS |
| muted on surface | 8.32:1 | 4.5 | PASS |
| pass on bg | 10.41:1 | 3.0 | PASS |
| fail on bg | 6.08:1 | 3.0 | PASS |
| warn on bg | 10.27:1 | 3.0 | PASS |
| pass on surface | 9.33:1 | 3.0 | PASS |
| fail on surface | 5.45:1 | 3.0 | PASS |
| warn on surface | 9.21:1 | 3.0 | PASS |
| bg (black) text on amber band | 10.27:1 | 4.5 | PASS |

Risk for B: amber `warn` and red-orange `fail` are close in hue. Always pair them with a word or glyph (see below).

### C Paper report (light)

| Token | Hex |
|---|---|
| bg | `#F7F4EC` |
| surface | `#EDE8DB` |
| text | `#1C1A17` |
| muted | `#5C574E` |
| pass | `#1D6B40` |
| fail | `#B3261E` |
| warn | `#855400` |
| accent | `#23408E` (ink blue for links) |

| Pair | Ratio | Min | Result |
|---|---:|---:|---|
| text on bg | 15.80:1 | 4.5 | PASS |
| muted on bg | 6.52:1 | 4.5 | PASS |
| accent on bg | 8.70:1 | 4.5 | PASS |
| text on surface | 14.19:1 | 4.5 | PASS |
| muted on surface | 5.86:1 | 4.5 | PASS |
| pass on bg | 5.92:1 | 3.0 | PASS |
| fail on bg | 5.95:1 | 3.0 | PASS |
| warn on bg | 5.85:1 | 3.0 | PASS |
| pass on surface | 5.32:1 | 3.0 | PASS |
| fail on surface | 5.34:1 | 3.0 | PASS |
| warn on surface | 5.26:1 | 3.0 | PASS |

All pass and fail tokens in all three palettes also clear 4.5:1 on bg, so they can be used as body-size text.

Colour-blind note (all directions): green and red alone fail for red-green colour blindness. Every status also needs a non-colour cue: a word (`PASS`, `FAIL`, `ERROR`) or a glyph (check, cross, triangle). The barrier-arm logo already does this with position (up = pass, down = fail).

### Contrast script

```python
def lum(hex_):
    h = hex_.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

print(f"{ratio('#E3ECE7', '#0B0F0E'):.2f}")  # 16.00, A text on bg
```

---

## 5. How GitHub renders Markdown (README, PR comment, job summary)

These limits decide how the Markdown report and the sticky PR comment can look "designed".

### What is the same everywhere

- READMEs, issues, PR comments and Actions job summaries all use GitHub Flavored Markdown (GFM). Job summaries: "Job summaries support GitHub flavored Markdown" (<https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary>).
- Tables work "in comments, issues, pull requests, and wikis" (<https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-tables>). Column alignment uses colons in the header row (`:--`, `:-:`, `--:`); links, inline code and text styling work in cells; escape a pipe as `\|`; a blank line is required before the table.

### What is removed (no custom CSS)

- GitHub sanitizes the HTML, "aggressively removing things that could harm you and your kin, such as `script` tags, inline-styles, and `class` or `id` attributes" (<https://github.com/github/markup#readme>, step 2). So: no `style=`, no `class=`, no colours from CSS, no web fonts.
- The GFM spec "tagfilter" extension escapes these tags: `<title>`, `<textarea>`, `<style>`, `<xmp>`, `<iframe>`, `<noembed>`, `<noframes>`, `<script>`, `<plaintext>` (<https://github.github.com/gfm/#disallowed-raw-html-extension->).

### What survives (tags and attributes)

GitHub's docs do not publish one full allowlist. The closest public source is the open-source `html-pipeline` SanitizationFilter (v2.14.3, <https://github.com/gjtorikian/html-pipeline/blob/v2.14.3/lib/html/pipeline/sanitization_filter.rb>). Treat it as approximate: GitHub's live renderer also accepts `<picture>` and `<source>`, which that list does not name. Test anything critical in a scratch PR.

- Elements in that list: `h1`-`h6`, `br`, `b`, `i`, `strong`, `em`, `a`, `pre`, `code`, `img`, `tt`, `div`, `ins`, `del`, `sup`, `sub`, `p`, `ol`, `ul`, `li`, `table`, `thead`, `tbody`, `tfoot`, `tr`, `td`, `th`, `blockquote`, `dl`, `dt`, `dd`, `kbd`, `q`, `samp`, `var`, `hr`, `ruby`, `rt`, `rp`, `s`, `strike`, `summary`, `details`, `caption`, `figure`, `figcaption`, `abbr`, `bdo`, `cite`, `dfn`, `mark`, `small`, `span`, `time`, `wbr`.
- Useful attributes in that list: `align`, `width`, `height`, `alt`, `title`, `open`, `colspan`, `rowspan`, `valign`, `nowrap`, `border`, `media`, `lang`, `dir`, `aria-label`, `aria-hidden`, `name`; `a[href]`, `img[src]`.

Documented features on docs.github.com:

| Feature | What it gives the design | Source |
|---|---|---|
| `<picture>` with `prefers-color-scheme` sources | Light and dark README banner (and charts) from one block. The `<img>` inside is the fallback when no source matches. | <https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/quickstart-for-writing-on-github#adding-an-image-to-suit-your-visitors>; "The `<picture>` HTML element is supported" at <https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#the-picture-element> |
| `<details>` / `<summary>`, `open` attribute | Collapse the full case table under a one-line verdict. Leave a blank line after `</summary>` so Markdown inside renders. | <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-collapsed-sections> |
| `<sub>`, `<sup>`, `<ins>` | `<sub>` for small footer metadata (run id, seed, casegate version). | basic-writing-and-formatting-syntax, "Styling text" |
| `<!-- comment -->` | Hidden content. A hidden marker line lets the Action find and update its own sticky comment. | basic-writing-and-formatting-syntax, "Hiding content with comments" |
| Alerts `> [!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]` | The only built-in coloured boxes. GitHub advises "one or two per article", not back to back, and alerts "cannot be nested within other elements". Example use: `[!CAUTION]` for a blocked PR, `[!WARNING]` for error cases. | basic-writing-and-formatting-syntax, "Alerts" |
| Emoji shortcodes (`:white_check_mark:` style) | Colour cues that survive sanitizing. | basic-writing-and-formatting-syntax, "Using emojis" |
| Colour models in backticks (`` `#RRGGBB` ``, `` `rgb(R,G,B)` ``, `` `hsl(H,S,L)` ``) | Shows a small swatch. Only "in issues, pull requests, and discussions", and no spaces inside the backticks. Useful in a PR comment, not in a README. | basic-writing-and-formatting-syntax, "Supported color models" |
| Footnotes `[^1]` | Report-style notes (direction C). | basic-writing-and-formatting-syntax, "Footnotes" |
| Fenced code with a language id (Linguist) | Monospace blocks with GitHub's own highlighting; the colours come from GitHub's theme, not from casegate. | <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-and-highlighting-code-blocks> |
| Mermaid, GeoJSON, TopoJSON, ASCII STL diagrams | Mermaid charts render "in GitHub Issues, GitHub Discussions, pull requests, wikis, and Markdown files". A Mermaid pie or bar of pass/fail is possible; the colours are Mermaid's. | <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams> |
| Custom anchors `<a name="...">` | Jump links from the summary to a case row; not shown in the outline. | basic-writing-and-formatting-syntax, "Custom anchors" |
| Images, relative links | In comments, repo images need `../blob/main/path.png?raw=true`; in `.md` files a plain relative path works. | basic-writing-and-formatting-syntax, "Images" |
| Job summary limits | 1 MiB per step; "a maximum of 20 job summaries from steps are displayed per job". | workflow-commands, "Step isolation and limits" |

Not confirmed on docs.github.com: the maximum length of a PR comment body (often quoted as 65,536 characters). Check it against the REST API before the report design depends on it.

### What this means for each direction

- Brand colour reaches GitHub only through images (banner, SVG chart exported by Rich, badges) and through emoji and alerts. Text colour and fonts are GitHub's.
- A: lean on fenced code blocks and `<samp>`/`<kbd>`-style monospace; ship a dark and a light SVG of the summary table via `<picture>`.
- B: put the hazard stripes and heavy wordmark in the `<picture>` banner; in the comment, use one `[!CAUTION]` alert for a blocked PR.
- C: the closest fit to GitHub's own look: tables with right-aligned numbers, footnotes, `<sub>` metadata, `<details>` for the full case list.
