"""The scorer registry and the one function that turns case YAML into scorer objects.

The loader and the runner both build scorers through `build_scorers`, so names, thresholds
and validation follow one rule set. Every problem in a case is collected first and raised
together as a SuiteError, so a suite author sees all mistakes in one run.
"""

from __future__ import annotations

import builtins
from pathlib import Path

from pydantic import ValidationError

from casegate.errors import SuiteError
from casegate.models import Case, Suite
from casegate.scorers.base import (
    DETERMINISTIC_TYPES,
    ScoreContext,
    Scorer,
    normalise,
    render_value,
    validation_lines,
)
from casegate.scorers.citation_support import CitationSupportScorer
from casegate.scorers.contains import ContainsScorer, NotContainsScorer
from casegate.scorers.exact import ExactScorer
from casegate.scorers.json_schema import JsonSchemaScorer
from casegate.scorers.llm_judge import LlmJudgeScorer
from casegate.scorers.state_match import StateMatchScorer
from casegate.scorers.tool_trajectory import ToolTrajectoryScorer

REGISTRY: dict[str, builtins.type[Scorer]] = {
    ExactScorer.type: ExactScorer,
    ContainsScorer.type: ContainsScorer,
    NotContainsScorer.type: NotContainsScorer,
    JsonSchemaScorer.type: JsonSchemaScorer,
    ToolTrajectoryScorer.type: ToolTrajectoryScorer,
    StateMatchScorer.type: StateMatchScorer,
    LlmJudgeScorer.type: LlmJudgeScorer,
    CitationSupportScorer.type: CitationSupportScorer,
}

__all__ = ["REGISTRY", "ScoreContext", "Scorer", "build_scorers", "normalise", "render_value"]


def unknown_type_line(prefix: str, scorer_type: str) -> str:
    return f"{prefix}: unknown scorer type {scorer_type} (known: {', '.join(sorted(REGISTRY))})"


def resolve_names(case: Case) -> tuple[list[str], list[str]]:
    """Name each scorer and write it into cfg.name; return (names, duplicate errors).

    Unnamed scorers are numbered per type (exact, exact#2, ...). Writing the names back makes
    a second call see the same names, so the loader and the runner always agree.
    """
    counts: dict[str, int] = {}
    names: list[str] = []
    for cfg in case.scorers:
        if cfg.name is None:
            counts[cfg.type] = counts.get(cfg.type, 0) + 1
            k = counts[cfg.type]
            cfg.name = cfg.type if k == 1 else f"{cfg.type}#{k}"
        names.append(cfg.name)
    seen: set[str] = set()
    dupes: dict[str, None] = {}
    for n in names:
        if n in seen:
            dupes[n] = None
        seen.add(n)
    return names, [f"case {case.id}: duplicate scorer name {n}" for n in dupes]


def build_scorers(case: Case, suite: Suite) -> list[Scorer]:
    """Build the case's scorers in config order, or raise SuiteError with every problem."""
    unknown = [cfg.type for cfg in case.scorers if cfg.type not in REGISTRY]
    if unknown:
        # Checked before anything else, so an unknown type never becomes a KeyError.
        raise SuiteError([unknown_type_line(f"case {case.id}", t) for t in unknown])
    names, errors = resolve_names(case)
    scorers: list[Scorer] = []
    for cfg, name in zip(case.scorers, names, strict=True):
        cls = REGISTRY[cfg.type]
        prefix = f"case {case.id} scorer {name}: "
        if cfg.threshold is not None:
            threshold = cfg.threshold
        else:
            threshold = 1.0 if cfg.type in DETERMINISTIC_TYPES else suite.threshold
        try:
            params = cls.Params.model_validate(cfg.model_extra or {})
        except ValidationError as err:
            errors += [prefix + line for line in validation_lines(err)]
            continue
        problems = cls.check(case, params, Path(suite.root))
        errors += [prefix + line for line in problems]
        if not problems:
            scorers.append(cls(name, threshold, params))
    if errors:
        raise SuiteError(errors)
    return scorers
