"""The shapes that every other module agrees on: suite config, cases, outputs and run results.

A run is written to JSON and read back later by compare, gate and calibrate, so the models
forbid unknown fields and must round-trip exactly. Keeping them in one file makes the run
format one thing to read and to version (`Run.schema_version`).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_PYTHON_PATH = re.compile(r"^[\w.]+:\w+$")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolCall(_Strict):
    name: str
    args: dict[str, Any] = {}
    result: Any | None = None  # for reports only; no scorer reads it


class Citation(_Strict):
    source_id: str
    quote: str
    claim: str


class Output(_Strict):
    text: str
    tool_calls: list[ToolCall] = []
    citations: list[Citation] = []
    state: dict[str, Any] = {}
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = 0.0  # None = unknown, which must never be summed as 0
    latency_ms: int = 0  # 0 tells the runner to fill in wall-clock latency


class Score(_Strict):
    scorer: str
    type: str
    value: float
    passed: bool
    threshold: float
    reason: str
    cost_usd: float | None = 0.0  # spend in THIS run, so a cache hit costs 0
    details: dict[str, Any] = {}


class ScorerConfig(BaseModel):
    # Each scorer validates its own params, so unknown keys are kept here, not rejected.
    model_config = ConfigDict(extra="allow")
    type: str
    name: str | None = None
    threshold: float | None = Field(default=None, ge=0, le=1)


class Case(_Strict):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,79}$")
    tags: list[str] = []
    input: dict[str, Any]
    expected: dict[str, Any] = {}
    scorers: list[ScorerConfig] = Field(min_length=1)
    source_file: str


class TargetConfig(_Strict):
    type: Literal["python", "http"]
    path: str | None = None
    url: str | None = None
    headers: dict[str, str] = {}
    version: str  # required: it is part of every output cache key (ADR 0005)
    model: str
    timeout_s: float | None = None

    @model_validator(mode="after")
    def _check_type_fields(self) -> TargetConfig:
        # Only ValueError: pydantic wraps it in ValidationError, which the loader collects.
        if self.type == "python" and (self.path is None or not _PYTHON_PATH.match(self.path)):
            raise ValueError(r"target.path is required for type python and must match ^[\w.]+:\w+$")
        if self.type == "http" and not self.url:
            raise ValueError("target.url is required for type http")
        return self


class JudgeConfig(_Strict):
    provider: Literal["anthropic", "openai"] = "anthropic"
    model_env: str = "CASEGATE_JUDGE_MODEL"
    model: str = "claude-sonnet-5-5"
    base_url_env: str = "CASEGATE_JUDGE_BASE_URL"
    api_key_env: str | None = None
    effort: Literal["low", "medium", "high"] = "medium"
    samples: int = Field(default=1, ge=1, le=9)  # odd numbers give a clean median
    max_tokens: int = 2000


class RetryConfig(_Strict):
    attempts: int = Field(default=4, ge=1, le=10)
    backoff_s: list[float] = Field(default=[1, 2, 4], min_length=1)
    max_retry_after_s: float = Field(default=30.0, ge=0)


class Suite(_Strict):
    name: str
    target: TargetConfig
    judge: JudgeConfig = JudgeConfig()
    concurrency: int = Field(default=8, ge=1, le=64)
    threshold: float = Field(default=0.7, ge=0, le=1)  # default for judge scorers only
    retries: RetryConfig = RetryConfig()
    cases: str = "cases/*.yaml"
    must_pass_tags: list[str] = []
    root: str


Status = Literal["pass", "fail", "error"]


class RepeatResult(_Strict):
    repeat: int
    status: Status
    scores: list[Score] = []
    output: Output | None = None
    error: str | None = None
    attempts: int = 1
    cached: bool = False
    latency_ms: int = 0
    cost_usd: float | None = 0.0
    # What the repeat would have cost with an empty cache; lets reports show cache savings.
    cost_usd_full: float | None = 0.0


class CaseResult(_Strict):
    id: str
    tags: list[str]
    repeats: list[RepeatResult]
    pass_rate: float | None
    mean_score: float | None
    variance: float | None


class RunSummary(_Strict):
    pass_rate: float | None
    pass_rate_std: float
    per_repeat_pass_rate: list[float | None]
    n_cases: int
    n_scored_cases: int
    n_repeats_total: int
    n_error_repeats: int
    by_tag: dict[str, float | None]
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    cost_usd_full: float | None
    cache_output_hits: int = 0
    cache_output_total: int = 0
    cache_judge_hits: int = 0
    cache_judge_total: int = 0
    duration_s: float


class Run(_Strict):
    schema_version: Literal[1] = 1
    casegate_version: str
    suite: str
    suite_path: str
    started_at: datetime
    finished_at: datetime
    git_sha: str | None
    target_version: str
    target_model: str
    judge_model: str | None
    repeat: int
    filters: dict[str, Any] = {}
    cases: list[CaseResult]
    summary: RunSummary
