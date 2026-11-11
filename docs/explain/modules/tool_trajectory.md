# scorers/tool_trajectory (`src/casegate/scorers/tool_trajectory.py`, 162 lines)

**30 seconds:** The `tool_trajectory` scorer: the agent must call the right tools, with the right arguments. An agent can give a good reply after it skipped a required lookup, or after it called a tool it must never call. This scorer compares the calls in one of three modes, and a forbidden call always scores 0.

**2 minutes:** `_resolve` at `src/casegate/scorers/tool_trajectory.py:40-55` `_resolve` takes `tools` and `forbidden` from the params, else from `expected.tools` and `expected.tools_forbidden`; at least one must exist. Each expected tool is a name or a `{name, args}` spec whose args are matchers (`src/casegate/scorers/tool_trajectory.py:25-28` `ToolSpec`). `score` at `src/casegate/scorers/tool_trajectory.py:97-162` `score` drops ignored tools from the comparison (`src/casegate/scorers/tool_trajectory.py:103-105`). In `exact` mode it counts the matching prefix (`src/casegate/scorers/tool_trajectory.py:111-121`). In `subsequence` mode it walks the actual calls once and moves a pointer on each match (`src/casegate/scorers/tool_trajectory.py:122-130`). In `set` mode each expected spec takes the first unused matching call (`src/casegate/scorers/tool_trajectory.py:131-149`). A forbidden call anywhere sets the value to 0 (`src/casegate/scorers/tool_trajectory.py:151-153`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/tool_trajectory.py:33` | the default mode is `subsequence` | the required order is checked and extra lookups are allowed, which fits most agents |
| `src/casegate/scorers/tool_trajectory.py:71-74` | a call matches by name and every listed arg | unlisted args are free; listed ones use matchers like `{lte: 39}` |
| `src/casegate/scorers/tool_trajectory.py:118` | exact mode: matched prefix over the longer list | an extra call at the end lowers the value |
| `src/casegate/scorers/tool_trajectory.py:151` | forbidden checks every call, ignored ones too | `ignore` cannot hide a forbidden call |
| `src/casegate/scorers/tool_trajectory.py:85-86` | `allow_extra: false` only in set mode | in the other modes the order rule already decides about extras |

## Trade-off
Edit distance between trajectories gives a smoother score, but its value is hard to explain and two very different mistakes can score the same. Three named modes with a "first unmatched" reason tell the author exactly what to fix.

## Failure modes
`tests/scorers/test_tool_trajectory.py:28` `test_subsequence_with_arg_matchers_passes`, `tests/scorers/test_tool_trajectory.py:69` `test_exact_mode`, `tests/scorers/test_tool_trajectory.py:79` `test_set_mode`, `tests/scorers/test_tool_trajectory.py:112` `test_empty_expected`, `tests/scorers/test_tool_trajectory.py:159` `test_forbidden_wins_over_ignore`, `tests/scorers/test_tool_trajectory.py:173` `test_load_errors`.

## What I would change
Set mode is greedy: each spec takes the first unused matching call. With arg matchers, a loose spec can use up a call that a stricter later spec needed, and the case fails although a full match exists. A bipartite match would find it. Cost: about 20 lines and harder to explain. (Greedy is safe in subsequence mode: the earliest match always leaves the most calls for later specs.)

## 10-minute version
`details` keep the expected names, the actual names, the matched count, the mode, the forbidden calls and the ignored count (`src/casegate/scorers/tool_trajectory.py:154-161`), so a report can show the trajectory. Reasons cut long lists after 8 names (`src/casegate/scorers/tool_trajectory.py:64-68` `_join`). With no expected tools, subsequence and set give 1.0 (`src/casegate/scorers/tool_trajectory.py:127`), so a case with only `forbidden` works.
