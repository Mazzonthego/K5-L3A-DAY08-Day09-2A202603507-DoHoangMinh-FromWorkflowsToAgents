# Báo cáo cá nhân — Trần Việt Tiến

## 1. Thông tin thành viên

- Họ tên: Trần Việt Tiến
- MSSV: 2A202603394
- Email: 
- Repo nhóm: https://github.com/lytrann236/K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents

## 2. Phần việc phụ trách

Phụ trách shape single agent trong `src/lab8/shapes/single.py`: điều tra claim bằng vòng ReAct, tính bồi thường và chuyển yêu cầu ghi refund qua host.

## 3. Đóng góp cụ thể

- Hoàn thiện `run_claim` với `run_react(max_steps=8)`, chỉ cho phép gọi tool đọc và ghi nhận chi phí qua `Budget`.
- Tính quote bằng `compute_compensation` từ order trong database; không dùng lời khách trong ticket để quyết định tiền.
- Truyền quote đầy đủ vào `issue_refund`, để host kiểm approval và trừ khoản đã hoàn trước đó.
- Truyền `crash_at`, cho lỗi crash truyền ra ngoài để kiểm tra resume; đóng kết nối database trong `finally`.
- Trả `RunResult` bằng `finish()`, ghi trace mà không đưa nội dung ticket hoặc dữ liệu nhạy cảm vào log.
- Thêm test cá nhân `tests/test_single_extra.py::test_single_uses_order_delay_despite_ticket_injection`: ticket nói trễ 99 ngày và yêu cầu bỏ policy, nhưng order chỉ trễ 2 ngày nên không hoàn tiền; kiểm tra cả kết quả và ledger/audit thực tế.
- Commit phần single và test: `87dd8b8` — `feat: implement bounded single-agent claim handling with regression test`.

## 4. Bằng chứng

Kết quả kiểm tra trong phiên làm việc:

- Test single: **62 passed**.
- Test cá nhân: **1 passed**.
- Test host (gồm test cá nhân): **55 passed**.
- Kiểm tra bổ sung bằng script tạm: ticket nói sai số ngày trễ, prompt injection, trace không lộ secret, claim không tồn tại, giới hạn bước và resume ở ba thời điểm crash đều đạt.
- Run id minh họa theo contract: `R-single-C-002-s55`.

Lệnh tái lập, chạy trong `src/` sau khi kích hoạt môi trường ảo:

```bash
python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"
python -m pytest -q tests/test_single_extra.py
python -m pytest -q
```

## 5. Công cụ AI đã dùng

- Công cụ: Codex.
- Phạm vi hỗ trợ: viết và chỉnh sửa code single
- Kiểm chứng: đối chiếu luật nghiệp vụ, kết quả 62 test single và 55 test host (gồm 1 test cá nhân); kiểm tra thêm injection, trace và crash/resume. Không sử dụng số liệu tự tạo hoặc kết luận vượt quá phạm vi test.

## 6. Tự đánh giá

Phần single đã qua test public và giữ bộ test host xanh. Điểm cần nắm vững là tiền do code tính, host là nơi ghi refund và quote đầy đủ khác số tiền thực trả. Chưa kiểm chứng trên bộ hidden, chưa điền bảng đóng góp trong `TEAM.md`. MockLLM chỉ mô phỏng lời gọi model; adapter Python chọn tool theo observation, chưa sử dụng đầu ra model để quyết định tool. Kết quả không đại diện cho agent dùng model thật.
