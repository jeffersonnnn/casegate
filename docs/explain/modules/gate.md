# gate (`src/casegate/gate.py`, 187 lines)

**30 seconds:** The CI gate: decide pass or block from a comparison, and write the PR comment (SPEC §11). Every check runs and reports, even after one fails, so a blocked pull request shows all its problems at once. The comment starts with a fixed marker, so CI edits the same comment on every push.

**2 minutes:** `gate` at `src/casegate/gate.py:77-113` `gate` builds a list of `GateCheck` items. `scored` fails when the run has no pass rate (`src/casegate/gate.py:86-92`). `max_drop` fails when the baseline pass rate minus the run pass rate is more than `max_drop` (`src/casegate/gate.py:93-102`). `max_errors` fails when the run has more error repeats than allowed, default 0 (`src/casegate/gate.py:103-109`). One `must_pass:<tag>` check per tag fails when any tagged case missed a single repeat, when a tagged baseline case is missing or lost the tag in the run (`<id> tag removed`), or when no case has the tag (`src/casegate/gate.py:56-74` `_must_pass`). The result passes only when every check passes (`src/casegate/gate.py:111-113`). `resolve_must_pass_tags` takes the CLI tags, else the run file's tags, never the baseline's (`src/casegate/gate.py:45-49` `resolve_must_pass_tags`). `render_gate_comment` writes the marker, the verdict, a headline, warnings, the metric table, the checks line, the flips and a footer (`src/casegate/gate.py:146-181` `render_gate_comment`). The CLI maps the result to exit 0 or 1 (`src/casegate/cli.py:207`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/gate.py:27` | `<!-- casegate-gate -->` marker | the Action finds and edits one sticky comment |
| `src/casegate/gate.py:45-49` | must-pass tags from the run, not the baseline | ADR 0008 spirit: a PR must not weaken what it is gated on through the baseline |
| `src/casegate/gate.py:52-53` | must-pass means every repeat passed | an adversarial case that fails 1 in 5 is a real risk, not noise |
| `src/casegate/gate.py:99` | `drop <= max_drop + 1e-9` | a NaN pass rate compares False, so a broken file fails closed |
| `src/casegate/gate.py:125-126` | a rounded zero says "unchanged" | never "fell 0.0 points" |
| `src/casegate/gate.py:163-180` | cut flip rows until the body fits 60,000 chars | GitHub rejects longer comments; the verdict and checks must survive |

## Trade-off
A single "pass rate dropped" check is simpler. Separate checks for drop, errors and must-pass cases mean an error storm or one failed safety case blocks the PR even when the average looks fine. The cost: more lines in the comment.

## Failure modes
The checks on the regressed fixture (`tests/test_compare_gate.py:96` `test_gate_checks_on_regressed`). A run against itself passes unchanged (`tests/test_compare_gate.py:107` `test_gate_against_itself_passes_unchanged`). The max-drop boundary and allowed errors (`tests/test_compare_gate.py:139` `test_gate_max_drop_boundary_and_errors_allowed`). Truncation at 60,000 (`tests/test_compare_gate.py:148` `test_gate_comment_truncates_at_60000`). NaN fails closed (`tests/test_compare_gate.py:191` `test_max_drop_fails_closed_on_nan_pass_rate`). Exit codes 0, 1 and 2 through the CLI (`tests/test_cli.py:242` `test_gate_exit_0_on_pass`, `tests/test_cli.py:251` `test_gate_exit_1_on_regression`, `tests/test_cli.py:264` `test_gate_exit_2_on_bad_input`). Live: the baseline against itself exits 0, and a doctored copy with 3 cases flipped to fail exits 1 (FACTS.md §8).

## What I would change
Let `--max-drop` default to the value in `evals/tolerance.json` when the file exists, so CI and local runs cannot drift apart. Cost: one more file read and a rule for which wins.

## 10-minute version
`write_comment` writes the body to `--comment-out` and appends it to `$GITHUB_STEP_SUMMARY` when set (`src/casegate/gate.py:184-191` `write_comment`); that is the only file `gate` writes, and bad input (exit 2) never reaches it (`src/casegate/cli.py:202`). The footer holds both shas, the casegate version, the max drop and the baseline std, so a reader can check the tolerance. The measured tolerance is 0.08 (`evals/tolerance.json` `max_drop`).
