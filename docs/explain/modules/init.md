# init (`src/casegate/__init__.py`, 11 lines)

**30 seconds:** The package root. It holds the one version string and re-exports the three errors that user code can raise or catch. A user writes `from casegate import RetryableError` and does not need to know the module layout.

**2 minutes:** `__version__` is set at `src/casegate/__init__.py:9` `__version__`. Two readers use it: hatch reads it to build the wheel (SPEC §1, the hatch version path), and the CLI prints it for `casegate --version` (`src/casegate/cli.py:14` `__version__`). The re-export at `src/casegate/__init__.py:7` `JudgeError` makes `SuiteError`, `JudgeError` and `RetryableError` the public error surface. All other error classes stay in `errors.py` because only casegate itself raises them.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/__init__.py:7` | re-exports three errors | targets and suites need them; internal errors stay internal |
| `src/casegate/__init__.py:9` | sets `__version__ = "0.1.0"` | one source for the wheel and the CLI, so they cannot disagree |

## Trade-off
The version could come from git tags (hatch-vcs). A literal string is simpler to read and to test, but a release must change it by hand.

## Failure modes
A wrong version string makes the wheel and `--version` wrong together, which is at least consistent. The M0 Verify stage ran `uv run casegate --version` and it printed `0.1.0`.

## What I would change
Add a test that compares `__version__` with the built wheel metadata. Cost: one more test that needs a build step.

## 10-minute version
Keep this file small: an import of `casegate` must not import typer, httpx or anthropic, so that a target module can import the errors cheaply. Today it imports only `errors.py`, which has no dependencies.
