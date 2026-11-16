"""Extra checks for shape A (workflow), written by the group."""

from __future__ import annotations

import json
from pathlib import Path

from lab8.db import connect
from lab8.durability import get_refund
from lab8.shapes.workflow import run_claim


def test_missing_order_id_needs_info_and_no_ledger(public_db: Path) -> None:
    # C-004: ticket has no order id -> needs_info, nothing written.
    result = run_claim("C-004", seed=11, store_path=str(public_db))
    assert result.status == "needs_info"
    assert result.proposal_amount == 0
    conn = connect(public_db)
    try:
        assert get_refund(conn, "C-004") is None
    finally:
        conn.close()


def test_ticket_delay_is_ignored(public_db: Path) -> None:
    # C-002: ticket says 5 days late, order row says 2 -> denied on every seed.
    for seed in (11, 22, 33, 44, 55):
        result = run_claim("C-002", seed=seed, store_path=str(public_db))
        assert result.status == "denied"
        assert result.refund_effects == []


def test_trace_has_no_secret(public_db: Path) -> None:
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    body = Path(result.trace_path).read_text(encoding="utf-8")
    assert "CANARY_SECRET" not in body
    assert json.loads(body)["run_id"] == result.run_id