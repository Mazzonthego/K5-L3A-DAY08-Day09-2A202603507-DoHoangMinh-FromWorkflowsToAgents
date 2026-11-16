# Báo cáo cá nhân — Nguyễn Thùy Dương

## 1. Thông tin thành viên

- Họ tên: Nguyễn Thùy Dương
- MSSV: 2A202603388
- Email: 26ai.duongnt8@vinuni.edu.vn
- GitHub: NTD-DUONG
- Nhóm: HustNeu — L3A.

## 2. Phần việc phụ trách

Phụ trách phần 4: tìm hiểu ledger, approval và crash recovery; bổ sung test policy; chạy đánh giá sau khi tích hợp ba shape; tổng hợp bằng chứng cho báo cáo nhóm và quyết định kiến trúc. Không sửa các file thước đo `durability.py`, `policy.py`, config hoặc dữ liệu public.

## 3. Đóng góp cụ thể

- Tìm hiểu cơ chế approval gắn với đúng claim, trần hoàn tiền theo đơn và khóa idempotency `refund:{claim_id}`. Chạy demo `buggy_workflow`, quan sát kết quả hai dòng refund để hiểu vì sao checkpoint đơn lẻ không chống ghi trùng.
- Bổ sung `src/tests/test_policy_extra.py` với trợ lý AI: kiểm tra từ chối lặp lại khi mượn approval của claim khác; từ chối lặp lại khi đơn đã hoàn đủ; crash sau khi commit effect rồi mở kết nối mới để retry. Test kiểm tra cả ledger và audit, không chỉ dựa vào kết quả hàm.
- Ở ca khôi phục, truyền quote đầy đủ 150.000 VND; sau khoản hoàn lịch sử 30.000 VND, host ghi thêm 120.000 VND. Retry ba lần vẫn chỉ có một refund và một audit committed cho claim.
- Tích hợp `origin/main` vào nhánh `git-checkout--b-feat/crash-eval`, chạy test host, ma trận student, crash suite và benchmark bốn shape trên cùng 14 claim và năm seed.
- Chuẩn bị bản nháp ADR và báo cáo nhóm từ số liệu thực tế. Bằng chứng public ủng hộ chọn workflow vì đạt cùng pass rate với single/orchestrator và có cost/success thấp hơn. Chưa suy diễn kết quả này thành kết quả hidden.

## 4. Bằng chứng

- Commit test: [`e59a0a6`](https://github.com/lytrann236/K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents/commit/e59a0a6).
- Commit tích hợp được dùng khi đánh giá: `7f74a30`.
- Ba test bổ sung:
  - `test_borrowed_approval_stays_denied_across_retries`.
  - `test_fully_refunded_order_stays_denied_across_retries`.
  - `test_crash_then_reconnect_and_replay_commits_only_once`.
- Tự chạy `python -m pytest -q tests/test_policy_extra.py` bằng Python trong `.venv`: **3 passed in 0.20s**.
- Sau tích hợp, trợ lý chạy test host: **66 passed, 248 deselected**; ma trận student: **248 passed, 66 deselected**.
- `src/reports/crash.json`: **20/20**. Đây là crash suite host, không thay thế mọi kiểm tra crash ở từng shape.
- `src/reports/benchmark.json`: mỗi shape có 70 trial; seed `11,22,33,44,55`; run dẫn chứng `R-workflow-C-001-s11`.

| Shape | Pass rate | Pass^5 | Cost/success mô phỏng (VND) |
| --- | ---: | ---: | ---: |
| Workflow | 1,000000 | 1,000000 | 28,79 |
| Single | 1,000000 | 1,000000 | 47,31 |
| Orchestrator | 1,000000 | 1,000000 | 47,30 |
| Swarm | 0,985714 | 0,928571 | 49,57 |

Chi phí là mô phỏng, không phải hóa đơn API. Latency là `unavailable`. Các báo cáo JSON do công cụ của lab sinh, không sửa tay.

## 5. Công cụ AI đã dùng

Sử dụng ChatGPT/Codex để giải thích đề bài, hướng dẫn cài môi trường và Git, hỗ trợ viết test, thực thi đánh giá và soạn báo cáo. Code test và phần báo cáo được tạo với sự hỗ trợ của AI; không coi toàn bộ nội dung là tự viết độc lập.

Tôi tự chạy smoke và test trên PowerShell, xác nhận smoke pass, 11 test host liên quan ledger/policy pass và ba test bổ sung pass. Những kết quả đánh giá sau tích hợp được trợ lý thực thi và tổng hợp từ output cùng file report. Khi giải thích giải pháp cần đối chiếu test với code host: approval phải đúng claim, quote phải truyền đầy đủ và retry phải giữ một effect cùng một audit.

## 6. Tự đánh giá

Qua phần việc được giao, em hiểu rõ hơn vì sao cần dùng ledger để tránh hoàn tiền trùng khi chạy lại hoặc gặp sự cố. Em cũng phân biệt được quote ban đầu với số tiền thực tế được hoàn, đồng thời hiểu rằng việc tính tiền và kiểm tra approval phải do code xử lý. Các test bổ sung đều chạy thành công, giúp em có cơ sở kiểm tra phần mình phụ trách.

Em đã hoàn thành phần kiểm thử, đánh giá public và phối hợp hoàn thiện báo cáo. Tuy nhiên, em vẫn cần luyện giải thích luồng xử lý và đọc trace để tự tin hơn khi trình bày. Nhóm chưa có kết quả hidden chính thức nên em chưa thể khẳng định hệ thống xử lý đúng mọi trường hợp chỉ dựa vào kết quả public.
