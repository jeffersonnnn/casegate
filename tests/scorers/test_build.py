import asyncio

import pytest

from casegate.errors import SuiteError
from casegate.models import Output
from casegate.scorers import REGISTRY, build_scorers
from casegate.scorers.base import clean_reason, normalise, render_value
from tests.scorers._util import make_case, make_ctx, make_suite

KNOWN = (
    "citation_support, contains, exact, json_schema, llm_judge, not_contains, state_match, "
    "tool_trajectory"
)
JUDGE_TYPES = {"citation_support", "llm_judge"}


def test_registry_holds_all_eight_types() -> None:
    assert sorted(REGISTRY) == KNOWN.split(", ")
    assert {t for t, cls in REGISTRY.items() if cls.needs_judge} == JUDGE_TYPES


def test_unknown_type_raises_suite_error_before_anything_else() -> None:
    # The bad params on the exact scorer must not be reported: unknown types stop the build.
    case = make_case([{"type": "exact", "bogus": 1}, {"type": "llm_judgy"}, {"type": "nope"}])
    with pytest.raises(SuiteError) as exc:
        build_scorers(case, make_suite())
    assert exc.value.errors == [
        f"case c1: unknown scorer type llm_judgy (known: {KNOWN})",
        f"case c1: unknown scorer type nope (known: {KNOWN})",
    ]
    assert case.scorers[0].name is None


def test_names_are_numbered_per_type_and_written_back() -> None:
    case = make_case(
        [
            {"type": "exact", "answer": "a"},
            {"type": "contains", "items": ["a"]},
            {"type": "exact", "answer": "a", "name": "strict"},
            {"type": "exact", "answer": "a"},
        ]
    )
    names = [s.name for s in build_scorers(case, make_suite())]
    assert names == ["exact", "contains", "strict", "exact#2"]
    assert [c.name for c in case.scorers] == names
    assert [s.name for s in build_scorers(case, make_suite())] == names


def test_duplicate_names() -> None:
    case = make_case(
        [{"type": "exact", "answer": "a"}, {"type": "exact", "answer": "a", "name": "exact"}]
    )
    with pytest.raises(SuiteError) as exc:
        build_scorers(case, make_suite())
    assert exc.value.errors == ["case c1: duplicate scorer name exact"]


def test_thresholds() -> None:
    case = make_case(
        [{"type": "exact", "answer": "a"}, {"type": "contains", "items": ["a"], "threshold": 0.4}]
    )
    exact, contains = build_scorers(case, make_suite(threshold=0.7))
    assert exact.threshold == 1.0  # deterministic default, not the suite threshold
    assert contains.threshold == 0.4


def test_all_errors_are_collected() -> None:
    case = make_case(
        [{"type": "exact"}, {"type": "contains", "items": [], "x": 1}, {"type": "not_contains"}]
    )
    with pytest.raises(SuiteError) as exc:
        build_scorers(case, make_suite())
    assert exc.value.errors == [
        "case c1 scorer exact: exact: needs answer or expected.answer",
        "case c1 scorer contains: x: Extra inputs are not permitted",
        "case c1 scorer not_contains: not_contains: needs items or expected.answer_not_contains",
    ]


def test_score_without_check_raises_value_error() -> None:
    case = make_case([{"type": "exact", "answer": "a"}])
    (scorer,) = build_scorers(case, make_suite())
    other = make_case([{"type": "exact"}], case_id="c2")
    scorer.params.answer = None  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="needs answer"):
        asyncio.run(scorer.score(other, Output(text="a"), make_ctx()))


def test_normalise() -> None:
    assert normalise("  \uff28ello\n\tWORLD!?. ") == "hello world"
    assert normalise("Straße") == "strasse"


def test_reason_helpers() -> None:
    assert clean_reason("a\nb\r\nc") == "a b c"
    long = clean_reason("x" * 400)
    assert len(long) == 300 and long.endswith("…")
    assert clean_reason("y" * 300) == "y" * 300
    assert render_value("é") == '"é"'
