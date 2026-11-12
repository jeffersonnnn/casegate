# pages (`.github/workflows/pages.yml`, 30 lines)

**30 seconds:** The workflow that publishes `site/` to GitHub Pages. It runs on a push to `main` that changes the site or this file, and by hand. It has one job with four pinned actions.

**2 minutes:** The trigger is a push to `main` with the path filter `site/**` and the workflow file, plus `workflow_dispatch` (`.github/workflows/pages.yml:3-7`). Permissions are read for contents, write for Pages and an OIDC token (`.github/workflows/pages.yml:9-12`). One concurrency group stops two deploys at the same time (`.github/workflows/pages.yml:14-15`). The job uses the `github-pages` environment and takes its URL from the deploy step (`.github/workflows/pages.yml:18-22`). The steps are checkout, configure, upload `site/` as the artifact, and deploy (`.github/workflows/pages.yml:24-30`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `.github/workflows/pages.yml:6` | paths filter | a code-only push must not redeploy the site |
| `.github/workflows/pages.yml:12` | `id-token: write` | `deploy-pages` proves the run with an OIDC token; no deploy key is stored |
| `.github/workflows/pages.yml:27-28` | `path: site` | Pages gets only `site/`; that is why the site never links `../docs` (`docs/DESIGN.md` §8) |
| `.github/workflows/pages.yml:24-30` | actions pinned by SHA with a `# vX.Y.Z` tag | a tag can move; a SHA cannot (FACTS.md §5, re-checked at M4) |

## Trade-off
A workflow deploy, not the "deploy from a branch" mode. The branch mode needs no YAML but publishes a whole folder of the default branch and has no path filter. The workflow mode publishes only `site/`.

## Failure modes
Pages is not on yet: the M4 real-world-test saw `gh api repos/jeffersonnnn/casegate/pages` return 404, and the site files are not pushed (a human step, BUILD.md M4). The first push came before Pages existed, so one manual `gh workflow run pages.yml` is needed after Pages is on. The workflow has not run on GitHub yet.

## What I would change
Add a job that runs Lighthouse on the deployed URL and fails under 100 accessibility. Cost: a Node step and about a minute per deploy.

## 10-minute version
No secrets are used. The `concurrency` group has no `cancel-in-progress`, so a second deploy waits instead of cancelling a deploy that is half done. The site has no build step, so the job only uploads files.
