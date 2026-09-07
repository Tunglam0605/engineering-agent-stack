# Engineering Agent Stack

> Research-driven, provider-aware engineering agents focused on **quality per unit of cost**, not maximum agent count.

[![Status](https://img.shields.io/badge/status-v0.1%20candidate%20%2B%20v0.2%20benchmarks-orange)](#roadmap)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Why this project exists

AI coding systems become wasteful when every task receives the strongest model, every problem spawns multiple agents, or every worker inherits a large context. This repository studies strong community and official implementations, extracts measurable patterns, and turns them into a small engineering stack.

The objective is:

```text
maximize:   quality / (cost × latency)
subject to: quality >= required threshold for the task risk
```

The project therefore optimizes **routing, context, evidence, and verification**, not agent count.

## Design principles

1. **Direct-first** — trivial/reversible work should not pay delegation overhead.
2. **Role != compute profile != provider** — expertise, budget, and runtime remain separate.
3. **Risk-adjusted routing** — escalate only when uncertainty or failure cost justifies it.
4. **Bounded/isolated context** — send the smallest useful context and return evidence, not transcripts.
5. **Adaptive budgets** — constrain waste, not the evidence required for correctness.
6. **Deterministic coordination, bounded autonomy** — the parent owns decomposition, integration and stop/escalate decisions.
7. **Independent verification** — meaningful changes are checked by a separate verification/review path.
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
adapters/        Provider/tool-specific generated integration layers
scripts/         Validation, installation, generation and evaluation tooling
docs/            Architecture, provenance, installation and roadmap
```

## Quick start with Codex

The current Codex adapter is a **v0.1 candidate** suitable for project-scoped smoke testing.

Generate/check the adapter:

```bash
python -m pip install -r requirements-dev.txt
python scripts/generate_codex_adapter.py
python scripts/generate_codex_adapter.py --check
```

Install into one project first:

```bash
python scripts/install_codex.py --project /path/to/project --dry-run
python scripts/install_codex.py --project /path/to/project
python scripts/install_codex.py --project /path/to/project --check
```

The installer copies generated role TOMLs into `<project>/.codex/agents/`. It never rewrites an existing Codex `config.toml`; existing configuration must be reviewed/merged deliberately.

See [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md) and [`adapters/codex/README.md`](adapters/codex/README.md).

## Research method

Every source is evaluated on taxonomy, role contract, delegation, model routing, context, concurrency/write ownership, verification, escalation, cost control, observability and portability.

Patterns are classified as **ADOPT**, **ADAPT**, **EXPERIMENT**, **REJECT**, or **HISTORICAL**. The implementation is a local synthesis; research sources are not treated as anonymous idea pools.

The current matrix covers fifteen sources:

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

Detailed research lineage and thanks are in [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md). The rules for conceptual references, adapted material, vendored material, generated material, and license-aware reuse are in [`docs/PROVENANCE.md`](docs/PROVENANCE.md).

Useful research artifacts:

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

These are benchmark candidates, not permanent role identities. See [`config/model-profiles.yaml`](config/model-profiles.yaml).

## Adaptive context/result budgets

Token control is split into three concerns:

```text
INPUT CONTEXT  -> bounded to relevant task evidence
WORK BUDGET    -> adaptive; do not starve correctness
RESULT BUDGET  -> compressed evidence instead of transcript dumps
```

Suggested result sizes vary by role and task complexity rather than imposing one hard total-token quota. Critical/safety evidence may exceed normal result targets when required.

See [`policies/context-budget.md`](policies/context-budget.md).

## Controlled benchmark suite

`benchmarks/tasks/index.yaml` defines the initial `controlled-v1` suite for repeated model/routing comparisons. It includes repository discovery, bounded implementation, seeded reviewer regressions, and direct-vs-delegated trivial work.

```bash
python scripts/validate_task_suite.py
```

Materialize a clean controlled run:

```bash
python scripts/prepare_benchmark_task.py \
  --task-id scout-symbol-001 \
  --experiment-id scout-luna-vs-terra \
  --model gpt-5.6-luna \
  --reasoning-effort medium \
  --profile cheap
```

The quality gate is evaluated before token/cost/latency preference. See [`benchmarks/README.md`](benchmarks/README.md) and [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Routing policy eval

`evals/routing-cases.yaml` contains structured **post-classification** fixtures. The evaluator tests policy behavior without pretending that keyword matching is an LLM routing benchmark.

```bash
python scripts/evaluate_routing.py
```

Natural-language classifier quality is evaluated separately from deterministic policy routing.

## Codex adapter

The Codex adapter is generated from canonical role YAML plus semantic compute-profile mappings.

```bash
python scripts/generate_codex_adapter.py
python scripts/generate_codex_adapter.py --check
```

The `--check` mode is a drift gate: CI fails if committed Codex TOMLs differ from canonical generation.

Current public Codex layout used by this adapter:

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

Run current local checks:

```bash
python scripts/validate_structure.py
python scripts/validate_provenance.py
python scripts/validate_agents.py
python scripts/evaluate_routing.py
python scripts/validate_task_suite.py
python scripts/validate_benchmarks.py
python scripts/generate_codex_adapter.py --check
```

GitHub Actions runs these gates plus controlled-task, installer, and capture-pipeline smoke tests on pushes and pull requests.

## Acknowledgements and attribution

This repository is deliberately built from **credited research**, not unattributed copying. We thank the maintainers and contributors of the fifteen upstream projects listed above for publishing systems the engineering community can study.

The project currently treats those upstream repositories as conceptual research inputs unless a local file explicitly records adapted/vendored material. Direct reuse must preserve the upstream license/notice requirements and record exact provenance before merge.

See:

- [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md) — full upstream source list and what we learned from each project
- [`docs/PROVENANCE.md`](docs/PROVENANCE.md) — attribution/reuse policy
- [`research/matrix/repository-comparison.yaml`](research/matrix/repository-comparison.yaml) — design decisions derived from research

No endorsement, sponsorship, or affiliation by those upstream projects is implied.

## Roadmap

- **v0.0.x — Research foundation:** exit criteria reached; research remains continuous.
- **v0.1.0 — Core agents:** candidate-complete; project-scoped Codex installation/smoke testing is now supported.
- **v0.2.0 — Efficiency controls:** controlled benchmark suite, run capture, adaptive context/result budgets, repeated model-tier experiments and routing measurements.
- **v0.3.0 — Engineering specialists:** Embedded, STM32, ROS 2, Robotics and tooling roles only when benchmark evidence justifies them.
- **v0.4.0 — Evaluation/portability:** multiple adapters, routing accuracy and specialist-vs-core ablation.
- **v1.0.0 — Stable stack:** benchmark-backed defaults, reproducible installer, migration strategy and compatibility policy.

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Current status

**v0.1 core/installation candidate + active v0.2 benchmark infrastructure.** The stack is ready for controlled project-scoped Codex trials; model routing defaults remain benchmark-gated until repeated real runs demonstrate the required quality/cost trade-off.

## License

Engineering Agent Stack itself is released under the MIT License. See [`LICENSE`](LICENSE).

Upstream projects retain their own licenses and copyrights. Refer to each upstream repository and [`docs/PROVENANCE.md`](docs/PROVENANCE.md) before directly reusing third-party material.
