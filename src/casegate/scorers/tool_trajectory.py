"""The `tool_trajectory` scorer: the agent must call the right tools, with the right args.

An agent can give a good reply after skipping a required lookup, or after calling a tool it
must never call. This scorer compares the calls the target made with the expected calls in
one of three modes, and a forbidden call always scores 0.
"""

from __future__ import annotations

import builtins
import json
from pathlib import Path
from typing import Any, ClassVar, Literal, cast

from pydantic import BaseModel, ConfigDict

from casegate.models import Case, Output, Score, ToolCall
from casegate.scorers.base import DeterministicScorer, ScoreContext, from_expected
from casegate.scorers.matchers import Matcher, MatcherError, parse

_SHOW = 8
_NEEDS = "tool_trajectory: needs tools, forbidden, expected.tools or expected.tools_forbidden"


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    args: dict[str, Any] = {}


class ToolTrajectoryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["exact", "subsequence", "set"] = "subsequence"
    tools: list[str | ToolSpec] | None = None
    forbidden: list[str] | None = None
    allow_extra: bool = True
    ignore: list[str] = []


def _resolve(case: Case, p: ToolTrajectoryParams) -> tuple[list[ToolSpec], list[str], list[str]]:
    """Return (expected specs, forbidden names, errors); params override expected (no merge)."""
    errors: list[str] = []
    tools, forbidden = p.tools, p.forbidden
    if tools is None:
        tools, errs = from_expected(ToolTrajectoryParams, case, "tools", "tools")
        errors += errs
    if forbidden is None:
        forbidden, errs = from_expected(ToolTrajectoryParams, case, "tools_forbidden", "forbidden")
        errors += errs
    if errors:
        return [], [], errors
    if tools is None and forbidden is None:
        return [], [], [_NEEDS]
    specs = [ToolSpec(name=t) if isinstance(t, str) else t for t in tools or []]
    return specs, list(forbidden or []), []


def _render_spec(spec: ToolSpec) -> str:
    if not spec.args:
        return spec.name
    return f"{spec.name}({json.dumps(spec.args, sort_keys=True, separators=(',', ':'))})"


def _join(names: list[str], sep: str) -> str:
    if not names:
        return "(none)"
    shown = sep.join(names[:_SHOW])
    return shown + (f"{sep}…(+{len(names) - _SHOW})" if len(names) > _SHOW else "")


def _matches(spec: ToolSpec, parsed: dict[str, Matcher], call: ToolCall) -> bool:
    if spec.name != call.name:
        return False
    return all(arg in call.args and m.match(call.args[arg], True) for arg, m in parsed.items())


class ToolTrajectoryScorer(DeterministicScorer):
    type: ClassVar[str] = "tool_trajectory"
    Params: ClassVar[builtins.type[BaseModel]] = ToolTrajectoryParams

    @classmethod
    def check(cls, case: Case, params: BaseModel, suite_root: Path) -> list[str]:
        p = cast(ToolTrajectoryParams, params)
        specs, _, errors = _resolve(case, p)
        if not p.allow_extra and p.mode != "set":
            errors.append("tool_trajectory: allow_extra is only valid with mode set")
        for spec in specs:
            for arg, raw in spec.args.items():
                try:
                    parse(raw)
                except MatcherError as exc:
                    errors.append(f"tool_trajectory: {spec.name}.{arg}: {exc}")
        clashes = dict.fromkeys(s.name for s in specs if s.name in p.ignore)
        errors += [f"tool_trajectory: {n} is both expected and ignored" for n in clashes]
        return errors

    async def score(self, case: Case, output: Output, ctx: ScoreContext) -> Score:
        p = cast(ToolTrajectoryParams, self.params)
        specs, forbidden, errors = _resolve(case, p)
        if errors:
            raise ValueError(errors[0])
        parsed = [{a: parse(v) for a, v in s.args.items()} for s in specs]
        # Ignored calls leave the comparison, but forbidden still sees every call.
        actual = [c for c in output.tool_calls if c.name not in p.ignore]
        names = [c.name for c in actual]

        def hit(i: int, call: ToolCall) -> bool:
            return _matches(specs[i], parsed[i], call)

        rendered = [_render_spec(s) for s in specs]
        if p.mode == "exact":
            matched = 0
            while matched < min(len(specs), len(actual)) and hit(matched, actual[matched]):
                matched += 1
            if len(specs) == len(actual) == matched:
                value = 1.0
            else:
                value = matched / max(len(specs), len(actual))
            problem = f"expected exact {_join(rendered, ' → ')}; got {_join(names, ' → ')}"
            if matched < len(specs):
                problem += f"; first unmatched: {rendered[matched]}"
        elif p.mode == "subsequence":
            matched = 0
            for call in actual:
                if matched < len(specs) and hit(matched, call):
                    matched += 1
            value = matched / len(specs) if specs else 1.0
            problem = f"expected subsequence {_join(rendered, ' → ')}; got {_join(names, ' → ')}"
            if matched < len(specs):
                problem += f"; first unmatched: {rendered[matched]}"
        else:
            used = [False] * len(actual)
            missing = []
            for i in range(len(specs)):
                j = next((j for j, c in enumerate(actual) if not used[j] and hit(i, c)), None)
                if j is None:
                    missing.append(rendered[i])
                else:
                    used[j] = True
            matched = len(specs) - len(missing)
            extra = [c.name for c, u in zip(actual, used, strict=True) if not u]
            value = matched / len(specs) if specs else 1.0
            if not p.allow_extra and extra:
                value = 0.0
            problem = f"expected set {_join(rendered, ', ')}"
            if missing:
                problem += f"; missing: {_join(missing, ', ')}"
            if not p.allow_extra and extra:
                problem += f"; extra: {_join(extra, ', ')}"

        forbidden_called = [c.name for c in output.tool_calls if c.name in forbidden]
        if forbidden_called:
            value, problem = 0.0, f"forbidden tool called: {forbidden_called[0]}"
        details = {
            "expected": [s.name for s in specs],
            "actual": names,
            "matched": matched,
            "mode": p.mode,
            "forbidden_called": forbidden_called,
            "ignored": len(output.tool_calls) - len(actual),
        }
        return self.make_score(value, problem, details)
