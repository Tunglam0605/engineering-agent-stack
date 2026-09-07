# Engineering Agent Stack

> Research-driven, provider-aware engineering agents focused on **quality per unit of cost**, not maximum agent count.

[![Status](https://img.shields.io/badge/status-v0.1%20candidate%20%2B%20v0.2%20benchmarks-orange)](#roadmap)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Why this project exists

AI coding systems become wasteful when every task receives the strongest model, every problem spawns multiple agents, or every worker inherits a large context. This repository studies strong community and official implementations, extracts measurable patterns, and turns them into a small engineering stack.

```text
maximize:   quality / (cost × latency)
subject to: quality >= required threshold for the task risk
```

The stack optimizes **routing, context, evidence, verification, and escalation** rather than maximizing agent count.

## Design principles

1. **Direct-first** — trivial/reversible work should not pay delegation overhead.
2. **Role != compute profile != provider** — expertise, budget, and runtime remain separate.
3. **Risk-adjusted routing** — escalate only when uncertainty or failure cost justifies it.
4. **Bounded/isolated context** — send the smallest useful context and return evidence, not transcripts.
5. **Adaptive budgets** — constrain waste, not evidence required for correctness.
6. **Deterministic coordination, bounded autonomy** — the parent owns decomposition, integration, and stop/escalate decisions.
7. **Independent verification** — high-risk or release-critical behavior gets independent assurance.
8. **Safe parallelism** — parallelize independent read-heavy work; partition or serialize writes.
9. **Runtime-enforced permissions** — sandbox/tool controls are security boundaries; prompts are not.
10. **Evidence before completion** — use the narrowest validation that can prove the claim.
11. **Benchmark before belief** — model/routing choices remain candidates until measured.
12. **Visible provenance** — upstream research influence is credited and directly reused material requires license-aware provenance.

## Architecture

```text
User / Task
    |
    v
Orchestrator / Main Codex
    |
    +--> classify task shape + risk
    +--> DIRECT or DELEGATE
    +--> choose role + semantic compute profile
    +--> send bounded context
    |
    +--> Scout / Researcher       [read-heavy]
    +--> Implementer / Debugger   [bounded write]
    +--> Test Engineer            [verification]
    +--> Reviewer / Architect     [independent assurance]
    |
    v
Quality Gate -> Result / Escalation / Block
```

Canonical layers:

```text
ROLE             What expertise/responsibility is needed?
COMPUTE PROFILE  How much model/reasoning budget is justified?
PROVIDER         Which runtime/model executes it?
POLICY           When may it run, write, escalate, or stop?
EVAL             Does the route preserve required quality?
BENCHMARK        At what token, cost, and latency budget?
PROVENANCE       Where did the design influence/material come from?
```

## Repository layout

```text
agents/          Provider-neutral role definitions and specialist catalog
config/          Semantic compute profiles and routing policy
policies/        Delegation, escalation, context and quality rules
research/        Source analysis, primary-source notes, patterns and anti-patterns
schemas/         Stable role/result/benchmark contracts
evals/           Routing and quality evaluation fixtures
benchmarks/      Controlled cost/latency/quality experiments
adapters/        Provider/tool-specific integration layers
scripts/         Validation, installation, acceptance, generation and evaluation tooling
docs/            Architecture, provenance, installation, acceptance and roadmap
```

## Quick start — Windows + Codex

The current Codex adapter is a **v0.1 candidate** suitable for project-scoped testing.

Install development dependencies:

```powershell
py -m pip install -r requirements-dev.txt
```

Validate the stack:

```powershell
py scripts\validate_structure.py
py scripts\validate_provenance.py
py scripts\validate_agents.py
py scripts\evaluate_routing.py
py scripts\validate_task_suite.py
py scripts\validate_benchmarks.py
py scripts\generate_codex_adapter.py --check
```

Install into one project first:

```powershell
py scripts\install_codex.py `
  --project C:\path\to\your\project `
  --project-instructions
```

`--project-instructions` manages one clearly marked block inside the target project's `AGENTS.md`. Installing child roles alone does not teach the **parent** Codex session when to work directly, when to delegate, how to avoid writer collisions, or when independent review is required.

### One-command Windows acceptance

Basic live acceptance:

```powershell
.\scripts\acceptance-test.ps1
```

Offline/no-model acceptance:

```powershell
.\scripts\acceptance-test.ps1 -Offline
```

Extended role coverage:

```powershell
.\scripts\acceptance-test.ps1 -Extended
```

The acceptance harness uses a disposable temporary Git repository; it does **not** test against your production project or install agents globally. It records PASS/WARN/SKIP/FAIL plus token, latency, and observable subagent-spawn telemetry.

See [`docs/ACCEPTANCE_WINDOWS.md`](docs/ACCEPTANCE_WINDOWS.md) and [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md).

## Core roles — v0.1 candidate

| Role | Primary responsibility | Default access | Codex candidate |
|---|---|---|---|
| Scout | repository discovery/call-flow mapping | read-only | Luna / medium |
| Researcher | current primary-source technical evidence | read-only + network intent | Luna / medium |
| Implementer | bounded approved implementation | workspace-write | Terra / medium |
| Debugger | evidence-first root cause/remediation | workspace-write | Terra / high |
| Test Engineer | targeted validation/failure evidence | test/build | Terra / medium |
| Reviewer | independent correctness/regression review | read-only | Terra / high |
| Architect | high-risk system decisions/trade-offs | read-only | Sol / high |

Canonical definitions live under [`agents/core/`](agents/core/). Model names never define role identity.

## Adaptive token/context budget

The stack separates three concerns:

```text
INPUT CONTEXT  -> bounded to relevant task evidence
WORK BUDGET    -> adaptive; do not starve correctness
RESULT BUDGET  -> compressed evidence instead of transcript dumps
```

Suggested result sizes are **soft/adaptive**, not hard total-token quotas. Critical, realtime, safety, security, or release evidence may exceed ordinary result targets when necessary.

See [`policies/context-budget.md`](policies/context-budget.md).

## Observable Codex subagent telemetry

The Codex JSONL normalizer records observable completed collaboration events when the current Codex build exposes them:

```text
collab_agent_tool_call
  tool = spawn_agent
  model
  reasoning_effort
  receiver agent role
```

This lets acceptance and benchmarks verify not only that a child was spawned, but—when runtime metadata is present—which model/reasoning profile actually executed it. Missing optional telemetry produces a warning rather than fabricated evidence.

See [`research/sources/openai-codex-exec-jsonl.md`](research/sources/openai-codex-exec-jsonl.md).

## Controlled benchmark suite

`benchmarks/tasks/index.yaml` defines the initial `controlled-v1` suite for repeated model/routing comparisons. It covers repository discovery, bounded implementation, seeded reviewer regressions, and direct-vs-delegated trivial work.

```powershell
py scripts\validate_task_suite.py
```

Quality is evaluated **before** token/cost/latency preference. See [`benchmarks/README.md`](benchmarks/README.md) and [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Research method

Every source is evaluated on taxonomy, role contract, delegation, model routing, context, concurrency/write ownership, verification, escalation, cost control, observability, and portability.

Patterns are classified as **ADOPT**, **ADAPT**, **EXPERIMENT**, **REJECT**, or **HISTORICAL**. The implementation is a local synthesis; research sources are not treated as anonymous idea pools.

### Upstream projects studied

- [`openai/codex`](https://github.com/openai/codex)
- [`msitarzewski/agency-agents`](https://github.com/msitarzewski/agency-agents)
- [`Yeachan-Heo/oh-my-codex`](https://github.com/Yeachan-Heo/oh-my-codex)
- [`infiquetra/infiquetra-codex-plugins`](https://github.com/infiquetra/infiquetra-codex-plugins)
- [`trailofbits/codex-config`](https://github.com/trailofbits/codex-config)
- [`KevinBigham/codex-safe-starter`](https://github.com/KevinBigham/codex-safe-starter)
- [`awslabs/cli-agent-orchestrator`](https://github.com/awslabs/cli-agent-orchestrator)
- [`openai/openai-agents-python`](https://github.com/openai/openai-agents-python)
- [`microsoft/agent-framework`](https://github.com/microsoft/agent-framework)
- [`microsoft/autogen`](https://github.com/microsoft/autogen)
- [`langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph)
- [`langchain-ai/deepagents`](https://github.com/langchain-ai/deepagents)
- [`crewAIInc/crewAI`](https://github.com/crewAIInc/crewAI)
- [`huggingface/smolagents`](https://github.com/huggingface/smolagents)
- [`OpenHands/OpenHands`](https://github.com/OpenHands/OpenHands)

Detailed lineage and thanks: [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md).

Rules for conceptual references, adapted material, vendored material, generated material, and license-aware reuse: [`docs/PROVENANCE.md`](docs/PROVENANCE.md).

## Validation

GitHub Actions validates both Linux repository behavior and an **offline Windows acceptance run**. Current gates cover structure, provenance, canonical agent contracts, routing policy, controlled benchmarks, installer behavior, acceptance harness behavior, Codex JSONL capture, and generated adapter drift.

## Roadmap

- **v0.0.x — Research foundation:** exit criteria reached; research remains continuous.
- **v0.1.0 — Core agents:** candidate-complete; Windows/local live acceptance is the remaining release gate.
- **v0.2.0 — Efficiency controls:** repeated real traces, context-budget measurement, compute-tier comparison, classifier/routing evaluation.
- **v0.3.0 — Engineering specialists:** Embedded, STM32, ROS 2, Robotics, and tooling roles only when benchmarks justify them.
- **v0.4.0 — Evaluation/portability:** multiple provider adapters, routing accuracy, compatibility checks, specialist-vs-core ablations.
- **v1.0.0 — Stable stack:** benchmark-backed defaults, reproducible installer, migration strategy, compatibility policy.

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Acknowledgements and attribution

This repository is deliberately built from **credited research**, not unattributed copying. Thank you to the maintainers and contributors of the upstream projects listed above for publishing work that the engineering community can inspect, compare, challenge, and learn from.

The upstream repositories are treated as conceptual research inputs unless a local file explicitly records adapted or vendored material. Direct reuse must preserve upstream license/notice requirements and exact provenance before merge.

No endorsement, sponsorship, or affiliation by any upstream project is implied.

## License

MIT for this repository's original material. Third-party material, if ever adapted or vendored, remains subject to its upstream license and the provenance rules above.
