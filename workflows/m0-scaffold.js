export const meta = {
  name: 'casegate-m0-scaffold',
  description: 'M0: scaffold the package, models, prices, retry, CI',
  whenToUse: 'Run after the previous milestone reported all_load_bearing_observed = true. See workflows/README.md.',
  phases: [{ title: 'Build' }, { title: 'Verify' }, { title: 'Real-world-test' }, { title: 'Explain' }],
}
const PREAMBLE = 'You build part of casegate. The repo docs at /Users/jefferson/Desktop/new-portfolio/evals are your whole context; you have no chat history.\nRead in order: README.md, SPEC.md (AUTHORITATIVE; wins on conflict except newer ADRs), BUILD.md, CONTEXT.md, FACTS.md, docs/DESIGN.md, DECISIONS.md + docs/adr/*.md.\nRules: work only from the repo root /Users/jefferson/Desktop/new-portfolio/evals (never run git from the home folder, it is a different repo). Never print or commit .env or any key; load keys with `set -a; . ./.env; set +a` only when a step needs the real API. Never send temperature/top_p/top_k to Anthropic. Write only the files assigned to you. Use the words in CONTEXT.md. Do not push, publish, create repos, set secrets or spend money beyond what this milestone states; if a step needs that, stop and report it as needs_human.'

const BUILD_SCHEMA = { type: 'object', properties: { files_written: { type: 'array', items: { type: 'string' } }, notes: { type: 'string' }, needs_human: { type: 'array', items: { type: 'string' } } }, required: ['files_written', 'notes', 'needs_human'] }
const VERIFY_SCHEMA = { type: 'object', properties: { passed: { type: 'boolean' }, commands: { type: 'array', items: { type: 'object', properties: { cmd: { type: 'string' }, exit_code: { type: 'integer' }, tail: { type: 'string' } }, required: ['cmd', 'exit_code', 'tail'] } }, fixed: { type: 'array', items: { type: 'string' } }, remaining_failures: { type: 'array', items: { type: 'string' } } }, required: ['passed', 'commands', 'fixed', 'remaining_failures'] }
const REVIEW_SCHEMA = { type: 'object', properties: { findings: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] }, file: { type: 'string' }, problem: { type: 'string' }, fixed: { type: 'boolean' } }, required: ['severity', 'file', 'problem', 'fixed'] } } }, required: ['findings'] }
const MILESTONE = 'M0'
const EXPLAIN_SCHEMA = { type: 'object', properties: { stops_added: { type: 'integer' }, modules_added: { type: 'integer' }, numbers_added: { type: 'integer' }, readability_failures: { type: 'array', items: { type: 'string' } }, check_passed: { type: 'boolean' } }, required: ['stops_added', 'modules_added', 'numbers_added', 'readability_failures', 'check_passed'] }
const RWT_SCHEMA = { type: 'object', properties: { claims: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, milestone: { type: 'string' }, how_observed: { type: 'string' }, evidence: { type: 'string' }, observed: { type: 'boolean' }, result: { type: 'string', enum: ['holds', 'broken', 'not_observed'] } }, required: ['claim', 'milestone', 'how_observed', 'evidence', 'observed', 'result'] } }, open_items_not_observed: { type: 'array', items: { type: 'string' } }, regressions: { type: 'array', items: { type: 'string' } }, all_load_bearing_observed: { type: 'boolean' } }, required: ['claims', 'open_items_not_observed', 'regressions', 'all_load_bearing_observed'] }

const TASKS = [
  { key: 'pyproject', task: "Write pyproject.toml (SPEC §1 exactly: deps, extras, dev group, scripts, hatch version path, ruff/mypy/pytest config incl. [tool.mypy] plugins = pydantic.mypy and [tool.coverage.report] exclude_also), Makefile (SPEC §19; the baseline target uses a fresh CASEGATE_CACHE_DIR), empty tests/__init__.py, LICENSE (MIT 2026 Jefferson Ighalo), results/.gitkeep, src/casegate/__init__.py (__version__ = '0.1.0', re-exports RetryableError, SuiteError, JudgeError), src/casegate/errors.py (all error classes with the exact SPEC §7.3 constructors), src/casegate/cli.py with only `app = typer.Typer(no_args_is_help=True)` and the eager --version callback that prints `0.1.0` alone (SPEC §15), tests/conftest.py (GITHUB_STEP_SUMMARY autouse fixture + assert_golden helper, SPEC §17: compares text exactly, writes it unchanged with UPDATE_GOLDEN=1, fails unless text ends with exactly one newline). Then run `uv sync --all-extras` and fix until it succeeds." },
  { key: 'models', task: 'Write src/casegate/models.py exactly per SPEC §2 (all models, Status; every Field default as a keyword, TargetConfig validator raises ValueError only) and tests/test_models.py (round-trip, extra rejected). Write src/casegate/prices.py per SPEC §13 with tests/test_prices.py.' },
  { key: 'retry', task: 'Write src/casegate/retry.py per SPEC §7.3 (with_retries, retry-after cap, injectable sleep, casegate_attempts on non-retryable errors, anthropic errors only if importable via the SPEC try/except import) and tests/test_retry.py with a fake sleep. Write .github/workflows/ci.yml per SPEC §18.2 with action SHAs from FACTS §5.' }
]
const ANCHORS = ['`uv run casegate --version` prints `0.1.0` alone on one line', '`uv run ruff check && uv run mypy --strict src/casegate && uv run pytest -q` all exit 0']
const PRIOR_ANCHORS = []
const RWT_RULES = 'Apply the real-world-test discipline: an assumption is a claim you have not checked. For each load-bearing claim below, convert it into a DIRECT observation against reality (run the real command, open the real file, call the real API where this milestone allows it, read the real output). "Tests pass" is not an observation of behaviour. Never use a mock to observe a claim that says real. Mark OPEN items you could not observe as not_observed (they make all_load_bearing_observed false unless the claim says it may stay OPEN). Then re-observe every PRIOR milestone\'s anchor claims listed under PRIOR ANCHORS to catch regressions. Fix nothing silently: if a claim is broken, report it as broken with evidence. all_load_bearing_observed = true only if every claim in THIS milestone and every prior anchor holds.'

phase('Build')
const built = await parallel(TASKS.map(t => () => agent(
  PREAMBLE + '\n\nYOUR TASK (' + t.key + '): ' + t.task + '\nWrite only these files. Other agents write the other files of this milestone at the same time; do not edit theirs. Run the relevant tests for your files before you finish.',
  { label: 'build:' + t.key, phase: 'Build', schema: BUILD_SCHEMA, agentType: 'general-purpose' })))
const needsHuman = built.filter(Boolean).flatMap(b => b.needs_human)
log('built: ' + built.filter(Boolean).map(b => b.files_written.length).reduce((a, b) => a + b, 0) + ' files; needs_human: ' + needsHuman.length)

phase('Verify')
let verify = null
for (let round = 1; round <= 3; round++) {
  verify = await agent(PREAMBLE + '\n\nVERIFY round ' + round + '. Run from the repo root: `uv sync --all-extras`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict src/casegate`, `uv run pytest -q --cov=casegate --cov-fail-under=85` (skip the commands that do not apply yet at this milestone and say so). Fix every failure in the code (not by deleting or weakening tests; never lower the coverage bar), re-run, and report the final exit codes.',
    { label: 'verify:' + round, phase: 'Verify', schema: VERIFY_SCHEMA, agentType: 'general-purpose' })
  if (verify && verify.passed) break
}
if (!verify || !verify.passed) { log('Verify did not pass after 3 rounds; stopping before review/live'); return { built, verify, needsHuman, all_load_bearing_observed: false } }

const reviews = []
const unfixed = []

const live = null

phase('Real-world-test')
const rwt = await agent(PREAMBLE + '\n\nREAL-WORLD-TEST STAGE.\n' + RWT_RULES +
  '\n\nTHIS MILESTONE CLAIMS:\n- ' + ANCHORS.join('\n- ') +
  '\n\nPRIOR ANCHORS:\n- ' + (PRIOR_ANCHORS.length ? PRIOR_ANCHORS.join('\n- ') : '(none)') +
  '\n\nKnown human-gated items not yet done (report them as not_observed, they may stay OPEN only if a claim depends on them): ' + JSON.stringify(needsHuman),
  { label: 'real-world-test', phase: 'Real-world-test', schema: RWT_SCHEMA, agentType: 'general-purpose' })
phase('Explain')
const explain = await agent(PREAMBLE + '\n\nEXPLAIN STAGE. Apply the walkthrough skill: read ~/.claude/skills/walkthrough/SKILL.md and ~/.claude/skills/walkthrough/FORMAT.md, then docs/explain/ in the repo. Update docs/explain/ for the files THIS milestone built: fill the [PLANNED: ' + MILESTONE + '] tour stops in 01-tour.md, add one modules/<name>.md page per new source file, fill drill answers marked [PLANNED: ' + MILESTONE + '], replace [TBD] numbers in 03-numbers.md only with values read from result files (name the file and field), add a failure story to 04-failures.md for each real failure found in this milestone, and fill the readability check table in docs/explain/README.md (SPEC §1b: 3-5 line module docstrings, files <= 250 lines (agent loop 200), why-not-what comments; list every failure, do not hide it). Never edit docs/explain/progress.md. Run `python scripts/check_explain.py` from the repo root and fix references until it exits 0.',
  { label: 'explain', phase: 'Explain', schema: EXPLAIN_SCHEMA, agentType: 'general-purpose' })
return { built, verify, reviews, unfixed, live, needsHuman, rwt, explain, all_load_bearing_observed: !!(explain && explain.check_passed && rwt && rwt.all_load_bearing_observed && unfixed.length === 0) }
