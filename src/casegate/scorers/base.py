"""The contract every scorer meets, plus the small helpers they all share.

Scorers are looked up by type name and built from YAML, so they must agree on one shape
(the Scorer protocol) and one way to write reasons. Judge and cache types are imported only
for type checking, so loading a deterministic scorer never pulls in the judge or the cache.
"""

from __future__ import annotations

import builtins
import json
import re
import unicodedata
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from pydantic import BaseModel, ValidationError

from casegate.models import Case, JudgeConfig, Output, RetryConfig, Score

if TYPE_CHECKING:
    from casegate.cache import Cache
    from casegate.judge import JudgeClient

DETERMINISTIC_TYPES = frozenset(
    {"exact", "contains", "not_contains", "json_schema", "tool_trajectory", "state_match"}
)
REASON_MAX = 300
_PASS_EPSILON = 1e-9


class Scorer(Protocol):
    type: ClassVar[str]
    Params: ClassVar[builtins.type[BaseModel]]
    needs_judge: ClassVar[bool]
    name: str
    threshold: float
    params: BaseModel

    def __init__(self, name: str, threshold: float, params: BaseModel) -> None: ...

    @classmethod
    def check(cls, case: Case, params: BaseModel, suite_root: Path) -> list[str]: ...

    async def score(self, case: Case, output: Output, ctx: ScoreContext) -> Score: ...


@dataclass
class ScoreContext:
    judge: JudgeClient | None
    judge_cfg: JudgeConfig
    judge_model: str | None
    cache: Cache | None
    retry: RetryConfig
    sleep: Callable[[float], Awaitable[None]]


class DeterministicScorer:
    """Shared constructor and Score assembly for the scorers that need no judge."""

    type: ClassVar[str]
    needs_judge: ClassVar[bool] = False

    def __init__(self, name: str, threshold: float, params: BaseModel) -> None:
        self.name = name
        self.threshold = threshold
        self.params = params

    def make_score(
        self, value: float, problem: str | None, details: dict[str, Any] | None = None
    ) -> Score:
        # A deterministic reason names what was wrong whenever the value is short of 1,
        # even when a lowered threshold lets it pass (SPEC §5.1).
        value = min(1.0, max(0.0, value))
        reason = problem if problem is not None and value < 1.0 else "ok"
        return Score(
            scorer=self.name,
            type=self.type,
            value=value,
            passed=value >= self.threshold - _PASS_EPSILON,
            threshold=self.threshold,
            reason=clean_reason(reason),
            cost_usd=0.0,
            details=details or {},
        )


def normalise(s: str) -> str:
    folded = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"\s+", " ", folded).strip().rstrip(".!?").rstrip()


def render_value(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, default=str)


def render_compact(v: Any) -> str:
    """Matchers render as compact JSON, e.g. {"lte":39}."""
    return json.dumps(v, ensure_ascii=False, default=str, separators=(",", ":"))


def clean_reason(reason: str) -> str:
    # Reasons go into one Markdown table cell, so they must be one short line.
    r = re.sub(r"\r\n|\r|\n", " ", reason)
    if len(r) > REASON_MAX:
        r = r[: REASON_MAX - 1] + "…"
    return r


def validation_lines(err: ValidationError) -> list[str]:
    """One `<loc joined by '.'>: <msg>` line per pydantic error."""
    lines = []
    for e in err.errors():
        loc = ".".join(str(part) for part in e["loc"])
        lines.append(f"{loc}: {e['msg']}" if loc else e["msg"])
    return lines


def from_expected(
    params_cls: builtins.type[BaseModel], case: Case, field: str, param: str, attr: str = ""
) -> tuple[Any, list[str]]:
    """Validate `case.expected[field]` with the scorer's own params model.

    Returns (value, errors); value is None when the field is absent. Using the params model
    means a bad `expected` value fails at load time with the same rules as a param would.
    """
    if field not in case.expected:
        return None, []
    try:
        model = params_cls.model_validate({param: case.expected[field]})
    except ValidationError as err:
        return None, [f"expected.{field}: {e['msg']}" for e in err.errors()]
    return getattr(model, attr or param), []
