import json, time, anthropic
from pydantic import BaseModel, Field
c = anthropic.Anthropic()
PRICE = {"claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.0, 10.0)}
def cost(m, u): pi, po = PRICE[m]; return (u.input_tokens*pi + u.output_tokens*po)/1e6
STORE = {"accounts": {"c1": {"name": "Ana", "orders": ["1042"]}}, "orders": {"1042": {"amount": 39.0, "status": "delivered", "customer": "c1"}}}
POLICY = [{"id": "P1", "text": "Damaged items can be refunded in full within 30 days of delivery."}, {"id": "P2", "text": "Refunds are issued to the original payment method; we do not promise a processing time."}]
def obj(props, req): return {"type": "object", "properties": props, "required": req, "additionalProperties": False}
TOOLS = [
 {"name": "get_account", "description": "Look up the customer account that owns an order.", "input_schema": obj({"order_id": {"type": "string"}}, ["order_id"]), "strict": True},
 {"name": "get_order", "description": "Get an order by id.", "input_schema": obj({"order_id": {"type": "string"}}, ["order_id"]), "strict": True},
 {"name": "issue_refund", "description": "Refund an order. Amount must not exceed the order amount.", "input_schema": obj({"order_id": {"type": "string"}, "amount": {"type": "number"}}, ["order_id", "amount"]), "strict": True},
 {"name": "escalate", "description": "Hand the case to a human.", "input_schema": obj({"reason": {"type": "string"}}, ["reason"]), "strict": True},
 {"name": "search_policy", "description": "Search the refund policy. Returns passages with ids; cite ids like [P1].", "input_schema": obj({"query": {"type": "string"}}, ["query"]), "strict": True},
]
def run_tool(n, a):
    if n == "get_account": o = STORE["orders"].get(a["order_id"]); return {"customer_id": o["customer"], **STORE["accounts"][o["customer"]]} if o else {"error": "not found"}
    if n == "get_order": return STORE["orders"].get(a["order_id"], {"error": "not found"})
    if n == "issue_refund":
        o = STORE["orders"][a["order_id"]]
        if a["amount"] > o["amount"]: return {"error": "amount exceeds cap"}
        o["status"] = "refunded"; return {"ok": True, "refunded": a["amount"]}
    if n == "escalate": return {"ok": True}
    if n == "search_policy": return POLICY
SYSTEM = "You are a refund support agent. Use tools. Before a refund, call get_account then get_order. When you state policy, cite passage ids like [P1]."
msgs = [{"role": "user", "content": "Order 1042 arrived broken. I'd like a refund."}]
calls, tot, t0 = [], 0.0, time.time()
for turn in range(8):
    r = c.messages.create(model="claude-haiku-5-5", max_tokens=4000, system=SYSTEM, tools=TOOLS, messages=msgs, output_config={"effort": "low"})
    tot += cost("claude-haiku-5-5", r.usage)
    print("turn", turn, r.stop_reason, "in", r.usage.input_tokens, "out", r.usage.output_tokens, "blocks", [b.type for b in r.content])
    msgs.append({"role": "assistant", "content": r.content})
    if r.stop_reason != "tool_use": break
    res = []
    for b in r.content:
        if b.type == "tool_use":
            calls.append((b.name, b.input)); res.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(run_tool(b.name, b.input))})
    msgs.append({"role": "user", "content": res})
final = "".join(b.text for b in r.content if b.type == "text")
print("TRAJECTORY", calls); print("STATE orders.1042.status =", STORE["orders"]["1042"]["status"]); print("FINAL", final[:400])
print("AGENT cost $%.5f latency %.1fs" % (tot, time.time()-t0))

class Verdict(BaseModel):
    reasoning: str = Field(description="Short reason, max 2 sentences")
    score: float = Field(description="0 to 1")
rubric = "The reply confirms the refund amount and does not promise a timeline."
jt = 0.0
for i in range(3):
    t1 = time.time()
    j = c.messages.parse(model="claude-sonnet-5-5", max_tokens=2000, output_format=Verdict, output_config={"effort": "medium"},
        messages=[{"role": "user", "content": f"Grade the reply against the rubric. Score 0-1.\nRUBRIC: {rubric}\nREPLY:\n{final}"}])
    jt += cost("claude-sonnet-5-5", j.usage)
    print("JUDGE", i, j.stop_reason, j.parsed_output, "in", j.usage.input_tokens, "out", j.usage.output_tokens, "%.1fs" % (time.time()-t1))
print("JUDGE cost 3 calls $%.5f" % jt)
# negative check: temperature must 400
try:
    c.messages.create(model="claude-sonnet-5-5", max_tokens=50, temperature=0, messages=[{"role": "user", "content": "hi"}]); print("TEMPERATURE accepted")
except Exception as e: print("TEMPERATURE rejected:", type(e).__name__, str(e)[:160])
