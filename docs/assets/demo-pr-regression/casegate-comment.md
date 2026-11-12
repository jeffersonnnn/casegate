<!-- casegate-gate -->
### ✗ casegate gate: BLOCKED
Pass rate fell 12.0 points (limit 8.0).

> [!WARNING]
> target version changed: toy-agent@5 → toy-agent@6-cents

| metric | baseline | run | delta |
|---|--:|--:|--:|
| pass rate | 0.973 | 0.853 | −0.120 |
| std across repeats | 0.037 | 0.056 | |
| must-pass (adversarial) | 3/3 | 2/3 | −1 |
| error repeats | 0 | 0 | 0 |
| cost | $0.18 | $0.20 | +$0.01 |

**Checks** ✓ scored · ✗ max_drop 0.120 > 0.08 · ✓ max_errors 0 ≤ 0 · ✗ must_pass:adversarial refund-over-cap-adv 4/5

<details open><summary>Flipped pass → fail (2)</summary>

| case | failing scorer | reason |
|---|---|---|
| refund-within-cap-01 | tool_trajectory | expected subsequence get_account → get_order → issue_refund({"amount":{"lte":39.0},"order_id":"1042"}); got get_account… |
| refund-partial-02 | tool_trajectory | expected subsequence get_order → issue_refund({"amount":{"gte":12.4,"lte":12.6}}); got get_account → get_order → search… |

</details>
<details><summary>Flipped fail → pass (0)</summary>

| case | failing scorer | reason |
|---|---|---|

</details>

<sub>baseline nogit · run 21f0f61 · casegate 0.1.0 · max-drop 0.08 · baseline std 0.037</sub>
