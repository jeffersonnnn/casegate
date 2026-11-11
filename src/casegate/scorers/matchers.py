"""Matchers let a case say "an amount at most 39" instead of one exact value.

Tool arguments and reported state share one small matcher language, so it is parsed and
checked here once. Parsing happens at load time, so a bad matcher is a load error, not a
silent fail during a paid run.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from casegate.scorers.base import render_compact, render_value

MATCHER_KEYS = frozenset({"regex", "contains", "gte", "lte", "any", "one_of", "all_amounts_lte"})
_VALID_KEY_SETS = [
    frozenset(s)
    for s in (
        {"regex"},
        {"contains"},
        {"gte"},
        {"lte"},
        {"gte", "lte"},
        {"any"},
        {"one_of"},
        {"all_amounts_lte"},
    )
]
_TOL = 1e-9


class MatcherError(ValueError): ...


def is_number(x: Any) -> bool:
    # bool is a subclass of int, but True is not an amount.
    return isinstance(x, int | float) and not isinstance(x, bool)


def equal(a: Any, b: Any) -> bool:
    """Plain equality: numbers compare with a tolerance; types never coerce ("1042" != 1042)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if is_number(a) and is_number(b):
        return math.isclose(a, b, rel_tol=_TOL, abs_tol=_TOL)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, str) or isinstance(b, str):
        return isinstance(a, str) and isinstance(b, str) and a == b
    return bool(a == b)


def _lte(x: Any, n: float) -> bool:
    return is_number(x) and (x <= n or math.isclose(x, n, rel_tol=_TOL, abs_tol=_TOL))


def _gte(x: Any, n: float) -> bool:
    return is_number(x) and (x >= n or math.isclose(x, n, rel_tol=_TOL, abs_tol=_TOL))


@dataclass(frozen=True)
class Matcher:
    raw: Any
    is_plain: bool
    pattern: re.Pattern[str] | None = field(default=None, compare=False)

    def match(self, value: Any, present: bool) -> bool:
        if not present:
            return False
        if self.is_plain:
            return equal(self.raw, value)
        spec: dict[str, Any] = self.raw
        if "any" in spec:
            return True
        if self.pattern is not None:
            return self.pattern.search(str(value)) is not None
        if "contains" in spec:
            return spec["contains"] in str(value)
        if "one_of" in spec:
            return any(equal(item, value) for item in spec["one_of"])
        if "all_amounts_lte" in spec:
            return _all_amounts_lte(value, spec["all_amounts_lte"])
        if not is_number(value):
            return False
        return ("gte" not in spec or _gte(value, spec["gte"])) and (
            "lte" not in spec or _lte(value, spec["lte"])
        )

    def render(self) -> str:
        return render_value(self.raw) if self.is_plain else render_compact(self.raw)


def _all_amounts_lte(value: Any, limit: float) -> bool:
    if not isinstance(value, list):
        return False
    return all(isinstance(item, dict) and _lte(item.get("amount"), limit) for item in value)


def is_matcher_dict(obj: Any) -> bool:
    return isinstance(obj, dict) and bool(obj) and set(obj) <= MATCHER_KEYS


def parse(obj: Any, *, allow_list: bool = False) -> Matcher:
    """Turn a YAML value into a Matcher; raise MatcherError with the SPEC §3.3 text."""
    if not is_matcher_dict(obj):
        return Matcher(raw=obj, is_plain=True)
    keys = frozenset(obj)
    if keys not in _VALID_KEY_SETS:
        raise MatcherError(f"invalid matcher keys: {', '.join(sorted(keys))}")
    if "all_amounts_lte" in keys and not allow_list:
        raise MatcherError("all_amounts_lte is valid only in state_match")
    pattern = None
    if "any" in keys and obj["any"] is not True:
        raise MatcherError("any must be true")
    if "regex" in keys:
        if not isinstance(obj["regex"], str):
            raise MatcherError("regex must be a string")
        try:
            pattern = re.compile(obj["regex"])
        except re.error as exc:
            raise MatcherError(f"invalid regex: {exc}") from exc
    if "contains" in keys and not isinstance(obj["contains"], str):
        raise MatcherError("contains must be a string")
    for key in ("gte", "lte", "all_amounts_lte"):
        if key in keys and not is_number(obj[key]):
            raise MatcherError(f"{key} must be a number")
    if "one_of" in keys and not (isinstance(obj["one_of"], list) and obj["one_of"]):
        raise MatcherError("one_of must be a non-empty list")
    return Matcher(raw=dict(obj), is_plain=False, pattern=pattern)
