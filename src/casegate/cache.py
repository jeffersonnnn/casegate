"""Content-addressed disk cache for target outputs and judge grades (ADR 0005).

Two namespaces keep a rubric edit from re-running the target: `outputs/` holds what the
target said, `judge/` holds what the judge said about it. A file that is missing, corrupt
or fails the caller's validation is a miss, so a bad cache can cost money but never a wrong score.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

Namespace = Literal["outputs", "judge"]

CACHE_DIR_ENV = "CASEGATE_CACHE_DIR"


def canonical_json(obj: Any) -> str:
    """One text per value, whatever the dict order, so equal keys hash equal."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def key(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


class Cache:
    hits: dict[str, int]
    lookups: dict[str, int]

    def __init__(self, root: Path | None = None) -> None:
        if root is None:
            env = os.environ.get(CACHE_DIR_ENV)
            root = Path(env) if env else Path.cwd() / ".casegate" / "cache"
        self.root = root
        self.hits = {"outputs": 0, "judge": 0}
        self.lookups = {"outputs": 0, "judge": 0}

    def path(self, ns: Namespace, key_obj: dict[str, Any]) -> Path:
        k = key(key_obj)
        return self.root / ns / k[:2] / f"{k}.json"

    def get(
        self,
        ns: Namespace,
        key_obj: dict[str, Any],
        validate: Callable[[dict[str, Any]], object] | None = None,
    ) -> dict[str, Any] | None:
        self.lookups[ns] += 1
        try:
            value = json.loads(self.path(ns, key_obj).read_text(encoding="utf-8"))
        except (OSError, ValueError):  # missing, unreadable, not UTF-8 or not JSON
            return None
        if not isinstance(value, dict):
            return None
        if validate is not None:
            try:
                validate(value)
            except Exception:  # an old or damaged entry: re-compute and overwrite it
                return None
        self.hits[ns] += 1
        return value

    def put(self, ns: Namespace, key_obj: dict[str, Any], value: dict[str, Any]) -> None:
        final = self.path(ns, key_obj)
        final.parent.mkdir(parents=True, exist_ok=True)
        # Write aside, then rename: concurrent runs or a crash never leave a half-written file.
        tmp = final.with_name(f"{final.name}.tmp-{os.getpid()}-{secrets.token_hex(4)}")
        try:
            tmp.write_text(canonical_json(value), encoding="utf-8")
            os.replace(tmp, final)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
