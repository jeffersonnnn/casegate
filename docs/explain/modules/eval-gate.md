# eval-gate (`.github/workflows/eval-gate.yml`, 82 lines)

**30 seconds:** The workflow that runs casegate on this repo. On a pull request it gates the PR against the baseline from the base branch and posts the sticky comment. On a push to `main` it only runs the suite and uploads the run, which becomes the next baseline.

**2 minutes:** It runs on pull requests (also on `labeled` and `unlabeled`), on pushes to `main`, and by hand, only when agent, eval, source or action files change (`.github/workflows/eval-gate.yml:3-20`). Permissions are `contents: read` and `pull-requests: write` (`.github/workflows/eval-gate.yml:22-24`). A new push to a PR cancels the old run; a push to `main` is never cancelled (`.github/workflows/eval-gate.yml:26-28`). With no API key secret, the first step writes a skip notice and every later step is skipped, so a fork PR is green and costs nothing (`.github/workflows/eval-gate.yml:36-41`). Checkout fetches the full history without saving the token (`.github/workflows/eval-gate.yml:43-49`). On a PR, the baseline comes from the base branch (`.github/workflows/eval-gate.yml:51-56`), and a change to `evals/baseline.json` fails without the label `baseline-update` (`.github/workflows/eval-gate.yml:58-69`). Then it calls the action in this repo with repeat 5, the literal tolerance and the literal must-pass tag (`.github/workflows/eval-gate.yml:71-82`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `.github/workflows/eval-gate.yml:5` | `labeled`, `unlabeled` triggers | adding `baseline-update` must start a new run; `gh run rerun` replays the old labels |
| `.github/workflows/eval-gate.yml:28` | cancel only PR runs | two quick pushes must not spend twice or post twice; a `main` run makes the baseline artifact |
| `.github/workflows/eval-gate.yml:36-41` | skip with a notice when there is no key | fork PRs get no secrets; a skip is honest, a red check would be noise |
| `.github/workflows/eval-gate.yml:49` | `persist-credentials: false` | the suite runs PR code with the API key; that code must not read the token in `.git/config` |
| `.github/workflows/eval-gate.yml:56` | `git show origin/$BASE_REF:evals/baseline.json` | a PR cannot lower its own bar (`docs/adr/0008-baseline-from-base-branch.md`) |
| `.github/workflows/eval-gate.yml:65-66` | save `git diff` output, then `grep -qx` | a pipe into `grep -q` can end in SIGPIPE under pipefail and make the check pass silently |
| `.github/workflows/eval-gate.yml:77` | `gate` only on `pull_request` | on `main` there is nothing to compare with; the run is the new baseline |
| `.github/workflows/eval-gate.yml:79-82` | `max-drop: "0.08"`, `must-pass-tag: adversarial` as literals | a value read from PR files at run time would let the PR raise its own tolerance |

## Trade-off
The baseline is a committed file, updated by a labelled PR (BUILD.md runbook). The alternative, a baseline from the latest `main` run artifact, needs no commit but makes the bar invisible in review and depends on artifact retention. The committed file is reviewable and diffable.

## Failure modes
`max-drop` must equal `evals/tolerance.json` `max_drop` by hand; the re-measure runbook in BUILD.md updates both. Known limit: a same-repo PR can edit this workflow or `action.yml` and so its own gate; CODEOWNERS and branch protection are out of scope (SPEC §18.3). The workflow has not run on GitHub yet: the M3 files are not pushed and the repo has no secret (M3 live notes). The demo PR (BLOCKED, then PASSED on the same comment) is a human step (BUILD.md "M3 demo PR").

## What I would change
Run the action and casegate from the base ref, not the PR head, so a PR cannot change the code that judges it. Cost: a second checkout and a `uses:` path into it; the PR's own `src/` changes then go untested by the gate.

## 10-minute version
The baseline path expression passes `$RUNNER_TEMP/baseline.json` on a PR and `evals/baseline.json` otherwise (`.github/workflows/eval-gate.yml:78`). `HAS_LABEL` is read from the event of that run, not from the API, so a label added after the run started needs a new run (`.github/workflows/eval-gate.yml:63`). The three-dot diff `origin/$BASE_REF...HEAD` lists only the PR's own changes, not changes on the base branch since the fork point. Cost per PR run: about $0.27 at repeat 5 on a cold cache (BUILD.md cost model, an estimate from FACTS.md §4.5).
