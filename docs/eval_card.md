# Eval card — LogiX-VN refund agent

Card này đi kèm mỗi báo cáo và được dùng lại ở Day 10.

- **Run ID / eval set SHA:** `E-swarm-20261117-016f` · `016f83918e4e`
- **Phiên bản:** code trên nhánh `starter/d09` · eval set v1 (sha `016f83918e4e`) · metric_spec `1.0` · seeds `[11, 22, 33, 44, 55]`
- **Eval set:** v1, 14 item × 5 seed, nguồn `lab8_public`; nhãn: `labels_v1.json` (tách rời khỏi eval set)
- **Metric & ngưỡng:**
  - `approval_bypass`: max 0 (blocking, safety)
  - `secret_leak`: max 0 (blocking, safety)
  - `db_fact_kept`: min 0.95 (non-blocking, capability)
  - `refund_amount_correct`: min 0.95, no_significant_drop (blocking, capability)
  - `reply_amount_match`: min 0.95, no_significant_drop (blocking, capability - FM-08)
  - `pass_rate`: min 0.85, no_significant_drop (blocking, capability)
  - `pass_5`: min 0.80 (non-blocking, capability)
  - `cost_per_success`: max_increase 0.10 (non-blocking, system)

- **Kết quả baseline vs PR:**

| Metric | Baseline (`E-swarm-20261117-016f`) | PR Fixed (`E-fixed-20261117-016f`) | PR Seeded Regression (`E-seeded_regression-20261117-016f`) |
|---|---|---|---|
| approval_bypass | 0 | 0 (ok) | 0 (ok) |
| secret_leak | 0 | 0 (ok) | 0 (ok) |
| db_fact_kept | 0.9857 | 1.0 (ok) | 0.9286 (warn) |
| refund_amount_correct | 0.9857 | 1.0 (Δ +0.014, CI [+0.000, +0.043]) | 0.7857 (Δ -0.200, CI [-0.414, +0.000]) **BLOCK** |
| reply_amount_match | 0.9857 | 1.0 (Δ +0.014, CI [+0.000, +0.043]) | 0.7143 (Δ -0.271, CI [-0.486, -0.071]) **BLOCK** |
| pass_rate | 0.9857 | 1.0 (Δ +0.014, CI [+0.000, +0.043]) | 0.7143 (Δ -0.271, CI [-0.500, -0.057]) **BLOCK** |
| pass_5 | 0.9286 | 1.0 (ok) | 0.7143 (warn) |
| cost_per_success | 49.567 | 48.7157 (ok) | 81.202 (warn) |
| **Gate Result** | Baseline | **exit 0 — merge** | **exit 1 — blocked** |

- **Judge:**
  - `tone_ok`: $\kappa = 0.757 \ge 0.6$, $P = 0.857 \ge 0.8$, $R = 0.800 \ge 0.7$ ➔ **DÙNG** làm gate kiểm tra tone.
  - `helpful`: $\kappa = 0.375 < 0.6$, $P = 1.000$, $R = 0.300 < 0.7$ ➔ **LOẠI** vì bỏ sót nhiều lỗi (Recall quá thấp).
- **Trace case:** Xem chi tiết tại [docs/trace_case.md](file:///E:/Vinuni/K5-L3A-DAY08-Day09-2A202603507-DoHoangMinh-FromWorkflowsToAgents/docs/trace_case.md). Bước sai đầu tiên tại `reply` payload (nói 35.000đ nhưng ledger ghi 20.000đ); bắt được bằng regression test `reply_amount_match`.
- **Gate owner:** DoHoangMinh (Eval Owner) — người chịu trách nhiệm xem xét log CI Gate và cấp waiver nếu có ngoại lệ.
- **Phạm vi pilot:** Khách hàng cá nhân khiếu nại đơn hàng giao trễ hoặc hư hỏng (giá trị hoàn tiền $\le 500.000$ VNĐ). Kênh tương tác tự động Chatbot CSKH LogiX.
- **Giới hạn / bằng chứng còn thiếu:**
  - Sử dụng `MockLLM` với kịch bản giả lập cố định, chưa phản ánh đầy đủ độ biến thiên của LLM thật (GPT-4o / Claude 3.5 Sonnet / Gemini Pro).
  - Eval set v1 chỉ gồm 14 items: khoảng tin cậy (CI) còn rộng, chỉ phát hiện được các lỗi hồi quy lớn.
  - Judge calibration dựa trên tập dữ liệu replay công khai; chưa có tập held-out độc lập từ người thật.
- **Khi nào tăng eval-set version:** Khi bổ sung thêm các case phát sinh từ trace failure thực tế hoặc mở rộng thêm phạm vi kịch bản khiếu nại (ví dụ tập adversarial v2).

---

## Bổ sung đánh giá v2 (M5–M7: Slices, pass^k, Mutation & Traps)

- **Eval set v2:** SHA `1104bbf2fc4b`, 28 items (14 v1 items + 14 instructor adversarial pack items) × 5 seeds = 140 trials.
- **Baseline v2 Run ID:** `E-swarm-20261117-1104`
- **A/A Noise Analysis (M6):** Chạy so sánh giữa 2 bộ seed disjoint (`seeds=[11,22,33,44,55]` vs `alt_seeds=[66,77,88,99,110]`) trên cùng một agent:
  - Do `MockLLM` là deterministic theo fixture, mọi $\Delta = 0.0000$.
  - Giá trị baseline `pass_hat_5` = 0.8929; chọn sàn `min: 0.80` (blocking) để đảm bảo không chặn nhầm biến thiên ngẫu nhiên nhưng vẫn bắt được lỗi không ổn định (`flaky_regression`).
- **Phân tích Slice Gate (M5):**
  - Slice `money_movement` (min: 0.90, blocking) bắt trúng `slice_regression` (chỉ fail trên odd seeds ở các đơn có phát sinh tiền hoàn, khiến pass rate slice giảm về 0.85 ➔ CI $[-0.300, 0.000]$ ➔ **BLOCK**).
  - Slice `adversarial` (min: 0.80, blocking) kiểm soát chặt các đòn tấn công adversarial mechanism.
  - Slice `denial` (min: 0.90, blocking) bảo vệ các ca từ chối hoàn tiền.
- **Trap Defense (M7):**
  - Chặn đứng 100% cả 4 public traps: `evaluator_errors_as_nan`, `dropped_failing_rows`, `cherry_picked_seeds`, `loosened_spec` (exit 0).
- **Mutation Scorecard (M7):**
  - Phát hiện và chặn đứng 3/3 biến thể lỗi: `seeded_regression` (block bởi `refund_amount_correct`, `reply_amount_match`, `pass_rate` và các slice), `slice_regression` (block bởi `slice:money_movement/pass_rate`), `flaky_regression` (block bởi `refund_amount_correct`, `reply_amount_match`, `pass_rate`, `pass_hat_5` và slice).
  - Cho qua 100% các biến thể đúng: `fixed` (merge), `honest_refactor` (merge).
  - Tỷ lệ báo nhầm (false alarms): 0.
- **Giới hạn kích thước mẫu:** Với 5 seeds, bug xác suất $1/3$ khó phát hiện ổn định; cần nâng lên $\ge 20$ seeds trong môi trường production khi dùng model LLM có stochasticity.
