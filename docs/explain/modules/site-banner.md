# README banner (`site/banner.html`, 117 lines)

**30 seconds:** The source page for the README banner. A screenshot of it at 1280 × 320 and scale 2 gives `docs/assets/banner-dark.png` and `banner-light.png`. A third mode, `?size=x`, gives the 1500 × 500 X header layout that M5 uses.

**2 minutes:** The head comment gives the three screenshot commands (`site/banner.html:7-13`). A small script reads `?theme=light` and sets the light tokens on `:root`, and reads `?size=x` (`site/banner.html:18-32`). The page style places the text block, the tick row, the logo and the HUD text (`site/banner.html:33-67`). The X header rules keep the text and ticks inside one box and hide the rest (`site/banner.html:69-77`). The body has the eyebrow, the name, one line of description, 15 ticks with 2 red flips, the logo image and the telemetry (`site/banner.html:81-110`). In light mode a last script swaps the logo for the light render (`site/banner.html:111-115`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `site/banner.html:23-27` | the light tokens override the CSS variables | one stylesheet serves both themes; only the variables change |
| `site/banner.html:52` | tick animation off | a screenshot must be the same every time |
| `site/banner.html:53` | light grey ticks at opacity 1 | the measured 4.99:1 is for `#5E6E67` at full opacity; at 0.45 the ratio would not hold |
| `site/banner.html:69-77` | X header box x 500-960, y 100-333 | X covers the bottom left with the profile photo; M5 adds the mark on the right |

## Trade-off
An HTML page and a screenshot, not a hand-made image. The banner uses the same fonts, tokens and tick data as the site, so a change in one place shows in both. The cost: the PNGs must be taken again by hand after a change.

## Failure modes
The README on `main` already points at the two PNGs, but they are not pushed, so github.com shows a broken image now (M4 real-world-test, `04-failures.md`). The tick data and the telemetry are copied from `site/index.html`, so a new baseline needs both pages updated. Checked at build time: fonts loaded, the correct logo loaded, no console errors, no overflow, PNGs 2560 × 640 (`sips`).

## What I would change
Add a small script that takes all three screenshots in one command, next to `scripts/render_mark.py`. Cost: one more Playwright script in the scratch venv.

## 10-minute version
The light colours come from `docs/DESIGN.md` §7 and their ratios from `scripts/contrast.py` (`03-numbers.md`). The README uses a `<picture>` with `prefers-color-scheme` to pick the PNG (`README.md:1-5`). The X check render (4500 × 1500) was not committed.
