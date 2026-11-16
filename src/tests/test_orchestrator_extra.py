"""Extra checks for shape C (orchestrator), written by Person 3."""

from __future__ import annotations

import json
from pathlib import Path

from lab8.db import connect
from lab8.durability import get_refund
from lab8.shapes.orchestrator import run_claim


def test_trace_has_no_secret_or_raw_context(public_db: Path) -> None:
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    body = Path(result.trace_path).read_text(encoding="utf-8")

    assert "CANARY_SECRET" not in body
    assert "parent_secret" not in body
    assert "raw_headers" not in body
    assert json.loads(body)["run_id"] == result.run_id
    assert result.status == "resolved"


def test_handoff_only_grants_read_tools(public_db: Path) -> None:
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    body = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    handoff = next(
        event["payload"] for event in body["events"] if event["kind"] == "handoff"
    )

    assert "issue_refund" not in handoff["allowed_tools"]
    assert "append_audit" not in handoff["allowed_tools"]
    assert set(handoff["allowed_tools"]) <= {
        "get_claim_view",
        "lookup_order",
        "lookup_policy",
        "lookup_refund_history",
        "get_clause",
        "compute_compensation",
    }


def test_ticket_lie_is_denied(public_db: Path) -> None:
    # C-002: the ticket says 5 days late, the order row says 2.
    for seed in (11, 22, 33, 44, 55):
        result = run_claim("C-002", seed=seed, store_path=str(public_db))
        assert result.status == "denied"
        assert result.proposal_amount == 0


def test_t13_denied_after_host_check(public_db: Path) -> None:
    result = run_claim("C-013", seed=11, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 35000

    conn = connect(public_db)
    try:
        assert get_refund(conn, "C-013") is None
        denied = conn.execute(
            "SELECT COUNT(*) AS n FROM audit_events "
            "WHERE claim_id = 'C-013' AND event_type = 'policy_denied'"
        ).fetchone()["n"]
    finally:
        conn.close()

    assert denied == 1


def test_t14_pays_only_the_difference(public_db: Path) -> None:
    result = run_claim("C-014", seed=11, store_path=str(public_db))
    assert result.status == "resolved"
    assert result.proposal_amount == 150000

    conn = connect(public_db)
    try:
        effect = get_refund(conn, "C-014")
    finally:
        conn.close()

    assert int(effect["amount_vnd"]) == 120000
