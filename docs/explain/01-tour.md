# Tour: one `casegate run`, then one `casegate gate`

One request end to end: `casegate run evals --repeat 5`, then `casegate gate` on a pull request. Stops are filled by each milestone's Explain stage. Until then they are planned.

### Stop 0: the observation that shaped the design
`scripts/derisk_claude.py:29-33`
**What:** a real Haiku 5.5 tool loop on the refund tools, run before any product code.
**Why:** prove the agent loop works and measure its cost before writing a spec (FACTS.md §4.1).
**Say it like this:** "Before I wrote code, I ran the real model once to measure cost and see how it calls tools."
**Check:** what did the agent do wrong in that first run, and why?

### Stop 0b: the judge call that showed leniency
`scripts/derisk_claude.py:50` `messages.parse`
**What:** a structured-output judge call on Sonnet 5.5, run 3 times on the same reply.
**Why:** measure judge stability and cost (FACTS.md §4.2); it scored 0.8, 0.85, 0.8 and was lenient.
**Say it like this:** "The same judge call gave three different scores, so I treat the judge as a noisy instrument."
**Check:** why can't you set temperature to 0 to fix this?

### Stop 0c: the run format every module agrees on
`src/casegate/models.py:168-182` `Run`
**What:** the `Run` model is the JSON file that one `casegate run` writes and that compare, gate and calibrate read back.
**Why:** all models forbid unknown fields (`src/casegate/models.py:19-20` `_Strict`) and carry `schema_version`, so a typo or a newer file fails loudly instead of being misread (SPEC §2).
**Say it like this:** "Every stage talks through one strict, versioned run file, so I can store a baseline and compare it months later."
**Check:** why is `cost_usd` a `float | None` and not a plain float?

### Stop 1: CLI entry point
`src/casegate/cli.py:114-163` `run`
**What:** `casegate run <suite_dir>` loads the suite, builds the cache and (only when a case needs one) the judge, runs it under a progress bar, writes the run JSON and `results/latest.md`, and prints the result table.
**Why:** the CLI stays thin; all logic is in the library, so tests call `load_suite` and `run_suite` directly. A `SuiteError` maps to exit 2 and Ctrl-C to exit 130 with no file written (`src/casegate/cli.py:149-152`). Failed cases still exit 0, because the gate decides, not `run` (`src/casegate/cli.py:126`).
**Say it like this:** "`run` only measures and writes a run file; it never fails the build. The gate is a separate step."
**Check:** what exit code does `run` give when a case fails, and when `suite.yaml` has no `target.version`?

### Stop 2: loading and validating the suite
`src/casegate/loader.py:26-53` `load_suite`
**What:** reads `suite.yaml` and every case file, validates them with pydantic, builds the scorers and the target once as a check, and raises one `SuiteError` that lists every problem.
**Why:** a suite author fixes YAML faster when one run shows all errors; an invalid suite still has its cases checked (`src/casegate/loader.py:39-41`). Building scorers and the target here means a bad suite fails before any paid call.
**Say it like this:** "The loader collects every error, file and case index included, and fails with exit 2 before anything costs money."
**Check:** why does the loader check unknown scorer types itself, before `build_scorers`?

### Stop 3: building the target
`src/casegate/targets/__init__.py:32-36` `build_target`
**What:** turns the suite's target config into a `PythonTarget` (an async function in the same process) or an `HttpTarget` (a POST per case); both meet the `Target` protocol (`src/casegate/targets/__init__.py:26-29` `Target`).
**Why:** the runner only knows `run` and `aclose`, so any system can be tested through one seam. Import faults, a sync function and a missing `${ENV}` header become `SuiteError` lines, not crashes mid-run.
**Say it like this:** "A target is an adapter: casegate gives it a case input and gets an Output back; it does not care what is behind it."
**Check:** why does `HttpTarget` open its HTTP client on the first call and not in `__init__`?

### Stop 4: the runner fans out (case × repeat, semaphore)
`src/casegate/runner.py:81-99` `semaphore`
**What:** `run_suite` makes one task per (case, repeat), all gathered at once, and an `asyncio.Semaphore` lets at most C of them run.
**Why:** C bounds all model work in flight, target and (from M2) judge calls in the same slot, so a big suite cannot flood a rate limit (`src/casegate/runner.py:81`). The runner closes a target only when it built it (`src/casegate/runner.py:83-99`).
**Say it like this:** "Every case-repeat pair is one task; a semaphore of size C caps how many talk to a model at once."
**Check:** why is the judge call inside the same semaphore slot as the target call?

### Stop 5: retries and errors
`src/casegate/retry.py:62-88` `with_retries`
**What:** one loop calls the target (or judge) up to 4 times, waits the server's `retry-after` hint capped at 30 s or a backoff of 1, 2, 4 s plus jitter, and returns the value with the try count.
**Why:** rate limits and overload pass; a run should not report them as errors, and an error is still not a fail when tries run out (`docs/adr/0003-errors-are-not-failures.md`). The runner calls it for every target call at `src/casegate/runner.py:156-162` `with_retries`.
**Say it like this:** "Transient API faults get a capped, jittered retry, and the run file records how many tries each repeat took."
**Check:** why does the loop catch `Exception` and not `BaseException`?

### Stop 6: the output cache
`src/casegate/runner.py:140-152` `key_obj`
**What:** before calling the target, the runner builds a key from the case input, target version, target model and repeat index, and reads `outputs/` in the disk cache; a valid hit skips the target call and costs 0.
**Why:** a rubric or scorer change then re-scores old outputs without re-running the agent (`docs/adr/0005-two-caches.md`). The repeat index keeps 5 real samples for `--repeat 5`. A corrupt or invalid entry is a miss (`src/casegate/cache.py:61-65`), and an error is never stored (`src/casegate/runner.py:167-168`).
**Say it like this:** "Outputs are cached by what went in and which build of the agent made them; bump the target version and every output is stale."
**Check:** a re-run of the 15 × 5 baseline on the same cache folder: how many target calls, and what cost? (FACTS.md §8: 75/75 output hits, $0.0000)

### Stop 7: the toy agent loop
`examples/toy_agent/agent.py:113-168` `run`
**What:** the target behind the example suite: a Haiku 5.5 tool loop of at most 8 turns over a fresh in-memory store, which returns an Output with the reply, the tool calls, the citations, the store state, tokens and cost.
**Why:** a small hand-written loop shows exactly what casegate grades. Each case gets a fresh store with a fixed today (`examples/toy_agent/store.py:89-140` `fresh_store`), so the refund rules give the same answer on every run. A bad stop reason raises, so a cut-off reply is an `error`, not a fail (`examples/toy_agent/agent.py:134-138`).
**Say it like this:** "The toy agent is about 50 lines of loop: call the model, run each tool on a fake shop, send results back, and at the end report what it did and what changed."
**Check:** why does the client have `max_retries=0`?

### Stop 8: tool_trajectory scoring
`src/casegate/scorers/tool_trajectory.py:122-130` `subsequence`
**What:** compares the tools the target called with the expected tools in `exact`, `subsequence` or `set` mode; in subsequence mode it walks the actual calls once and advances a pointer on each match.
**Why:** an agent can give a good reply after it skipped a required lookup; the trajectory catches that. A forbidden tool call sets the value to 0 in every mode (`src/casegate/scorers/tool_trajectory.py:151-153`).
**Say it like this:** "I grade what the agent did, not only what it said: the expected tools must appear in order, extra calls are allowed, and a forbidden call is an automatic zero."
**Check:** with expected `[get_account, get_order]` and actual `get_order, get_account, get_order`, what is the value?

### Stop 9: state_match and the refund_attempts rule
`src/casegate/scorers/state_match.py:85-104` `score`
**What:** for each expected state path, it walks the reported state (`src/casegate/scorers/state_match.py:44-54` `lookup`) and checks the value with a matcher; the value is the fraction of paths that match.
**Why:** a reply can say "refunded" when the order is not; state grades what happened. The matcher `all_amounts_lte` (`src/casegate/scorers/matchers.py:97-100` `_all_amounts_lte`) checks every refund attempt is at most the cap, and it is valid only in `state_match` (`src/casegate/scorers/matchers.py:114-115`). The toy agent logs every refund attempt, refused ones too, so `refund-over-cap-adv` catches a $390 try that the store blocked (`examples/toy_agent/store.py:184-188`).
**Say it like this:** "I check the world after the case, path by path, with small matchers like `lte` and `all_amounts_lte`."
**Check:** what does a path that does not resolve give: a fail, or an error?

### Stop 10: the LLM judge with samples and median
`src/casegate/scorers/llm_judge.py:178-196` `score`
**What:** builds one fixed prompt (rubric, conversation, reply, tool calls), calls the judge k times through `cached_grade`, takes the median score, and uses the reasoning of the sample closest to the median as the reason.
**Why:** temperature cannot be set on the Anthropic API (`docs/adr/0004-judge-client-two-adapters.md`), so stability comes from a strict prompt with anchors and a hedging rule (`src/casegate/scorers/llm_judge.py:24-42` `JUDGE_SYSTEM`), k samples and the median. The cache key is the whole request plus the sample index (`src/casegate/judge.py:100-111`).
**Say it like this:** "The judge is a noisy instrument, so I fix its prompt, take the median of k samples and report the spread."
**Check:** a rubric changes by one word: what is re-run, and what is not?

### Stop 11: aggregation (pass rate, std across repeats)
`src/casegate/stats.py:35-100` `aggregate`
**What:** a pure function that turns the repeats into case pass rates and one run summary: errors leave the denominator, the suite pass rate is the mean of case pass rates, and the std is taken across the per-repeat suite pass rates.
**Why:** errors are not failures (`docs/adr/0003-errors-are-not-failures.md`); the std across repeats feeds the gate tolerance (`docs/adr/0006-gate-tolerance-from-measured-variance.md`). It is pure, so tests call it on hand-made results (`tests/test_runner.py:311` `test_aggregate_maths`).
**Say it like this:** "A case pass rate is passes over scored repeats; the suite rate is their mean; the std across repeats tells me how noisy one run is."
**Check:** a case has 5 repeats: 3 pass, 1 fail, 1 error. What is its pass rate?

### Stop 11b: the cost of each call, or "unknown"
`src/casegate/prices.py:45-50` `cost`
**What:** turns input and output tokens into dollars from a dated price table, and returns None for a model with no price.
**Why:** a missing price must show as "cost unknown", never as a free run (FACTS.md §4.4 for the prices).
**Say it like this:** "Cost comes from a dated table that users can override, and an unknown model gives None, not zero."
**Check:** how does a user fix a wrong price without a new release?

### Stop 12: the Markdown report
`src/casegate/report.py:140-149` `render_markdown`
**What:** turns a run into `results/latest.md`: a header line with pass rate ± std, a summary table with this-run and full cost, the pass rate per tag, the 10 worst cases with the failing scorer and reason, and the errors.
**Why:** a reader needs the headline and the reason a case failed, not 75 raw repeats. The cells are shared with the terminal table (`src/casegate/console.py:32`), so both always agree.
**Say it like this:** "After every run there is a Markdown page that says the number, what it cost, and the worst cases with the exact scorer and reason."
**Check:** after a fully cached re-run, what do "cost this run" and "cost full" show? (`results/latest.md`: $0.00 and $0.05)

### Stop 13: compare and flips
`src/casegate/compare.py:84-137` `compare`
**What:** matches cases by id, gives each a majority verdict, lists pass-to-fail flips with the failing scorer and reason, fail-to-pass flips, error changes, added and removed cases, the 10 largest pass-rate deltas, and warnings when the target version, judge model or repeat count changed.
**Why:** a pass-rate delta says that quality moved; the flips say which case and why. The warnings stop a reviewer from blaming the agent for a judge change.
**Say it like this:** "Compare tells you which cases changed verdict and the reason, not only that the number moved."
**Check:** a case goes from 5/5 to 4/5. Is that a flip?

### Stop 14: the gate checks and exit codes
`src/casegate/gate.py:77-113` `gate`
**What:** runs every check and reports all of them: `scored`, `max_drop` (baseline pass rate minus run pass rate at most the tolerance), `max_errors`, and one `must_pass:<tag>` check per tag (every repeat of every tagged case must pass). The CLI exits 0 when all pass, 1 when any fails, 2 on bad input (`src/casegate/cli.py:185-207` `gate_cmd`).
**Why:** the average can hide one broken safety case, so must-pass cases are checked on their own. The tolerance comes from measured noise: 0.08 (`evals/tolerance.json` `max_drop`, `docs/adr/0006-gate-tolerance-from-measured-variance.md`). A NaN pass rate fails closed (`src/casegate/gate.py:99`).
**Say it like this:** "The gate blocks on a drop larger than the measured noise, on any error, or on any failed adversarial case, and it shows every failed check at once."
**Check:** what did the gate do on the baseline against itself, and on a copy with 3 cases flipped to fail? (FACTS.md §8: exit 0 and exit 1)

### Stop 15: the sticky PR comment
`action.yml:128-146` `Post or edit the PR comment`
**What:** on a pull request, the action looks for an earlier comment by `github-actions[bot]` whose body holds the marker `<!-- casegate-gate -->`; it edits that comment with PATCH, or posts a new one with POST when there is none.
**Why:** one comment that changes in place gives the reviewer the current verdict without a stack of old ones. The marker is the first line of the body that `gate` writes (`src/casegate/gate.py:184-191` `write_comment`). A failed call only prints a notice, because the job summary already holds the table; the step exit code does not decide the check. The last step does (`action.yml:148-158` `Result`): it exits with the gate exit code and counts an empty code as 1, so it fails closed.
**Say it like this:** "The action finds its own comment by a hidden marker and edits it, so every push updates one comment, and the check result comes from the gate exit code."
**Check:** why does the search also check `user.login`, and not only the marker? (A user could paste the marker into their own comment; the bot cannot edit it.) Is the edit-in-place behaviour observed on a real PR yet? (No: OPEN-2 in SPEC §20; the demo PR is a human step.)

### Stop 16: baseline from the base branch
`.github/workflows/eval-gate.yml:51-56` `Read the baseline from the base branch`
**What:** on a pull request, the workflow reads `evals/baseline.json` from the base branch with `git show "origin/$BASE_REF:evals/baseline.json"` and passes that copy to the action as `baseline` (`.github/workflows/eval-gate.yml:78`).
**Why:** a PR must not lower its own bar (`docs/adr/0008-baseline-from-base-branch.md`). For the same reason the PR cannot change three other inputs: a PR that edits `evals/baseline.json` fails without the label `baseline-update` (`.github/workflows/eval-gate.yml:58-69`), and `max-drop: "0.08"` and `must-pass-tag: adversarial` are literals, not read from PR files (`.github/workflows/eval-gate.yml:79-82`). Checkout keeps the token out of `.git/config`, because the suite runs PR code with the API key (`.github/workflows/eval-gate.yml:48-49`).
**Say it like this:** "The bar comes from main, not from the PR: the baseline is read from the base branch, the tolerance and the must-pass tag are literals, and a baseline change needs a label."
**Check:** what can a same-repo PR still change to pass the gate? (`eval-gate.yml` itself and `action.yml`; branch protection with CODEOWNERS is out of scope, SPEC §18.3 Known limit.)

### Stop 17: calibration, the judge against a person
`src/casegate/calibrate.py:142-180` `calibrate`
**What:** joins human pass/fail labels from a CSV to the judge scores in one run by `(case_id, repeat, scorer)`, and reports agreement, Cohen's kappa, a confusion table and every disagreement.
**Why:** a judge score is only worth gating on if a person gives the same verdict. Kappa removes the agreement that chance alone gives (`src/casegate/calibrate.py:131-139` `_kappa`); when one class is the only class, kappa is undefined and the output says so instead of printing a number. Calibration never gates: it exits 0, or 2 on bad input (`src/casegate/cli.py:210-233` `calibrate_cmd`).
**Say it like this:** "I label 40 judge results by hand, and casegate tells me how often the judge agrees with me, corrected for chance, and lists each case where we disagree."
**Check:** a judge and a person agree on 7 of 10 rows. The judge passes 7 and the person passes 6. What is kappa? (0.35: `tests/test_calibrate.py:47` `test_metrics_match_hand_computation`.) What is the real kappa? ([TBD: needs `evals/labels.csv`, 40 human labels, OPEN-5].)
