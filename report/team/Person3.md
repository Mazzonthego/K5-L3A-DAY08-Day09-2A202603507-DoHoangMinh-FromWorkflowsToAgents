# Person3.md

## Phần việc phụ trách
- Orchestrator: xây dựng lab8.handoff.make_handoff, chỉ cho phép tool đọc; chạy investigator bằng run_readonly_investigators; tính quote rồi gọi issue_refund.
- Handoff: đảm bảo chỉ truyền các field trong allowlist, không đưa parent_secret, header hay CANARY_SECRET vào trace.

## Đóng góp cụ thể
- Thêm/modify lab8/orchestrator.py:
  - Sử dụng lab8.handoff.make_handoff để tạo handoff từ claim tới investigator.
  - Kiểm tra trace không chứa CANARY_SECRET, CANARY_CLAIM, CANARY_POLICY, CANARY_CLAIM, CANARY_POLICY.
  - Gọi compute_compensation (hoặc tương đương) để tính quote, sau đó gọi durability.issue_refund.
  - Đảm bảo idempotency: không gọi refund nếu đã hoàn trong trace.
- Thêm/modify tests:
  - Kiểm thử orchestrator với pytest -k orchestrator (62 passed).
  - Kiểm thử trace không chứa secret bằng pytest -q tests/test_handoff_secret.py.
- Đảm bảo orchestrator và investigator chạy độc lập trên nhánh riêng, không chung code với shape khác.

## Bằng chứng
- Chạy `pytest -k orchestrator` trả về 62 passed.
- Chạy `pytest -q tests/test_handoff_secret.py` trả về 0 failed, trace không chứa CANARY_SECRET.
- Kiểm tra code tại lab8/orchestrator.py tuân thủ allowlist và không rò rỉ secret.