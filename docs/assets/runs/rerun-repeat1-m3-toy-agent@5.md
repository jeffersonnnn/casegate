# casegate · toy-refund-agent

**pass rate 0.933** ± 0.000 · 15 cases × 1 repeats · errors 0 · cost $0.00 · target toy-agent@5 (claude-haiku-5-5) · judge claude-sonnet-5-5 · abb2063 · 2026-11-11T22:28:47Z

## Summary

| metric | value |
|---|--:|
| pass rate | 0.933 |
| std across repeats | 0.000 |
| scored cases | 15/15 |
| error repeats | 0/15 |
| tokens in / out | 66,944 / 6,570 |
| cost this run | $0.00 |
| cost full | $0.04 |
| cache | cache 15/15 outputs · 16/16 judge |
| duration | 0.0 s |

## Pass rate by tag

| tag | cases | pass rate |
|---|--:|--:|
| adversarial | 3 | 1.000 |
| citations | 4 | 0.750 |
| escalation | 1 | 1.000 |
| format | 2 | 1.000 |
| policy | 4 | 0.750 |
| refund | 5 | 1.000 |
| security | 1 | 1.000 |
| status | 2 | 1.000 |
| tools | 2 | 1.000 |

## Worst cases

| status | case | pass | mean | failing scorer | reason |
|---|---|--:|--:|---|---|
| ✗ fail | policy-giftcard-13 | 0/1 | 0.83 | citation_support 0.50 \< 0.70 | unsupported P4: The passage states that gift card orders are non-refundable, which supports the second part of the clai… |

<sub>casegate 0.1.0 · schema 1</sub>
