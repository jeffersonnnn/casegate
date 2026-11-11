# toy agent loop (`examples/toy_agent/agent.py`, 168 lines)

**30 seconds:** The system under test in the example suite: a refund support agent on Claude Haiku 5.5. It is small on purpose, so a reader can see the whole tool loop and how casegate's Output (trajectory, state, citations, tokens, cost) is built from one agent run. The runner owns retries, so this module lets API errors propagate.

**2 minutes:** The model, effort, token limit and turn limit are constants at the top (`examples/toy_agent/agent.py:22-25` `MODEL`). The system prompt is read from `prompt.md` (`examples/toy_agent/agent.py:27` `SYSTEM_PROMPT`). `TOOLS` declares five strict tools: `get_account`, `get_order`, `issue_refund`, `escalate` and `search_policy` (`examples/toy_agent/agent.py:40-71` `TOOLS`). `run` at `examples/toy_agent/agent.py:113-168` `run` makes a fresh store per case and loops at most 8 turns (`examples/toy_agent/agent.py:120-157`). Each turn calls `messages.create` with the tools and an effort level, and no sampling fields (`examples/toy_agent/agent.py:121-128`). `end_turn` ends the loop; any stop reason other than `tool_use` is an error (`examples/toy_agent/agent.py:132-136`). For each `tool_use` block it runs the tool on the store, records a `ToolCall`, and sends the result back (`examples/toy_agent/agent.py:143-157`). At the end it builds the Output: the reply text, the trajectory, the citations from `[Pn]` markers, the store state, the tokens and the cost (`examples/toy_agent/agent.py:159-168`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `examples/toy_agent/agent.py:21-23` | model and effort are constants | a change of either must bump `target.version`, so the output cache goes stale |
| `examples/toy_agent/agent.py:76-81` | lazy client with `max_retries=0` | import needs no key, and casegate's retry loop counts every try |
| `examples/toy_agent/agent.py:134-138` | bad stop reason and turn limit raise | a cut-off reply is an `error` repeat, not a scored fail |
| `examples/toy_agent/agent.py:141` | the assistant content goes back unchanged | thinking blocks must be returned as is, or the next call fails |
| `examples/toy_agent/agent.py:88-110` | one Citation per `[Pn]` marker, the sentence is the claim | `citation_support` can grade each marker on its own |
| `examples/toy_agent/agent.py:107-108` | an unknown id becomes a citation with "(no such passage)" | the judge marks it unsupported instead of the id being dropped |

## Trade-off
A framework (an agent SDK) would hide the loop. A hand-written loop of about 50 lines shows exactly which tool calls and state casegate grades. The cost: no streaming, no parallel tool calls in one turn beyond what the API returns.

## Failure modes
The loop is tested with a scripted client (`tests/test_toy_store.py:167` `test_run_tool_loop`). A bad stop reason raises (`tests/test_toy_store.py:199` `test_run_bad_stop_reason`). The turn limit raises (`tests/test_toy_store.py:205` `test_run_turn_limit`). Citation extraction, including a marker after the full stop (`tests/test_toy_store.py:121` `test_extract_citations`). Live: the 15 × 5 baseline had 0 error repeats (`evals/baseline.json` `summary.n_error_repeats`).

## What I would change
Split a sentence at each `[Pn]` marker, so each claim is only the clause that the marker covers. The baseline fails come from two-part claims graded against one passage (`04-failures.md`). Cost: a target version bump, a new baseline (about $0.23, `evals/baseline.json` `summary.cost_usd_full`), and a rule for clauses with no marker.

## 10-minute version
The prompt fixes "today" at 2026-11-01 to match the store (`tests/test_toy_store.py:23` `test_prompt_date_equals_store_today`). toy-agent@2 added one prompt line: a refusal must give the rule. toy-agent@3 to @5 replaced the two citation lines with three: one policy claim per cited sentence, one marker before the full stop, order facts in separate sentences without markers (FACTS.md §8, `04-failures.md`). Cost per call uses the dated price table (`src/casegate/prices.py:45-50` `cost`). The agent is the `PythonTarget` path `examples.toy_agent.agent:run` in `evals/suite.yaml`; casegate imports it once and calls it per (case, repeat).
