# DECISIONS

Index of the architecture decision records. The full text of each is in `docs/adr/`.

| # | Decision | One line |
|---|---|---|
| [0001](docs/adr/0001-name-casegate.md) | Name the project `casegate` | `evalgate` was taken on PyPI three times over. |
| [0002](docs/adr/0002-case-passes-when-every-scorer-passes.md) | A case passes only when every scorer passes | A failed case always has a concrete failed scorer and reason. |
| [0003](docs/adr/0003-errors-are-not-failures.md) | Errors leave the pass rate and have their own gate limit | An outage cannot look like a regression, and cannot pass in silence. |
| [0004](docs/adr/0004-judge-client-two-adapters.md) | A small JudgeClient with two adapters, no litellm | Anthropic and OpenAI-compatible; no temperature on Anthropic. |
| [0005](docs/adr/0005-two-caches.md) | Separate caches for target outputs and judge results | A rubric change re-grades without re-running the agent. |
| [0006](docs/adr/0006-gate-tolerance-from-measured-variance.md) | Gate tolerance from measured variance | max-drop = 2 × measured std of the suite pass rate, at least 0.02. |
| [0007](docs/adr/0007-design-direction-lab-instrument.md) | Design direction A, "Lab instrument" | Dark, one signal colour, monospace; B and C rejected. |
| [0008](docs/adr/0008-baseline-from-base-branch.md) | The PR gate reads the baseline from the base branch | A PR cannot lower its own bar; baseline edits need the `baseline-update` label. |
