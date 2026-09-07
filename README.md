# Engineering Agent Stack

> Research-driven, provider-aware engineering agents focused on **quality per unit of cost**, not maximum agent count.

[![Status](https://img.shields.io/badge/status-v0.2%20runtime%20candidate-orange)](#roadmap)
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
Classification + Routing Policy
    |
    +--> DIRECT -------------------------------> verify
    |
    +--> DELEGATE
             |
             v
       Delegation Preflight
        PASS | REJECT | ESCALATE
             |
             v
       Resolved Execution Plan
             |
             v
        Provider Adapter
             |
             v
           Execution
             |
             +--> Agent Registry / Status
             +--> observed telemetry/evidence
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
runtime/         Provider-neutral preflight, resolved-plan, registry and context-packet contracts
research/        Source analysis, primary-source notes, patterns and anti-patterns
schemas/         Stable role/result/benchmark contracts
evals/           Routing and quality evaluation fixtures
benchmarks/      Controlled cost/latency/quality experiments
adapters/        Provider/tool-specific integration layers
scripts/         Validation, installation, acceptance, probes and evaluation tooling
docs/            Architecture, provenance, installation, acceptance and roadmap
```

## Quick start — Windows + Codex

Install development dependencies:

```powershell
py -m pip install -r requirements-dev.txt
```

Validate the repository:

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

`--project-instructions` manages one clearly marked Engineering Agent Stack block inside the target project's `AGENTS.md`.

### Stack-owned release acceptance

Normal live release gate:

```powershell
.\scripts\acceptance-test.ps1
```

Offline/no-model gate:

```powershell
.\scripts\acceptance-test.ps1 -Offline
```

The release gate checks repository, routing, installer, direct-first behavior, and exact bounded write scope in a disposable sandbox. It **does not require provider child spawning or child-model routing to pass**.

### Codex provider/runtime probe

Test `spawn_agent`, custom-role selection, Multi-Agent V2 behavior, and child-model telemetry separately:

```powershell
.\scripts\provider-probe.ps1
```

Extended role probe:

```powershell
.\scripts\provider-probe.ps1 -Extended
```

A provider probe may fail while the stack-owned release gate remains green. That separation prevents upstream Codex runtime behavior from falsely marking the stack itself as broken.

Retained local evidence from 2026-09-07 shows the stack-owned live gate passing on Windows with `codex-cli 0.153.4`, while the basic provider probe remained diagnostic-only and unhealthy because public spawn evidence was unavailable and the Implementer path reported an upstream `502 Bad Gateway`. Scout remained read-only, the parent did not silently perform the failed delegated edit, and Extended was not run after the basic probe failed. Collaboration counts, token usage, latency, and other provider telemetry are run-specific; use the report produced by the current acceptance/probe command for exact measurements. See [`docs/ACCEPTANCE_WINDOWS.md`](docs/ACCEPTANCE_WINDOWS.md).

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

## Runtime-first v0.2 contracts

The repository now exposes an executable provider-neutral **preflight/planning gate** for stack-controlled delegation:

```text
route -> preflight -> resolved execution plan -> provider adapter -> execution -> status/telemetry -> quality gate
```

Use the gate explicitly before a delegated provider call:

```powershell
py scripts\resolve_delegation.py `
  --request schemas\delegation-request.example.yaml `
  --format json
```

Exit codes are `0=PASS`, `3=REJECT`, `4=ESCALATE`, and `2=invalid request`. YAML scalar types are strict: for example, the string `"false"` is rejected rather than coerced to boolean false. Only `PASS` produces a resolved execution plan.

This Python gate **does not automatically intercept arbitrary native `spawn_agent` calls made inside a normal Codex session**. Provider adapters and parent orchestration must invoke/enforce the stack contract when using this path; Codex sandbox/tool controls remain the actual runtime permission boundary.

`runtime/preflight.py` rejects hard capability/policy violations and escalates unresolved budget/review gates. Codex-specific reasoning overrides are read from `adapters/codex/role-profiles.yaml` rather than duplicated into the runtime layer. `runtime/registry.py` exposes concise human-readable status plus JSON while keeping unavailable token/latency data as unknown. `runtime/context_packet.py` provides the bounded-evidence experiment foundation; the controlled harness now materializes genuinely different full-context and bounded-context prompts, but no universal efficiency win is claimed without repeated quality-gated provider runs.

Render a captured registry snapshot with:

```powershell
py scripts\agent_status.py --input status.json --format text
py scripts\agent_status.py --input status.json --format json
```

Provider adapters remain responsible for provider-specific execution details. The canonical runtime contracts do not make Codex behavior the definition of a role.

## Adaptive token/context budget

The stack separates three concerns:

```text
INPUT CONTEXT  -> bounded to relevant task evidence
WORK BUDGET    -> adaptive; do not starve correctness
RESULT BUDGET  -> compressed evidence instead of transcript dumps
```

Suggested result sizes are **soft/adaptive**, not hard total-token quotas. Critical, realtime, safety, security, or release evidence may exceed ordinary result targets when necessary.

See [`policies/context-budget.md`](policies/context-budget.md).

## Codex telemetry boundary

Codex JSONL is treated as provider telemetry, not as a stack-owned release invariant. The normalizer accepts current `collab_tool_call` spawn items and older/experimental `collab_agent_tool_call` traces.

When exposed, the capture pipeline records:

```text
agent_spawns  # compatibility name: spawn_agent events observed in public JSONL
agent_spawn_thread_ids
agent_spawn_models
agent_spawn_roles
input/output/reasoning tokens
latency
```

Current Codex builds may omit child model/role metadata or other internal activity from public JSONL. Missing optional telemetry is not fabricated, and `agent_spawns = 0` means only that zero spawn events were observed in that stream; it does not prove no child was spawned. Provider/runtime diagnostics remain separate from the stack-owned release gate.

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
- [`can1357/oh-my-pi`](https://github.com/can1357/oh-my-pi)
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

GitHub Actions validates Linux repository behavior and an **offline Windows stack-owned acceptance run**. CI also includes a Windows UTF-8 subprocess regression so Codex JSONL capture cannot silently fall back to cp1252.

Provider delegation probes are intentionally not executed as release-blocking CI because they depend on external authenticated Codex runtime behavior.

## Roadmap

- **v0.0.x — Research foundation:** exit criteria reached; research remains continuous.
- **v0.1.0 — Core agents:** stack-owned release acceptance, installer, routing and role contracts; provider delegation remains an observed adapter capability.
- **v0.2.0 — Runtime efficiency controls:** provider-neutral delegation preflight/resolution, lightweight status, bounded context-packet experiments, repeated real traces, and compute/routing evaluation.
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
