# Team

## Thông tin nhóm

- Tên nhóm: HustNeu
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/lytrann236/K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents, `main`, b74ef96

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Trần Thị Lý | 2A202603404 |26ai.lytt@vinuni.edu.vn | lytrann236 | Workflow + integration |
|   2 | Trần Việt Tiến | 2A202603394 |26ai.tientv@vinuni.edu.vn | chuvoicon-cpu | Single agent và kiểm thử single |
|   3 | Đỗ Hoàng Minh | 2A202603507 | 26ai.hoangd@vinuni.edu.vn | Mazzonthego | Orchestrator + handoff |
|   4 | Nguyễn Thùy Dương | 2A202603388 | 26ai.duongnt8@vinuni.edu.vn | NTD-DUONG | Ledger/crash + evaluation/report |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Trần Thị Lý | Workflow + integration | 02bd691 | `src/tests/test_workflow_extra.py` |
| Trần Việt Tiến | Single agent | `87dd8b8` | `src/tests/test_single_extra.py::test_single_uses_order_delay_despite_ticket_injection` |
| Đỗ Hoàng Minh | Orchestrator + handoff | `4de8972`, `9e77971` | `src/tests/test_orchestrator_extra.py` |
| Nguyễn Thùy Dương | Ledger/crash + evaluation/report | `e59a0a6` (test), `956a585` (research/ablation) | `src/tests/test_policy_extra.py` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603404_TranThiLy

### Phần việc phụ trách

- Shape A `workflow` (`src/lab8/shapes/workflow.py`), CP2 + CP3.
- Integration: tạo repo nhóm, review và merge PR, giữ `pytest -q` xanh trên `main`.

### Đóng góp cụ thể

- Viết workflow theo các bước cố định: đọc claim qua `get_claim_view`, thiếu order → `needs_info`, order không thấy → `escalated`, quote bằng `compute_compensation`, quote 0 → `denied`, quote > 0 → `durability.issue_refund` với quote đầy đủ.
- Truyền `crash_at` vào `issue_refund`, không bắt `InjectedCrash` (T12).
- Trace chỉ ghi field an toàn, không ghi ticket, claim row hay order row.
- Thêm 3 test: thiếu order_id không ghi ledger; bỏ qua số ngày trễ trong ticket trên cả 5 seed; trace không chứa `CANARY_SECRET`.

### Bằng chứng

- Commit `02bd691`, PR #1 (merge `d665216`).
- `python -m pytest -q -m student -o addopts= -k workflow` → 62 passed.
- `python -m pytest -q tests/test_workflow_extra.py` → 3 passed.
- Báo cáo: [2A202603404_TranThiLy.md](<report/team/2A202603404_TranThiLy.md>).
## 2A202603394_TranVietTien

### Phần việc phụ trách

- Hoàn thiện `src/lab8/shapes/single.py` và test cá nhân cho single agent.

### Đóng góp cụ thể

- Dùng `run_react(max_steps=8)` với tool chỉ đọc, ghi nhận lời gọi MockLLM và chi phí qua `Budget`.
- Tính quote từ order bằng `compute_compensation`; truyền quote đầy đủ vào `issue_refund` để host kiểm approval và giới hạn tiền hoàn.
- Xử lý crash/resume, trả kết quả bằng `finish()` và ghi trace không chứa ticket hay dữ liệu nhạy cảm.
- Thêm test ticket nói trễ 99 ngày và yêu cầu bỏ policy, nhưng order chỉ trễ 2 ngày: từ chối refund và không ghi ledger/audit committed.

### Bằng chứng

- Commit code và test: `87dd8b8`; báo cáo cá nhân: `c8be9f3`.
- Kết quả kiểm tra: 62 test single pass, 1 test cá nhân pass, 55 test host pass (đã gồm test cá nhân).
- Báo cáo: [2A202603394_TranVietTien.md](<report/team/2A202603394_TranVietTien.md>).

## 2A202603507_DoHoangMinh

### Phần việc phụ trách

- Shape C `orchestrator` (`src/lab8/shapes/orchestrator.py`), test riêng `src/tests/test_orchestrator_extra.py`

### Đóng góp cụ thể

- Dựng handoff bằng `make_handoff` với `facts={}` và ba tool đọc `lookup_order`, `lookup_policy`, `compute_compensation`; không đưa secret, header hay claim row qua ranh giới.
- Chạy investigator bằng `run_readonly_investigators`, lấy quote từ order chứ không từ ticket; truyền quote đầy đủ vào `issue_refund` để host tự trừ phần đã hoàn và kiểm trần (T13/T14).
- Không tự deny khi quote > 0: vẫn gọi `issue_refund` để host ghi audit `policy_denied`. Truyền `crash_at`, chỉ bắt `InjectedCrash` để ghi trace rồi `raise` (T12).
- Trace chỉ ghi handoff đã sanitize và field allowlist, mọi nhánh return đều có trace.
- Thêm 5 test: trace sạch, handoff chỉ tool đọc, C-002 `denied`, C-013 có audit `policy_denied`, C-014 chỉ hoàn 120.000.

### Bằng chứng

- Commit `4de8972` (code), `9e77971` (test + `benchmark.json`, `crash.json`); merge `94b0247`.
- `python -m pytest -q -m student -o addopts= -k orchestrator` → 62 passed; `tests/test_orchestrator_extra.py` → 5 passed; toàn bộ → 311 passed; crash `20/20`.
- Benchmark: pass 1.000, pass^5 1.000, cost/success 47.30.

## 2A202603388_NguyenThuyDuong

### Phần việc phụ trách

- Ledger/crash, kiểm thử policy và evaluation/report.

### Đóng góp cụ thể

- Bổ sung ba test retry/approval/order cap và khôi phục sau crash qua kết nối mới; chạy đánh giá sau tích hợp và tổng hợp báo cáo nhóm, ADR, báo cáo cá nhân.
- Hoàn thiện research card R2 theo MAST, thêm biến thể thí nghiệm chỉ tắt ticket-delay override của swarm và chạy benchmark đối chứng; không sửa host hoặc swarm tham chiếu.
- Rà 280 trace JSON với 54 giá trị nhạy cảm của fixture public; không phát hiện chuỗi nhạy cảm trong phạm vi kiểm tra.

### Bằng chứng

- Commit `e59a0a6`; test bổ sung 3 passed; sau tích hợp: host 66 passed, student 248 passed, crash 20/20.
- Commit research `956a585`; `src/reports/research_ablation.json`: swarm 69/70, biến thể 70/70; đây là kiểm chứng lỗi đã biết, không phải kết quả hidden.
- Rà soát tại commit `0be318c`: toàn bộ 314 test pass; `check_submission` đạt 0 FAIL, 0 WARN. Checker không thay thế rà soát hồ sơ thủ công hoặc chấm hidden.
- Báo cáo: [2A202603388_NguyenThuyDuong.md](report/team/2A202603388_NguyenThuyDuong.md).
