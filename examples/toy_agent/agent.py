"""The system under test in the example suite: a refund support agent on Claude Haiku.

It is small on purpose, so a reader can see the whole tool loop and how casegate's Output
(trajectory, state, citations, tokens, cost) is built from one agent run. The runner owns
retries, so this module lets rate-limit and connection errors propagate.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import anthropic

from casegate.models import Citation, Output, ToolCall
from casegate.prices import cost
from examples.toy_agent.store import POLICY, call_tool, fresh_store

# Both must equal evals/suite.yaml target.model; a change of either bumps target.version.
MODEL = "claude-haiku-5-5"
EFFORT = "low"
MAX_TOKENS = 4000
MAX_TURNS = 8

SYSTEM_PROMPT = Path(__file__).with_name("prompt.md").read_text(encoding="utf-8").strip()


def _schema(**props: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": props,
        "required": list(props),
        "additionalProperties": False,
    }


_STR = {"type": "string"}
TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_account",
        "description": "Look up the customer who owns an order and the ids of all their orders.",
        "input_schema": _schema(order_id=_STR),
        "strict": True,
    },
    {
        "name": "get_order",
        "description": "Get one order with its amount, items, status, delivery dates and note.",
        "input_schema": _schema(order_id=_STR),
        "strict": True,
    },
    {
        "name": "issue_refund",
        "description": "Refund an amount in dollars on an order, if the refund policy allows it.",
        "input_schema": _schema(order_id=_STR, amount={"type": "number"}),
        "strict": True,
    },
    {
        "name": "escalate",
        "description": "Hand the conversation to a human agent, with the reason.",
        "input_schema": _schema(reason=_STR),
        "strict": True,
    },
    {
        "name": "search_policy",
        "description": "Search the refund policy; returns passages with ids such as P1 to cite.",
        "input_schema": _schema(query=_STR),
        "strict": True,
    },
]

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    # Lazy, so importing the module (tests, the loader's target check) needs no API key.
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(max_retries=0)
    return _client


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_MARKER = re.compile(r"\[(P\d+)\]")


def extract_citations(text: str) -> list[Citation]:
    """One Citation per [Pn] marker, with the sentence it sits in as the claim."""
    sentences: list[str] = []
    for part in _SENTENCE_SPLIT.split(text):
        part = part.strip()
        if not part:
            continue
        # A marker after the full stop ("...delivery. [P1]") cites the sentence before it.
        if sentences and _MARKER.sub("", part).strip() == "":
            sentences[-1] = f"{sentences[-1]} {part}"
        else:
            sentences.append(part)
    citations: list[Citation] = []
    seen: set[tuple[str, str]] = set()
    for sentence in sentences:
        for source_id in _MARKER.findall(sentence):
            if (source_id, sentence) in seen:
                continue
            seen.add((source_id, sentence))
            # An unknown id still becomes a citation, so the judge marks it unsupported.
            quote = POLICY.get(source_id, "(no such passage)")
            citations.append(Citation(source_id=source_id, quote=quote, claim=sentence))
    return citations


async def run(case_input: dict[str, Any]) -> Output:
    store = fresh_store()
    messages: list[dict[str, Any]] = [dict(m) for m in case_input["messages"]]
    tool_calls: list[ToolCall] = []
    tokens_in = tokens_out = 0
    client = _get_client()

    for turn in range(MAX_TURNS):
        response = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
            output_config={"effort": EFFORT},
        )
        tokens_in += response.usage.input_tokens
        tokens_out += response.usage.output_tokens
        reason = response.stop_reason
        if reason == "end_turn":
            break
        if reason != "tool_use":
            # max_tokens, refusal or anything unexpected: an error, not something to retry.
            raise RuntimeError(f"stop_reason {reason}")
        if turn == MAX_TURNS - 1:
            raise RuntimeError("turn limit")

        # Thinking blocks must go back unchanged, so the assistant content is passed as is.
        messages.append({"role": "assistant", "content": response.content})
        results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            args = dict(block.input)
            result, is_error = call_tool(store, block.name, args)
            tool_calls.append(ToolCall(name=block.name, args=args, result=result))
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": results})

    text = "\n".join(b.text for b in response.content if b.type == "text").strip()
    return Output(
        text=text,
        tool_calls=tool_calls,
        citations=extract_citations(text),
        state=store.state(),
        input_tokens=tokens_in,
        output_tokens=tokens_out,
        cost_usd=cost(MODEL, tokens_in, tokens_out),
    )
