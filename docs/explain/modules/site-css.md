# site styles (`site/assets/site.css`, 214 lines)

**30 seconds:** All the CSS for the site and the banner. It holds the dark tokens of `docs/DESIGN.md` §1 as CSS variables, and the hero, tick row, HUD, 3D stage, panels and phone rules.

**2 minutes:** The `:root` block holds the colour and font tokens (`site/assets/site.css:2-15`). Focus rings use the pass colour (`site/assets/site.css:29-32`). The hero has a hairline grid and a two-column grid (`site/assets/site.css:62-74`). Each tick is 6 px wide, grows in with a 43 ms step, and a flipped tick turns red at 900 ms (`site/assets/site.css:103-122`). The HUD sits in the hero corners (`site/assets/site.css:130-136`). The stage is square; the fallback SVG hides once WebGL runs (`site/assets/site.css:138-150`). The rise-in runs only when the page has the `js` class (`site/assets/site.css:189-195`). Under 760 px the hero is one column, the stage moves first and the HUD hides (`site/assets/site.css:197-207`). Reduced motion turns off every animation (`site/assets/site.css:211-214`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `site/assets/site.css:2-15` | tokens as variables | `site/banner.html` sets the light theme by changing only these |
| `site/assets/site.css:112-116` | the flip animation after 900 ms | the row first looks all grey, then two ticks turn red: the regression is shown, not only stated |
| `site/assets/site.css:144` | `.stage.gl .fallback { display: none; }` | the SVG shows until the script proves WebGL works |
| `site/assets/site.css:189-195` | `.js .rise` | with JS off nothing adds `in`, so the rise-in would hide the page |
| `site/assets/site.css:206` | `.hud { display: none; }` on phones | on a phone the hero has no free corner, and the HUD must never overlap the eyebrow or the h1 (`docs/DESIGN.md` §11) |

## Trade-off
One hand-written stylesheet, not Tailwind. The site is one page with no build step; a utility framework would need a build or a large CDN file.

## Failure modes
A token changed here is not checked by `scripts/contrast.py`, which keeps its own copy of the colours (`contrast.md`). Checked locally: Lighthouse accessibility 100, no horizontal scroll from 360 to 1920 px, the HUD never overlaps the eyebrow or the h1.

## What I would change
Generate the `:root` block and the contrast pairs from one token file. Cost: a small script and one more file to keep.

## 10-minute version
`.grid2 > * { min-width: 0; }` stops the wide `pre` blocks from pushing the grid wider than the page on phones; the `pre` scrolls inside its panel instead. The copy button is at least 44 px high for touch.
