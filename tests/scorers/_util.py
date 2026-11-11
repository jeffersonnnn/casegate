"""Helpers shared by the scorer tests: build a case, a suite and a context, then score."""

import asyncio
from pathlib import Path
from typing import Any

from casegate.models import Case, JudgeConfig, Output, RetryConfig, Score, Suite, TargetConfig
from casegate.scorers import ScoreContext, build_scorers


def make_suite(root: Path | str = ".", threshold: float = 0.7) -> Suite:
    target = TargetConfig(type="python", path="m:f", version="v1", model="none")
    return Suite(name="s", target=target, threshold=threshold, root=str(root))


def make_case(
    scorers: list[dict[str, Any]], expected: dict[str, Any] | None = None, case_id: str = "c1"
) -> Case:
    return Case.model_validate(
        {
            "id": case_id,
            "input": {},
            "expected": expected or {},
            "scorers": scorers,
            "source_file": "cases/x.yaml",
        }
    )


def make_ctx() -> ScoreContext:
    async def no_sleep(_: float) -> None:
        return None

    return ScoreContext(
        judge=None,
        judge_cfg=JudgeConfig(),
        judge_model=None,
        cache=None,
        retry=RetryConfig(),
        sleep=no_sleep,
    )


def score(
    scorer: dict[str, Any],
    output: Output | str,
    expected: dict[str, Any] | None = None,
    root: Path | str = ".",
) -> Score:
    case = make_case([scorer], expected)
    (built,) = build_scorers(case, make_suite(root))
    out = Output(text=output) if isinstance(output, str) else output
    return asyncio.run(built.score(case, out, make_ctx()))
