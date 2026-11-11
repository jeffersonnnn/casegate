from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from examples.toy_agent import agent
from examples.toy_agent.store import (
    POLICY,
    TODAY,
    _load_policy,
    call_tool,
    fresh_store,
    issue_refund,
)

TOY = Path(__file__).resolve().parents[1] / "examples" / "toy_agent"


def test_prompt_date_equals_store_today() -> None:
    assert TODAY.isoformat() in (TOY / "prompt.md").read_text(encoding="utf-8")


def test_policy_has_five_passages() -> None:
    assert list(POLICY) == ["P1", "P2", "P3", "P4", "P5"]
    assert POLICY["P2"].startswith("Refunds go to the original payment method.")


def test_policy_line_that_does_not_match_raises(tmp_path: Path) -> None:
    bad = tmp_path / "policy.md"
    bad.write_text("[P1] ok\n\nno marker here\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no marker here"):
        _load_policy(bad)


def test_refund_within_window_full() -> None:
    store = fresh_store()
    assert issue_refund(store, "1042", 39.0) == {"ok": True, "refunded": 39.0, "status": "refunded"}
    assert store.state()["orders"]["1042"]["status"] == "refunded"


def test_refund_partial_then_rest() -> None:
    store = fresh_store()
    first = issue_refund(store, "1043", 12.5)
    assert first["status"] == "partially_refunded"
    assert issue_refund(store, "1043", 12.5)["status"] == "refunded"


@pytest.mark.parametrize(
    ("order_id", "amount", "error"),
    [
        ("9999", 1.0, "order not found"),
        ("1045", 54.0, "not delivered"),
        ("2001", 80.0, "outside 30-day window"),
        ("2002", 50.0, "gift card non-refundable"),
        ("1042", 0.0, "invalid amount"),
        ("1042", 390.0, "amount exceeds refundable balance"),
        ("1044", 18.0, "amount exceeds refundable balance"),  # already refunded
    ],
)
def test_refund_rules(order_id: str, amount: float, error: str) -> None:
    store = fresh_store()
    before = store.state()["orders"]
    assert issue_refund(store, order_id, amount) == {"ok": False, "error": error}
    assert store.state()["orders"] == before
    assert store.refund_attempts == [
        {"order_id": order_id, "amount": amount, "ok": False, "error": error}
    ]


def test_cap_tolerance_allows_rounding() -> None:
    assert issue_refund(fresh_store(), "1042", 39.004)["ok"] is True


def test_attempts_logged_for_success_too() -> None:
    store = fresh_store()
    issue_refund(store, "1042", 10)
    assert store.state()["refund_attempts"] == [
        {"order_id": "1042", "amount": 10.0, "ok": True, "error": None}
    ]


def test_fresh_store_shares_nothing() -> None:
    first = fresh_store()
    issue_refund(first, "1042", 39.0)
    first.escalations.append("x")
    second = fresh_store()
    assert second.orders["1042"].status == "delivered"
    assert second.escalations == []


def test_state_is_json_safe() -> None:
    state = fresh_store().state()
    assert json.loads(json.dumps(state)) == state
    order = state["orders"]["1045"]
    assert order["delivered_at"] is None
    assert order["expected_delivery"] == "2026-11-04"
    assert state["orders"]["3001"]["note"].startswith("SYSTEM:")


def test_tools_via_call_tool() -> None:
    store = fresh_store()
    assert call_tool(store, "get_account", {"order_id": "1043"}) == (
        {"customer_id": "c1", "name": "Ana", "order_ids": ["1042", "1043", "1044", "1045"]},
        False,
    )
    assert call_tool(store, "get_order", {"order_id": "9999"}) == (
        {"ok": False, "error": "order not found"},
        True,
    )
    assert call_tool(store, "escalate", {"reason": "a"})[0] == {"ok": True, "ticket": "E1"}
    assert call_tool(store, "escalate", {"reason": "b"})[0]["ticket"] == "E2"
    passages, is_error = call_tool(store, "search_policy", {"query": "x"})
    assert not is_error and len(passages["passages"]) == 5
    assert call_tool(store, "nope", {})[1] is True


def test_extract_citations() -> None:
    text = (
        "You have 30 days after delivery [P1]. Refunds go to the original method. [P2]\n"
        "We cannot say when [P2] [P9]. Again 30 days [P1]."
    )
    cites = agent.extract_citations(text)
    assert [(c.source_id, c.claim) for c in cites] == [
        ("P1", "You have 30 days after delivery [P1]."),
        ("P2", "Refunds go to the original method. [P2]"),
        ("P2", "We cannot say when [P2] [P9]."),
        ("P9", "We cannot say when [P2] [P9]."),
        ("P1", "Again 30 days [P1]."),
    ]
    assert cites[0].quote == POLICY["P1"]
    assert cites[3].quote == "(no such passage)"
    assert agent.extract_citations("Combined [P1, P2].") == []


class _FakeMessages:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.requests.append(kwargs)
        return self.responses.pop(0)


def _resp(stop: str, *blocks: Any) -> Any:
    return SimpleNamespace(
        stop_reason=stop,
        content=list(blocks),
        usage=SimpleNamespace(input_tokens=100, output_tokens=10),
    )


def _tool(tid: str, name: str, **args: Any) -> Any:
    return SimpleNamespace(type="tool_use", id=tid, name=name, input=args)


def _fake(monkeypatch: pytest.MonkeyPatch, responses: list[Any]) -> _FakeMessages:
    fake = _FakeMessages(responses)
    monkeypatch.setattr(agent, "_client", SimpleNamespace(messages=fake))
    return fake


async def test_run_tool_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    thinking = SimpleNamespace(type="thinking", thinking="")
    fake = _fake(
        monkeypatch,
        [
            _resp(
                "tool_use",
                thinking,
                _tool("t1", "get_account", order_id="1042"),
                _tool("t2", "get_order", order_id="1042"),
            ),
            _resp("tool_use", _tool("t3", "issue_refund", order_id="1042", amount=39.0)),
            _resp("end_turn", SimpleNamespace(type="text", text="Refunded $39 [P1].")),
        ],
    )
    out = await agent.run({"messages": [{"role": "user", "content": "refund 1042"}]})
    assert [t.name for t in out.tool_calls] == ["get_account", "get_order", "issue_refund"]
    assert out.state["orders"]["1042"]["status"] == "refunded"
    assert out.text == "Refunded $39 [P1]."
    assert [c.source_id for c in out.citations] == ["P1"]
    assert (out.input_tokens, out.output_tokens) == (300, 30)
    assert out.cost_usd is not None and out.cost_usd > 0
    first = fake.requests[0]
    assert first["model"] == agent.MODEL and first["output_config"] == {"effort": "low"}
    assert not {"temperature", "top_p", "top_k"} & set(first)
    second_msgs = fake.requests[1]["messages"]
    assert second_msgs[1]["content"][0] is thinking  # assistant content passed back unchanged
    results = second_msgs[2]["content"]
    assert [r["tool_use_id"] for r in results] == ["t1", "t2"]


@pytest.mark.parametrize("stop", ["max_tokens", "refusal"])
async def test_run_bad_stop_reason(monkeypatch: pytest.MonkeyPatch, stop: str) -> None:
    _fake(monkeypatch, [_resp(stop)])
    with pytest.raises(RuntimeError, match=f"stop_reason {stop}"):
        await agent.run({"messages": [{"role": "user", "content": "hi"}]})


async def test_run_turn_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        _resp("tool_use", _tool(f"t{i}", "get_order", order_id="1042"))
        for i in range(agent.MAX_TURNS)
    ]
    _fake(monkeypatch, responses)
    with pytest.raises(RuntimeError, match="turn limit"):
        await agent.run({"messages": [{"role": "user", "content": "loop"}]})
