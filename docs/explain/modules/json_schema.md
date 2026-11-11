# scorers/json_schema (`src/casegate/scorers/json_schema.py`, 104 lines)

**30 seconds:** The `json_schema` scorer: the reply must be JSON that fits a JSON Schema (Draft 2020-12). Structured replies break in two ways, bad JSON or the wrong shape, and the reason says which one and where. The schema is resolved and checked at load time.

**2 minutes:** `_resolve_schema` at `src/casegate/scorers/json_schema.py:47-59` `_resolve_schema` takes an inline `schema`, a `schema_path` file (`.json`, `.yaml`, `.yml`, relative to the suite root), or `expected.schema`; `schema` and `schema_path` together are an error. `check` at `src/casegate/scorers/json_schema.py:72-86` `check` validates the schema itself with `Draft202012Validator.check_schema` and stores it in `schema_`. `score` at `src/casegate/scorers/json_schema.py:88-104` `score` takes the first fenced block if the reply has one (`src/casegate/scorers/json_schema.py:62-65` `extract_json_text`), parses it, and reports the shallowest schema error as a `$.path: message` reason.

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/scorers/json_schema.py:27-29` | the field is `schema_` with the alias `schema` | a field named `schema` shadows a pydantic method (FACTS.md §7) |
| `src/casegate/scorers/json_schema.py:62-65` | the first fenced block is used | models often wrap JSON in a code fence |
| `src/casegate/scorers/json_schema.py:84-85` | `check` stores the resolved schema | `score` reads one field, whatever the source was, and never reads a file during a run |
| `src/casegate/scorers/json_schema.py:99-102` | the first error is the shallowest path | the root cause is shown, not a deep side effect |

## Trade-off
Pydantic models as schemas would be more Pythonic, but JSON Schema is language-neutral and fits an HTTP target written in any language. The value is binary (0 or 1); a partial score per field would hide which field broke.

## Failure modes
`tests/scorers/test_json_schema.py:31` `test_fenced_json_is_extracted`, `tests/scorers/test_json_schema.py:36` `test_invalid_json_reason`, `tests/scorers/test_json_schema.py:47` `test_first_error_is_shallowest_path`, `tests/scorers/test_json_schema.py:63` `test_schema_path_errors`.

## What I would change
Report every schema error (up to a limit) in `details`, not only the first in the reason. Cost: a larger run file.

## 10-minute version
`check` writes into the params object (`p.schema_ = schema`), so the scorer must be built through `build_scorers`; `score` raises `ValueError` otherwise (`src/casegate/scorers/json_schema.py:90-91`). The fence regex accepts any language tag, so ```` ```json ```` and a bare ```` ``` ```` both work.
