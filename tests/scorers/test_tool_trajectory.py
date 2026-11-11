from typing import Any

import pytest

from casegate.errors import SuiteError
from casegate.models import Output, Score, ToolCall
from casegate.scorers import build_scorers
from tests.scorers._util import make_case, make_suite, score


def calls(*names: str, **args: dict[str, Any]) -> Output:
    return Output(text="", tool_calls=[ToolCall(name=n, args=args.get(n, {})) for n in names])


def traj(output: Output, expected: dict[str, Any] | None = None, **params: Any) -> Score:
    return score({"type": "tool_trajectory", **params}, output, expected)


def errors_for(scorer: dict, expected: dict | None = None) -> list[str]:
    with pytest.raises(SuiteError) as exc:
        build_scorers(make_case([scorer], expected), make_suite())
    return exc.value.errors


REFUND = {"name": "issue_refund", "args": {"order_id": "1042", "amount": {"lte": 39.0}}}


def test_subsequence_with_arg_matchers_passes() -> None:
    out = calls(
        "get_account",
        "search",
        "get_order",
        "issue_refund",
        issue_refund={"order_id": "1042", "amount": 39, "note": "x"},
    )
    s = traj(out, {"tools": ["get_account", "get_order", REFUND], "tools_forbidden": ["escalate"]})
    assert (s.value, s.passed, s.reason) == (1.0, True, "ok")
    assert s.details == {
        "expected": ["get_account", "get_order", "issue_refund"],
        "actual": ["get_account", "search", "get_order", "issue_refund"],
        "matched": 3,
        "mode": "subsequence",
        "forbidden_called": [],
        "ignored": 0,
    }


def test_subsequence_fail_reason() -> None:
    s = traj(calls("issue_refund"), {"tools": ["get_account", "issue_refund"]})
    assert s.value == 0.0
    assert s.reason == (
        "expected subsequence get_account → issue_refund; got issue_refund; "
        "first unmatched: get_account"
    )


def test_arg_mismatch_and_missing_arg_do_not_match() -> None:
    over = traj(
        calls("issue_refund", issue_refund={"order_id": "1042", "amount": 50}), {"tools": [REFUND]}
    )
    assert over.value == 0.0
    assert over.reason.endswith(
        'first unmatched: issue_refund({"amount":{"lte":39.0},"order_id":"1042"})'
    )
    missing = traj(calls("issue_refund", issue_refund={"amount": 10}), {"tools": [REFUND]})
    assert missing.value == 0.0


def test_exact_mode() -> None:
    assert traj(calls("a", "b"), {"tools": ["a", "b"]}, mode="exact").value == 1.0
    s = traj(calls("a", "c"), {"tools": ["a", "b"]}, mode="exact")
    assert s.value == 0.5
    assert s.reason == "expected exact a → b; got a → c; first unmatched: b"
    longer = traj(calls("a", "b", "c"), {"tools": ["a", "b"]}, mode="exact")
    assert longer.value == pytest.approx(2 / 3)
    assert longer.reason == "expected exact a → b; got a → b → c"


def test_set_mode() -> None:
    assert traj(calls("b", "a", "x"), {"tools": ["a", "b"]}, mode="set").value == 1.0
    s = traj(
        calls("get_account", "search_policy"),
        {"tools": ["get_account", "escalate"]},
        mode="set",
        allow_extra=False,
    )
    assert s.value == 0.0
    assert s.reason == "expected set get_account, escalate; missing: escalate; extra: search_policy"
    half = traj(calls("a"), {"tools": ["a", "b"]}, mode="set")
    assert half.value == 0.5 and half.reason == "expected set a, b; missing: b"
    extras = traj(calls("a", "z"), {"tools": ["a"]}, mode="set", allow_extra=False)
    assert extras.value == 0.0 and extras.reason == "expected set a; extra: z"


def test_set_uses_first_unused_call() -> None:
    assert traj(calls("a"), {"tools": ["a", "a"]}, mode="set").value == 0.5
    assert traj(calls("a", "a"), {"tools": ["a", "a"]}, mode="set").value == 1.0


@pytest.mark.parametrize(
    ("mode", "allow_extra", "actual", "value"),
    [
        ("subsequence", True, [], 1.0),
        ("subsequence", True, ["a"], 1.0),
        ("set", True, ["a"], 1.0),
        ("set", False, [], 1.0),
        ("set", False, ["a"], 0.0),
        ("exact", True, [], 1.0),
        ("exact", True, ["a"], 0.0),
    ],
)
def test_empty_expected(mode: str, allow_extra: bool, actual: list[str], value: float) -> None:
    params: dict[str, Any] = {"mode": mode, "tools": []}
    if not allow_extra:
        params["allow_extra"] = False
    assert traj(calls(*actual), **params).value == value


def test_forbidden_overrides_and_names_first_in_actual_order() -> None:
    s = traj(
        calls("a", "refund", "escalate"),
        {"tools": ["a"], "tools_forbidden": ["escalate", "refund"]},
    )
    assert s.value == 0.0 and s.reason == "forbidden tool called: refund"
    assert s.details["forbidden_called"] == ["refund", "escalate"]
    only_forbidden = traj(calls("a"), {"tools_forbidden": ["escalate"]})
    assert only_forbidden.value == 1.0


def test_long_actual_list_is_cut_after_eight() -> None:
    names = [f"t{i}" for i in range(10)]
    s = traj(calls(*names), {"tools": ["zz"]})
    assert "got t0 → t1 → t2 → t3 → t4 → t5 → t6 → t7 → …(+2)" in s.reason


@pytest.mark.parametrize("mode", ["exact", "subsequence", "set"])
def test_ignore_in_each_mode(mode: str) -> None:
    s = traj(
        calls("search_docs", "a", "search_docs", "b"),
        {"tools": ["a", "b"]},
        mode=mode,
        ignore=["search_docs"],
    )
    assert s.value == 1.0
    assert s.details["actual"] == ["a", "b"] and s.details["ignored"] == 2


def test_ignore_with_allow_extra_false() -> None:
    s = traj(
        calls("search_docs", "a"),
        {"tools": ["a"]},
        mode="set",
        allow_extra=False,
        ignore=["search_docs"],
    )
    assert s.value == 1.0


def test_forbidden_wins_over_ignore() -> None:
    s = traj(
        calls("a", "search_docs"),
        {"tools": ["a"], "tools_forbidden": ["search_docs"]},
        ignore=["search_docs"],
    )
    assert s.value == 0.0 and s.reason == "forbidden tool called: search_docs"


def test_params_override_expected() -> None:
    s = traj(calls("x"), {"tools": ["a"], "tools_forbidden": ["x"]}, tools=["x"], forbidden=[])
    assert s.passed


def test_load_errors() -> None:
    pre = "case c1 scorer tool_trajectory: tool_trajectory: "
    assert errors_for({"type": "tool_trajectory"}) == [
        pre + "needs tools, forbidden, expected.tools or expected.tools_forbidden"
    ]
    assert errors_for({"type": "tool_trajectory", "tools": ["a"], "allow_extra": False}) == [
        pre + "allow_extra is only valid with mode set"
    ]
    assert errors_for({"type": "tool_trajectory", "tools": ["a"], "ignore": ["a"]}) == [
        pre + "a is both expected and ignored"
    ]
    bad_args = {"name": "r", "args": {"amount": {"all_amounts_lte": 3}, "id": {"regex": 1}}}
    assert errors_for({"type": "tool_trajectory"}, {"tools": [bad_args]}) == [
        pre + "r.amount: all_amounts_lte is valid only in state_match",
        pre + "r.id: regex must be a string",
    ]


def test_explicit_allow_extra_true_is_fine_in_any_mode() -> None:
    case = make_case([{"type": "tool_trajectory", "tools": ["a"], "allow_extra": True}])
    assert len(build_scorers(case, make_suite())) == 1


def test_expected_tool_item_with_unknown_key_fails() -> None:
    errs = errors_for({"type": "tool_trajectory"}, {"tools": [{"name": "a", "bogus": 1}]})
    assert errs and all(
        e.startswith("case c1 scorer tool_trajectory: expected.tools: ") for e in errs
    )
