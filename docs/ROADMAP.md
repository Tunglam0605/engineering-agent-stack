# Roadmap

## v0.0.x — Research foundation

Status: **exit criteria reached; research remains continuous.**

Exit criteria:

- at least 6 reference repositories analyzed with one matrix ✅
- common patterns and anti-patterns documented ✅
- provider-neutral role/result schemas drafted ✅
- routing, context, escalation and verification policies documented ✅
- repository validation runs in CI ✅

## v0.1.0 — Core agents

Status: **in progress — experimental core and Codex adapter now exist.**

Exit criteria:

- seven core roles implemented ✅
- each role conforms to the agent contract ✅ by structure; semantic validation pending
- bounded result format implemented ✅ schema; runtime enforcement pending
- one Codex adapter generated from canonical definitions ⏳ adapter candidates exist; generator/drift check pending
- direct-vs-delegate routing tests exist ⏳ seed cases exist; executable evaluator pending

## v0.2.0 — Efficiency controls

Exit criteria:

- explicit context budgets
- semantic compute tiers benchmarked
- escalation rules tested
- token, latency and quality measurements recorded
- over-delegation regression cases added

## v0.3.0 — Engineering specialists

Candidates:

- Embedded Firmware Engineer
- STM32 Debugger
- Realtime Systems Reviewer
- ROS 2 Engineer
- Robotics Integration Engineer
- Developer Tooling Engineer

A specialist is accepted only if it outperforms the generic core stack on repeated domain tasks enough to justify the maintenance and routing complexity.

## v0.4.0 — Evaluation and portability

- multiple provider adapters
- routing accuracy benchmark
- cross-version compatibility checks
- specialist-vs-core ablation studies

## v1.0.0 — Stable stack

- stable canonical schemas
- reproducible installer/generator
- documented release process
- benchmark-backed default routing
- migration strategy for model/provider changes
