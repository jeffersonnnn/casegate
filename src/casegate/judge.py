"""The judge seam: the one path a scorer takes to ask a model for a grade.

Two small adapters (Anthropic here, OpenAI-compatible in judge_openai.py) and a scripted fake
sit behind one protocol, and `cached_grade` puts the judge cache and the retry loop in front of
all of them, so every grade is keyed, retried and costed the same way (ADR 0004, ADR 0005).
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Literal, Protocol, TypeVar, cast

from pydantic import BaseModel, ConfigDict

from casegate.errors import JudgeError, SuiteError
from casegate.models import JudgeConfig
from casegate.prices import cost
from casegate.retry import with_retries

if TYPE_CHECKING:
    from casegate.scorers.base import ScoreContext

T = TypeVar("T", bound=BaseModel)  # judge.py's own TypeVar; retry.py's T is unbound


class Verdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reasoning: str
    score: float


class CitationVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reasoning: str
    supported: bool


@dataclass
class JudgeResult(Generic[T]):
    parsed: T
    input_tokens: int
    output_tokens: int
    cost_usd: float | None


class JudgeClient(Protocol):
    provider: str  # "anthropic" | "openai" | "fake"; part of the judge cache key (SPEC §8)

    async def grade(
        self, *, system: str, prompt: str, schema: type[T], model: str
    ) -> JudgeResult[T]: ...

    async def aclose(self) -> None: ...


def build_judge(cfg: JudgeConfig) -> JudgeClient:
    if cfg.provider == "anthropic":
        return AnthropicJudge(cfg)
    from casegate.judge_openai import OpenAICompatJudge  # it imports this module back

    return OpenAICompatJudge(cfg)


def resolve_judge_model(cfg: JudgeConfig) -> str:
    return os.environ.get(cfg.model_env) or cfg.model


def _check_entry(v: dict[str, Any], schema: type[BaseModel]) -> None:
    """A judge cache entry must hold a valid verdict and its counts; else it is a miss.

    Without this, an old or damaged entry missing `cost_usd` would raise inside the scorer
    and turn the repeat into an error instead of a fresh, paid grade.
    """
    schema.model_validate(v["parsed"])
    for name in ("input_tokens", "output_tokens"):
        if type(v[name]) is not int:
            raise ValueError(f"judge cache: {name} is not an int")
    c = v["cost_usd"]
    if c is not None and type(c) not in (int, float):
        raise ValueError("judge cache: cost_usd is not a number")


async def cached_grade(
    ctx: ScoreContext,
    *,
    kind: Literal["llm_judge", "citation"],
    system: str,
    prompt: str,
    schema: type[T],
    sample: int,
) -> tuple[JudgeResult[T], bool, int]:
    """Grade once through the judge cache and the retry loop: (result, cache hit, attempts)."""
    judge, model = ctx.judge, ctx.judge_model
    if judge is None or model is None:
        raise JudgeError("no judge configured")
    cfg = ctx.judge_cfg
    # The key is the whole request: a new rubric, model, provider or effort must re-grade.
    key_obj = {
        "v": 1,
        "kind": kind,
        "system": system,
        "prompt": prompt,
        "schema": schema.__name__,
        "provider": judge.provider,
        "judge_model": model,
        "effort": cfg.effort if judge.provider == "anthropic" else None,
        "max_tokens": cfg.max_tokens,
        "sample": sample,
    }
    if ctx.cache is not None:
        v = ctx.cache.get("judge", key_obj, validate=lambda v: _check_entry(v, schema))
        if v is not None:
            parsed = schema.model_validate(v["parsed"])
            return (
                JudgeResult(parsed, v["input_tokens"], v["output_tokens"], v["cost_usd"]),
                True,
                0,
            )
    result, attempts = await with_retries(
        lambda: judge.grade(system=system, prompt=prompt, schema=schema, model=model),
        ctx.retry,
        ctx.sleep,
    )
    if ctx.cache is not None:
        value = {
            "parsed": result.parsed.model_dump(mode="json"),
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cost_usd": result.cost_usd,
        }
        ctx.cache.put("judge", key_obj, value)
    return result, False, attempts


class AnthropicJudge:
    """Structured output through messages.parse; no sampling fields (FACTS §4.3)."""

    provider = "anthropic"

    def __init__(self, cfg: JudgeConfig, client: Any | None = None) -> None:
        self.cfg = cfg
        self._owns_client = client is None
        if client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise SuiteError("pip install 'casegate[anthropic]'") from exc
            name = cfg.api_key_env or "ANTHROPIC_API_KEY"
            key = os.environ.get(name)
            if not key:  # never let the SDK fall back to another variable
                raise SuiteError(f"{name} is not set")
            # SDK retries off: casegate's retry layer owns retries and counts the attempts.
            client = anthropic.AsyncAnthropic(api_key=key, max_retries=0, timeout=120.0)
        self._client = client

    async def grade(
        self, *, system: str, prompt: str, schema: type[T], model: str
    ) -> JudgeResult[T]:
        resp = await self._client.messages.parse(
            model=model,
            max_tokens=self.cfg.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_format=schema,
            output_config={"effort": self.cfg.effort},
        )
        parsed = resp.parsed_output
        if parsed is None or resp.stop_reason in ("refusal", "max_tokens"):
            raise JudgeError(f"judge gave no verdict (stop_reason {resp.stop_reason})")
        n_in, n_out = resp.usage.input_tokens, resp.usage.output_tokens
        return JudgeResult(cast(T, parsed), n_in, n_out, cost(model, n_in, n_out))

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.close()


FakeScript = Sequence[BaseModel] | Callable[[str, str, type[BaseModel]], BaseModel] | None


@dataclass
class FakeJudge:
    """A judge with scripted verdicts for tests and `--fake-judge`; it never costs money."""

    script: FakeScript = None
    provider: str = "fake"  # its own cache namespace: fake grades never serve a real run
    calls: int = 0
    requests: list[tuple[str, str, str]] = field(default_factory=list)

    async def grade(
        self, *, system: str, prompt: str, schema: type[T], model: str
    ) -> JudgeResult[T]:
        index = self.calls
        self.calls += 1
        self.requests.append((system, prompt, model))
        item = self._next(index, system, prompt, schema)
        if not isinstance(item, schema):
            raise JudgeError(f"FakeJudge gave {type(item).__name__}, expected {schema.__name__}")
        return JudgeResult(item, 0, 0, 0.0)

    def _next(self, index: int, system: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
        if self.script is None:
            if schema is Verdict:
                return Verdict(reasoning="fake", score=1.0)
            if schema is CitationVerdict:
                return CitationVerdict(reasoning="fake", supported=True)
            raise JudgeError(f"FakeJudge has no default for {schema.__name__}")
        if callable(self.script):
            return self.script(system, prompt, schema)
        if index >= len(self.script):
            raise JudgeError("FakeJudge script exhausted")
        return self.script[index]

    async def aclose(self) -> None:
        return None
