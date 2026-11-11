# Diagrams

## Architecture

```mermaid
flowchart LR
  CASES[suite.yaml + cases/*.yaml] --> LOADER[Loader + validation]
  LOADER --> RUNNER[Async runner: semaphore, retries, repeats]
  RUNNER --> OCACHE[(outputs cache)]
  RUNNER --> TARGET[Target adapter: Python / HTTP]
  TARGET --> SUT[System under test]
  RUNNER --> SCORERS[7 scorers]
  SCORERS --> JUDGE[JudgeClient: Anthropic / OpenAI-compatible]
  JUDGE --> JCACHE[(judge cache)]
  SCORERS --> RUN[Run JSON]
  RUN --> REPORT[Markdown report]
  RUN --> COMPARE[Compare with baseline]
  COMPARE --> GATE[Gate: exit code + PR comment]
  RUN --> CALIB[Calibrate vs human labels]
```
Whiteboard: draw left to right. Cases in, runner in the middle with two cylinders (caches), run JSON on the right. Then the three consumers of the run: report, compare → gate, calibrate.

## One PR, sequence

```mermaid
sequenceDiagram
  participant PR as Pull request
  participant WF as eval-gate workflow
  participant CG as casegate
  participant M as main branch
  PR->>WF: push
  WF->>M: read evals/baseline.json
  WF->>CG: run evals --repeat 5
  CG-->>WF: run.json
  WF->>CG: gate --baseline --run
  CG-->>WF: exit 0/1 + comment.md
  WF->>PR: create or edit the sticky comment
```
Whiteboard: four lifelines; the key arrow is the baseline read from main, not from the PR.

## Case status

```mermaid
stateDiagram-v2
  [*] --> running
  running --> error: target or scorer fails after retries
  running --> pass: every scorer passes
  running --> fail: any scorer fails
```
Whiteboard: three end states; say "error is not fail" (ADR 0003).

## Data model

From `src/casegate/models.py:168-182` `Run` and the models above it.

```mermaid
classDiagram
  Run "1" --> "1" RunSummary
  Run "1" --> "*" CaseResult
  CaseResult "1" --> "*" RepeatResult : one per repeat
  RepeatResult "1" --> "0..1" Output
  RepeatResult "1" --> "*" Score
  Output "1" --> "*" ToolCall
  Output "1" --> "*" Citation
  Suite "1" --> "1" TargetConfig
  Suite "1" --> "1" JudgeConfig
  Suite "1" --> "1" RetryConfig
  Case "1" --> "*" ScorerConfig
  class RepeatResult {
    status
    attempts
    cached
    cost_usd
    cost_usd_full
  }
  class Run {
    schema_version
    target_version
    repeat
  }
```
Whiteboard: draw config on the left (Suite, Case) and results on the right (Run down to Score). Say that Output is None when the repeat errored. Say that every model forbids unknown fields, except ScorerConfig, which keeps scorer params.
