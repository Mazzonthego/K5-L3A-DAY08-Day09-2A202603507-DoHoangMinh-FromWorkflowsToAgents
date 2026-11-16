# Research card

## Phiếu của nhóm

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 — Failure taxonomy: lỗi kiểm chứng dữ kiện trong swarm |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri và cộng sự, 2025, *Why Do Multi-Agent LLM Systems Fail?*, https://arxiv.org/abs/2503.13657v3 — nghiên cứu thực nghiệm trên trace MAS; kiểm tra nguồn ngày 16/11/2026. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | MAST phân loại 14 dạng lỗi thành ba nhóm: thiết kế hệ thống, lệch hướng giữa agent và kiểm chứng nhiệm vụ. Phân loại giúp phân tích lỗi ngoài việc chỉ nhìn điểm cuối. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Nguồn nghiên cứu các framework MAS và task coding, math, general agent; không nghiên cứu trực tiếp LogiX-VN hay MockLLM. Ánh xạ lỗi của lab sang nhóm kiểm chứng là diễn giải của nhóm, không phải kết luận tác giả về lab. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Tắt việc dùng số ngày trong ticket để ghi đè delay_days của order ở swarm sẽ sửa trial C-002/seed 55: pass rate dự kiến từ 69/70 lên 70/70 (+1/70), pass^5 từ 13/14 lên 14/14. Giả thuyết dựa trên điểm yếu đã được đề bài công bố và benchmark trước đó, không phải dự đoán mù. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | So swarm với swarm_order_only, giữ cùng code tham chiếu, MockLLM, prompt, registry tool, corpus public 14 claim, world, năm seed, giá, evaluator và SQLite mới mỗi trial. Chỉ tắt nhánh sử dụng parsed_delay từ ticket bằng scoped patch trả None tại swarm_reference.parse_delay_days. Không sửa swarm, host, data, config hay metric gốc. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: dùng lời khách thay dữ kiện order, dẫn tới resolved thay denied ở T02. Đo pass rate, pass^5, seed min–max, variance, cost/success và đối chiếu trial cùng claim/seed. Không coi biến động cost do nhánh recompute là một biến can thiệp độc lập. |

## Kết quả ablation

Lệnh đã chạy từ `src/` bằng Python của `.venv`:

```powershell
.\.venv\Scripts\python.exe -m lab8.benchmark --shapes swarm,swarm_order_only --extra-shape swarm_order_only=bonus.swarm_order_only:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/research_ablation.json
```

- Code biến thể: `src/bonus/swarm_order_only.py`. Đây là thí nghiệm research card, không đăng ký hay tuyên bố đạt điểm bonus.
- File report: `src/reports/research_ablation.json`, do benchmark sinh, không sửa JSON bằng tay.
- Run dẫn chứng: `R-swarm-C-002-s55`. Wrapper giữ run id nội bộ của reference; phân biệt hai nhánh bằng field `shape` trong trial (`swarm` / `swarm_order_only`). Chạy tuần tự; trace cùng run id của nhánh sau ghi đè nhánh trước, vì vậy so sánh hai nhánh dựa trên kết quả evaluator đã lưu trong report, không coi trace cuối là hai bằng chứng độc lập.

| Metric | Swarm gốc | Tắt ticket override |
| --- | ---: | ---: |
| Pass/trial | 69/70 | 70/70 |
| Pass rate | 0,985714 | 1,000000 |
| Pass^5 | 0,928571 | 1,000000 |
| Seed min–max | 0,928571–1,000000 | 1,000000–1,000000 |
| Seed variance | 0,000816 | 0,000000 |
| Cost/success mô phỏng, VND | 49,57 | 48,72 |

Kết quả phù hợp giả thuyết về lỗi đã biết. Nhóm diễn giải đây là thiếu kiểm chứng nguồn dữ kiện trước tính quote; host vẫn kiểm approval nhưng không sửa được quote sai do shape đã dùng sai delay. Tắt override loại bỏ lỗi này trên corpus public. Chi phí có thể giảm vì không đi vào nhánh recompute và có thêm một trial thành công ở mẫu số cost/success.

## Giới hạn

MockLLM không phải model sản xuất; latency là `unavailable`, giá chỉ mô phỏng. Không đo được chất lượng lập luận thật hay suy ra hiệu quả trên hidden. Lỗi được cài cố ý và biết trước; đây là kiểm chứng cơ chế, không phải phát hiện độc lập hoặc tái lập toàn bộ paper MAST. Scoped patch chỉ dành cho benchmark tuần tự, không an toàn nếu chạy đồng thời trong cùng process. Thí nghiệm không chứng minh topology nào tốt hơn và không thay đổi lựa chọn workflow dựa trên benchmark chính thức.
