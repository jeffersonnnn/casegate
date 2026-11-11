# action (`action.yml`, 158 lines)

**30 seconds:** The GitHub Action that any repo can use. It installs casegate with uv, runs the suite, gates the run against a baseline, uploads the run file, and posts or edits one sticky comment on the pull request. Its check is red when the gate exit code is not 0.

**2 minutes:** It is a composite action with 11 inputs and 3 outputs (`action.yml:9-66`). Step 1 sets up uv (`action.yml:71-72`). The Run step picks what to install: the action's own checkout, or the `casegate-source` requirement used verbatim (`action.yml:84`). It runs `casegate run` with `--no-project`, so uv does not sync the caller's own project first, and saves the exit code instead of failing (`action.yml:88-94`). The Gate step runs only when the run exit code is 0 and `gate` is true (`action.yml:98`); it turns the space-separated `must-pass-tag` into flags and writes the comment file (`action.yml:107-115`). The Upload step always runs, so a failed run still leaves its file (`action.yml:117-126`). The Comment step edits or posts the sticky comment (`action.yml:128-146`). The Result step decides the check: run exit code first, then gate exit code, and an empty code counts as 1 (`action.yml:148-158` `Result`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `action.yml:76-82` | inputs reach the script only through `env:` | no `${{ }}` inside a `run:` script, so an input value cannot inject shell code (SPEC §18.1) |
| `action.yml:84` | install from `GITHUB_ACTION_PATH` by default | the action runs the casegate of the same commit; a pinned PyPI version is opt-in |
| `action.yml:88-94` | `set +e`, save the exit code, `exit 0` | the upload and the comment must run even when `run` fails; the last step returns the real code |
| `action.yml:93` | `pass-rate` from `jq`, empty when null | an output is a string; a null pass rate must not print "null" |
| `action.yml:85-86` | a `casegate-source` with a newline fails the step | a newline would write a second, forged key into `GITHUB_OUTPUT` (SPEC §18.1, 2026-11-11) |
| `action.yml:108` | `MP=()` loop over `$MUST_PASS`, inside `set -f` | an empty input passes no flag, so the run file's tags apply; `set -f` stops a `*` or `?` in a tag from expanding to file names |
| `action.yml:137-139` | find the comment by bot login and marker | a user can paste the marker; only the bot's own comment is edited |
| `action.yml:141-146` | a failed PATCH or POST prints a notice | a fork PR token cannot comment; the job summary still has the table |
| `action.yml:156-157` | `${RUN_EXIT:-1}`, `${GATE_EXIT:-1}` | `exit` with an empty value exits 0 in bash (FACTS.md §7), so empty must mean failure |

## Trade-off
A composite action is plain YAML and bash: no build step and no JavaScript bundle to audit. A JavaScript action would give typed inputs and a native API client, at the cost of a `dist/` bundle that must be rebuilt and committed. The comment uses `gh api` from the runner image, not a marketplace comment action, so there is one less third-party pin.

## Failure modes
The action was checked with actionlint and shellcheck, and the Run and Gate steps ran locally with `bash -eo pipefail` on `tests/fixtures/suite_fake` (M3 build notes; not a committed test). It has not run on GitHub yet: the M3 files are not pushed, so the sticky comment edit (OPEN-2, SPEC §20) is not observed. Hardening not done: a newline in `casegate-source` could add a step output, and `for t in $MUST_PASS` is unquoted, so a tag `*` expands to file names. Both inputs come from the workflow author, not from PR content.

## What I would change
Write the outputs with the heredoc form of `$GITHUB_OUTPUT` and quote the tag loop. Cost: a few lines, and the SPEC scripts change.

## 10-minute version
Outputs: `passed` is `true` only on gate exit 0, `false` otherwise, and empty when `gate` is false (`action.yml:57-66`). The artifact `casegate-run` holds `casegate-run.json` and `casegate-comment.md` at its root, and `overwrite: true` lets a re-run upload the same name again (`action.yml:117-126`). The baseline is an input: the action does not know where it came from; the workflow decides that (`modules/eval-gate.md`). The comment body comes from `gate --comment-out` (`src/casegate/gate.py:184-191` `write_comment`), which also appends it to the job summary.
