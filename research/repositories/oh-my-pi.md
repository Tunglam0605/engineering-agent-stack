# can1357/oh-my-pi

- Repository: https://github.com/can1357/oh-my-pi
- Classification: conceptual reference
- Studied for: runtime agent discovery/resolution, delegation preflight, agent status/observability, bounded context management, checkpoint-style context reduction, and provider/model indirection.

## Useful patterns

- Resolve role/model/tool policy before launching child work instead of discovering incompatibility after execution starts.
- Keep role identity separate from the concrete provider/model chosen at runtime.
- Make parent/child task state and known telemetry inspectable; missing telemetry should remain unknown.
- Reduce long investigation context into bounded evidence rather than forwarding entire transcripts.
- Treat persistent memory as supporting context that must be checked against current evidence.

## Risks / limitations for this project

`oh-my-pi` is a broad coding-agent runtime with a large tool/provider surface. Recreating its TUI, built-in tool catalog, provider catalog, or full runtime would duplicate capabilities already supplied by Codex/other providers and would move this repository away from its small orchestration-policy objective.

## Decisions

- Delegation preflight: **ADAPT** into a provider-neutral local contract.
- Runtime role/model resolution: **ADAPT** through semantic compute profiles and provider adapters.
- Lightweight agent registry/status: **ADAPT** without a dedicated TUI.
- Checkpoint/evidence-packet context reduction: **EXPERIMENT** through controlled benchmarks.
- Memory as heuristic context: **EXPERIMENT** later; repository evidence remains authoritative.
- Full native tool runtime / large provider catalog: **REJECT** for the current roadmap.

## Local artifacts affected

- `runtime/` provider-neutral runtime contracts
- `schemas/delegation-preflight.yaml`
- `schemas/resolved-execution-plan.yaml`
- `schemas/agent-status.yaml`
- `schemas/context-packet-benchmark.yaml`
- `policies/delegation.md`
- `policies/context-budget.md`
- v0.2 benchmark plan and roadmap

No upstream code, prompts, or documentation text is copied into these artifacts.
