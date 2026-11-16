"""Additional host checks for repeated denials and restart after a crash."""

import json

import pytest

from lab8.db import connect
from lab8.durability import (
    InjectedCrash,
    committed_audit_count,
    get_refund,
    issue_refund,
)
from lab8.policy import order_refunded_vnd


def denial_reasons(conn, claim_id):
    rows = conn.execute(
        "SELECT details_json FROM audit_events "
        "WHERE claim_id = ? AND event_type = 'policy_denied'",
        (claim_id,),
    ).fetchall()
    return [json.loads(row["details_json"])["reason"] for row in rows]


def test_borrowed_approval_stays_denied_across_retries(public_db):
    conn = connect(public_db)
    try:
        # A-001 belongs to C-001, even though its amount fits this request.
        conn.execute(
            "UPDATE claims SET approval_id = 'A-001' WHERE claim_id = 'C-010'"
        )
        conn.commit()
        total_before = order_refunded_vnd(conn, "O-107")

        for _ in range(3):
            result = issue_refund(conn, "C-010", 35000)
            assert result["ok"] is False
            assert result["reason"] == "approval_claim_mismatch"

        assert get_refund(conn, "C-010") is None
        assert committed_audit_count(conn, "C-010") == 0
        assert order_refunded_vnd(conn, "O-107") == total_before
        assert denial_reasons(conn, "C-010") == ["approval_claim_mismatch"]
    finally:
        conn.close()


def test_fully_refunded_order_stays_denied_across_retries(public_db):
    conn = connect(public_db)
    try:
        # O-505 already has a historical shipping refund in the public fixture.
        total_before = order_refunded_vnd(conn, "O-505")
        assert total_before == 35000
        for _ in range(3):
            result = issue_refund(conn, "C-013", 35000)
            assert result["ok"] is False
            assert result["reason"] == "order_already_refunded"

        assert order_refunded_vnd(conn, "O-505") == total_before
        assert get_refund(conn, "C-013") is None
        assert committed_audit_count(conn, "C-013") == 0
        assert denial_reasons(conn, "C-013") == ["order_already_refunded"]
    finally:
        conn.close()


def test_crash_then_reconnect_and_replay_commits_only_once(public_db):
    conn = connect(public_db)
    try:
        with pytest.raises(InjectedCrash, match="after_effect_before_checkpoint"):
            issue_refund(
                conn, "C-014", 150000,
                crash_at="after_effect_before_checkpoint",
            )
        assert conn.execute(
            "SELECT 1 FROM checkpoints WHERE claim_id = 'C-014'"
        ).fetchone() is None
    finally:
        conn.close()

    # A fresh connection models restarting the process after the committed effect.
    conn = connect(public_db)
    try:
        for _ in range(3):
            result = issue_refund(conn, "C-014", 150000)
            assert result["ok"] is True
            assert result["reason"] == "idempotent_replay"

        effect = get_refund(conn, "C-014")
        assert effect["amount_vnd"] == 120000
        assert effect["idempotency_key"] == "refund:C-014"
        assert conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-014'"
        ).fetchone()["n"] == 1
        assert committed_audit_count(conn, "C-014") == 1
        assert order_refunded_vnd(conn, "O-515") == 150000
        checkpoint = conn.execute(
            "SELECT result_json FROM checkpoints "
            "WHERE claim_id = 'C-014' AND step = 'issue_refund'"
        ).fetchone()
        assert json.loads(checkpoint["result_json"])["amount_vnd"] == 120000
    finally:
        conn.close()
