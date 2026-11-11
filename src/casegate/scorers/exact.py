"""The `exact` scorer: the reply must equal one of the expected answers.

It is the strictest and cheapest check, used for short fixed replies. Normalisation is on
by default so that case, spacing and a final full stop do not decide a pass.
"""

from __future__ import annotations

import builtins
from pathlib import Path
from typing import ClassVar, cast

from pydantic import BaseModel, ConfigDict

from casegate.models import Case, Output, Score
from casegate.scorers.base import DeterministicScorer, ScoreContext, from_expected, normalise
from casegate.scorers.base import render_value as rv


class ExactParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str | list[str] | None = None
    normalise: bool = True


def resolve_answers(case: Case, params: ExactParams) -> tuple[list[str], list[str]]:
    """Return (answers, errors); params override `expected.answer`."""
    if params.answer is not None:
        answer, field = params.answer, "answer"
    else:
        value, errors = from_expected(ExactParams, case, "answer", "answer")
        if errors:
            return [], errors
        if value is None:
            return [], ["exact: needs answer or expected.answer"]
        answer, field = value, "expected.answer"
    answers = [answer] if isinstance(answer, str) else list(answer)
    if not answers:
        return [], [f"exact: {field} must not be empty"]
    return answers, []


class ExactScorer(DeterministicScorer):
    type: ClassVar[str] = "exact"
    Params: ClassVar[builtins.type[BaseModel]] = ExactParams

    @classmethod
    def check(cls, case: Case, params: BaseModel, suite_root: Path) -> list[str]:
        return resolve_answers(case, cast(ExactParams, params))[1]

    async def score(self, case: Case, output: Output, ctx: ScoreContext) -> Score:
        p = cast(ExactParams, self.params)
        answers, errors = resolve_answers(case, p)
        if errors:
            raise ValueError(errors[0])
        prep = normalise if p.normalise else str
        got = prep(output.text)
        value = 1.0 if any(prep(a) == got for a in answers) else 0.0
        problem = f"expected {' | '.join(rv(a) for a in answers)}, got {rv(output.text[:80])}"
        return self.make_score(value, problem)
