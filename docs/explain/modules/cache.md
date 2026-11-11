# cache (`src/casegate/cache.py`, 79 lines)

**30 seconds:** A content-addressed disk cache with two namespaces: `outputs/` for what the target said and `judge/` for what the judge said about it (`docs/adr/0005-two-caches.md`). A rubric edit re-grades old outputs and does not re-run the agent. A missing, corrupt or invalid file is a miss, so a bad cache can cost money but never give a wrong score.

**2 minutes:** `canonical_json` at `src/casegate/cache.py:23-25` `canonical_json` writes a value with sorted keys and no spaces, so two equal key objects give one text. `key` at `src/casegate/cache.py:28-29` `key` is the SHA-256 of that text. `Cache` at `src/casegate/cache.py:32-42` `Cache` takes its root from the argument, else `CASEGATE_CACHE_DIR`, else `.casegate/cache` in the working folder (`src/casegate/cache.py:37-39`). `path` puts each entry in a two-character sub-folder of its namespace (`src/casegate/cache.py:44-46` `path`). `get` counts a lookup, reads the JSON, and returns None for a missing or broken file (`src/casegate/cache.py:54-58`), for a value that is not a dict (`src/casegate/cache.py:59-60`), or when the caller's `validate` raises (`src/casegate/cache.py:61-65`). Only then does it count a hit (`src/casegate/cache.py:66`). `put` writes to a temporary name and renames it into place (`src/casegate/cache.py:72-76`). The callers build the keys: the runner for outputs (`src/casegate/runner.py:140-146`) and `cached_grade` for grades (`src/casegate/judge.py:100-111`).

## Key lines
| Lines | What happens | Why it is done this way |
|---|---|---|
| `src/casegate/cache.py:18` | two namespaces, `outputs` and `judge` | a judge change is measured apart from a target change (`docs/adr/0005-two-caches.md`) |
| `src/casegate/cache.py:23-25` | sorted keys, fixed separators | dict order must not change the hash |
| `src/casegate/cache.py:37-39` | `CASEGATE_CACHE_DIR` wins over the default | the baseline run uses a fresh temp folder (SPEC §16.3), and CI can point all runs at one folder |
| `src/casegate/cache.py:61-65` | `validate` failure is a miss | an entry from an older schema is re-computed and overwritten, not a crash mid-run |
| `src/casegate/cache.py:72-79` | write aside, then `os.replace`; delete the temp file on any failure | two runs at once, or a crash, never leave a half-written entry |

## Trade-off
SQLite would hold every entry in one file and allow queries. One JSON file per key needs no locking, is atomic with one rename, and a person can open an entry with `cat`. The cost is many small files and no eviction.

## Failure modes
A corrupt file is a miss and is overwritten (`tests/test_cache.py:60` `test_corrupt_file_is_a_miss_and_is_overwritten`). A failed validate is a miss with no hit counted (`tests/test_cache.py:71` `test_validate_failure_is_a_miss_without_a_hit`). A failed write leaves no temp file (`tests/test_cache.py:83` `test_failed_write_leaves_no_temp_file`). A second run is all hits and costs 0 (`tests/test_cache.py:161` `test_second_run_is_all_hits_and_costs_zero`). A target version bump misses (`tests/test_cache.py:194` `test_version_bump_misses_and_bad_entry_is_rewritten`). A target error is never cached (`tests/test_cache.py:231` `test_target_error_is_not_cached`). Live: a re-run of the baseline on the same cache folder hit 75/75 outputs and 74/74 grades at cost 0 (FACTS.md §8).

## What I would change
Add `casegate cache prune --older-than 30d`. Today the folder only grows. Cost: about 20 lines and a test; the entries need a written-at time (the file mtime is enough).

## 10-minute version
The output key is `{v, input, target_version, target_model, repeat}` (`src/casegate/runner.py:140-146`). The repeat index is in it, so `--repeat 5` makes 5 real target calls on the first run: without it, 5 repeats would be one sample read 5 times and the std would be a lie. The expected values and the scorers are not in the key, so a scorer change re-scores cached outputs at no target cost. The judge key is the whole judge request plus the sample index (`src/casegate/judge.py:100-111`), but not the repeat index. So when two repeats produce the same claim and passage, the second grade is a cache hit, even on a fresh cache. This is why the fresh-cache baseline shows 7 of 74 judge hits (`evals/baseline.json` `summary.cache_judge_hits`). The runner stores an output only after a successful target call (`src/casegate/runner.py:167-168`), so an error is retried on the next run.
