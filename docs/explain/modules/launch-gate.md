# film scene 3: the gate (`launch/film/compositions/gate.html`, 210 lines)

**30 seconds:** Film seconds 18.5 to 45, the core of the film. The 3D arm drops on BLOCKED, the real sticky comment comes in, push 2 re-runs the cases, the arm lifts and the same comment turns to PASSED. Then the claim and the end card with `uv add casegate`. It shows what the gate does, not only a number.

**2 minutes:** The mark is a 760 px WebGL canvas inside a wrapper that GSAP moves (`launch/film/compositions/gate.html:20-21`). The comment card is rebuilt in HTML from `casegate-comment.md` (BLOCKED) and the passed screenshot (PASSED), as two layers in one card (`launch/film/compositions/gate.html:73-116`). The tick heights for the regression and the fix come from the two run files (`launch/film/compositions/gate.html:129-130`). `cycleFrame` maps a scene frame to a DESIGN §4 cycle frame: up and drop, hold blocked, lift, then the pass pose (`launch/film/compositions/gate.html:145-150` `cycleFrame`). The mark draws in a `buildReady` promise, because three.js loads async (`launch/film/compositions/gate.html:157-165`). The timeline drives one clock, and every update renders the pose for that frame and sets the state label (`launch/film/compositions/gate.html:166-167`). For the drop the mark is alone and 1.35× large; then it moves left on an arc while the card enters (`launch/film/compositions/gate.html:172-177`). The headline and the flips get highlight sweeps, with a scroll between them (`launch/film/compositions/gate.html:182-184`). Push 2 arrives at 8.3 s and the ticks run again 0.1 s apart (`launch/film/compositions/gate.html:186-188`). At scene 10.8 s the BLOCKED layer goes out and the PASSED layer comes in, on film frame 880 (`launch/film/compositions/gate.html:190-193`). The card leaves and the claim comes in (`launch/film/compositions/gate.html:196-200`); the end card follows (`launch/film/compositions/gate.html:201-207`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `launch/film/compositions/gate.html:145-150` | `cycleFrame`: `sf + 18`, hold 90, `sf − 184`, 0 | the drop lands on scene frame 64 = film frame 619 and the green colour on film frame 880 (launch/SPEC.md "Logo cycle at 30 fps") |
| `launch/film/compositions/gate.html:161-162` | `Math.round(clock.t * FPS)` then `/ FPS` | every pose is a whole 30 fps frame, so a seek gives the same pose |
| `launch/film/compositions/gate.html:163-164` | the state label reads the returned `st.f` | the label, the arm colour and the click change on the same frame |
| `launch/film/compositions/gate.html:172` | scale 1.35, centred, before the hit | staging: one thing on screen when the arm drops |
| `launch/film/compositions/gate.html:191-192` | BLOCKED out and PASSED in, 0.067 s each, at 10.8 | the same comment is edited in place, as on the real PR (FACTS.md §9, OPEN-2) |
| `launch/film/compositions/gate.html:24` | the mini tick row at top 790 | below the state label after the move; before the fix it covered the label (04-failures.md) |

## Trade-off
The comment is rebuilt in HTML at about 1.6×, not the 828 px PNG scaled up. The PNG goes soft at 1080p (launch/REVIEW.md "Creative calls"). The cost: the HTML is a transcription, so a typo would be a false screen; each value was taken from `docs/assets/demo-pr-regression/casegate-comment.md` and `docs/assets/pr-comment-passed.png`.

## Failure modes
The green re-run ticks use the baseline heights, because the push-2 run JSON is not in the repo; no number is attached to them (launch/SPEC.md). The final `hyperframes check` keeps info findings for the card: it runs past the canvas while it scrolls (`canvas_overflow`, `container_overflow`), and the `.hlbar` spans give `negative_z_index` warnings, with `isolation: isolate` on the parent (`launch/film/compositions/gate.html:50-51`). `.g-tele` sets `font-size` twice, 22px then 20px; the second wins and the first is dead (`launch/film/compositions/gate.html:16`).

## What I would change
Download the push-2 run artifact and commit it, so the green ticks have their own heights. Cost: one `gh run download` and a file under `docs/assets/`.

## 10-minute version
Time map: scene time + 18.5 = film time. Drop: scene 2.133 s, film 20.633 s, thud peak measured at 20.6336 s. PASSED: scene 10.833 s, film 29.333 s, click peak 29.3450 s, one frame after (launch/REVIEW.md "Sync"). The mark turns in on Y as it lands on the end card (`launch/film/compositions/gate.html:153` `rotYAt`). The end card types `uv add casegate` one letter per 0.05 s (`launch/film/compositions/gate.html:205`), the text of the site install chip.
