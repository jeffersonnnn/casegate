import pytest

from casegate.errors import SuiteError
from casegate.scorers import build_scorers
from tests.scorers._util import make_case, make_suite, score


def errors_for(scorer: dict, expected: dict | None = None) -> list[str]:
    with pytest.raises(SuiteError) as exc:
        build_scorers(make_case([scorer], expected), make_suite())
    return exc.value.errors


def test_contains_all_present_normalised() -> None:
    s = score(
        {"type": "contains"}, "Refund of $39 ISSUED.", {"answer_contains": ["refund", "issued"]}
    )
    assert (s.value, s.passed, s.reason) == (1.0, True, "ok")


def test_contains_fraction_and_any_of_group_reason() -> None:
    expected = {"answer_contains": ["refund", "x", ["already", "previously"]]}
    s = score({"type": "contains"}, "Your refund is done", expected)
    assert s.value == pytest.approx(1 / 3)
    assert not s.passed
    assert s.reason == 'missing: "x", ("already" | "previously")'


def test_contains_any_of_group_matches_one_member() -> None:
    expected = {"answer_contains": [["already", "previously"]]}
    assert score({"type": "contains"}, "It was previously refunded", expected).value == 1.0


def test_contains_below_one_passes_with_lower_threshold_but_keeps_missing_reason() -> None:
    s = score({"type": "contains", "threshold": 0.5}, "a", {"answer_contains": ["a", "b"]})
    assert s.passed and s.value == 0.5 and s.reason == 'missing: "b"'


def test_contains_normalise_false() -> None:
    s = score({"type": "contains", "normalise": False, "items": ["Refund"]}, "refund")
    assert s.value == 0.0


def test_contains_param_overrides_expected() -> None:
    s = score({"type": "contains", "items": ["a"]}, "a", {"answer_contains": ["zzz"]})
    assert s.passed


def test_not_contains_pass_and_fail_reason_in_config_order() -> None:
    assert score({"type": "not_contains", "items": ["x"]}, "clean").reason == "ok"
    s = score({"type": "not_contains"}, "Y and X", {"answer_not_contains": ["x", "z", "y"]})
    assert (s.value, s.passed) == (0.0, False)
    assert s.reason == 'found banned: "x", "y"'


def test_missing_inputs() -> None:
    assert errors_for({"type": "contains"}) == [
        "case c1 scorer contains: contains: needs items or expected.answer_contains"
    ]
    assert errors_for({"type": "not_contains"}) == [
        "case c1 scorer not_contains: not_contains: needs items or expected.answer_not_contains"
    ]


def test_empty_lists_and_groups() -> None:
    assert errors_for({"type": "contains", "items": []}) == [
        "case c1 scorer contains: contains: items must not be empty"
    ]
    assert errors_for({"type": "contains"}, {"answer_contains": ["a", []]}) == [
        "case c1 scorer contains: contains: expected.answer_contains must not be empty"
    ]
    assert errors_for({"type": "not_contains"}, {"answer_not_contains": []}) == [
        "case c1 scorer not_contains: not_contains: expected.answer_not_contains must not be empty"
    ]


def test_expected_wrong_type_fails_at_load() -> None:
    errs = errors_for({"type": "contains"}, {"answer_contains": "x"})
    assert errs == [
        "case c1 scorer contains: expected.answer_contains: Input should be a valid list"
    ]
