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

Status: **candidate complete; release hardening before tag.**

Exit criteria:

- seven core roles implemented ✅
- canonical roles receive semantic contract validation ✅
- bounded result contract referenced by all roles and generated adapter instructions ✅
- Codex adapter generated deterministically from canonical definitions ✅
- generated adapter drift check runs in CI ✅
- direct-vs-delegate policy fixtures run through an executable evaluator ✅
- current public Codex custom-agent behavior recorded as an authoritative source ✅

Remaining before a v0.1.0 tag:

- smoke-test installation in a real Codex project
- confirm custom-agent discovery/permissions on the user's current Codex build
- record the first real task traces for v0.2 benchmark input

## v0.2.0 — Efficiency controls

Status: **next active milestone.**

Exit criteria:

- explicit context budgets measured against real runs
- semantic compute tiers benchmarked
- natural-language routing/classifier accuracy evaluated separately from policy routing
- escalation rules tested against difficult/critical fixtures
- token, latency and quality measurements recorded
- over-delegation regression cases enforced
- task-level cost comparison supports Luna/Terra/Sol default decisions

## v0.3.0 — Engineering specialists

Candidates:

- Embedded Firmware Engineer
- STM32 Debugger
- Realtime Systems Reviewer
- ROS 2 Engineer
- Robotics Integration Engineer
- Developer Tooling Engineer

A specialist is accepted only if it outperforms the generic core stack on repeated domain tasks enough to justify its maintenance and routing complexity.

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
