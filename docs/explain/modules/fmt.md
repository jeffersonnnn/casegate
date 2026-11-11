# fmt (`src/casegate/fmt.py`, 104 lines)

**30 seconds:** Every number, money and table-cell format that casegate prints, in one place. The terminal, the Markdown report, the comparison, the PR comment and calibration all show the same numbers, so one module keeps them the same everywhere. Its rules are tested in one file.

**2 minutes:** `fmt_rate` at `src/casegate/fmt.py:35-36` `fmt_rate` gives 3 decimals or `—` for None. `fmt_money` at `src/casegate/fmt.py:39-45` `fmt_money` gives `unknown` for None, 4 decimals below one cent and 2 otherwise (`src/casegate/fmt.py:27-32` `_money_digits`), and never a signed zero. The delta formats add `+` or a real minus sign U+2212 (`src/casegate/fmt.py:21-24` `_signed`). `fmt_cache` at `src/casegate/fmt.py:80-87` `fmt_cache` prints `cache off` when there were no output lookups. `md_cell` at `src/casegate/fmt.py:96-114` `md_cell` makes free text safe for one Markdown cell: newlines to spaces, `|` escaped, and for Markdown `<` escaped and a zero-width joiner after `@` (the terminal passes `markdown=False`), cut with `…`.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/fmt.py:18` | U+2212 minus sign | a hyphen looks wrong next to digits |
| `src/casegate/fmt.py:43-44` | a rounded zero is `$0.00`, never `−$0.00` | a signed zero reads as a bug |
| `src/casegate/fmt.py:40-41` | None money is `unknown` | a missing price must not show as free |
| `src/casegate/fmt.py:110-112` | a cut never leaves a lone `\` before the ellipsis | a lone backslash would escape the next character and break the table |

## Trade-off
Formatting inline in each renderer is shorter at first, but the same delta would soon print three ways. One module costs one import per renderer.

## Failure modes
`tests/test_fmt.py:54` `test_fmt_money`, `tests/test_fmt.py:70` `test_fmt_delta`, `tests/test_fmt.py:123` `test_fmt_cache`, `tests/test_fmt.py:152` `test_md_cell_cut_never_splits_an_escaped_pipe`.

## What I would change
Add a locale option for the money format. Cost: a dependency (`babel`) for a feature no current user needs.

## 10-minute version
M1 uses only `fmt_rate`, `fmt_money` and `fmt_cache`, in the terminal summary line (`src/casegate/console.py:106-111`). M2's report, compare and gate use the rest. `fmt_ts` reads a naive time as UTC, because run files always hold UTC (`src/casegate/fmt.py:90-93` `fmt_ts`).
