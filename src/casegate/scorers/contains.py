"""The `contains` and `not_contains` scorers: required and banned phrases in the reply.

They share one file because they read the same way and use the same normalisation. A
`contains` item may be a group of synonyms (any one is enough), so a case does not fail
on wording that a person would accept.
"""

from __future__ import annotations

import builtins
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, cast

from pydantic import BaseModel, ConfigDict

from casegate.models import Case, Output, Score
from casegate.scorers.base import DeterministicScorer, ScoreContext, from_expected, normalise
from casegate.scorers.base import render_value as rv


class ContainsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[str | list[str]] | None = None
    normalise: bool = True


class NotContainsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[str] | None = None
    normalise: bool = True


def resolve_items(
    kind: str,
    params_cls: builtins.type[BaseModel],
    items: Sequence[str | list[str]] | None,
    case: Case,
) -> tuple[list[str | list[str]], list[str]]:
    """Return (items, errors); params override expected.answer_<not_>contains."""
    field = "answer_contains" if kind == "contains" else "answer_not_contains"
    label = "items"
    if items is None:
        value, errors = from_expected(params_cls, case, field, "items")
        if errors:
            return [], errors
        if value is None:
            return [], [f"{kind}: needs items or expected.{field}"]
        items, label = value, f"expected.{field}"
    if not items or any(isinstance(g, list) and not g for g in items):
        return [], [f"{kind}: {label} must not be empty"]
    return list(items), []


def _render_item(item: str | list[str]) -> str:
    if isinstance(item, str):
        return rv(item)
    return "(" + " | ".join(rv(s) for s in item) + ")"


class ContainsScorer(DeterministicScorer):
    type: ClassVar[str] = "contains"
    Params: ClassVar[builtins.type[BaseModel]] = ContainsParams

    @classmethod
    def check(cls, case: Case, params: BaseModel, suite_root: Path) -> list[str]:
        p = cast(ContainsParams, params)
        return resolve_items(cls.type, ContainsParams, p.items, case)[1]

    async def score(self, case: Case, output: Output, ctx: ScoreContext) -> Score:
        p = cast(ContainsParams, self.params)
        items, errors = resolve_items(self.type, ContainsParams, p.items, case)
        if errors:
            raise ValueError(errors[0])
        prep = normalise if p.normalise else str
        text = prep(output.text)
        missing = []
        for item in items:
            group = [item] if isinstance(item, str) else item
            if not any(prep(s) in text for s in group):
                missing.append(item)
        value = (len(items) - len(missing)) / len(items)
        problem = "missing: " + ", ".join(_render_item(m) for m in missing)
        return self.make_score(value, problem)


class NotContainsScorer(DeterministicScorer):
    type: ClassVar[str] = "not_contains"
    Params: ClassVar[builtins.type[BaseModel]] = NotContainsParams

    @classmethod
    def check(cls, case: Case, params: BaseModel, suite_root: Path) -> list[str]:
        p = cast(NotContainsParams, params)
        return resolve_items(cls.type, NotContainsParams, p.items, case)[1]

    async def score(self, case: Case, output: Output, ctx: ScoreContext) -> Score:
        p = cast(NotContainsParams, self.params)
        items, errors = resolve_items(self.type, NotContainsParams, p.items, case)
        if errors:
            raise ValueError(errors[0])
        prep = normalise if p.normalise else str
        text = prep(output.text)
        found = [s for s in items if isinstance(s, str) and prep(s) in text]
        value = 0.0 if found else 1.0
        return self.make_score(value, "found banned: " + ", ".join(rv(s) for s in found))
