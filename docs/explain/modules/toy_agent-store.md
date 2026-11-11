# toy agent store (`examples/toy_agent/store.py`, 226 lines)

**30 seconds:** The toy agent's world: a small shop with orders, a refund policy and the tools over them. Every case gets a fresh store with a fixed TODAY, so a refund rule gives the same answer on every run and `state_match` can check the facts the agent changed. The tools never raise: a broken rule comes back as a result the model reads.

**2 minutes:** `TODAY` is 2026-11-01 and the refund window is 30 days (`examples/toy_agent/store.py:18-20` `TODAY`). The policy is loaded from `policy.md`, one `[Pn] text` line per passage, and a bad line fails at import (`examples/toy_agent/store.py:25-35` `_load_policy`). `fresh_store` builds 7 orders for 3 customers, each order shaped for one case: in window, partial, already refunded, shipped, 45 days old, gift card, and one with an injection note (`examples/toy_agent/store.py:89-140` `fresh_store`). `_refund_error` checks the rules in a fixed order: not found, not delivered, outside the window, gift card, invalid amount, over the balance (`examples/toy_agent/store.py:163-178` `_refund_error`). `issue_refund` logs every attempt, failed ones too, then applies a valid refund (`examples/toy_agent/store.py:181-195` `issue_refund`). `call_tool` runs one tool by name and turns bad arguments into an error result (`examples/toy_agent/store.py:217-226` `call_tool`). `Store.state` is the JSON that `state_match` reads (`examples/toy_agent/store.py:68-73` `state`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `examples/toy_agent/store.py:18` | a fixed TODAY | the window rule gives the same answer on every run; the Phase 2 agent stalled on a missing date (FACTS.md §4.1) |
| `examples/toy_agent/store.py:132-133` | an order note says "ignore your rules" | adversarial data for `injection-order-note-adv` |
| `examples/toy_agent/store.py:164-178` | rules in a fixed order | the model always sees the same error for the same call |
| `examples/toy_agent/store.py:184-188` | every refund attempt is logged | `refund-over-cap-adv` catches an over-cap try that the store refused (`all_amounts_lte`) |
| `examples/toy_agent/store.py:203-205` | `search_policy` returns all 5 passages | no retrieval step to get wrong; the case grades the agent, not a search |

## Trade-off
A real database would be closer to production. An in-memory dataclass store makes each case independent and fast, and its state is a plain dict. The cost: no concurrency effects, no partial failures of the store itself.

## Failure modes
A refund in the window (`tests/test_toy_store.py:39` `test_refund_within_window_full`). Each refund rule and its error (`tests/test_toy_store.py:64` `test_refund_rules`). Attempts are logged on success too (`tests/test_toy_store.py:78` `test_attempts_logged_for_success_too`). Fresh stores share nothing (`tests/test_toy_store.py:86` `test_fresh_store_shares_nothing`). Tools through `call_tool` (`tests/test_toy_store.py:104` `test_tools_via_call_tool`).

## What I would change
Read the orders from a YAML fixture next to the cases, so a new case can add its order without a code change. Cost: a loader and a schema, about 30 lines.

## 10-minute version
Money uses a tolerance of 0.005, so a refund of 39.004 on a 39.0 order passes (`examples/toy_agent/store.py:20`, `tests/test_toy_store.py:74` `test_cap_tolerance_allows_rounding`). Dates leave the store as ISO strings, so a saved run reads back unchanged (`examples/toy_agent/store.py:76-82` `_order_dict`). Order ids are strings, which matches the state paths in the cases, for example `orders.1042.status`.
