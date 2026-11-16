# Team

## Thông tin nhóm

- Tên nhóm: HustNeu
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/lytrann236/K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents, `main`, (điền ở CP5)

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Trần Thị Lý | 2A202603404 | | lytrann236 | Workflow + integration |
|   2 | <Họ tên> | <MSSV> | | <github> | Single agent |
|   3 | <Họ tên> | <MSSV> | | <github> | Orchestrator + handoff |
|   4 | <Họ tên> | <MSSV> | | <github> | Ledger/crash + evaluation/report |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Trần Thị Lý | Workflow + integration | 02bd691 | `src/tests/test_workflow_extra.py` |
| <Họ tên> | Single agent | <commit> | <file test> |
| <Họ tên> | Orchestrator + handoff | <commit> | <file test> |
| <Họ tên> | Ledger/crash + evaluation/report | <commit> | <file test> |

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

## <MSSV_HoTen người 2>

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-

## <MSSV_HoTen người 3>

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-

## <MSSV_HoTen người 4>

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-