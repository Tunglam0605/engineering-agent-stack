# Engineering Agent Stack

> Research-driven, provider-aware engineering agents focused on **quality per unit of cost**, not maximum agent count.

[![Status](https://img.shields.io/badge/status-research%20foundation-blue)](#roadmap)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Why this project exists

AI coding systems can become wasteful when every task receives the strongest model, every problem spawns multiple agents, or every worker inherits a large context. This repository studies strong community implementations and turns the useful patterns into a small, measurable engineering stack.

The target is not "minimum tokens" and not "maximum intelligence everywhere". The target is:

```text
maximize:   quality / (cost × latency)
subject to: quality >= required threshold for the task risk
```

## Design principles

1. **Direct-first** — do not delegate trivial work.
2. **Role != model** — responsibilities and compute tier are configured separately.
3. **Risk-adjusted routing** — escalate compute only when complexity or failure cost requires it.
4. **Bounded context** — pass the smallest useful task context; return evidence, not transcripts.
5. **Independent verification** — implementation and final review are separate for meaningful changes.
6. **Safe parallelism** — parallelize read-heavy work; partition write ownership before concurrent edits.
7. **Evidence before completion** — a task is done only after the narrowest sufficient validation passes.
8. **Benchmark before belief** — routing decisions should be backed by repeatable evals.

## Architecture

```text
User / Task
    |
    v
Orchestrator
    |
    +--> classify risk + task shape
    +--> choose direct work or specialist
    +--> choose compute profile
    +--> allocate bounded context
    |
    +--> Scout / Researcher       [read-heavy]
    +--> Implementer / Debugger   [bounded write]
    +--> Test Engineer            [verification]
    +--> Reviewer / Architect     [independent assurance]
    |
    v
Quality Gate -> Result / Escalation
```

The project separates three concerns:

```text
ROLE             What expertise/responsibility is needed?
COMPUTE PROFILE  How much model/reasoning budget is justified?
POLICY           When may the role run, write, escalate, or stop?
```

## Repository layout

```text
agents/          Agent role definitions and specialist catalog
config/          Compute profiles, routing policy, budgets
policies/        Delegation, escalation, context and quality rules
research/        Source-repo analysis, patterns and anti-patterns
schemas/         Stable contracts for roles/results/configuration
evals/           Quality and routing evaluation design
benchmarks/      Cost/latency/quality experiments
adapters/        Provider/tool-specific integration layers
scripts/         Validation and repository tooling
docs/            Architecture and roadmap
```

## Research method

Every reference repository is evaluated using the same dimensions:

- agent taxonomy
- role contract
- delegation policy
- routing and model selection
- reasoning level
- context management
- concurrency
- write ownership
- verification
- escalation
- cost control
- portability

A pattern is classified as **ADOPT**, **ADAPT**, **EXPERIMENT**, or **REJECT**. See [`research/`](research/README.md).

## Initial reference set

The first research wave includes:

- [`msitarzewski/agency-agents`](https://github.com/msitarzewski/agency-agents)
- [`Yeachan-Heo/oh-my-codex`](https://github.com/Yeachan-Heo/oh-my-codex)
- [`infiquetra/infiquetra-codex-plugins`](https://github.com/infiquetra/infiquetra-codex-plugins)
- [`trailofbits/codex-config`](https://github.com/trailofbits/codex-config)
- [`KevinBigham/codex-safe-starter`](https://github.com/KevinBigham/codex-safe-starter)
- [`awslabs/cli-agent-orchestrator`](https://github.com/awslabs/cli-agent-orchestrator)

These projects are **references, not upstream code dependencies**. This repository does not copy their prompts wholesale; useful ideas are documented and re-designed around explicit contracts and benchmarks.

## Core roles — planned v0.1

The first implementation deliberately stays small:

| Role | Primary responsibility | Default access |
|---|---|---|
| Scout | repository discovery and call-flow mapping | read-only |
| Researcher | external/official technical evidence | read-only |
| Implementer | bounded implementation from an approved scope | write-limited |
| Debugger | root-cause analysis and targeted remediation | write-limited |
| Test Engineer | targeted validation and failure evidence | test/build |
| Reviewer | independent correctness/regression review | read-only |
| Architect | high-risk architecture and trade-off decisions | read-only |

Specialists such as Embedded, STM32, ROS 2 and Robotics will be added only after the core contracts and evaluation harness are stable.

## Compute profiles

Compute profiles are semantic tiers, not permanent model bindings:

```text
cheap     -> scanning, classification, simple validation
standard  -> ordinary implementation and debugging
deep      -> complex debugging and high-confidence review
critical  -> architecture, realtime/safety/release-critical work
```

Current candidate mappings live in [`config/model-profiles.yaml`](config/model-profiles.yaml). They are intentionally marked as benchmark-driven and replaceable.

## Validation

Run:

```bash
python scripts/validate_structure.py
```

The validator checks required research, policy, schema and configuration artifacts without requiring third-party Python packages.

## Roadmap

- **v0.0.x — Research foundation**: source analysis, decision matrix, architecture contracts.
- **v0.1.0 — Core agents**: seven core roles, output contracts, first Codex adapter.
- **v0.2.0 — Cost optimization**: context budgets, escalation rules, token/latency metrics.
- **v0.3.0 — Engineering specialists**: Embedded, STM32, ROS 2, Robotics and tooling roles.
- **v0.4.0 — Evaluation**: routing accuracy, model-tier benchmarks, regression suite.
- **v1.0.0 — Stable stack**: documented compatibility, installer and repeatable quality gates.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for exit criteria.

## Current status

**v0.0.1 — Research Foundation.** The repository architecture and evaluation discipline are being established before production agent prompts are finalized.

## License

MIT. See [`LICENSE`](LICENSE).
