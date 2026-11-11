"""The `state_match` scorer: the world after the case must be in the expected state.

A reply can say "refunded" while the order is not. This scorer reads the state the target
reports and checks each expected path with a matcher, so a case grades what happened,
not what the reply claims.
"""

from __future__ import annotations

import builtins
import re
from pathlib import Path
from typing import Any, ClassVar, cast

from pydantic import BaseModel, ConfigDict

from casegate.models import Case, Output, Score
from casegate.scorers.base import DeterministicScorer, ScoreContext, from_expected, render_value
from casegate.scorers.matchers import MatcherError, parse

_PATH = re.compile(r'^[^.\[]+(?:\.[^.\[]+|\["[^"]*"\])*$')
_TAIL = re.compile(r'\.([^.\[]+)|\["([^"]*)"\]')
_INDEX = re.compile(r"^[0-9]+$")
_MISSING = object()


class StateMatchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: dict[str, Any] | None = None


def split_path(path: str) -> list[str] | None:
    """`orders["a.b"].status` -> ["orders", "a.b", "status"]; None when malformed."""
    if not _PATH.match(path):
        return None
    head = re.match(r"^[^.\[]+", path)
    assert head is not None  # guaranteed by _PATH
    segs = [head.group(0)]
    for m in _TAIL.finditer(path, head.end()):
        segs.append(m.group(1) if m.group(1) is not None else m.group(2))
    return segs


def lookup(state: Any, segs: list[str]) -> Any:
    """Walk dicts by key and lists by index; return _MISSING when the path does not resolve."""
    node = state
    for seg in segs:
        if isinstance(node, dict) and seg in node:
            node = node[seg]
        elif isinstance(node, list) and _INDEX.match(seg) and int(seg) < len(node):
            node = node[int(seg)]
        else:
            return _MISSING
    return node


def resolve_state(case: Case, p: StateMatchParams) -> tuple[dict[str, Any], list[str]]:
    state = p.state
    if state is None:
        state, errors = from_expected(StateMatchParams, case, "state", "state")
        if errors:
            return {}, errors
    if not state:
        return {}, ["state_match: needs non-empty state or expected.state"]
    return state, []


class StateMatchScorer(DeterministicScorer):
    type: ClassVar[str] = "state_match"
    Params: ClassVar[builtins.type[BaseModel]] = StateMatchParams

    @classmethod
    def check(cls, case: Case, params: BaseModel, suite_root: Path) -> list[str]:
        state, errors = resolve_state(case, cast(StateMatchParams, params))
        for path, spec in state.items():
            if split_path(path) is None:
                errors.append(f"state_match: malformed path {render_value(path)}")
                continue
            try:
                parse(spec, allow_list=True)
            except MatcherError as exc:
                errors.append(f"state_match: {path}: {exc}")
        return errors

    async def score(self, case: Case, output: Output, ctx: ScoreContext) -> Score:
        state, errors = resolve_state(case, cast(StateMatchParams, self.params))
        if errors:
            raise ValueError(errors[0])
        mismatches: list[str] = []
        failed: list[str] = []
        for path, spec in state.items():
            segs = split_path(path)
            if segs is None:
                raise ValueError(f"state_match: malformed path {render_value(path)}")
            matcher = parse(spec, allow_list=True)
            actual = lookup(output.state, segs)
            present = actual is not _MISSING
            if not matcher.match(actual, present):
                got = render_value(actual) if present else "<missing>"
                mismatches.append(f"{path}: expected {matcher.render()}, got {got}")
                failed.append(path)
        value = (len(state) - len(failed)) / len(state)
        details = {"matched": len(state) - len(failed), "total": len(state), "failed": failed}
        return self.make_score(value, "; ".join(mismatches), details)
