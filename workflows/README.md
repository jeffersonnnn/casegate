# workflows — run order

Each file is a self-contained Workflow script for one milestone in `BUILD.md`. Agents in each script read only the repo docs (README → SPEC → BUILD → CONTEXT → FACTS → DESIGN → ADRs). Each script ends with Verify (lint, types, tests, coverage), an adversarial Review where money or security is involved (M2, M3), a Live stage where real APIs or human-gated steps apply, and a recursive Real-world-test that re-checks every earlier milestone's anchors.

| Order | Script | Needs before | Human-gated inside |
|---|---|---|---|
| 1 | `m0-scaffold.js` | nothing | none |
| 2 | `m1-core.js` | M0 observed | none |
| 3 | `m2-judge-gate-toy.js` | M1 observed | real API spend ≤ $2 (key in `.env`) |
| 4 | `m3-calibrate-action-publish.js` | M2 observed | public repo + push, repo secret, demo PR, PyPI publishers, 40 labels, tag v0.1.0 |
| 5 | `m4-brand-site.js` | M3 observed | push, enable Pages |
| 6 | `m5-launch-assets.js` | M4 observed | none |

Run one at a time: `Workflow({scriptPath: "<repo>/workflows/m0-scaffold.js"})`. A milestone is done only when the result has `all_load_bearing_observed: true`. If a script stops (Verify failed or a human step is pending), fix what it reports, then resume with `resumeFromRunId`.

Syntax check (all scripts): `for f in workflows/m*.js; do sed -e 's/^export const meta/const meta/' "$f" | { echo "(async () => {"; cat; echo "})();"; } > /tmp/chk.js && node --check /tmp/chk.js && echo "$f ok"; done`

## Post-/compact prompt

Paste this after `/compact` (or in a new session) to drive the build:

```
Build casegate from the kit in ~/Desktop/new-portfolio/evals. Read README.md, then SPEC.md (authoritative), then BUILD.md and workflows/README.md. Run the milestone workflows in order, one at a time, with the Workflow tool (scriptPath = workflows/mN-*.js). After each run, read its result: fix what Verify, Review or Real-world-test flags, and treat a milestone as done only when all_load_bearing_observed = true (which includes the Explain stage's check_passed). After each milestone, tell me to run `/walkthrough tour` on what was built. Load the API key from .env (set -a; . ./.env; set +a), never print it, never send temperature to Anthropic. Stop and ask me before: any spend above the milestone budget, creating or pushing the public repo, setting a repo secret, opening the demo PR, publishing to TestPyPI/PyPI, enabling Pages, or anything posted publicly. The human-only steps are listed in BUILD.md. Run git only from the repo root, never from ~.
```
