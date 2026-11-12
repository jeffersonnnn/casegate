# contrast (`scripts/contrast.py`, 73 lines)

**30 seconds:** A WCAG 2.x contrast check for every colour pair the brand uses. It prints each ratio and exits 1 if a pair is under its minimum. It is the proof behind the ratio tables in `docs/DESIGN.md` §1 and §7.

**2 minutes:** `_channel` turns one 0-255 value into linear light with the sRGB curve (`scripts/contrast.py:14-16` `_channel`). `luminance` weights the three channels (`scripts/contrast.py:19-24` `luminance`). `ratio` puts the lighter colour on top and adds 0.05 to each side (`scripts/contrast.py:27-29` `ratio`). The pairs list holds every dark text token on the page background and on the surface, and the light banner pairs (`scripts/contrast.py:32-51`). Text needs 4.5:1 and graphics need 3.0:1 (`scripts/contrast.py:10-11`). With no arguments `main` prints the table and counts the failures; with two colours it prints one ratio (`scripts/contrast.py:54-69` `main`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `scripts/contrast.py:10-11` | two minimums | WCAG 1.4.3 for text, 1.4.11 for graphics; the arm is a graphic, so 3.83:1 is enough |
| `scripts/contrast.py:28` | `sorted(..., reverse=True)` | the ratio must not depend on which colour is passed first |
| `scripts/contrast.py:36-44` | each dark token on both bg and surface | text sits on both, and the surface is the lower-contrast case |
| `scripts/contrast.py:69` | exit 1 on any failure | a palette change that breaks contrast fails a command, not only a review |

## Trade-off
A 73-line script with no dependency, not a library such as `wcag-contrast-ratio`. The formula is short and sits in `_channel`, `luminance` and `ratio`, so it can be checked by hand. A library would hide that.

## Failure modes
A colour that is not `#RRGGBB` raises `ValueError` (`scripts/contrast.py:21-22`). Hairlines are `rgba` and are not in the pairs list (`scripts/contrast.py:32-51`). The pairs are copied from DESIGN by hand, so a token changed in `site/assets/site.css` and not here is not caught. No test file; M4 compared the output with the DESIGN §1 table (16.00, 14.63, 6.41 matched).

## What I would change
Read the pairs from the `:root` block of `site/assets/site.css` and from the light token block of `site/banner.html`, so the check follows the real tokens. Cost: a small CSS parser and a mapping of which token sits on which background.

## 10-minute version
The light palette was designed with this script: the dark post colour `#E3ECE7` is 1.12:1 on `#F4F7F5` (FACTS.md §7), so the light logo uses `#0B0F0E` for the post and `#1A8F4E` for the arm. The output is in `03-numbers.md` and `docs/DESIGN.md` §7.
