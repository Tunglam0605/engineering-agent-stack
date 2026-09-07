# Engineering Agent Stack

> Research-driven, provider-aware engineering agents focused on **quality per unit of cost**, not maximum agent count.

[![Status](https://img.shields.io/badge/status-v0.1%20experimental-orange)](#roadmap)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Why this project exists

AI coding systems can become wasteful when every task receives the strongest model, every problem spawns multiple agents, or every worker inherits a large context. This repository studies strong community and official implementations, extracts measurable patterns, and turns them into a small engineering stack.

The target is not "minimum tokens" and not "maximum intelligence everywhere". The target is:

```text
maximize:   quality / (cost × latency)
subject to: quality >= required threshold for the task risk
```

## Design principles

1. **Direct-first** — do not delegate trivial work.
2. **Role != compute profile != provider** — expertise, budget, and runtime are separate dimensions.
3. **Risk-adjusted routing** — escalate compute only when complexity or failure cost requires it.
4. **Bounded/isolated context** — pass the smallest useful task context; return evidence, not transcripts.
5. **Deterministic coordination, bounded autonomy** — the orchestrator owns topology and integration.
6. **Independent verification** — implementation and final review are separate for meaningful changes.
7. **Safe parallelism** — parallelize read-heavy work; partition or serialize writes.
8. **Runtime-enforced permissions** — sandbox/tool boundaries are security controls; prompts are not.
9. **Evidence before completion** — the narrowest sufficient validation must support the claim.
10. **Benchmark before belief** — routing/model choices remain hypotheses until measured.

## Architecture

```text
User / Task
    |
    v
Orchestrator / Control Plane
    |
    +--> classify task shape + risk
    +--> choose direct execution or delegation
    +--> choose role + semantic compute profile + provider adapter
    +--> allocate bounded context + write ownership
    |
    +--> Scout / Researcher       [read-heavy]
    +--> Implementer / Debugger   [bounded write]
    +--> Test Engineer            [verification]
    +--> Reviewer / Architect     [independent assurance]
    |
    v
Quality Gate -> Result / Escalation / Block
```

The project separates four concerns:

```text
ROLE             What expertise/responsibility is needed?
COMPUTE PROFILE  How much reasoning/model budget is justified?
PROVIDER         Which runtime/model implementation executes it?
POLICY           When may it run, write, escalate, or stop?
```

## Repository layout

```text
agents/          Provider-neutral role definitions and specialist catalog
config/          Semantic compute profiles and routing policy
policies/        Delegation, escalation, context and quality rules
research/        Source analysis, primary-source notes, patterns and anti-patterns
schemas/         Stable contracts for roles/results/configuration
evals/           Quality and routing evaluation cases
benchmarks/      Cost/latency/quality experiments
adapters/        Provider/tool-specific integration layers
scripts/         Validation and repository tooling
docs/            Architecture and roadmap
```

## Research method

Every reference implementation is evaluated using the same dimensions: taxonomy, role contract, delegation, routing/model selection, context, concurrency/write ownership, verification, escalation, cost control, observability and portability.

A pattern is classified as **ADOPT**, **ADAPT**, **EXPERIMENT**, or **REJECT**. Historical sources can also be marked **HISTORICAL** when a maintained successor supersedes them.

### Research Wave 2 sources

The matrix now covers fourteen sources, including:

- `msitarzewski/agency-agents`
- `Yeachan-Heo/oh-my-codex`
- `infiquetra/infiquetra-codex-plugins`
- `trailofbits/codex-config`
- `KevinBigham/codex-safe-starter`
- `awslabs/cli-agent-orchestrator`
- `openai/openai-agents-python`
- `microsoft/agent-framework` and historical `microsoft/autogen`
- `langchain-ai/langgraph` and `langchain-ai/deepagents`
- `crewAIInc/crewAI`
- `huggingface/smolagents`
- `OpenHands/OpenHands`

These are references, not upstream code dependencies. Prompts are not copied wholesale; patterns are re-designed behind our own contracts and evals.

See [`research/matrix/repository-comparison.yaml`](research/matrix/repository-comparison.yaml) and [`research/patterns/wave-2-synthesis.md`](research/patterns/wave-2-synthesis.md).

## Core roles — experimental v0.1

| Role | Primary responsibility | Default access | Codex candidate |
|---|---|---|---|
| Scout | repository discovery/call-flow mapping | read-only | Luna / medium |
| Researcher | current primary-source technical evidence | read-only + network | Luna / medium |
| Implementer | bounded approved implementation | workspace write | Terra / medium |
| Debugger | evidence-first root cause/remediation | workspace write | Terra / high |
| Test Engineer | targeted validation/failure evidence | test/build | Terra / medium |
| Reviewer | independent correctness/regression review | read-only | Terra / high |
| Architect | high-risk system decisions/tradeoffs | read-only | GPT-5.6 / high |

Canonical role definitions live in [`agents/core/`](agents/core/). Codex-specific candidates live separately under [`adapters/codex/`](adapters/codex/), preserving `role != model`.

## Compute profiles

```text
cheap     -> scanning, classification, high-volume bounded work
standard  -> ordinary implementation, testing and research
deep      -> difficult debugging and high-confidence review
critical  -> architecture, realtime/safety/security/release-critical work
```

Current OpenAI candidate mappings are Luna -> Terra -> Terra/high -> GPT-5.6/high. GPT-6 Astra is intentionally only a critical-tier benchmark candidate until its additional cost produces measurable quality gain.

See [`config/model-profiles.yaml`](config/model-profiles.yaml) and the dated source snapshot in [`research/sources/`](research/sources/).

## Codex adapter

The first experimental adapter provides seven custom-agent TOML files and a conservative `[agents]` baseline capped at four concurrent child threads. This is deliberately lower than some example fan-outs until benchmarks prove more parallelism is worthwhile.

See [`adapters/codex/README.md`](adapters/codex/README.md).

## Validation

```bash
python scripts/validate_structure.py
```

The validator checks required research, policies, schemas, all seven core roles, routing seed cases and Codex adapter artifacts without third-party Python packages.

## Roadmap

- **v0.0.x — Research foundation:** exit criteria reached; research remains continuous.
- **v0.1.0 — Core agents:** core role candidates + Codex adapter exist; generator and executable routing evals remain.
- **v0.2.0 — Efficiency controls:** context budgets, model-tier/token/latency benchmarks, escalation regressions.
- **v0.3.0 — Engineering specialists:** Embedded, STM32, ROS 2, Robotics and tooling roles accepted only when they outperform generic roles.
- **v0.4.0 — Evaluation/portability:** multiple adapters, routing accuracy and ablation studies.
- **v1.0.0 — Stable stack:** benchmark-backed defaults, reproducible installer/generator and migration strategy.

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Current status

**Research Wave 2 complete; v0.1 core stack is experimental.** The next gate is not more agent count: it is executable routing evaluation, adapter generation/drift checking, and measured Luna/Terra/GPT-5.6 quality-cost benchmarks.

## License

MIT. See [`LICENSE`](LICENSE).
