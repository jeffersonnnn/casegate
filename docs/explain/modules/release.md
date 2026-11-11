# release (`.github/workflows/release.yml`, 57 lines)

**30 seconds:** The workflow that publishes casegate. A `v*` tag builds the wheel once, checks it, publishes it to TestPyPI, and then to PyPI after a person approves. No API token is stored: PyPI trusts this workflow through OIDC.

**2 minutes:** It runs only on tags that start with `v` (`.github/workflows/release.yml:3-5`), with read-only permissions by default (`.github/workflows/release.yml:7-8`). The `build` job checks that the tag equals `__version__` in `src/casegate/__init__.py`, so `v0.1.1` cannot ship a 0.1.0 wheel (`.github/workflows/release.yml:16-18`). It builds with `uv build --no-sources`, installs the wheel in a clean environment and runs `casegate --version` (`.github/workflows/release.yml:19-24`), then uploads `dist/` (`.github/workflows/release.yml:25-28`). The `testpypi` job downloads the same `dist/` and publishes it with `id-token: write` in the `testpypi` environment (`.github/workflows/release.yml:30-44`). The `pypi` job needs `testpypi` and runs in the `pypi` environment, which has a required reviewer (`.github/workflows/release.yml:46-57`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `.github/workflows/release.yml:18` | tag must equal `__version__` | the package name and the git tag must never disagree |
| `.github/workflows/release.yml:21` | `uv build --no-sources` | builds the way a user installs it, without local path sources |
| `.github/workflows/release.yml:24` | smoke test the built wheel | a broken entry point fails here, before any upload |
| `.github/workflows/release.yml:35` | `id-token: write` only in the publish jobs | trusted publishing: no long-lived PyPI token in repo secrets |
| `.github/workflows/release.yml:44` | `skip-existing: true` on TestPyPI | a re-run after a later failure must not fail on a file already uploaded |
| `.github/workflows/release.yml:49` | `environment: pypi` | the required reviewer is the last human check before a public release |

## Trade-off
One build, two uploads: the file on PyPI is the file that was tested on TestPyPI. Building again in each job would be simpler YAML but could give two different wheels. TestPyPI first costs a few minutes per release and catches metadata errors before the real index, where a version number can never be used again.

## Failure modes
The publish jobs need human set-up first: the GitHub environments `testpypi` and `pypi` and both pending publishers (OPEN-3, SPEC §20). Without them the publish step fails with an OIDC error, and nothing is published. No tag is pushed yet, so the workflow has not run (M3 real-world-test: pypi.org returns 404 for casegate).

## What I would change
Attach the wheel and a checksum to a GitHub release in the same run. Cost: one more job with `contents: write`.

## 10-minute version
The publish jobs do not check out the repo, so no repo code runs with `id-token: write` (`.github/workflows/release.yml:36-44`). All actions are pinned to full SHAs with the tag in a comment (FACTS.md §5). After PyPI, the README quick start becomes `uvx --from 'casegate[anthropic]' casegate run evals` (SPEC §19).
