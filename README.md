# Engineering Agent Stack

> Research-driven, provider-aware engineering agents focused on **quality per unit of cost**, not maximum agent count.

[![Status](https://img.shields.io/badge/status-v0.1%20candidate-orange)](#roadmap)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Why this project exists

AI coding systems become wasteful when every task receives the strongest model, every problem spawns multiple agents, or every worker inherits a large context. This repository studies strong community and official implementations, extracts measurable patterns, and turns them into a small engineering stack.

The objective is:

```text
maximize:   quality / (cost × latency)
subject to: quality >= required threshold for the task risk
```

The project therefore optimizes **routing and evidence**, not agent count.

## Design principles

1. **Direct-first** — trivial/reversible work should not pay delegation overhead.
2. **Role != compute profile != provider** — expertise, budget, and runtime remain separate.
3. **Risk-adjusted routing** — escalate only when uncertainty or failure cost justifies it.
4. **Bounded/isolated context** — send the smallest useful context and return evidence, not transcripts.
5. **Deterministic coordination, bounded autonomy** — the parent owns decomposition, integration and stop/escalate decisions.
6. **Independent verification** — meaningful changes are checked by a separate verification/review path.
7. **Safe parallelism** — parallelize independent read-heavy work; partition or serialize writes.
8. **Runtime-enforced permissions** — sandbox/tool controls are security boundaries; prompts are not.
9. **Evidence before completion** — use the narrowest validation that can prove the claim.
10. **Benchmark before belief** — model/routing choices remain candidates until measured.

## Architecture

```text
User / Task
    |
    v
Orchestrator / Main Agent
    |
    +--> classify task shape + risk
    +--> direct vs delegate
    +--> role + semantic compute profile
    +--> provider adapter
    +--> bounded context + write ownership
    |
    +--> Scout / Researcher       [read-heavy]
    +--> Implementer / Debugger   [bounded write]
    +--> Test Engineer            [verification]
    +--> Reviewer / Architect     [independent assurance]
    |
    v
Quality Gate -> Result / Escalation / Block
```

The canonical layers are:

```text
ROLE             What expertise/responsibility is needed?
COMPUTE PROFILE  How much model/reasoning budget is justified?
PROVIDER         Which runtime/model executes it?
POLICY           When may it run, write, escalate, or stop?
EVAL             Does the route preserve required quality?
BENCHMARK        At what token, cost and latency budget?
```

## Repository layout

```text
agents/          Provider-neutral role definitions and specialist catalog
config/          Semantic compute profiles and routing policy
policies/        Delegation, escalation, context and quality rules
research/        Source analysis, primary-source notes, patterns and anti-patterns
schemas/         Stable role/result contracts
evals/           Routing and quality evaluation fixtures
benchmarks/      Cost/latency/quality experiments
adapters/        Provider/tool-specific generated integration layers
scripts/         Validation, generation and evaluation tooling
docs/            Architecture and roadmap
```

## Research method

Every source is evaluated on taxonomy, role contract, delegation, model routing, context, concurrency/write ownership, verification, escalation, cost control, observability and portability.

Patterns are classified as **ADOPT**, **ADAPT**, **EXPERIMENT**, or **REJECT**. Historical sources may also be marked **HISTORICAL**.

The current matrix covers fifteen sources, including `agency-agents`, `oh-my-codex`, OpenAI Codex/Agents SDK, Microsoft Agent Framework, LangGraph/Deep Agents, CrewAI, smolagents, OpenHands, and CLI Agent Orchestrator.

See:

- [`research/matrix/repository-comparison.yaml`](research/matrix/repository-comparison.yaml)
- [`research/patterns/wave-2-synthesis.md`](research/patterns/wave-2-synthesis.md)
- [`research/repositories/openai-codex.md`](research/repositories/openai-codex.md)

## Core roles — v0.1 candidate

| Role | Primary responsibility | Default access | Codex candidate |
|---|---|---|---|
| Scout | repository discovery/call-flow mapping | read-only | Luna / medium |
| Researcher | current primary-source technical evidence | read-only + network intent | Luna / medium |
| Implementer | bounded approved implementation | workspace-write | Terra / medium |
| Debugger | evidence-first root cause/remediation | workspace-write | Terra / high |
| Test Engineer | targeted validation/failure evidence | test/build | Terra / medium |
| Reviewer | independent correctness/regression review | read-only | Terra / high |
| Architect | high-risk system decisions/tradeoffs | read-only | Sol / high |

Canonical definitions live under [`agents/core/`](agents/core/). Model names never appear in canonical role identity.

## Compute profiles

```text
cheap     -> Luna; scanning/classification/high-volume bounded work
standard  -> Terra/medium; ordinary implementation/testing/research
deep      -> Terra/high; difficult debugging and high-confidence review
critical  -> Sol/high; architecture, realtime/safety/security/release assurance
```

GPT-6 Astra remains a critical-tier benchmark candidate rather than a default until task-level measurements justify its additional per-token price.

See [`config/model-profiles.yaml`](config/model-profiles.yaml).

## Routing policy eval

`evals/routing-cases.yaml` contains structured **post-classification** fixtures. The evaluator tests policy behavior without pretending that keyword matching is an LLM routing benchmark.

```bash
python scripts/evaluate_routing.py
```

Natural-language classifier quality will be evaluated separately in v0.2.

## Codex adapter

The Codex adapter is generated from canonical role YAML plus semantic compute-profile mappings.

```bash
python scripts/generate_codex_adapter.py
python scripts/generate_codex_adapter.py --check
```

The `--check` mode is a **drift gate**: CI fails if committed Codex TOMLs differ from canonical generation.

Current public Codex behavior uses:

```text
project roles   .codex/agents/*.toml
personal roles  ~/.codex/agents/*.toml
global controls [agents] in config.toml
```

See [`adapters/codex/README.md`](adapters/codex/README.md).

## Validation

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run all current local checks:

```bash
python scripts/validate_structure.py
python scripts/validate_agents.py
python scripts/evaluate_routing.py
python scripts/generate_codex_adapter.py --check
```

GitHub Actions runs the same gates on pushes and pull requests.

## Roadmap

- **v0.0.x — Research foundation:** exit criteria reached; research remains continuous.
- **v0.1.0 — Core agents:** canonical roles, semantic validation, deterministic policy eval and generated Codex adapter are now present; release hardening remains.
- **v0.2.0 — Efficiency controls:** token/cost/latency capture, model-tier benchmarks, classifier evals, escalation regressions.
- **v0.3.0 — Engineering specialists:** Embedded, STM32, ROS 2, Robotics and tooling roles only when benchmark evidence justifies them.
- **v0.4.0 — Evaluation/portability:** multiple adapters, routing accuracy and specialist-vs-core ablation.
- **v1.0.0 — Stable stack:** benchmark-backed defaults, reproducible installer, migration strategy and compatibility policy.

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Current status

**v0.1 core infrastructure candidate.** The next priority is not more agents: it is measuring whether Luna/Terra/Sol routing preserves quality while reducing token and latency cost.

## License

MIT. See [`LICENSE`](LICENSE).
