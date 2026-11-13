# the vertical cut scene (`launch/cut/compositions/cut.html`, 151 lines)

**30 seconds:** The one scene of the 20 s vertical cut. It is only the gate moment from the film: the tick row with two flips, the arm drop and BLOCKED, push 2, the arm lift and PASSED, then `casegate` and `uv add casegate`. It is made for a phone feed, where 20 s is the budget.

**2 minutes:** The layout stacks the mark on top (900 px canvas), the state label, the claim "Unit tests pass. The agent got worse.", the comment card and the tick row at the bottom (`launch/cut/compositions/cut.html:18-44`). The comment card has the BLOCKED and PASSED layers, shorter than in the film: headline, lede, two table rows, the flip count (`launch/cut/compositions/cut.html:55-78`). The tick heights are at 3× (`launch/cut/compositions/cut.html:89-95`). `cycleFrame` here is `sf + 7`, hold 90 from frame 83, then `sf − 210` (`launch/cut/compositions/cut.html:100-105` `cycleFrame`). The draw callback renders the pose and sets the label, as in the film (`launch/cut/compositions/cut.html:111-115`). The ticks grow from 0.1 s and the two flips turn red at 1.7 s (`launch/cut/compositions/cut.html:119-120`). At the drop the claim leaves and the card rises into its place (`launch/cut/compositions/cut.html:123-125`). Push 2: the chip takes the state line and the ticks run again (`launch/cut/compositions/cut.html:131-136`). On frame 351 the layers swap (`launch/cut/compositions/cut.html:138-140`). The end moves the mark down and wipes in the name and the command (`launch/cut/compositions/cut.html:142-148`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `launch/cut/compositions/cut.html:100-105` | `cycleFrame` with offsets 7 and 210 | drop on frame 75 (cycle frame 82), green on frame 351 (cycle frame 141), launch/SPEC.md |
| `launch/cut/compositions/cut.html:53` | the claim is on screen at frame 0 | the hook: a phone viewer decides in the first second |
| `launch/cut/compositions/cut.html:131-132` | the chip replaces the state label | the frame is narrow; two lines in the same place would collide |

## Trade-off
The cut repeats the film's logic in its own file, not a shared scene with two layouts. A shared scene would remove the copy, but every position and time differs. The copy keeps each file simple to read and to check against launch/SPEC.md.

## Failure modes
The same hand-copied tick heights as the film (`launch/cut/compositions/cut.html:89-90`), with no test against the run files. The `container_overflow` warning on `#c-mark` is kept on purpose (launch/REVIEW.md).

## What I would change
Move the tick arrays and `cycleFrame` offsets into one shared data file for both videos. Cost: each project copies it in `make_assets.sh`, like `mark3d.js`.

## 10-minute version
Frames looked at: 0, 75, 150, 300, 350, 351, 450, 599 (launch/REVIEW.md). Sync on the delivered file: thud peak 2.5006 s = frame 75.02, click peak 11.7116 s = frame 351.35. The mark wrapper sits at top −34 px, so the post base sits higher on the screen (`launch/cut/compositions/cut.html:18`).
