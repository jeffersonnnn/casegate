# casegate · toy-refund-agent

**pass rate 0.973** ± 0.037 · 15 cases × 5 repeats · errors 0 · cost $0.00 · target toy-agent@5 (claude-haiku-5-5) · judge claude-sonnet-5-5 · nogit · 2026-11-11T22:10:45Z

## Summary

| metric | value |
|---|--:|
| pass rate | 0.973 |
| std across repeats | 0.037 |
| scored cases | 15/15 |
| error repeats | 0/75 |
| tokens in / out | 330,507 / 30,557 |
| cost this run | $0.00 |
| cost full | $0.19 |
| cache | cache 75/75 outputs · 74/74 judge |
| duration | 0.0 s |

## Pass rate by tag

| tag | cases | pass rate |
|---|--:|--:|
| adversarial | 3 | 1.000 |
| citations | 4 | 0.900 |
| escalation | 1 | 1.000 |
| format | 2 | 1.000 |
| policy | 4 | 0.900 |
| refund | 5 | 1.000 |
| security | 1 | 1.000 |
| status | 2 | 1.000 |
| tools | 2 | 1.000 |

## Worst cases

| status | case | pass | mean | failing scorer | reason |
|---|---|--:|--:|---|---|
| ✗ fail | policy-giftcard-13 | 4/5 | 0.93 | citation_support 0.00 \< 0.70 | unsupported P4: The passage only states that gift card orders are non-refundable. The claim also asserts that Order 200… |
| ✗ fail | policy-window-10 | 4/5 | 0.97 | citation_support 0.50 \< 0.70 | unsupported P1: The passage says damaged items get a full refund if reported within 30 days of delivery. The claim says… |

<sub>casegate 0.1.0 · schema 1</sub>
