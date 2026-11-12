# site page (`site/index.html`, 205 lines, and `site/assets/mark.js`, 91 lines)

**30 seconds:** The one-page site for casegate on GitHub Pages. It shows what casegate does, the real terminal output of a run and of the gate, and the two PR comment screenshots from the demo PR. Every number on it comes from a committed run file, through one command that is written in the page (`docs/DESIGN.md` §8).

**2 minutes:** The head links the fonts, `assets/site.css` and the icons, and marks the page `js` at once so the rise-in runs only with JS (`site/index.html:9-16`). The hero comment holds the exact value command and its output (`site/index.html:33-41`). The HUD lines, the h1, the install chip and the tick row follow (`site/index.html:42-67`); the two red ticks are the two cases that flipped in the demo PR. The 3D stage is a `role="img"` div with the state text outside it (`site/index.html:70-73`). The "Seven scorers" section shows `docs/assets/term-run.txt` and `term-gate.txt` with colour spans (`site/index.html:78-143`). The gate section shows the blocked and passed screenshots and three cards (`site/index.html:145-180`). One script handles the copy button and the rise-in (`site/index.html:185-201`). A module script tag loads `assets/mark.js` (`site/index.html:203`), which loads three.js and runs the logo cycle (`site/assets/mark.js:1-91`). The scene sits in its own file so the page stays under the 250-line rule.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `site/index.html:33-41` | the value command and its output in an HTML comment | the site has no build step; the comment lets the real-world-test run the command again and diff it with the page |
| `site/index.html:70` | `role="img"` on the stage, canvas and SVG `aria-hidden` | axe flags `aria-label` on a plain div, which would block Lighthouse 100 (`docs/DESIGN.md` §8) |
| `site/index.html:73` | `#state` outside the stage, `aria-live="off"` | the text changes every cycle; a screen reader must not read it each time |
| `site/assets/mark.js:10` | `await import(...)` in a `try` | no network or no WebGL leaves the fallback SVG, not a broken page |
| `site/assets/mark.js:62` | reduced motion holds the pass pose | `prefers-reduced-motion` must hold still (`docs/DESIGN.md` §11) |
| `site/assets/mark.js:76-90` | the loop stops when the tab is hidden or the stage is off screen | a looping WebGL canvas costs battery for nothing when no one sees it |

## Trade-off
Static HTML with the numbers written in, not a page that fetches `evals/baseline.json` at load time. A fetch would follow every new baseline, but Pages uploads only `site/` and a fetch needs JS. Written-in values work with JS off, and the comment command makes them checkable (`docs/adr/0007-design-direction-lab-instrument.md` for the look).

## Failure modes
Stale numbers: a new baseline does not change the page until someone runs the command again. The footer says `0.1.0`, but casegate is not on PyPI yet, so the `uv add casegate` chip does not install anything until the M3 release (M4 live notes). The section title "Seven scorers" follows DESIGN §8, but README says eight scorer types in seven files (`README.md:108`). Checked on a local server only: Lighthouse accessibility 100 on mobile and desktop (`docs/assets/runs/lighthouse-local-mobile-m4.json`), no horizontal scroll from 360 to 1920 px, the fallback SVG with WebGL off. The deployed site is not live yet.

## What I would change
Run the value command in `pages.yml`, so the page cannot go stale. Cost: a build step in the deploy job, which DESIGN avoided on purpose.

## 10-minute version
Tick heights are `8 + round(36 × mean_score)` px from `evals/baseline.json`; the flips come from `compare` on the demo pair in `docs/assets/demo-pr-regression/` (`docs/DESIGN.md` §8). The pointer moves the logo a little, but only without reduced motion (`site/assets/mark.js:57-58`). `angleAt` is the same function as in the render harness (`site/assets/mark.js:45-55` `angleAt`). The page was 294 lines before the scene moved to `mark.js` (2026-11-12 fix); see the readability table in `README.md`.
