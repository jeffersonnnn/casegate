# FACTS

Every line here was observed directly, with the date. Anything not observed is marked OPEN.
Detail and source URLs for CI and packaging: `docs/research/github-actions-and-pypi.md`.
Design references: `docs/research/design-references.md`.

## 1. Environment (observed 2026-11-11)

| Fact | Value |
|---|---|
| Repo | `~/Desktop/new-portfolio/evals`, own git repo (`git init -b main`). `~` is also a git repo: never run git from `~`. |
| Python | 3.14.5 default; 3.10 to 3.13 installed via Homebrew |
| uv | 0.13.7 (Homebrew) |
| gh | 2.83.2, logged in as `jeffersonnnn`, ssh protocol |
| Key | `ANTHROPIC_API_KEY` in gitignored `.env` (mode 600). The shell's own `ANTHROPIC_API_KEY` has no credit: load `.env` (`set -a; . ./.env; set +a`) or let `python-dotenv`-free code read the env the caller sets. |

## 2. Names (observed 2026-11-11 12:47 UTC)

| Name | Status |
|---|---|
| PyPI `casegate` | free (404) |
| TestPyPI `casegate` | free (404) |
| GitHub `jeffersonnnn/casegate` | free |
| PyPI `evalgate`, `evalgate-ai`, `evalgate-cli` | taken (reason for ADR 0001) |

A pending trusted publisher does not reserve the name. Re-check before the first publish.

## 3. Library versions (installed and imported 2026-11-11, Python 3.13 venv)

| Package | Version |
|---|---|
| anthropic | 2.8.0 |
| pydantic | 2.14.3 |
| typer | 0.29.1 |
| httpx | 0.28.1 |
| jsonschema | 4.26.0 (read the version with `importlib.metadata`; `jsonschema.__version__` is deprecated) |
| rich, pyyaml | installed, imported |

## 4. Claude API behaviour (observed with real calls, 2026-11-11)

Script: `scripts/derisk_claude.py`.

### 4.1 Toy agent tool loop: Claude Haiku 5.5 (`claude-haiku-5-5`), `output_config={"effort": "low"}`

- `client.messages.create(model, max_tokens, system, tools, messages, output_config={"effort": "low"})` works.
- Tools with `"strict": True` and `additionalProperties: false` work.
- Turn 0: `stop_reason=tool_use`, content blocks `[thinking, tool_use, tool_use, tool_use]`. **The model makes parallel tool calls in one turn.** All `tool_result` blocks go back in one user message.
- Turn 1: `stop_reason=end_turn`, blocks `[thinking, text]`. Thinking blocks are present (empty text by default) and must be passed back unchanged in `assistant` content.
- Usage: turn 0 in 824 / out 247; turn 1 in 1285 / out 315. Agent cost for one case: **$0.00049**. Latency **8.3 s** for 2 turns.
- Trajectory observed: `get_account(1042)`, `get_order(1042)`, `search_policy(...)`. **No `issue_refund`**: the agent asked for the delivery date because the fake order had no `delivered_at`. Consequence for SPEC: every fake order carries `delivered_at` and the store has a fixed "today", or a refund case cannot pass.
- The final text cited `[P1]` as instructed. Citation extraction by regex `\[(P\d+)\]` is viable.

### 4.2 Judge: Claude Sonnet 5.5 (`claude-sonnet-5-5`), `client.messages.parse(output_format=Verdict, output_config={"effort": "medium"})`

- `messages.parse` with a pydantic model (`reasoning: str`, `score: float`) returns `parsed_output` as a validated instance, `stop_reason=end_turn`.
- 3 calls on the same reply and rubric gave scores **0.8, 0.85, 0.8**. **The judge is not deterministic** (ADR 0004 amendment, judge_samples option).
- **The judge was lenient**: it scored 0.8 on "confirms the refund amount" although the reply did not confirm a refund (it was conditional). This is the first recorded judge disagreement; the rubric prompt must ask for a strict reading and calibration must expose cases like this.
- Usage: in 529, out 101 to 113. Cost: **$0.00213 per judge call** (3 calls $0.00640). Latency 2.3 to 3.6 s.

### 4.3 Sampling parameters

- anthropic SDK 2.8.0: `messages.create(..., temperature=0)` raises `TypeError: Messages.create() got an unexpected keyword argument 'temperature'` before any request. The API (version `2026-10-21`) also rejects it with a 400 on every model (claude-api skill reference). **Never send temperature, top_p or top_k to Anthropic.**

### 4.4 Prices used by the built-in price table (claude-api skill, cached 2026-11-03)

| Model | Input $/1M | Output $/1M |
|---|---|---|
| claude-haiku-5-5 | 0.10 (0.50 above 100K prompt tokens) | 0.50 (2.50 above 100K) |
| claude-sonnet-5-5 | 2.00 | 10.00 |
| claude-opus-5-5 | 4.00 | 20.00 |

### 4.5 Cost estimate from observations

One toy-suite run, 15 cases x 5 repeats, about 1.5 judge calls per case: 75 x ($0.0005 + 1.5 x $0.0021) = **about $0.27**. Phase 2 spent **$0.0069**.

## 5. GitHub Actions and PyPI (verified from primary sources 2026-11-11)

Pins (tag and full commit SHA):

| Action | Tag | SHA |
|---|---|---|
| actions/checkout | v7.0.1 | 3d3c42e5aac5ba805825da76410c181273ba90b1 |
| astral-sh/setup-uv | v10.3.3 | 68559e99cc807c1eb7e9238fd43a15bba460eec2 |
| actions/upload-artifact | v7.0.2 | cf430e030ddbb5b0abf93d22962f4752f3646cd9 |
| actions/download-artifact | v8.0.2 | 9000827ccba6bdab643e8b6fd33ac0654aef8333 |
| pypa/gh-action-pypi-publish | v1.14.3 | 7245906fb61fa33a13554f9d5fb856fe61758086 |
| actions/setup-python | v7.1.0 | 6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 |
| actions/configure-pages | v6.0.0 | 45bfe0192ca1faeb007ade9deae92b16b8254a0d |
| actions/upload-pages-artifact | v5.0.0 | fc324d3547104276b827a68afc52ff2a11cc49c9 |
| actions/deploy-pages | v5.0.1 | 368f82528645a54fb793d4d04e342629a3f51346 |

The three Pages rows were read on 2026-11-11 (cold-build audit round 2) with `gh api repos/actions/<name>/releases/latest --jq .tag_name` and `gh api repos/actions/<name>/git/ref/tags/<tag>` (each ref is a commit, not an annotated tag). Re-check at M4 (DESIGN §8).

Gotchas:
- Composite action: `using: composite`; every `run` step needs `shell:`; own path is `${{ github.action_path }}`; no `secrets` context, pass secrets as inputs.
- Permissions: `pull-requests: write` + `contents: read` (setting any permission sets the rest to `none`).
- Fork PRs: read-only token and no secrets. Comment calls 403. Fall back to `$GITHUB_STEP_SUMMARY`.
- A secret cannot be used in `if:`. Map it to job `env` and test `env.ANTHROPIC_API_KEY != ''`.
- Sticky comment: find by marker `<!-- casegate-gate -->` with `gh api --paginate "repos/$GH_REPO/issues/$PR/comments?per_page=100" --jq '.[] | select(.user.login == "github-actions[bot]" and (.body | contains("<!-- casegate-gate -->"))) | .id' | head -n1` (the author filter stops a pasted marker in a human comment from being edited); create with `POST .../issues/$PR/comments -F body=@comment.md`; edit with `PATCH .../issues/comments/$ID -F body=@comment.md`. Do not use `gh pr comment --edit-last`.
- Trusted publishing: job-level `id-token: write`; Linux runner; not in a reusable workflow; TestPyPI `repository-url: https://test.pypi.org/legacy/`.
- `uv init` copies the git author email into `authors`; set authors on purpose (OPEN-1).
- Job summary limit 1 MiB per step.

## 6. OPEN (not observed)

| Id | Item | Resolve at |
|---|---|---|
| OPEN-1 | RESOLVED 2026-11-11: author `Jefferson Ighalo <heyjeffersonighalo@gmail.com>` (SPEC §1) | done |
| OPEN-2 | A real sticky comment posted and edited by `GITHUB_TOKEN` in a real PR | M3 real-world-test |
| OPEN-3 | Trusted-publisher forms on PyPI and TestPyPI (human) | M3 |
| OPEN-4 | RESOLVED 2026-11-11 (M2 live): `evals/baseline.json` (toy-agent@5, 15 cases × 5 repeats, fresh cache) has `pass_rate` 0.973 and `pass_rate_std` 0.0365; `max_drop = max(0.02, ceil(round(2*0.0365*100, 6))/100)` = 0.08, in `evals/tolerance.json` (§8). It replaces the toy-agent@2 baseline (0.867, std 0.0667, max_drop 0.14) | done |
| OPEN-5 | 40 human labels for calibration (human) | M3 |

## 7. Observed during cold-build audits (2026-11-11)

Round 1 rows were checked in a scratch folder with `uv run --no-project --with ...` (Python 3.13). Round 2 rows (marked R2) were checked in the scratch venv with Python 3.13.5, pydantic 2.14.3, mypy 1.13.0, bash and the Python 3.13 stdlib. Round 3 rows (marked R3, 2026-11-11) were checked in the same venv, which also has typer 0.29.1. Commands are in `docs/audit/README.md`.

| Fact | Observation | Consequence (SPEC) |
|---|---|---|
| jsonschema typing | `jsonschema` 4.26.0 ships no `py.typed`; `mypy --strict` on `import jsonschema` fails with "Library stubs not installed" | `types-jsonschema` in the dev group (§1); version 4.26.0.20261006 installed and removed that error |
| `type` ClassVar shadowing | mypy 1.13 `--strict`: `type: ClassVar[str]` then `Params: ClassVar[type[BaseModel]]` in one class body fails with `Variable "Scorer.type" is not valid as a type [valid-type]`; `builtins.type[BaseModel]` passes | §5.1 uses `builtins.type` |
| pydantic field `schema` | pydantic 2.14.3: a field named `schema` warns `Field name "schema" ... shadows an attribute in parent "BaseModel"`; `schema_: ... = Field(default=None, alias="schema")` with `populate_by_name=True` validates `{"schema": {...}}` with no warning and passes mypy --strict | §5.2 `json_schema` Params |
| uv requirement with extra | `uv run --with 'casegate==0.1.0[anthropic]'` fails: "after parsing `0.1.0`, found `[anthropic]`, which is not part of a valid version"; the form `casegate[anthropic]==0.1.0` parses | §18.1 `casegate-source` |
| ruff on kit scripts | ruff 0.7.4 with rules E,F,I,UP,B,SIM,RUF, line length 100, target py311 finds 113 errors in `scripts/` + `docs/design/options/`, and would reformat `scripts/derisk_claude.py` and `docs/design/options/build.py` | §1 `extend-exclude` |
| Tolerance float noise | `math.ceil(2*std*100)/100` is wrong for std 0.035, 0.07 and 0.14 (of 0.001..0.199): 2*0.035*100 = 7.000000000000001 → 0.08. `math.ceil(round(2*std*100, 6))/100` gives 0.07. (std 0.015, the auditor's example, is not affected.) | §16.3 formula |
| R2: positional `Field` default | mypy 1.13 `--strict`, no plugin: `samples: int = Field(1, ge=1, le=9)` then `judge: JudgeConfig = JudgeConfig()` fails with `Missing named argument "samples" for "JudgeConfig" [call-arg]`. The keyword form `Field(default=1, ge=1, le=9)` passes with no plugin. With `plugins = pydantic.mypy` both pass | §1 Types (plugin on, every default written as a keyword), §2 |
| R2: nested params class | mypy 1.13 `--strict`: a scorer class with a nested `class Params(BaseModel)` does not match the protocol member `Params: ClassVar[builtins.type[BaseModel]]`; `REGISTRY: dict[str, builtins.type[Scorer]] = {Nested.type: Nested}` fails with `[dict-item]`. A module-level model plus `Params: ClassVar[builtins.type[BaseModel]] = FlatParams` passes | §5.1 module-level `<Name>Params` |
| R2: empty exit code | bash: `exit $EMPTY` (unset) exits 0; `exit "${EMPTY:-1}"` exits 1 | §18.1 step 6 fails closed |
| R2: csv line ends | `csv.writer(buf).writerow(["a","b"])` writes `'a,b\r\n'` (CRLF by default) | §12 template uses `lineterminator="\n"` |
| R2: ValueError in a validator | pydantic 2.14.3: a `ValueError` raised in a `model_validator(mode="after")` is wrapped in `ValidationError` (loc `()` for that model, msg `Value error, <text>`), so the loader can collect it | §2 TargetConfig validator raises ValueError only |
| R2: JSON schema of a forbid model | `model_json_schema()` of a model with `extra="forbid"` has `additionalProperties: False` at the top level, plus `title` keys | §6 OpenAICompatJudge schema |
| R2: light-banner contrast | WCAG 2.x: `#1A8F4E` on `#F4F7F5` = 3.83:1; `#E3ECE7` on `#F4F7F5` = 1.12:1; `#0B0F0E` on `#F4F7F5` = 17.88:1 | DESIGN §3 `mark-512-light.png` |
| R3: typer unset list option | typer 0.29.1, `CliRunner`: `x: Optional[list[str]] = typer.Option(None, "--x")` and `x: list[str] \| None = typer.Option(None, ...)` both give `None` when the flag is not given and `['a', 'b']` for `--x a --x b`; a `list[str] = typer.Option([], ...)` default gives `[]` | §11 `resolve_must_pass_tags` treats None and `[]` the same; cli.py uses the None default |
| R3: TYPE_CHECKING import of a missing module | mypy 1.13 `--strict`: `if TYPE_CHECKING: from cg.calibrate import Calibration` with no `cg/calibrate.py` fails with `Cannot find implementation or library stub for module named "cg.calibrate" [import-not-found]` | §14 `render_calibration` is added in M3, not M2 |
| R3: refund status rule | order total 25.00, one refund of 12.5: `math.isclose(order.refunded_amount, order.amount, abs_tol=0.005)` → `partially_refunded`; the old rule `math.isclose(refunded_amount, amount)` with `amount` = the call amount 12.5 → `refunded` (wrong) | §16.1 `issue_refund` |
| R3: tolerance floor | `max(0.02, math.ceil(round(2*std*100, 6))/100)`: std 0.0, 0.004 and 0.0099 → 0.02; std 0.035 → 0.07 | §16.3, ADR 0006 amendment |
| R3: union field errors | pydantic 2.14.3: `answer: str \| list[str] \| None` validated with `42` gives two errors, loc `answer.str` msg `Input should be a valid string`, and loc `answer.list[str]` msg `Input should be a valid list` | §3.3 `expected` lines: one line per union member |
| R3: `re.error` text | `str(re.error)` for `re.compile("(")` is `missing ), unterminated subpattern at position 0` | §3.3 `invalid regex: <str(re.error)>` |
| R3: `#` in shell args | bash: `echo --bg #0B0F0E end` prints `--bg` (the rest is a comment); `echo --bg '#0B0F0E' end` prints all three words | DESIGN §3, M5 stills commands quote the colour |

## 8. Observed in the M2 live runs (2026-11-11)

Real Claude API, target `claude-haiku-5-5` (effort low), judge `claude-sonnet-5-5` (effort medium). Spend is `summary.cost_usd` of each run JSON.

| Run | Target | Cache | pass_rate | std | errors | cost_usd | duration_s |
|---|---|---|--:|--:|--:|--:|--:|
| repeat 1 (`/tmp/cg-r1.json`, first) | toy-agent@1 | fresh | 0.867 | 0.000 | 0 | 0.0406 | 14.3 |
| repeat 5, first baseline attempt | toy-agent@1 | fresh | not kept (replaced) | | | ≈ 0.22 (estimate) | |
| repeat 5, old `evals/baseline.json` (replaced; kept as `docs/assets/runs/baseline-toy-agent@2.json`) | toy-agent@2 | fresh | 0.867 | 0.0667 | 0 | 0.2182 | 58.5 |
| re-run check, same cache dir | toy-agent@2 | 75/75 outputs, 91/91 judge hits | 0.867 | 0.0667 | 0 | 0.0000 | 0.03 |
| repeat 1 (`/tmp/cg-r1.json`, again) | toy-agent@2 | fresh | 0.867 | 0.000 | 0 | 0.0496 | 31.3 |
| `--tag citations --repeat 2` (`docs/assets/runs/citations-toy-agent@3.json`) | toy-agent@3 | fresh | 0.875 | 0.177 | 0 | 0.0302 | 10.4 |
| `--tag citations --repeat 2` (`docs/assets/runs/citations-toy-agent@4.json`) | toy-agent@4 | fresh | 0.875 | 0.177 | 0 | 0.0227 | 9.7 |
| `--tag citations --repeat 2` (`docs/assets/runs/citations-toy-agent@5.json`) | toy-agent@5 | fresh | 1.000 | 0.000 | 0 | 0.0266 | 10.2 |
| repeat 5, `evals/baseline.json` (current) | toy-agent@5 | fresh | 0.973 | 0.0365 | 0 | 0.1835 | 51.5 |
| re-run check, same cache dir | toy-agent@5 | 75/75 outputs, 74/74 judge hits | 0.973 | 0.0365 | 0 | 0.0000 | 0.02 |

- toy-agent@2 baseline acceptance (SPEC §16.3): `n_error_repeats` 0; the 3 adversarial cases at pass_rate 1.0. toy-agent@2 adds one prompt line (a refusal must give the rule, for example that a refund cannot be more than the order amount).
- toy-agent@2: `casegate gate --baseline evals/baseline.json --run evals/baseline.json` exits 0. A doctored copy with 3 cases flipped to fail (pass_rate −0.2) exits 1, and the comment's first line is `<!-- casegate-gate -->`.
- toy-agent@2 (history): the only failures are `citation_support` on the 4 policy cases (by_tag citations 0.5 in that baseline). Cause: the agent writes one sentence with two claims (two policy rules, or an order fact plus a rule) and cites one passage; the judge grades the whole sentence against that one passage and says unsupported. The scorer follows SPEC §5.6 and the cases are correct, so this is an agent fault. The cases and the scorer were not changed; the prompt fix is toy-agent@3..@5 below.
- The toy-agent@2 rows are history. Its run file is kept as `docs/assets/runs/baseline-toy-agent@2.json`.
- toy-agent@3 to @5 (decision 2026-11-11, the user): fix the prompt, not the cases or the scorer. The two `prompt.md` lines "Cite each passage in its own brackets, like [P1] [P3]." and "Put the brackets inside the sentence they support, before its final full stop." are replaced by three lines: one policy fact per sentence, close to the passage words and readable on its own; one passage marker per policy sentence, before the full stop; order facts, advice and conclusions in separate sentences without markers. @4 and @5 only add to the third line (do not join an order fact to a rule with "and", then a worked example with P5). @3 and @4 still failed `policy-giftcard-13` once in 2 ("It is a gift card order, and gift card orders are non-refundable [P4]."); @5 passed all 8 repeats. The demo-PR lines (BUILD M3) are unchanged.
- toy-agent@5 baseline: `n_error_repeats` 0, adversarial 1.0, `by_tag.citations` 0.9 (was 0.5). Still below 1.0: `policy-window-10` 0.8 ("Items reported within that window qualify for a full refund [P1]." drops "damaged" and leans on "that window") and `policy-giftcard-13` 0.8 (the same order-fact-plus-rule sentence). Per-repeat pass rates 1.0, 1.0, 1.0, 0.933, 0.933.
- `casegate gate --baseline evals/baseline.json --run evals/baseline.json` exits 0 on the toy-agent@5 baseline. With `--max-drop 0.08`, a copy with `summary.pass_rate` lowered by 1/15 (one case at 0/5) exits 0, and by 2/15 exits 1.
- max_drop 0.08 is above 0.06 because 2 of 75 repeats still fail, and on 5 points one failing repeat moves a repeat pass rate by 0.067: per-repeat rates 1, 1, 1, 0.933, 0.933 give std 0.0365. The 3-iteration limit on prompt changes was used, so the remaining citation flakiness stays as measured signal.
- Total M2 live spend: about $0.55 before the prompt fix, plus $0.263 for the toy-agent@3..@5 runs = about $0.81 of the $2 budget.
