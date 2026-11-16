# Person3 — Orchestrator và handoff

## 1. Phần việc phụ trách

- Viết `src/lab8/shapes/orchestrator.py` (shape C):
  - Dựng handoff bằng `lab8.handoff.make_handoff`, chỉ cấp tool đọc.
  - Chạy investigator bằng `lab8.runtime.run_readonly_investigators`.
  - Lấy quote từ investigator rồi gọi `lab8.durability.issue_refund`.
  - Trace chỉ ghi handoff đã sanitize và dữ liệu đã qua allowlist.
- Không đưa `parent_secret`, raw header, ticket, nguyên claim row hoặc nguyên order row vào handoff/trace.
- Tự kiểm:
  - `python -m pytest -q -m student -o addopts= -k orchestrator` → `62 passed`.
  - `python -m pytest -q tests/test_handoff_secret.py` → `3 passed`.
  - Tạo thêm `src/tests/test_orchestrator_extra.py`, ví dụ kiểm trace không chứa `CANARY_SECRET`.

## 2. Ba điểm cần sửa so với bản nháp trước

1. File cần viết là `src/lab8/shapes/orchestrator.py`, **không phải** `lab8/orchestrator.py`.
2. `-k orchestrator` là **62 test của riêng shape orchestrator** (12 claim × 5 seed + T11 + T12), không phải toàn bộ test.
3. `src/tests/test_orchestrator_extra.py` **chưa tồn tại**, phải tự tạo.

## 3. Trạng thái repo tại thời điểm kiểm tra

| Lệnh | Kết quả hiện tại |
|---|---|
| `python -m lab8.smoke` | `lab8.smoke pass` |
| `python -m pytest -q` | `58 passed, 248 deselected` |
| `python -m pytest -q tests/test_handoff_secret.py` | `3 passed` |
| `python -m pytest -q -m student -o addopts= -k orchestrator` | **`62 failed`** vì `orchestrator.py` còn stub |

---

## 4. Nhật ký thực hiện

### 2026-11-16 — Bước 1: Chạy baseline

- Trạng thái: **đã chạy xong**.
- Kết quả thực tế: `62 failed, 244 passed, 3 warnings in 37.86s`.
- Diễn giải:
  - 62 failed là toàn bộ test của shape `orchestrator` (file còn stub).
  - 244 passed gồm host gate và test của `swarm`, `workflow`, `single` (workflow/single đã có người làm).
- Việc cần làm tiếp: viết `src/lab8/shapes/orchestrator.py` để chuyển 62 failed thành 62 passed.

### 2026-11-16 — Bước 2: Tạo nhánh và xử lý `TEAM.md`

- `git status` trước khi làm:
  - Đang ở nhánh `main`, up to date với `origin/main`.
  - `report/team/Person3.md` đang staged.
  - `TEAM.md` đang xung đột (`both modified`).
  - `plan.txt` untracked.
- Đã chạy:
  - `git switch -c feature/person3-orchestrator` → tạo nhánh thành công.
  - `git add TEAM.md`
  - `git commit -m "merge: resolve TEAM.md conflict"` → commit `5439214`.
- Kết quả commit: `2 files changed, 29 insertions(+)`, tạo `report/team/Person3.md`.
- Lưu ý: bản `Person3.md` trong commit `5439214` là bản nháp ngắn; bản runbook đầy đủ hiện vẫn là thay đổi chưa commit. Cần `git add report/team/Person3.md` và commit tiếp.

### 2026-11-16 — Bước 3: Đọc contract và mã nguồn liên quan

- Trạng thái: **đã đọc xong**.
- Các file đã đọc:
  - `docs/business_rules.md`: trễ ≥ 3 ngày hoàn phí ship; damage đã verify hoàn theo DMG-04; chọn số lớn hơn; T13/T14 tính theo trần của đơn; không lấy order id từ ticket.
  - `docs/contracts.md`: 5 status hợp lệ; `proposal_amount` là quote đầy đủ; trace phải có `run_id` và `events`, ghi ở mọi nhánh return.
  - `src/lab8/handoff.py`: `ALLOWED_FIELDS`, `READONLY_TOOLS`, `make_handoff` tự lọc field và từ chối tool ghi/secret.
  - `src/lab8/runtime.py`: `run_readonly_investigators` trả `claim_view` + `tools`; chỉ chạy tool có trong handoff.
  - `src/lab8/durability.py`: `issue_refund` là nơi duy nhất ghi ledger, tự trừ phần đã hoàn, idempotency key `refund:{claim_id}`.
- Kết luận rút ra:
  - Orchestrator chỉ điều phối; investigator chỉ đọc; host (`issue_refund`) mới ghi tiền.
  - Không log ticket, claim row, order row; chỉ log handoff đã sanitize và field allowlist.
  - Quote > 0 nhưng host từ chối vẫn phải gọi `issue_refund` để có audit `policy_denied`.

### 2026-11-16 — Bước 4: Viết `src/lab8/shapes/orchestrator.py`

- Trạng thái: **đã viết xong**.
- Nội dung chính:
  - `get_claim_view` → `failed` nếu không có claim, `needs_info` nếu thiếu `order_id`.
  - `make_handoff` với tool đọc: `lookup_order`, `lookup_policy`, `compute_compensation`.
  - `run_readonly_investigators` chạy investigator, lấy `order_view` và `quote`.
  - Order không visible → `escalated`.
  - Quote ≤ 0 → `denied`, không gọi `issue_refund`.
  - Quote > 0 → gọi `issue_refund` với quote đầy đủ; truyền `crash_at`; không bắt `InjectedCrash`.
  - Mọi return dùng `finish()`; trace chỉ ghi handoff sanitize, claim id, trạng thái order, quote amount/reason/clause ids.
- Kết quả kiểm tra:
  - `python -m pytest -q -m student -o addopts= -k orchestrator` → **`62 passed, 244 deselected`**.
  - `python -m pytest -q tests/test_handoff_secret.py` → **`3 passed`**.
  - `python -m pytest -q` → **`58 passed, 248 deselected`**.
  - `python -m pytest -q -o addopts=` (toàn bộ 306 test) → **`306 passed`**.
  - Chạy tay `C-001`: `status = resolved`, `proposal_amount = 35000`, `refund_effects` có 1 dòng 35000, trace `R-orchestrator-C-001-s11.json`.

---

## Bước 0 — Mở terminal đúng thư mục và kích hoạt venv

```powershell
cd E:\Vinuni\K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents\src
.\.venv\Scripts\Activate.ps1
python -m lab8.smoke
```

Kỳ vọng:

```text
lab8.smoke pass
python 3.13.x | Windows AMD64
manifest 1.1 | MockLLM seeded | swarm C-001 refund 35000 | trace clean
```

Nếu PowerShell chặn activate:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Hoặc không cần activate, dùng trực tiếp:

```powershell
.\.venv\Scripts\python.exe -m lab8.smoke
```

---

## Bước 1 — Chạy baseline trước khi sửa

```powershell
python -m pytest -q
python -m pytest -q -m student -o addopts= -k orchestrator
```

Kỳ vọng:

- Host gate: `58 passed, 248 deselected`.
- Orchestrator: `62 failed` — baseline chứng minh shape chưa làm.

Ghi lại 2 con số này để cuối buổi so sánh.

---

## Bước 2 — Tạo nhánh riêng

```powershell
git status
git switch -c feature/person3-orchestrator
```

Lưu ý: repo có thể đang có xung đột `UU TEAM.md`. Nếu git không cho tạo nhánh, xử lý `TEAM.md` trước:

```powershell
git status
# Mở TEAM.md, giữ phần đúng, xóa các marker <<<<<<< ======= >>>>>>>
git add TEAM.md
git commit -m "merge: resolve TEAM.md conflict"
```

Sau đó mới tạo nhánh.

---

## Bước 3 — Đọc 5 file để hiểu nghiệp vụ

| File | Cần lấy gì |
|---|---|
| `docs/business_rules.md` | Khi nào refund, khi nào deny, T13/T14 xử lý theo đơn |
| `docs/contracts.md` | `RunResult.status`, `proposal_amount`, trace contract |
| `src/lab8/handoff.py` | Allowlist, chỉ tool đọc, `make_handoff` |
| `src/lab8/runtime.py` | `run_readonly_investigators` trả gì |
| `src/lab8/durability.py` | `issue_refund`, `crash_at`, idempotency |

Tóm tắt nghiệp vụ:

- Tiền **không phải** do LLM quyết. LLM chỉ viết câu trả lời.
- `compute_compensation` tính quote từ order và policy hiện hành.
- Orchestrator **không tự trừ** tiền đã hoàn trước đó. Nó đưa **quote đầy đủ** cho `issue_refund`; host tự trừ.
- Nếu quote > 0 nhưng host từ chối, vẫn phải gọi `issue_refund` rồi trả `denied` với `proposal_amount` = quote đầy đủ. Không được tự deny sớm, vì như vậy thiếu audit `policy_denied`.
- Handoff chỉ được chứa field trong allowlist. Không đưa `parent_secret`, header, ticket, nguyên claim row vào trace.
- Trace phải được ghi ở **mọi nhánh return**, kể cả `needs_info`, `escalated`, `denied`, `failed`.

---

## Bước 4 — Viết `src/lab8/shapes/orchestrator.py`

Luồng code đúng thứ tự:

1. `connect(store_path)`.
2. Tạo `Budget()` và `Trace(make_run_id("orchestrator", claim_id, seed))`.
3. `get_claim_view(conn, claim_id)`.
4. Không tìm thấy claim → `failed`, reason `unknown_claim`.
5. Không có `order_id` → `needs_info`, không ghi ledger.
6. Tạo handoff bằng `make_handoff(...)` với tool chỉ đọc.
7. Ghi trace **handoff đã sanitize**.
8. `run_readonly_investigators(...)`.
9. Lấy `lookup_order` và `compute_compensation` từ kết quả investigator.
10. Order không visible → `escalated`.
11. Quote ≤ 0 → `denied`, proposal = 0, không gọi `issue_refund`.
12. Quote > 0 → gọi `issue_refund(conn, claim_id, proposal, crash_at=crash_at)`.
13. `InjectedCrash` → ghi trace crash, `trace.write()`, rồi `raise` (không bắt).
14. Kết quả host:
    - `ok=True` → `resolved`.
    - `conflict=True` → `failed`.
    - còn lại → `denied`.
15. Mọi return dùng `finish(...)` của `lab8.shapes.common`.

Khung code tham khảo:

```python
"""Shape C — orchestrator plus read-only investigators."""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "orchestrator"


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, amount: int, reason: str | None) -> RunResult:
        trace.add(
            "decision",
            {"status": status, "proposal_amount": amount, "reason": reason},
        )
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

    # 1. Claim view allowlist — không log ticket.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    trace.add(
        "claim",
        {
            "claim_id": claim_id,
            "found": claim["found"],
            "has_order_id": bool(claim.get("order_id")),
        },
    )

    if not claim["found"]:
        return done("failed", 0, "unknown_claim")

    if not claim.get("order_id"):
        return done("needs_info", 0, "missing_order_id")

    # 2. Handoff chỉ gồm field allowlist và tool đọc.
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},  # không đưa claim row / secret / header vào đây
        allowed_tools=[
            "lookup_order",
            "lookup_policy",
            "compute_compensation",
            # "lookup_refund_history",  # optional
        ],
    )
    trace.add("handoff", safe_dump(handoff))

    # 3. Investigator chỉ chạy tool đọc.
    investigated = run_readonly_investigators(
        conn,
        budget,
        handoff,
        principal_id=claim["principal_id"],
    )
    tools = investigated["tools"]
    order_view = tools.get("lookup_order", {})
    quote = tools.get("compute_compensation", {})

    trace.add(
        "investigator",
        {
            "order_visible": bool(order_view.get("visible")),
            "order_reason": order_view.get("reason"),
            "policy_count": len(
                (tools.get("lookup_policy") or {}).get("policies") or []
            ),
        },
    )

    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return done("escalated", 0, order_view.get("reason"))

    # 4. Quote lấy từ investigator, không lấy từ ticket.
    proposal = int(quote.get("amount_vnd") or 0)
    trace.add(
        "quote",
        {
            "amount_vnd": proposal,
            "reason": quote.get("reason"),
            "clause_ids": quote.get("clause_ids", []),
        },
    )
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return done("denied", 0, quote.get("reason"))

    # 5. Host là nơi duy nhất ghi tiền. Luôn truyền quote đầy đủ.
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise  # không được nuốt crash, T12 cần thấy crash thật

    trace.add("issue_refund", {"ok": outcome["ok"], "reason": outcome["reason"]})

    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        return done(status, proposal, outcome["reason"])

    return done("resolved", proposal, None)
```

Năm điều tuyệt đối không làm:

- Không `SELECT * FROM claims` rồi log nguyên row.
- Không log `ticket`.
- Không log nguyên `order` row.
- Không tự trừ tiền đã hoàn trước khi gọi `issue_refund`.
- Không bắt `InjectedCrash`.

---

## Bước 5 — Chạy thử một claim

```powershell
python -m lab8.run --shape orchestrator --claim-id C-001 --seed 11 --db data/run_orch.sqlite
```

Kỳ vọng: JSON có `"status": "resolved"`, `"proposal_amount": 35000`, `refund_effects` có 1 dòng.

Chạy thêm T13 và T14:

```powershell
python -m lab8.run --shape orchestrator --claim-id C-013 --seed 11 --db data/run_orch_t13.sqlite
python -m lab8.run --shape orchestrator --claim-id C-014 --seed 11 --db data/run_orch_t14.sqlite
```

Kỳ vọng:

- `C-013`: `denied`, `proposal_amount = 35000`, không có refund.
- `C-014`: `resolved`, `proposal_amount = 150000`, refund thực tế `120000`.

---

## Bước 6 — Chạy test handoff secret

```powershell
python -m pytest -q tests/test_handoff_secret.py
```

Kỳ vọng:

```text
3 passed
```

File này kiểm 3 việc:

- `sanitize` bỏ `parent_secret`, `raw_headers`.
- Worker không được nhận `issue_refund`.
- `get_claim_view` và ReAct observation không chứa `CANARY_SECRET_`.

---

## Bước 7 — Tạo `src/tests/test_orchestrator_extra.py`

File này chưa có. Đây là test riêng, nên kiểm các điểm sau:

Ví dụ:

```python
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
        e["payload"] for e in body["events"] if e["kind"] == "handoff"
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
    # C-002: ticket nói 5 ngày, order row nói 2 ngày.
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
```

Chạy:

```powershell
python -m pytest -q tests/test_orchestrator_extra.py
```

Kỳ vọng: tất cả pass.

Không gắn `@pytest.mark.student` cho file này, nếu không lệnh `-m student -k orchestrator` sẽ đếm thêm test và ra hơn 62.

---

## Bước 8 — Chạy đúng 62 test orchestrator

```powershell
python -m pytest -q -m student -o addopts= -k orchestrator
```

Kỳ vọng:

```text
62 passed
```

Nếu muốn chắc chắn chỉ chạy ma trận public:

```powershell
python -m pytest -q -m student -o addopts= tests/test_public_matrix.py -k orchestrator
```

---

## Bước 9 — Chạy lại toàn bộ host gate

```powershell
python -m pytest -q
```

Kỳ vọng: vẫn xanh, không có `failed`. Số passed có thể tăng do test extra.

Chạy crash suite nếu nhóm chuẩn bị CP4:

```powershell
python -m lab8.crash_test --count 20 --out reports/crash.json
```

Kỳ vọng: `crash_safety = 20/20`.

Chạy benchmark nếu cần số liệu CP5:

```powershell
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
```

Kiểm tra bài nộp:

```powershell
python -m lab8.check_submission
```

Kỳ vọng: `0 FAIL`.

---

## Bước 10 — Commit, bằng chứng, báo cáo

```powershell
git add src/lab8/shapes/orchestrator.py src/tests/test_orchestrator_extra.py
git commit -m "feat(orchestrator): add read-only handoff and host-issued refund"
git push -u origin feature/person3-orchestrator
```

Cập nhật phần Bằng chứng bằng kết quả thật:

```text
- python -m pytest -q -m student -o addopts= -k orchestrator -> 62 passed
- python -m pytest -q tests/test_handoff_secret.py -> 3 passed
- python -m pytest -q -> ... passed
- python -m pytest -q tests/test_orchestrator_extra.py -> ... passed
- commit: <hash>
```

---

## Bảng tra nhanh khi test fail

| Lỗi | Nguyên nhân thường gặp |
|---|---|
| `status failed != resolved` | Còn stub hoặc code ném exception |
| `proposal_mismatch` | T13/T14 không truyền quote đầy đủ |
| `missing_policy_denied` | Tự deny trước khi gọi `issue_refund` |
| `result_ledger_mismatch` | Tự tạo `RunResult` thay vì dùng `finish()` |
| `forbidden_substring:CANARY_SECRET...` | Log nguyên claim row hoặc ticket |
| `forbidden_substring:090...` | Log nguyên order row |
| `missing_trace` | Có nhánh return không ghi trace |
| `stale_trace` | Dùng lại trace cũ / không tạo `Trace` mới |
| `trace_run_id_mismatch` | `Trace.run_id` khác `make_run_id(...)` |
| `crash did not fire` | Không truyền `crash_at` hoặc bắt `InjectedCrash` |
| `unexpected_ledger_rows` | Tự ghi ledger, không qua `issue_refund` |

---

## Checklist tổng

- [x] `python -m lab8.smoke` → `lab8.smoke pass`
- [x] Baseline: `62 failed, 244 passed` (62 fail là orchestrator)
- [x] Tạo nhánh `feature/person3-orchestrator`
- [x] Commit bản runbook `report/team/Person3.md`
- [x] Viết `src/lab8/shapes/orchestrator.py`
- [ ] Chạy thử `C-001`, `C-013`, `C-014`
- [x] `python -m pytest -q tests/test_handoff_secret.py` → `3 passed`
- [ ] Tạo `src/tests/test_orchestrator_extra.py`
- [x] `python -m pytest -q -m student -o addopts= -k orchestrator` → `62 passed`
- [x] `python -m pytest -q` → không có `failed`
- [ ] Crash suite / benchmark / `check_submission` nếu làm CP4–CP5
- [ ] Commit, push nhánh, cập nhật báo cáo và `TEAM.md`
