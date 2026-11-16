# Báo cáo cá nhân — Đỗ Hoàng Minh

## 1. Thông tin thành viên

- Họ tên: Đỗ Hoàng Minh
- MSSV: 2A202603507
- Email: 26ai.hoangd@vinuni.edu.vn
- GitHub: Mazzonthego

## 2. Phần việc phụ trách

- Shape C — **Orchestrator + handoff**, file `src/lab8/shapes/orchestrator.py`.
- Dựng handoff bằng `lab8.handoff.make_handoff`, chỉ cấp các tool đọc:
  `lookup_order`, `lookup_policy`, `compute_compensation`.
- Chạy investigator bằng `lab8.runtime.run_readonly_investigators`.
- Lấy quote từ investigator (không lấy từ nội dung ticket) rồi gọi
  `lab8.durability.issue_refund` với **quote đầy đủ**.
- Truyền `crash_at` vào `issue_refund`, không bắt `InjectedCrash`.
- Ghi trace chỉ gồm handoff đã sanitize và dữ liệu đã qua allowlist; không ghi
  `parent_secret`, header, ticket, nguyên claim row hoặc nguyên order row.
- Viết test riêng `src/tests/test_orchestrator_extra.py`.
- Chạy các kiểm tra CP2–CP5: 62 test orchestrator, test handoff secret, crash
  suite, benchmark và `check_submission`.

## 3. Đóng góp cụ thể

### 3.1. Commit chính

| Commit | Nội dung |
|---|---|
| `5439214` | Xử lý xung đột `TEAM.md`; thêm bản nháp `report/team/Person3.md` |
| `4de8972` | Viết `src/lab8/shapes/orchestrator.py`: handoff chỉ đọc, investigator, quote, `issue_refund`, trace sanitize |
| `9e77971` | Thêm `src/tests/test_orchestrator_extra.py` và bằng chứng `src/reports/benchmark.json`, `src/reports/crash.json` |
| `c3cb9b9` | Merge nhánh `feat/orchestrator` vào `main` (phần code orchestrator) |
| `05f3add` | Cập nhật runbook `report/team/Person3.md` với kết quả bước 3–4 |
| `94b0247` | Merge `feat/orchestrator` vào `main` (phần test và bằng chứng CP4–CP5) |

### 3.2. Quyết định kỹ thuật

1. **Handoff dùng allowlist, không tóm tắt LLM.** Chỉ cấp `lookup_order`,
   `lookup_policy`, `compute_compensation`; `facts={}`; `make_handoff` tự lọc field
   và từ chối tool ghi.

2. **Trace chỉ ghi dữ liệu đã sanitize.** Ghi `claim_id`, `found`, `has_order_id`,
   handoff, `order_visible`, `order_reason`, `policy_count`, quote
   amount/reason/clause_ids, kết quả `issue_refund`. Không ghi ticket, claim row,
   order row, SĐT, địa chỉ hay tên hàng. Mọi nhánh return đều có trace, kể cả
   `needs_info`, `escalated`, `denied`, `failed`.

3. **Luôn truyền quote đầy đủ cho `issue_refund`.** Orchestrator không tự trừ phần
   đã hoàn; host kiểm approval, trần theo đơn và idempotency. Nhờ vậy T13
   (`order_already_refunded`) và T14 đều đúng: quote 150.000, ledger ghi 120.000.

4. **Không tự deny khi quote > 0.** Approval hỏng hoặc đơn đã hoàn đủ thì vẫn phải
   gọi `issue_refund` để host ghi audit `policy_denied`; deny sớm sẽ thiếu audit và
   test fail.

5. **Crash phải lan truyền.** Truyền `crash_at` vào `issue_refund`; chỉ bắt
   `InjectedCrash` để ghi trace rồi `raise` lại. Nhờ vậy T12 kiểm được crash thật và
   lần chạy lại vẫn chỉ có một refund.

6. **Dùng `finish()` thay vì tự dựng `RunResult`.** `finish()` lấy `refund_effects`,
   `committed_audit_count` và budget từ ledger; tránh `result_ledger_mismatch` và
   `audit_count_mismatch`.

7. **Test riêng kiểm rủi ro của shape C.** Trace không chứa `CANARY_SECRET`,
   `parent_secret`, `raw_headers`; handoff không có `issue_refund`/`append_audit`;
   C-002 `denied` dù ticket sai số ngày; C-013 `denied`, proposal 35.000, có audit
   `policy_denied`, không ghi ledger; C-014 `resolved`, proposal 150.000, ledger
   120.000.

## 4. Bằng chứng

### 4.1. Kết quả test

| Lệnh | Kết quả |
|---|---|
| `python -m pytest -q -m student -o addopts= -k orchestrator` | `62 passed, 249 deselected` |
| `python -m pytest -q tests/test_handoff_secret.py tests/test_orchestrator_extra.py` | `8 passed` |
| `python -m pytest -q` | `63 passed, 248 deselected` |
| `python -m pytest -q -o addopts=` | `311 passed` |
| `python -m lab8.crash_test --count 20 --out reports/crash.json` | `crash_safety 20/20` |

### 4.2. Chạy tay ba claim đại diện

| Claim | Status | Proposal | Refund thực tế | Audit |
|---|---|---:|---:|---:|
| `C-001` | `resolved` | 35.000 | 35.000 | 1 |
| `C-013` | `denied` | 35.000 | 0 | 0 |
| `C-014` | `resolved` | 150.000 | 120.000 | 1 |

Run id tương ứng:

```text
R-orchestrator-C-001-s11
R-orchestrator-C-013-s11
R-orchestrator-C-014-s11
```

### 4.3. Benchmark

Kết quả dòng `orchestrator` trong `src/reports/benchmark.json`:

| Pass | Pass^5 | Variance | Min | Max | Cost/success | Steps |
|---:|---:|---:|---:|---:|---:|---:|
| 1.000 | 1.000 | 0.000000 | 1.000 | 1.000 | 47.30 | 5.36 |

So sánh nhanh:

- `workflow`: pass 1.000, cost/success 28.79, steps 4.43.
- `single`: pass 1.000, cost/success 47.31, steps 9.07.
- `orchestrator`: pass 1.000, cost/success 47.30, steps 5.36.
- `swarm`: pass 0.986, pass^5 0.929, variance 0.000816.

### 4.4. `check_submission`

```text
== shapes ==
[ OK ] workflow: 12/12
[ OK ] single: 12/12
[ OK ] orchestrator: 12/12

== reports ==
[ OK ] benchmark.json: 4 shape x 14 claim x 5 seed
[ OK ] crash.json: 20/20

== docs ==
8 FAIL
```

8 FAIL nằm ở `report/team/decision_adr.md` và `report/team/research_card.md` vì
phần nội dung nhóm chưa điền. Đây không phải lỗi code, test hay bằng chứng.

### 4.5. Link commit

- [`4de8972` — implement orchestrator](https://github.com/lytrann236/K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents/commit/4de8972)
- [`9e77971` — test + CP4–CP5 evidence](https://github.com/lytrann236/K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents/commit/9e77971)
- [`94b0247` — merge vào main](https://github.com/lytrann236/K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents/commit/94b0247)

### 4.6. Ghi chú

Runbook chi tiết từng bước nằm ở `report/Person3.md` (bản local) và trên nhánh
`feat/orchestrator`. Trên `main`, `report/team/Person3.md` đã bị xóa bởi commit
`8750747` sau khi hợp nhất; code, test và bằng chứng của shape C không bị ảnh hưởng.

## 5. Công cụ AI đã dùng

- **Claude Code / OpenCode (trợ lý AI)**:
  - Đọc và tóm tắt `docs/business_rules.md`, `docs/contracts.md`,
    `lab8/handoff.py`, `lab8/runtime.py`, `lab8/durability.py`.
  - Gợi ý khung `orchestrator.py`, cách dựng handoff, cách ghi trace an toàn.
  - Gợi ý và soạn `src/tests/test_orchestrator_extra.py`.
  - Chạy `pytest`, `lab8.crash_test`, `lab8.benchmark`, `lab8.check_submission`
    và phân tích output lỗi.
- **Cách tự kiểm tra kết quả AI:**
  - Không tin ngay code gợi ý; đọc lại từng nhánh return và đối chiếu với
    `docs/contracts.md`.
  - Chạy lại toàn bộ test trên máy, không dùng số liệu AI tự nghĩ ra.
  - Mở file trace JSON và kiểm tra không có `CANARY_SECRET`, `parent_secret`,
    `raw_headers`, ticket hoặc order row.
  - Đối chiếu `proposal_amount`, `refund_effects`, `committed_audit_count` với
    ledger SQLite thật.
  - Chỉ ghi run id, commit hash và số liệu benchmark lấy từ output thực tế của
    `lab8.benchmark` / `lab8.crash_test`.

## 6. Tự đánh giá

**Điểm mạnh:**

- Hoàn thành shape C đúng contract: handoff chỉ đọc, investigator tách quyền ghi,
  host là nơi duy nhất ghi refund.
- Trace sạch, không lộ secret/PII; đã kiểm bằng test riêng và bằng mắt.
- Xử lý đúng T11/T12 (idempotency, crash/resume), T13/T14 (trần theo đơn,
  quote đầy đủ) và T07 (approval hỏng vẫn có audit `policy_denied`).
- Kết quả đo được: 62/62 test orchestrator, 311 test toàn bộ, crash 20/20,
  benchmark pass 1.000 và pass^5 1.000.

**Hạn chế:**

- `check_submission` còn 8 FAIL vì `decision_adr.md` và `research_card.md` chưa
  điền nội dung; cần hoàn thiện ở CP5.
- Chưa chạy self-check trên bộ hidden `student_drop/`.
- Orchestrator tốn nhiều tool call hơn workflow (cost/success 47.30 so với 28.79),
  có thể tối ưu bằng cách bỏ bớt tool không cần thiết sau khi đo lại.
- Phần báo cáo nhóm và ADR cần các thành viên khác phối hợp để thống nhất shape
  chọn và số liệu cuối.

**Tự chấm:** 8.5/10 — phần code, test và bằng chứng của shape C hoàn thành tốt;
phần tài liệu/nhóm còn phụ thuộc nội dung ADR, research card và báo cáo chung.
