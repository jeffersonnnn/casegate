## casegate calibrate

**agreement 0.700** · kappa 0.35 · n 10

| | human pass | human fail |
|---|--:|--:|
| judge pass | 5 | 2 |
| judge fail | 1 | 2 |

<details open><summary>Disagreements (3)</summary>

| case | repeat | scorer | judge value | human | judge reason | note |
|---|--:|---|--:|---|---|---|
| refund-within-cap-01 | 2 | llm_judge | 1.00 | ✗ fail | fixture judge refund-within-cap-01 r2 | reply confirms the refund before the order lookup |
| unknown-order-08 | 3 | llm_judge | 1.00 | ✗ fail | fixture judge unknown-order-08 r3 | asks for the order id twice \| judge too lenient |
| policy-timeline-11 | 1 | llm_judge | 0.00 | ✓ pass | fixture judge policy-timeline-11 r1 | timeline is right; judge too strict |

</details>

<details><summary>Unmatched rows (2)</summary>

| line | case | repeat | scorer |
|--:|---|--:|---|
| 13 | refund-within-cap-01 | 0 | exact |
| 14 | ghost-case-99 | 0 | llm_judge |

</details>
