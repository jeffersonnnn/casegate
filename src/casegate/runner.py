"""Run every case of a suite N times against a target, score each output, and sum it up.

This is the one place where target calls, retries, the output cache, scorers and the
concurrency limit meet. The pass-rate maths lives in stats.py as pure functions; it is
re-exported here because callers know it as `runner.aggregate` (SPEC §2).
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from casegate import __version__
from casegate.cache import Cache
from casegate.errors import RetriesExhausted, SuiteError
from casegate.judge import JudgeClient
from casegate.models import Case, Output, RepeatResult, Run, Score, Status, Suite
from casegate.retry import with_retries
from casegate.scorers import ScoreContext, Scorer, build_scorers
from casegate.stats import aggregate, case_status, sum_costs
from casegate.targets import Target, build_target

__all__ = ["ProgressEvent", "aggregate", "case_status", "git_sha", "run_suite"]


@dataclass(frozen=True)
class ProgressEvent:
    case_id: str
    repeat: int
    status: Status
    cached: bool


def _describe(exc: BaseException) -> str:
    last = exc.last if isinstance(exc, RetriesExhausted) else exc
    return f"{type(last).__name__}: {last}"


def git_sha() -> str | None:
    if sha := os.environ.get("GITHUB_SHA"):
        return sha
    try:
        done = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    return done.stdout.strip() or None


async def run_suite(
    suite: Suite,
    cases: list[Case],
    *,
    repeat: int = 1,
    concurrency: int | None = None,
    cache: Cache | None,
    judge: JudgeClient | None,
    target: Target | None = None,
    progress: Callable[[ProgressEvent], None] | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    tags: list[str] | None = None,
) -> Run:
    started, t0 = datetime.now(UTC), time.perf_counter()
    scorers = {c.id: build_scorers(c, suite) for c in cases}
    needs_judge = any(s.needs_judge for built in scorers.values() for s in built)
    if needs_judge and judge is None:
        raise SuiteError("suite needs a judge")
    # Same rule as judge.resolve_judge_model (SPEC §6): the env var wins over the suite file.
    judge_model = (
        (os.environ.get(suite.judge.model_env) or suite.judge.model) if needs_judge else None
    )
    ctx = ScoreContext(judge, suite.judge, judge_model, cache, suite.retries, sleep)
    # One slot per task; judge calls inside scoring use the same slot, so C bounds all model work.
    semaphore = asyncio.Semaphore(concurrency or suite.concurrency)
    own_target = target is None
    tgt = build_target(suite.target) if target is None else target

    async def one(case: Case, k: int) -> RepeatResult:
        async with semaphore:
            t_task = time.perf_counter()
            rep = await _run_repeat(case, k, tgt, scorers[case.id], ctx, suite)
            rep.latency_ms = int((time.perf_counter() - t_task) * 1000)
        if progress is not None:
            progress(ProgressEvent(case.id, k, rep.status, rep.cached))
        return rep

    try:
        flat = await asyncio.gather(*(one(c, k) for c in cases for k in range(repeat)))
    finally:
        if own_target:
            await tgt.aclose()

    grouped = [(c, list(flat[i * repeat : (i + 1) * repeat])) for i, c in enumerate(cases)]
    case_results, summary = aggregate(
        grouped,
        repeat=repeat,
        duration_s=time.perf_counter() - t0,
        cache_hits=dict(cache.hits) if cache is not None else None,
        cache_lookups=dict(cache.lookups) if cache is not None else None,
    )
    filters: dict[str, object] = {"must_pass_tags": list(suite.must_pass_tags)}
    if tags is not None:
        filters["tags"] = list(tags)
    try:
        suite_path = os.path.relpath(suite.root)
    except ValueError:  # another drive on Windows: keep the absolute path
        suite_path = suite.root
    return Run(
        casegate_version=__version__,
        suite=suite.name,
        suite_path=suite_path,
        started_at=started,
        finished_at=datetime.now(UTC),
        git_sha=git_sha(),
        target_version=suite.target.version,
        target_model=suite.target.model,
        judge_model=judge_model,
        repeat=repeat,
        filters=filters,
        cases=case_results,
        summary=summary,
    )


async def _run_repeat(
    case: Case, k: int, target: Target, scorers: list[Scorer], ctx: ScoreContext, suite: Suite
) -> RepeatResult:
    """One (case, repeat) task: get an Output (cache or target), then score it in order."""
    output: Output | None = None
    error: str | None = None
    attempts, cached = 1, False
    key_obj = {
        "v": 1,
        "input": case.input,
        "target_version": suite.target.version,
        "target_model": suite.target.model,
        "repeat": k,
    }
    if ctx.cache is not None:
        hit = ctx.cache.get(
            "outputs", key_obj, validate=lambda v: Output.model_validate(v["output"])
        )
        if hit is not None:
            output, attempts, cached = Output.model_validate(hit["output"]), 0, True
    if output is None:
        t_call = time.perf_counter()
        try:
            got, attempts = await with_retries(
                lambda: target.run(case.input, case_id=case.id), suite.retries, ctx.sleep
            )
        except RetriesExhausted as exc:
            error, attempts = _describe(exc), exc.attempts
        except Exception as exc:
            error, attempts = _describe(exc), getattr(exc, "casegate_attempts", 1)
        else:
            if got.latency_ms == 0:
                ms = int((time.perf_counter() - t_call) * 1000)
                got = got.model_copy(update={"latency_ms": ms})
            if ctx.cache is not None:
                ctx.cache.put("outputs", key_obj, {"output": got.model_dump(mode="json")})
            output = got

    scores: list[Score] = []
    if output is not None:
        for scorer in scorers:
            try:
                scores.append(await scorer.score(case, output, ctx))
            except Exception as exc:  # the scores so far stay in the result
                error = f"scorer {scorer.name}: {_describe(exc)}"
                break

    status: Status = "error" if error else ("pass" if all(s.passed for s in scores) else "fail")
    score_cost = [s.cost_usd for s in scores]
    full_cost = [s.details.get("cost_usd_full", s.cost_usd) for s in scores]
    target_cost = [] if output is None else [0.0 if cached else output.cost_usd]
    return RepeatResult(
        repeat=k,
        status=status,
        scores=scores,
        output=output,
        error=error,
        attempts=attempts,
        cached=cached,
        cost_usd=sum_costs([*target_cost, *score_cost]),
        cost_usd_full=sum_costs([*([] if output is None else [output.cost_usd]), *full_cost]),
    )
