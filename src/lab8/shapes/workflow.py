"""Shape A — deterministic workflow.

Fixed Python steps. Money is computed in code by `compute_compensation`;
MockLLM is only used to draft the reply text. The host
(`durability.issue_refund`) checks approval, per-order cap and idempotency.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "workflow"


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        budget = Budget()
        trace = Trace(make_run_id(SHAPE, claim_id, seed))

        def done(status: str, amount: int, reason: str | None) -> RunResult:
            trace.add("decision", {"status": status, "proposal_amount": amount, "reason": reason})
            return finish(
                conn,
                shape=SHAPE,
                claim_id=claim_id,
                seed=seed,
                status=status,
                proposal_amount=amount,
                budget=budget,
                trace=trace,
                error_reason=reason,
            )

        # 1. Read the claim through the allowlisted view (never SELECT *).
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        if not claim["found"]:
            return done("failed", 0, "unknown_claim")
        # Ticket text is user data: we do not parse numbers or order ids from it.
        trace.add("claim", {"claim_id": claim_id, "has_order_id": bool(claim["order_id"])})

        # 2. Missing order_id -> needs_info, no ledger write.
        if not claim["order_id"]:
            complete(budget, seed=seed, purpose="draft", prompt="needs_info")
            return done("needs_info", 0, "missing_order_id")

        # 3. Order lookup (ownership checked by the tool). Not visible -> escalated.
        budget.add_tool(tool_cost())
        order_view = lookup_order(conn, claim["order_id"], claim["principal_id"])
        trace.add("lookup_order", {"visible": order_view["visible"], "reason": order_view["reason"]})
        if not order_view["visible"]:
            complete(budget, seed=seed, purpose="draft", prompt="escalated")
            return done("escalated", 0, order_view["reason"])

        # 4. Quote from the order row + current policy, in code.
        budget.add_tool(tool_cost())
        quote = compute_compensation(conn, order_view["order"])
        proposal = int(quote["amount_vnd"])
        trace.add("quote", quote)

        # 8. Model only drafts text; it never chooses or commits money.
        complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

        # 5. Quote 0 -> denied, do not call issue_refund.
        if proposal <= 0:
            return done("denied", 0, quote.get("reason"))

        # 6. Full quote to the host. Do not subtract earlier refunds ourselves.
        try:
            outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        except InjectedCrash:
            trace.add("crash", {"at": crash_at})
            trace.write()
            raise  # never swallow the injected crash (T12)
        trace.add("issue_refund", {"ok": outcome["ok"], "reason": outcome["reason"]})

        if not outcome["ok"]:
            status = "failed" if outcome["conflict"] else "denied"
            return done(status, proposal, outcome["reason"])

        # 7. Success: one ledger row, one refund_committed audit.
        return done("resolved", proposal, None)
    finally:
        conn.close()