import pytest

from casegate.errors import SuiteError
from casegate.scorers import build_scorers
from tests.scorers._util import make_case, make_suite, score


def errors_for(scorer: dict, expected: dict | None = None) -> list[str]:
    with pytest.raises(SuiteError) as exc:
        build_scorers(make_case([scorer], expected), make_suite())
    return exc.value.errors


def test_normalised_match_passes_with_ok_reason() -> None:
    s = score({"type": "exact"}, "  Hello   WORLD! ", {"answer": "hello world"})
    assert (s.value, s.passed, s.reason, s.threshold) == (1.0, True, "ok", 1.0)
    assert (s.scorer, s.type, s.cost_usd) == ("exact", "exact", 0.0)


def test_any_of_list_and_fail_reason() -> None:
    s = score({"type": "exact"}, "nope", {"answer": ["Yes", "Sure"]})
    assert s.value == 0.0 and not s.passed
    assert s.reason == 'expected "Yes" | "Sure", got "nope"'


def test_reason_cuts_output_to_80_chars_before_dumping() -> None:
    s = score({"type": "exact"}, "x" * 100, {"answer": "y"})
    assert s.reason == f'expected "y", got "{"x" * 80}"'


def test_normalise_false_is_case_sensitive() -> None:
    assert score({"type": "exact", "normalise": False}, "ok", {"answer": "OK"}).value == 0.0
    assert score({"type": "exact", "normalise": False}, "OK", {"answer": "OK"}).value == 1.0


def test_param_overrides_expected() -> None:
    assert score({"type": "exact", "answer": "a"}, "a", {"answer": "b"}).passed


def test_lowered_threshold_passes_a_zero_value() -> None:
    s = score({"type": "exact", "threshold": 0.0}, "no", {"answer": "yes"})
    assert s.passed and s.reason.startswith("expected")


def test_missing_answer() -> None:
    assert errors_for({"type": "exact"}) == [
        "case c1 scorer exact: exact: needs answer or expected.answer"
    ]


def test_expected_answer_wrong_type_gives_one_line_per_union_member() -> None:
    assert errors_for({"type": "exact"}, {"answer": 42}) == [
        "case c1 scorer exact: expected.answer: Input should be a valid string",
        "case c1 scorer exact: expected.answer: Input should be a valid list",
    ]


def test_empty_lists() -> None:
    assert errors_for({"type": "exact", "answer": []}) == [
        "case c1 scorer exact: exact: answer must not be empty"
    ]
    assert errors_for({"type": "exact"}, {"answer": []}) == [
        "case c1 scorer exact: exact: expected.answer must not be empty"
    ]


def test_unknown_param_is_a_params_error() -> None:
    assert errors_for({"type": "exact", "answer": "a", "bogus": 1}) == [
        "case c1 scorer exact: bogus: Extra inputs are not permitted"
    ]
