import pytest

from casegate.errors import SuiteError
from casegate.models import Output
from casegate.scorers import build_scorers
from casegate.scorers.state_match import split_path
from tests.scorers._util import make_case, make_suite, score

STATE = {
    "orders": {"1042": {"status": "delivered", "refunds": [{"amount": 10.0}]}, "a.b": {"x": 1}},
    "items": ["p", "q"],
}


def out(state: dict) -> Output:
    return Output(text="", state=state)


def errors_for(scorer: dict, expected: dict | None = None) -> list[str]:
    with pytest.raises(SuiteError) as exc:
        build_scorers(make_case([scorer], expected), make_suite())
    return exc.value.errors


def test_all_paths_match() -> None:
    expected = {
        "state": {
            "orders.1042.status": "delivered",
            'orders["a.b"].x': 1,
            "items.1": "q",
            "orders.1042.refunds": {"all_amounts_lte": 39},
        }
    }
    s = score({"type": "state_match"}, out(STATE), expected)
    assert (s.value, s.passed, s.reason) == (1.0, True, "ok")


def test_mismatch_and_missing_reason_in_expected_order() -> None:
    expected = {
        "state": {
            "orders.1042.status": "refunded",
            "orders.9.status": "x",
            "items.5": "p",
            "items.x": "p",
            "orders.1042.refunds": {"all_amounts_lte": 5},
        }
    }
    s = score({"type": "state_match"}, out(STATE), expected)
    assert s.value == 0.0
    assert s.reason == (
        'orders.1042.status: expected "refunded", got "delivered"; '
        'orders.9.status: expected "x", got <missing>; '
        'items.5: expected "p", got <missing>; '
        'items.x: expected "p", got <missing>; '
        'orders.1042.refunds: expected {"all_amounts_lte":5}, got [{"amount": 10.0}]'
    )


def test_fraction_and_matcher_render() -> None:
    expected = {"state": {"a": {"lte": 39}, "b": True}}
    s = score({"type": "state_match"}, out({"a": 40, "b": True}), expected)
    assert s.value == 0.5 and s.reason == 'a: expected {"lte":39}, got 40'
    assert s.details == {"matched": 1, "total": 2, "failed": ["a"]}


def test_param_overrides_expected() -> None:
    s = score({"type": "state_match", "state": {"a": 1}}, out({"a": 1}), {"state": {"a": 2}})
    assert s.passed


def test_split_path() -> None:
    assert split_path('orders["a.b"].status') == ["orders", "a.b", "status"]
    assert split_path("a.0.b") == ["a", "0", "b"]
    for bad in ["", "a.", ".a", "a..b", "a[0]", 'a["x"', "a[b"]:
        assert split_path(bad) is None, bad


def test_load_errors() -> None:
    pre = "case c1 scorer state_match: state_match: "
    assert errors_for({"type": "state_match"}) == [pre + "needs non-empty state or expected.state"]
    assert errors_for({"type": "state_match", "state": {}}) == [
        pre + "needs non-empty state or expected.state"
    ]
    assert errors_for({"type": "state_match"}, {"state": ["x"]}) == [
        "case c1 scorer state_match: expected.state: Input should be a valid dictionary"
    ]
    assert errors_for({"type": "state_match", "state": {"a..b": 1, "c": {"regex": "("}}}) == [
        pre + 'malformed path "a..b"',
        pre + "c: invalid regex: missing ), unterminated subpattern at position 0",
    ]
