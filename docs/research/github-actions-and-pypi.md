# GitHub Actions, sticky PR comment, and PyPI trusted publishing: verified facts

Collected: 2026-11-11. Every fact has a source and the date it was checked. "OBSERVED" means
I ran the command myself on 2026-11-11. "UNVERIFIED" means I could not confirm it from a
primary source.

---

## 1. Action versions (pin by commit SHA)

Method: `gh api repos/<repo>/releases/latest`, then `gh api repos/<repo>/git/ref/tags/<tag>`
(annotated tags dereferenced to the commit). OBSERVED 2026-11-11.

| Action | Latest tag | Published | Commit SHA | Runtime |
|---|---|---|---|---|
| actions/checkout | v7.0.1 | 2026-07-20 | `3d3c42e5aac5ba805825da76410c181273ba90b1` | node24 |
| astral-sh/setup-uv | v10.3.3 | 2026-10-28 | `68559e99cc807c1eb7e9238fd43a15bba460eec2` | node24 |
| actions/upload-artifact | v7.0.2 | 2026-10-07 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | node24 |
| actions/download-artifact | v8.0.2 | 2026-10-07 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` | node24 |
| pypa/gh-action-pypi-publish | v1.14.3 | 2026-10-20 | `7245906fb61fa33a13554f9d5fb856fe61758086` | composite (Docker inside) |
| actions/setup-python | v7.1.0 | 2026-10-22 | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` | node24 |

Cross-check: the setup-uv README pins the same SHA `68559e99...` for v10.3.3
(https://github.com/astral-sh/setup-uv/blob/main/README.md, 2026-11-11).

Pin format to use:

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
- uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
- uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
- uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
- uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086 # v1.14.3
- uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
```

GitHub says the commit SHA of a release is "the safest for stability and security"
(https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax, 2026-11-11).

### Breaking changes in the latest majors

| Action | Change | Source |
|---|---|---|
| checkout v7 | Blocks checkout of fork PR code for `pull_request_target` and `workflow_run`. New input `allow-unsafe-pr-checkout` (default `false`) to override. Module moved to ESM. | https://github.com/actions/checkout/releases/tag/v7.0.0 ; action.yml (2026-11-11) |
| setup-uv v10 | `enable-cache: auto` (default) now DISABLES the cache on `pull_request_target`, `workflow_run`, `release`. New `version: latest-known`. Reads Python version from `.tool-versions`. | https://github.com/astral-sh/setup-uv/releases/tag/v10.0.0 (2026-08-12) |
| setup-uv v9 | `prune-cache` default changed to `false`. | https://github.com/astral-sh/setup-uv/releases/tag/v9.0.0 (2026-07-21) |
| upload-artifact v7 | New `archive` input (default `true`). `archive: false` uploads ONE file unzipped; `name` is then ignored and the artifact takes the file name; fails if the glob matches more than one file. ESM. | https://github.com/actions/upload-artifact/releases/tag/v7.0.0 |
| download-artifact v8 | Hash mismatch now fails by default (`digest-mismatch: error`). Does not unzip non-zip files; new `skip-decompress`. ESM. | https://github.com/actions/download-artifact/releases/tag/v8.0.0 |
| setup-python v7 | Removed the `pip-install` input. Removed EOL Python versions. ESM. | https://github.com/actions/setup-python/releases/tag/v7.0.0 (2026-07-20) |
| gh-action-pypi-publish v1.14.3 | Security fix GHSA-5xjx-3w67-w9x9. No input break. Canonical inputs are kebab-case (`repository-url`, `packages-dir`, `skip-existing`, `verify-metadata`, `print-hash`); snake_case are aliases. `attestations` default `true`. | https://github.com/pypa/gh-action-pypi-publish/releases/tag/v1.14.3 ; action.yml (2026-11-11) |

Notes for casegate:
- upload-artifact `archive: false` fits `run.json` (one file, no zip). The default (zip, `name: artifact`) also works.
- setup-uv v10 inputs (action.yml, 2026-11-11): `version`, `version-file`, `python-version`,
  `activate-environment`, `working-directory`, `enable-cache` (default `auto`),
  `cache-dependency-glob`, `github-token` (default `${{ github.token }}`), and others.
  Outputs include `uv-version`, `uv-path`, `cache-hit`, `python-version`.
- setup-uv README: `python-version` sets `UV_PYTHON` for the rest of the workflow
  (https://github.com/astral-sh/setup-uv/blob/main/README.md, 2026-11-11).
- uv docs recommend pinning the uv version, e.g. `version: "0.13.7"`
  (https://docs.astral.sh/uv/guides/integration/github/, 2026-11-11). The uv docs page still
  shows setup-uv v9.0.0; the latest is v10.3.3.
- Current versions on PyPI (https://pypi.org/pypi/<name>/json, 2026-11-11): uv 0.13.7,
  hatchling 1.33.0, typer 0.29.1.

---

## 2. Composite action syntax (`action.yml`)

Source for all rows: https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax
and https://docs.github.com/en/actions/reference/workflows-and-actions/contexts (2026-11-11).

| Rule | Exact fact |
|---|---|
| Runtime | `runs.using` is required: "You must set this value to 'composite'." |
| Steps | `runs.steps` is required; steps are `run` steps or `uses` steps. |
| Shell | `runs.steps[*].shell`: "Required if `run` is set." There is no default shell in a composite step. |
| Supported step keys | `name`, `id`, `if`, `run`, `shell`, `env`, `working-directory`, `uses`, `with` (all documented on the page). |
| Inputs | Reference with `${{ inputs.<name> }}`. |
| Own path | `${{ github.action_path }}` or env `$GITHUB_ACTION_PATH`. "This property is only supported in composite actions." Doc example: `run: ${{ github.action_path }}/test/script.sh`. |
| Outputs | Declare `outputs.<id>.value` (required for composite) mapped to an expression, usually `${{ steps.<step_id>.outputs.<name> }}`. The step writes `echo "name=value" >> "$GITHUB_OUTPUT"`. |
| Secrets | "The secrets context is not available for composite actions due to security reasons. If you want to pass a secret to a composite action, you need to do it explicitly as an input." |
| `if` and `!` | "You must always use the `${{ }}` expression syntax or escape with '', "", or () when the expression starts with `!`". |
| Env for later steps | To change env for the rest of the job, write `echo "{name}={value}" >> $GITHUB_ENV` in a composite step. |
| Same-repo action | A composite can call a sibling action with `$/.github/actions/x` (resolves at the running commit, no `@ref`; not on GHES). |

Outputs example (from the docs):

```yaml
outputs:
  verdict:
    description: "pass or fail"
    value: ${{ steps.gate.outputs.verdict }}
runs:
  using: "composite"
  steps:
    - id: gate
      shell: bash
      run: echo "verdict=pass" >> "$GITHUB_OUTPUT"
```

Multiline outputs use the heredoc delimiter form, the same as multiline env vars
(https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands, 2026-11-11):

```bash
{
  echo "table<<EOF"
  cat table.md
  echo "EOF"
} >> "$GITHUB_OUTPUT"
```

Security note (UNVERIFIED as a quote, standard GitHub guidance referenced by the contexts page link
"use an intermediate environment variable"): pass `${{ inputs.x }}` into `env:` and read `"$X"` in
the script, instead of pasting `${{ inputs.x }}` into the `run:` text. This stops script injection.

---

## 3. Permissions, fork PRs, and missing secrets

### Permissions to comment on a PR

| Endpoint | Fine-grained permission (either one is enough) | Source |
|---|---|---|
| `GET /repos/{owner}/{repo}/issues/{issue_number}/comments` | Issues (read) OR Pull requests (read) | https://docs.github.com/en/rest/issues/comments (2026-11-11) |
| `POST /repos/{owner}/{repo}/issues/{issue_number}/comments` | Issues (write) OR Pull requests (write) | same |
| `PATCH /repos/{owner}/{repo}/issues/comments/{comment_id}` | Issues (write) OR Pull requests (write) | same |

- "Every pull request is an issue, but not every issue is a pull request." (same source)
- `per_page` max 100, default 30 (same source).
- Answer: `issues: write` is NOT needed when the number is a PR. `pull-requests: write` is enough
  per the REST docs. The GITHUB_TOKEN maps to the same permission model. Recommended minimal block:

```yaml
permissions:
  contents: read
  pull-requests: write
```

- "If you specify the access for any of these permissions, all of those that are not specified
  are set to `none`." So list `contents: read` too, or checkout fails
  (https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax, 2026-11-11).
- UNVERIFIED by a live test: I did not post a real comment with a token that has only
  `pull-requests: write`. The REST docs say it works. A first real PR run will confirm.

### Fork PRs (`pull_request` event)

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (2026-11-11).

- "With the exception of `GITHUB_TOKEN`, secrets are not passed to the runner when a workflow is
  triggered from a forked repository."
- "The `GITHUB_TOKEN` has read-only permissions in pull requests from forked repositories."
  Result: the comment POST/PATCH fails with 403 on fork PRs. The action must not fail the job for
  that. It should fall back to the job summary only.
- A first-time contributor's PR to a public repo may need a maintainer to approve the workflow run.
- Do not switch to `pull_request_target` to get a write token: checkout v7 now blocks fork PR
  checkout there unless `allow-unsafe-pr-checkout: true`, and setup-uv v10 disables the cache there.

Detect a fork PR in an expression:
`github.event.pull_request.head.repo.full_name != github.repository`
(UNVERIFIED as a quoted doc line; the fields are standard `pull_request` webhook payload fields.)

### Detect a missing secret

Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets (2026-11-11).

- "Secrets cannot be directly referenced in `if:` conditionals. Instead, consider setting secrets
  as job-level environment variables, then referencing the environment variables to conditionally
  run steps in the job."
- "If a secret has not been set, the return value of an expression referencing the secret ... will
  be an empty string."

Pattern (caller workflow):

```yaml
jobs:
  eval:
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    steps:
      - if: env.ANTHROPIC_API_KEY != ''
        uses: owner/casegate@<sha>
        with:
          api-key: ${{ env.ANTHROPIC_API_KEY }}
```

Inside the composite, test the input instead: `if: inputs.api-key != ''`, or in bash
`if [ -z "$API_KEY" ]; then ...`.

---

## 4. `gh` commands for the sticky comment

Sources: https://cli.github.com/manual/gh_api and https://cli.github.com/manual/gh_pr_comment
(2026-11-11). Latest gh release v2.103.3 (`gh api repos/cli/cli/releases/latest`, 2026-11-11).

- "GitHub CLI is preinstalled on all GitHub-hosted runners. For each step that uses GitHub CLI,
  you must set an environment variable called `GH_TOKEN`"
  (https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli, 2026-11-11).
- Placeholders `{owner}`, `{repo}` are filled from the current directory's repo or `GH_REPO`.
  In a composite step, set `GH_REPO: ${{ github.repository }}` so it works without a checkout.
- `-F key=@file` reads the value from a file. `-f` sends a raw string. Adding fields switches the
  method to POST. `--slurp` "is not supported with `--jq`" (OBSERVED, gh 2.83.2).
- With `--paginate --jq`, the filter runs once per page. Use `| head -n1` to keep one id.

```bash
export GH_TOKEN="$TOKEN" GH_REPO="$REPO"   # from inputs via env
MARKER='<!-- casegate-gate -->'
PR="$PR_NUMBER"                             # ${{ github.event.pull_request.number }}

# 1. Find the existing comment id by marker (empty if none)
ID=$(gh api --paginate "repos/{owner}/{repo}/issues/$PR/comments?per_page=100" \
  --jq ".[] | select(.body | contains(\"$MARKER\")) | .id" | head -n1)

# 2a. Create
gh api --method POST "repos/{owner}/{repo}/issues/$PR/comments" -F body=@comment.md

# 2b. Edit by id
gh api --method PATCH "repos/{owner}/{repo}/issues/comments/$ID" -F body=@comment.md
```

OBSERVED 2026-11-11:
- The list + `select(.body | contains(marker))` filter ran on a public PR (astral-sh/uv #23211)
  and returned an empty id when the marker was absent.
- `gh api --method POST /markdown -F text=@file` sent the file content. The rendered GFM hid the
  `<!-- casegate-gate -->` line, so the marker is invisible in the comment.
- Not tested: a real POST or PATCH of a comment (no test repo write was done).

Tip: also filter on the author, e.g. `select(.user.login == "github-actions[bot]" and (.body | contains(...)))`,
so a human who quotes the marker is not edited. (The bot login is UNVERIFIED from a doc; it is the
name GitHub shows for GITHUB_TOKEN comments.)

### `gh pr comment --edit-last`

- `--edit-last`: "Edit the last comment of the current user".
- `--create-if-none`: "Create a new comment if no comments are found. Can be used only with `--edit-last`".
- With GITHUB_TOKEN, "current user" is the Actions bot, so `--edit-last` edits the bot's LAST
  comment on the PR, which can belong to another workflow. Use the marker method above instead.
- New in current gh: `--attach <file>` uploads images. Local gh 2.83.2 does not have it.

---

## 5. PyPI and TestPyPI trusted publishing

### Human steps (one time, per index)

Sources: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/ ,
https://docs.pypi.org/trusted-publishers/adding-a-publisher/ , form source
https://github.com/pypi/warehouse/blob/main/warehouse/oidc/forms/github.py (2026-11-11).

1. Log in to pypi.org. Open the account sidebar, "Publishing". (Project does not exist yet, so use
   the "pending publisher" form in the account, not a project page.)
2. Fill the GitHub form:

| Field | Required | Value for casegate | Rule |
|---|---|---|---|
| PyPI project name | yes | `casegate` | pending form only |
| Owner | yes | GitHub user or org | "Specify GitHub repository owner (username or organization)" |
| Repository name | yes | repo name | regex-validated |
| Workflow name | yes | e.g. `release.yml` | "must end with .yml or .yaml"; "filename only, without directories" |
| Environment name | optional, strongly recommended | `pypi` | max 255 chars, no leading or trailing space |

3. Repeat on test.pypi.org (separate account) with environment `testpypi`.
4. In GitHub repo settings, create environments `pypi` and `testpypi`. Optional: add required
   reviewers to `pypi`.

Warnings:
- "A 'pending' publisher does not create a project or reserve a project's name until it is
  actually used to publish." If someone else registers the name first, the pending publisher is
  invalidated.
- "Reusable workflows cannot currently be used as the workflow in a Trusted Publisher."
  (https://docs.pypi.org/trusted-publishers/troubleshooting/). The publish job must live in the
  registered workflow file itself.
- Rate limit: 100 publisher registrations per user or IP per 24 hours (same page).

### Workflow requirements

Sources: https://docs.pypi.org/trusted-publishers/using-a-publisher/ and
https://github.com/pypa/gh-action-pypi-publish README (2026-11-11).

- `id-token: write` is mandatory: "without it, GitHub Actions will refuse to give you an OIDC
  token." Set it at job level ("strongly recommended"), not workflow level.
- Do not pass `user`/`password`; the action then uses trusted publishing.
- TestPyPI: `repository-url: https://test.pypi.org/legacy/`.
- Separate the build job from the publish job; share `dist/` via upload/download-artifact.
- The action is Docker-based: Linux runners only; `container:` jobs not supported.
- Attestations (PEP 740) are on by default with trusted publishing.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
        with: { enable-cache: false }
      - run: uv build --no-sources
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with: { name: dist, path: dist/ }
  testpypi:
    needs: build
    runs-on: ubuntu-latest
    environment: { name: testpypi, url: https://test.pypi.org/p/casegate }
    permissions: { id-token: write }
    steps:
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with: { name: dist, path: dist/ }
      - uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086 # v1.14.3
        with: { repository-url: https://test.pypi.org/legacy/ }
  pypi:
    needs: testpypi
    runs-on: ubuntu-latest
    environment: { name: pypi, url: https://pypi.org/p/casegate }
    permissions: { id-token: write }
    steps:
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with: { name: dist, path: dist/ }
      - uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086 # v1.14.3
```

UNVERIFIED: the workflow above is assembled from the documented pieces; it has not run.

---

## 6. Name check: `casegate`

OBSERVED 2026-11-11 12:47 UTC:

| URL | HTTP | Meaning |
|---|---|---|
| https://pypi.org/pypi/casegate/json | 404 | free |
| https://pypi.org/simple/casegate/ | 404 | free |
| https://test.pypi.org/pypi/casegate/json | 404 | free |
| https://test.pypi.org/simple/casegate/ | 404 | free |

A pending publisher does not reserve the name (section 5). Publish soon after setup.

---

## 7. hatchling src layout, typer entry point, uv build and publish

OBSERVED 2026-11-11 with uv 0.13.7: `uv init --package --build-backend hatch casegate` made
`src/casegate/__init__.py` and this `pyproject.toml` (authors line removed here):

```toml
[project]
name = "casegate"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
casegate = "casegate:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

`uv build` then made `dist/casegate-0.1.0.tar.gz` and `dist/casegate-0.1.0-py3-none-any.whl`.
The wheel has `casegate/__init__.py` at the top level (src/ stripped) and `entry_points.txt`.
`uv run casegate` printed the stub text.

- No `[tool.hatch.build.targets.wheel]` is needed: hatchling's default heuristic checks
  `<NAME>/__init__.py`, then `src/<NAME>/__init__.py`, then `<NAME>.py`
  (https://hatch.pypa.io/latest/plugins/builder/wheel/, 2026-11-11). To be explicit, add
  `[tool.hatch.build.targets.wheel] packages = ["src/casegate"]`.
- Note: `uv init` writes `authors` from the local git config. Set authors on purpose in the spec.
- "Using the entry point tables requires a build system to be defined."
  (https://docs.astral.sh/uv/concepts/projects/config/, 2026-11-11)
- Typer entry point: a `typer.Typer()` instance is callable, so point the script at it:
  `casegate = "casegate.cli:app"`. (UNVERIFIED from typer docs in this pass; standard typer usage.)
- `uv build` puts artifacts in `dist/`. Use `uv build --no-sources` before publishing
  (https://docs.astral.sh/uv/guides/package/, 2026-11-11).
- `uv publish` with trusted publishing needs no credentials. Flags (OBSERVED `uv publish --help`):
  `--index`, `--publish-url`, `--check-url`, `--trusted-publishing`, `-t/--token`.
- TestPyPI with uv (same source):

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
explicit = true
```

  then `uv publish --index testpypi`. "When using `--index`, the index URL is used as check URL."
- Smoke test after upload: `uv run --with casegate --no-project -- python -c "import casegate"`.
- Choice: `pypa/gh-action-pypi-publish` and `uv publish` both support trusted publishing. uv's
  example adds `astral-sh/attest-action` for attestations; pypi-publish does them by default.

---

## 8. Job summary (`$GITHUB_STEP_SUMMARY`)

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands (2026-11-11).

- "Job summaries support GitHub flavored Markdown ... add your Markdown content for a step to the
  `GITHUB_STEP_SUMMARY` environment file. `GITHUB_STEP_SUMMARY` is unique for each step in a job."
- All step summaries are grouped into one job summary on the run summary page.
- Max 1 MiB per step. Over the limit, the upload fails with an error annotation, but "Upload
  failures for job summaries do not affect the overall status of a step or a job."
- "A maximum of 20 job summaries from steps are displayed per job."
- Works for fork PRs too (it needs no token), so it is the fallback when the comment fails.

```bash
cat comment.md >> "$GITHUB_STEP_SUMMARY"
```

The hidden marker line is harmless in the summary (GFM hides HTML comments, OBSERVED via the
`/markdown` render in section 4).
