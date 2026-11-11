from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from casegate.models import (
    Case,
    CaseResult,
    Citation,
    Output,
    RepeatResult,
    Run,
    RunSummary,
    Score,
    ScorerConfig,
    Suite,
    TargetConfig,
    ToolCall,
)


def _output() -> Output:
    return Output(
        text="Refunded $40.",
        tool_calls=[ToolCall(name="refund", args={"order_id": "A1", "amount": 40}, result="ok")],
        citations=[Citation(source_id="P1", quote="Refunds within 30 days.", claim="It is due.")],
        state={"A1": {"status": "refunded"}},
        input_tokens=120,
        output_tokens=30,
        cost_usd=None,
        latency_ms=812,
    )


def _run() -> Run:
    score = Score(scorer="exact", type="exact", value=1.0, passed=True, threshold=1.0, reason="ok")
    repeats = [
        RepeatResult(repeat=0, status="pass", scores=[score], output=_output(), cost_usd=None),
        RepeatResult(repeat=1, status="error", error="RuntimeError: boom", attempts=4),
    ]
    case = CaseResult(
        id="refund-01", tags=["core"], repeats=repeats, pass_rate=1.0, mean_score=1.0, variance=0.0
    )
    summary = RunSummary(
        pass_rate=1.0,
        pass_rate_std=0.0,
        per_repeat_pass_rate=[1.0, None],
        n_cases=1,
        n_scored_cases=1,
        n_repeats_total=2,
        n_error_repeats=1,
        by_tag={"core": 1.0},
        input_tokens=120,
        output_tokens=30,
        cost_usd=None,
        cost_usd_full=None,
        duration_s=1.5,
    )
    return Run(
        casegate_version="0.1.0",
        suite="toy",
        suite_path="evals",
        started_at=datetime(2026, 11, 11, 9, 0, tzinfo=UTC),
        finished_at=datetime(2026, 11, 11, 9, 1, tzinfo=UTC),
        git_sha=None,
        target_version="toy-agent@1",
        target_model="claude-haiku-5-5",
        judge_model=None,
        repeat=2,
        filters={"must_pass_tags": []},
        cases=[case],
        summary=summary,
    )


def test_output_round_trip() -> None:
    out = _output()
    assert Output.model_validate_json(out.model_dump_json()) == out


def test_run_round_trip() -> None:
    run = _run()
    text = run.model_dump_json(indent=2)
    assert Run.model_validate_json(text) == run
    assert '"started_at": "2026-11-11T09:00:00Z"' in text
    assert '"schema_version": 1' in text


@pytest.mark.parametrize(
    ("model", "data"),
    [
        (Output, {"text": "x", "surprise": 1}),
        (ToolCall, {"name": "t", "extra": True}),
        (
            Score,
            {
                "scorer": "s",
                "type": "exact",
                "value": 1,
                "passed": True,
                "threshold": 1,
                "reason": "ok",
                "oops": 0,
            },
        ),
    ],
)
def test_extra_fields_rejected(model: type, data: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        model.model_validate(data)


def test_run_extra_field_rejected() -> None:
    data = _run().model_dump(mode="json")
    data["summary"]["bonus"] = 1
    with pytest.raises(ValidationError):
        Run.model_validate(data)


def test_scorer_config_keeps_params() -> None:
    cfg = ScorerConfig.model_validate({"type": "contains", "case_sensitive": True})
    assert cfg.model_extra == {"case_sensitive": True}
    with pytest.raises(ValidationError):
        ScorerConfig(type="llm_judge", threshold=1.5)


def test_case_id_pattern_and_scorers_required() -> None:
    ok = {"id": "a.b-c_1", "input": {}, "scorers": [{"type": "exact"}], "source_file": "c.yaml"}
    assert Case.model_validate(ok).id == "a.b-c_1"
    with pytest.raises(ValidationError):
        Case.model_validate({**ok, "id": "Bad Id"})
    with pytest.raises(ValidationError):
        Case.model_validate({**ok, "scorers": []})


def test_target_python_path_required() -> None:
    base = {"type": "python", "version": "v1", "model": "none"}
    assert TargetConfig.model_validate({**base, "path": "pkg.mod:run"}).path == "pkg.mod:run"
    for bad in (None, "pkg.mod.run"):
        with pytest.raises(ValidationError, match=r"target.path is required for type python"):
            TargetConfig.model_validate({**base, "path": bad})


def test_target_http_url_required() -> None:
    base = {"type": "http", "version": "v1", "model": "none"}
    assert TargetConfig.model_validate({**base, "url": "http://x"}).url == "http://x"
    with pytest.raises(ValidationError, match=r"target\.url is required for type http"):
        TargetConfig.model_validate(base)


def test_suite_defaults() -> None:
    suite = Suite.model_validate(
        {
            "name": "s",
            "root": "/tmp/s",
            "target": {"type": "python", "path": "m:f", "version": "1", "model": "none"},
        }
    )
    assert suite.concurrency == 8
    assert suite.threshold == 0.7
    assert suite.cases == "cases/*.yaml"
    assert suite.judge.model == "claude-sonnet-5-5"
    assert suite.judge.samples == 1
    assert suite.retries.attempts == 4
    assert suite.retries.backoff_s == [1, 2, 4]
    assert suite.retries.max_retry_after_s == 30.0
