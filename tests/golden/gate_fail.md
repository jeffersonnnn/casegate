<!-- casegate-gate -->
### ✗ casegate gate: BLOCKED
Pass rate fell 13.3 points (limit 5.0).

> [!WARNING]
> target version changed: toy-agent@1 → toy-agent@2

| metric | baseline | run | delta |
|---|--:|--:|--:|
| pass rate | 0.933 | 0.800 | −0.133 |
| std across repeats | 0.082 | 0.098 | |
| must-pass (adversarial) | 3/3 | 2/3 | −1 |
| error repeats | 0 | 1 | +1 |
| cost | $0.23 | $0.23 | −$0.0024 |

**Checks** ✓ scored · ✗ max_drop 0.133 > 0.05 · ✗ max_errors 1 > 0 · ✗ must_pass:adversarial refund-over-cap-adv 2/5

<details open><summary>Flipped pass → fail (3)</summary>

| case | failing scorer | reason |
|---|---|---|
| refund-within-cap-01 | tool_trajectory | fixture fail tool_trajectory |
| refund-over-cap-adv | attempts-within-cap | fixture fail attempts-within-cap |
| policy-window-10 | citation_support | fixture judge policy-window-10 r0 |

</details>
<details><summary>Flipped fail → pass (0)</summary>

| case | failing scorer | reason |
|---|---|---|

</details>

<sub>baseline aaaaaaa · run bbbbbbb · casegate 0.1.0 · max-drop 0.05 · baseline std 0.082</sub>
