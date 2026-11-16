"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("single", claim_id, seed))
    conn = connect(store_path)
    try:
        def result(status, proposal=0, reason=None):
            trace.add("decision", {"status": status, "proposal_amount": proposal})
            return finish(
                conn, shape="single", claim_id=claim_id, seed=seed,
                status=status, proposal_amount=proposal, budget=budget,
                trace=trace, error_reason=reason,
            )

        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        # Never log the ticket: even user-supplied text can contain PII or secrets.
        trace.add("claim", {"found": claim["found"]})
        if not claim["found"]:
            return result("failed", reason="unknown_claim")
        if not claim.get("order_id"):
            return result("needs_info", reason="missing_order_id")

        evidence = {}

        def decide(observation):
            last_tool = observation.get("last_tool")
            if last_tool:
                evidence[last_tool] = observation["last_result"]
                # Tool payloads stay in memory; trace only the observation type.
                trace.add("observation", {"tool": last_tool})

            # MockLLM returns seeded text, not structured tool calls. This bounded
            # adapter maps the observed state to the next allowed read action.
            # Neither ticket instructions nor model text can alter tool arguments.
            complete(
                budget, seed=seed, purpose="react",
                prompt=f"Read-only claim investigation. Observed tools: {','.join(sorted(evidence))}",
            )
            if "lookup_order" not in evidence:
                action = {"tool": "lookup_order", "args": {
                    "order_id": claim["order_id"], "principal_id": claim["principal_id"],
                }}
            elif not evidence["lookup_order"].get("visible"):
                action = {"final": {"status": "escalated"}}
            elif "lookup_policy" not in evidence:
                action = {"tool": "lookup_policy", "args": {}}
            elif "lookup_refund_history" not in evidence:
                action = {"tool": "lookup_refund_history", "args": {
                    "order_id": claim["order_id"], "principal_id": claim["principal_id"],
                }}
            else:
                action = {"final": {"status": "investigated"}}
            trace.add("react", {"action": action.get("tool", "final")})
            return action

        investigation = run_react(
            conn, budget, observation={"claim": {
                "claim_id": claim_id, "order_id": claim["order_id"],
            }}, decide=decide, max_steps=8, worker=True,
        )
        if investigation["stopped"] != "final":
            return result("failed", reason="step_cap")
        order_view = evidence.get("lookup_order", {})
        if not order_view.get("visible"):
            return result("escalated", reason=order_view.get("reason", "missing_order_evidence"))

        # Money is computed after the read-only loop, from the actual order row.
        budget.add_tool(tool_cost())
        quote = compute_compensation(conn, order_view["order"])
        proposal = int(quote["amount_vnd"])
        trace.add("quote", {"amount_vnd": proposal})
        if proposal <= 0:
            return result("denied", reason=quote["reason"])

        # Pass the full entitlement: only the host subtracts earlier refunds.
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        if not outcome["ok"]:
            return result(
                "failed" if outcome["conflict"] else "denied",
                proposal, outcome["reason"],
            )
        return result("resolved", proposal)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    finally:
        conn.close()
