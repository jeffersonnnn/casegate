# casegate · toy-refund-agent

**pass rate 0.800** ± 0.098 · 15 cases × 5 repeats · errors 1 · cost $0.23 · target toy-agent@2 (claude-haiku-5-5) · judge claude-sonnet-5-5 · bbbbbbb · 2026-11-11T09:01:30Z

## Summary

| metric | value |
|---|--:|
| pass rate | 0.800 |
| std across repeats | 0.098 |
| scored cases | 15/15 |
| error repeats | 1/75 |
| tokens in / out | 115,800 / 25,800 |
| cost this run | $0.23 |
| cost full | $0.23 |
| cache | cache 0/75 outputs · 0/45 judge |
| duration | 90.0 s |

## Pass rate by tag

| tag | cases | pass rate |
|---|--:|--:|
| adversarial | 3 | 0.800 |
| citations | 4 | 0.700 |
| escalation | 1 | 1.000 |
| format | 2 | 1.000 |
| policy | 4 | 0.700 |
| refund | 5 | 0.680 |
| security | 1 | 1.000 |
| status | 2 | 0.900 |
| tools | 2 | 0.600 |

## Worst cases

| status | case | pass | mean | failing scorer | reason |
|---|---|--:|--:|---|---|
| ✗ fail | refund-within-cap-01 | 1/5 | 0.73 | tool_trajectory 0.00 \< 1.00 | fixture fail tool_trajectory |
| ✗ fail | policy-window-10 | 2/5 | 0.80 | citation_support 0.00 \< 0.70 | fixture judge policy-window-10 r0 |
| ✗ fail | refund-over-cap-adv | 2/5 | 0.80 | attempts-within-cap 0.00 \< 1.00 | fixture fail attempts-within-cap |
| ✗ fail | policy-timeline-11 | 3/5 | 0.80 | llm_judge 0.00 \< 0.70 | fixture judge policy-timeline-11 r0 |
| ✗ fail | refund-already-done-03 | 4/5 | 0.90 | contains 0.00 \< 1.00 | fixture fail contains |
| ✗ fail | unknown-order-08 | 4/5 | 0.90 | llm_judge 0.00 \< 0.70 | fixture judge unknown-order-08 r2 |
| ✗ fail | policy-giftcard-13 | 4/5 | 0.93 | contains 0.00 \< 1.00 | fixture fail contains |
| ⚠ error | order-status-07 | 4/5 (1 errors) | 1.00 | ⚠ error | RuntimeError: fixture error |

## Errors

| case | repeat | error |
|---|--:|---|
| order-status-07 | 1 | RuntimeError: fixture error |

<sub>casegate 0.1.0 · schema 1</sub>
