# Decision record

- Shape chọn: workflow
- Commit hash: 7f74a30 (evaluated code)
- Run id dẫn chứng: R-workflow-C-001-s11; src/reports/benchmark.json
- Pass rate / pass^5 / seed min-max / variance: 1.0 / 1.0 / 1.0-1.0 / 0.0 (public, 70 trials)
- Cost per success (mô phỏng, VND): 28.79
- Crash safety: 20/20 (host suite; src/reports/crash.json)
- Secret leak / approval bypass: Hidden counters unavailable; workflow public 70/70 pass, student 248 passed

## Decision

Select workflow: workflow, single and orchestrator each pass 70/70 public trials. Workflow has the lowest simulated cost/success (28.79 versus 47.31 and 47.30). Swarm passes 69/70. Reconsider if new tasks require flexible or parallel investigation and measured benefits exceed cost.

## Evidence and limits

Code commit: 7f74a30. Model: MockLLM; latency unavailable; simulated prices. Public data: 14 claims, seeds 11,22,33,44,55. Host crash suite: 20/20. This does not establish hidden pass rate. No student_drop supplied. Workflow traces contain claim identifiers, visibility, quote, host outcomes and decisions; raw tickets, secrets, headers and private order fields are excluded. Public evaluation checks trace contract and forbidden strings. Separate trace review remains pending. Research card now includes a separate ticket-override ablation: swarm 69/70 versus order-only 70/70; see reports/research_ablation.json. This mechanism check does not isolate topology effects.
