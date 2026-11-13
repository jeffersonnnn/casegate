# film scene 1: the diff (`launch/film/compositions/diff.html`, 80 lines)

**30 seconds:** The first 8.5 s of the film. It shows the real `store.py` diff of the demo PR, the green unit tests and lint, and then the claim "The agent got worse." It sets up the problem: the change looks safe and every normal check passes.

**2 minutes:** The telemetry lines name PR #1 and push 1, `toy-agent@6-cents` (`launch/film/compositions/diff.html:40-41`). The panel holds the real diff of commit `a62cf60`: three context lines, five added lines that turn money into integer cents, and `return data` (`launch/film/compositions/diff.html:45-46`). The check row says "✓ unit tests 468 passed ✓ lint" (`launch/film/compositions/diff.html:48`; 468 is from FACTS.md §9). On the timeline, a green sweep marks each added line from 0.4 s (`launch/film/compositions/diff.html:58-60`). The title words blur in (`launch/film/compositions/diff.html:62`). The panel rises 60 px to make room, and the checks blur in at 3.0 s (`launch/film/compositions/diff.html:64-65`). At 4.9 to 5.4 s the title leaves, the panel steps back and blurs, and the claim words come in (`launch/film/compositions/diff.html:67-69`). "worse." starts 40 px high, drops, squashes and springs back (`launch/film/compositions/diff.html:71-76`). A vertical whip ends the scene at 8.18 s (`launch/film/compositions/diff.html:78`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `launch/film/compositions/diff.html:46` | the five `+` lines, as in `git show a62cf60` | every frame is a real artefact of the demo PR (launch/SPEC.md "Approved figures") |
| `launch/film/compositions/diff.html:28-29` | `isolation: isolate` on the line, sweep at `z-index: -1` | the sweep must paint under the text but over the panel background |
| `launch/film/compositions/diff.html:71-76` | anticipation, drop, squash 0.86, elastic settle | the word lands heavy; the Lasseter use is listed in launch/REVIEW.md |

## Trade-off
The diff is rebuilt as HTML text, not a screenshot of GitHub. A screenshot would look more "real", but it goes soft at 1080p and it rebuilds GitHub chrome, which reads as a mock-up (launch/STORYLINES.md, storyline B cut).

## Failure modes
The final `hyperframes check` keeps 2 `negative_z_index` warnings on `.dl.add .sw`; the parent has `isolation: isolate`, so the sweep renders (checked in frames, launch/REVIEW.md "Warnings kept on purpose"). It also lists `content_overlap` info on the added lines, because the sweep span and the text share a box.

## What I would change
Read the diff lines from `git show` at build time instead of pasting them. Cost: a build step, and HyperFrames would need the text before it renders.

## 10-minute version
The scene reads no run file: the numbers here are the commit, "468 passed" and PR #1 (launch/SPEC.md table). The whip out goes up (`y: -240`) and the run scene comes in from below (`launch/film/compositions/run.html:85`), so the motion reads as one camera move.
