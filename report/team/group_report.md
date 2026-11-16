# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: HustNeu — L3A.
- Repo: https://github.com/lytrann236/K5-L3A-DAY08-HustNeu-FromWorkflowsToAgents.
- Commit code dùng để đánh giá: `7f74a30`, thống nhất với ADR hiện tại. Đây là commit tích hợp dùng để đo, chưa phải commit chốt toàn bộ hồ sơ.

| Thành viên | MSSV | Phần việc |
| --- | --- | --- |
| Trần Thị Lý | 2A202603404 | Workflow và integration |
| Trần Việt Tiến | 2A202603394 | Single agent và test single |
| Đỗ Hoàng Minh | 2A202603507 | Orchestrator, handoff và test orchestrator |
| Nguyễn Thùy Dương | 2A202603388 | Ledger, crash, test policy, evaluation và báo cáo |

## 2. Mục tiêu và cách tiếp cận

Nhóm xử lý cùng claim của LogiX-VN bằng ba shape tự triển khai và swarm tham chiếu. Mục tiêu là chọn kiến trúc ít tự chủ nhất đáp ứng nghiệp vụ, dựa trên độ đúng, độ ổn định giữa seed và chi phí mô phỏng.

Các thành viên phát triển trên nhánh riêng và bổ sung test cho phần phụ trách. Sau khi ba shape được merge vào main, nhánh evaluation tích hợp `origin/main`, chạy lại test host, ma trận student, crash suite và benchmark. Báo cáo lấy số liệu từ file do công cụ sinh, không chỉnh tay JSON kết quả.

## 3. Giải pháp

### Luồng nghiệp vụ và ranh giới code/model

Nguồn sự thật là order và policy hiện hành có hiệu lực tại mốc `2026-11-15`. Số ngày trễ hay câu yêu cầu bỏ policy trong ticket không thay thế dữ liệu order. Thiếu `order_id` trả `needs_info`; không tìm thấy đơn hoặc ngoài phạm vi principal trả `escalated`. Code tính quote bằng `compute_compensation`: quote bằng 0 trả `denied`; quote dương đi qua `durability.issue_refund` để host kiểm approval và ghi audit phù hợp.

Model không tính số tiền, cấp approval hay ghi ledger. Khi host chấp nhận, shape trả `resolved`; khi host từ chối, `proposal_amount` vẫn giữ quote đầy đủ. Conflict số tiền khi retry trả `failed`. Hàm `finish()` tạo kết quả từ ledger, ghi trace và tổng hợp budget.

| Shape | Cách triển khai |
| --- | --- |
| Workflow | Các bước Python cố định: đọc claim an toàn, lookup order theo principal, tính quote, gọi host. MockLLM chỉ soạn phản hồi. |
| Single | `run_react(max_steps=8, worker=True)` đọc order, policy và lịch sử refund. Sau vòng lặp, code tính quote và gọi host. Mỗi lời gọi MockLLM được ghi vào Budget. Adapter chọn hành động đọc từ trạng thái quan sát; ticket không thay đổi tool arguments. |
| Orchestrator | `make_handoff` tạo handoff allowlist; `run_readonly_investigators` thực thi các tool đọc `lookup_order`, `lookup_policy`, `compute_compensation`. Orchestrator lấy quote rồi gọi host. |
| Swarm | Giữ nguyên bản tham chiếu để đối chứng, gồm điểm yếu cố ý tin số ngày trong ticket ở seed chia hết cho 5. |

Single hiện dùng adapter ánh xạ trạng thái sang tool đọc; đây là giới hạn khi so sánh với agent dùng model thật để lập kế hoạch.

### Ledger, approval và crash recovery

Approval mà claim trỏ tới phải thuộc chính claim đó, còn hiệu lực và hợp lệ. Host áp trần theo đơn, xét tiền đã hoàn từ claim trước. Shape truyền **quote đầy đủ**: entitlement 150.000 VND, đã hoàn 30.000 VND thì host ghi thêm 120.000 VND. Shape tự trừ trước sẽ dẫn tới trừ hai lần.

Ledger dùng khóa `refund:{claim_id}`; refund và audit `refund_committed` được ghi cùng transaction SQLite. Retry cùng số tiền trả effect đã commit; số tiền khác tạo conflict và giữ effect cũ. Demo checkpoint đơn lẻ tạo hai dòng refund, cho thấy checkpoint không thay được ledger. Các shape truyền `crash_at` vào host và để `InjectedCrash` lan ra; khi bắt để ghi trace crash thì ném lại exception.

### Handoff và trace

Handoff chỉ mang field trong allowlist, không chuyển parent context hay nguyên claim row; investigator chỉ có tool đọc. Trace ghi thông tin cần thiết như trạng thái lookup, quote, hành động đọc, handoff đã sanitize và quyết định cuối. Không ghi ticket thô, parent_secret, header, SĐT, địa chỉ, tên hàng hoặc ghi chú nội bộ.

Evaluator public kiểm tra trace contract và chuỗi cấm của fixture. Kết quả này chỉ áp dụng cho các trial đã chạy, chưa thay thế việc rà độc lập mọi file trace hay chứng minh không rò rỉ trên dữ liệu mới.

## 4. Kết quả

Nguồn: `src/reports/benchmark.json`. Mỗi shape chạy 14 claim × 5 seed (`11,22,33,44,55`), tổng cộng 280 trial; mỗi trial dùng SQLite mới. Các shape dùng cùng MockLLM, mốc policy, bảng giá và evaluator. Run dẫn chứng: `R-workflow-C-001-s11`; toàn bộ run id nằm trong danh sách `trials` của report.

| Shape | Pass/trial | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success mô phỏng (VND) | Mean/p95 steps |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Workflow | 70/70 | 1,000000 | 1,000000 | 1,000000–1,000000 | 0,000000 | 28,79 | 4,43 / 5 |
| Single | 70/70 | 1,000000 | 1,000000 | 1,000000–1,000000 | 0,000000 | 47,31 | 9,07 / 10 |
| Orchestrator | 70/70 | 1,000000 | 1,000000 | 1,000000–1,000000 | 0,000000 | 47,30 | 5,36 / 6 |
| Swarm | 69/70 | 0,985714 | 0,928571 | 0,928571–1,000000 | 0,000816 | 49,57 | 2,80 / 3 |

Steps là số event trace theo định nghĩa lab. Mean steps của single lớn hơn 8 không có nghĩa vòng ReAct vượt giới hạn 8 bước. Chi phí là mô phỏng, không phải hóa đơn API; latency là `unavailable`.

| Kiểm tra | Kết quả thực tế |
| --- | --- |
| Test host sau tích hợp | 66 passed, 248 deselected |
| Ma trận student | 248 passed, 66 deselected |
| Test bổ sung của người 4 | 3 passed |
| Crash suite host | 20/20, nguồn `src/reports/crash.json` |
| Hidden self-check | Chưa chạy vì chưa có `student_drop/` |

Crash suite host và T11/T12 trong ma trận student cung cấp bằng chứng bổ sung cho nhau; không coi crash suite host là kiểm tra mọi tình huống crash của từng shape. Swarm có một trial sai trạng thái ở seed 55, phù hợp điểm yếu T02 được tài liệu lab mô tả.

Theo dữ liệu public, chọn **workflow**: độ đúng bằng single và orchestrator, variance bằng 0, cost/success thấp nhất. Chưa thấy lợi ích độ đúng từ mức tự chủ cao hơn trên corpus này. Xem xét lại khi task mới cần điều tra linh hoạt hoặc song song và đánh giá có kiểm soát chứng minh lợi ích đủ bù chi phí. Chi tiết: [decision_adr.md](decision_adr.md).

Các lệnh tái lập chạy trong `src/`, dùng Python đã cài requirements:

```powershell
python -m pytest -q
python -m pytest -q -m student -o addopts=
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
```

## 5. Khó khăn và cách xử lý

- Chạy `cd src` từ thư mục cha repo gây lỗi đường dẫn. Chuyển vào đúng repo rồi vào `src`.
- Python ban đầu thiếu pytest. Tạo `.venv`, cài requirements và gọi trực tiếp `.venv\Scripts\python.exe`; smoke pass và test chạy được.
- Pytest qua sandbox gặp `PermissionError` ở thư mục tạm Windows. Chạy lại với quyền truy cập phù hợp cho kết quả pass; không thay logic host để né lỗi môi trường.
- `TEAM.md` từ main còn dấu conflict đã được commit. Xóa dấu conflict, giữ thông tin thành viên hai phía và cập nhật đóng góp người 4.

## 6. Tổng hợp đóng góp

| Thành viên | Đóng góp và bằng chứng |
| --- | --- |
| Trần Thị Lý | Workflow, integration, `test_workflow_extra.py`; commit `02bd691` |
| Trần Việt Tiến | Single, test ticket injection dựa trên order thực, `test_single_extra.py`; commit `87dd8b8` |
| Đỗ Hoàng Minh | Orchestrator/handoff, `test_orchestrator_extra.py`; commit code `4de8972`, test `9e77971` |
| Nguyễn Thùy Dương | `test_policy_extra.py`: retry approval sai claim, đơn đã hoàn đủ, reconnect sau crash; commit `e59a0a6`; chạy evaluation và tổng hợp báo cáo với trợ lý AI |

Chi tiết nằm trong `TEAM.md` và báo cáo cá nhân. Nhóm sử dụng AI để giải thích, hỗ trợ code/test, thực thi đánh giá và soạn báo cáo. Số liệu lấy từ lần chạy thực tế.

## 7. Hạn chế và hướng cải thiện

Public chỉ có 14 claim và năm seed; chưa có hidden grade để kết luận đạt ngưỡng hidden 0,75 hoặc báo số đếm leak/bypass chính thức. MockLLM không đại diện cho độ tin cậy, chi phí hay latency của model sản xuất. Chênh lệch steps còn phụ thuộc cách ghi event trace.

So sánh hiện tại thay đổi cả kiến trúc lẫn cách gọi model, chưa cô lập tác động nhân quả của topology. Research card và ablation một biến cần hoàn thiện; chưa tuyên bố đã có kết quả thí nghiệm này. Trước khi nộp cần rà trace riêng, bổ sung bằng chứng còn thiếu và chạy lại `check_submission` đến `0 FAIL`. Nếu thay code sau lần đo, cần đánh giá lại và cập nhật commit/run id tương ứng.

## 8. Tài liệu tham khảo

- [Đề bài](../../README.md), [quy định](../../RULES.md), [rubric](../../RUBRIC.md).
- [Luật nghiệp vụ](../../docs/business_rules.md), [contract](../../docs/contracts.md), [kiến trúc](../../docs/architecture.md), [metric](../../docs/metrics.md).
- Mã host: `src/lab8/durability.py`, `src/lab8/policy.py`; ba shape và test trong repo.
- Bằng chứng do công cụ sinh: `src/reports/benchmark.json`, `src/reports/crash.json`.
