# Architecture

## Objective

The stack optimizes engineering outcomes under three constrained resources: model capability, context/token budget and latency.

A routing decision should minimize unnecessary compute while preserving the quality threshold implied by task risk.

## Layers

### 0. Distribution layer

`eas_cli/`, `install.ps1`, and `install.sh` are the operational surface for installation, project initialization, health/status, guarded updates, and ownership-aware uninstall. This layer does not redefine role semantics or provider execution; it manages the artifacts that expose the stack to Codex.

The recommended personal distribution is source-managed under `~/.codex/engineering-agent-stack`, with seven generated role files under `~/.codex/agents/` and a launcher under `~/.local/bin/`. Update and uninstall are deliberately conservative so distribution automation never becomes an implicit overwrite mechanism.

See [`DISTRIBUTION.md`](DISTRIBUTION.md).

### 1. Orchestration layer

Responsibilities:

- classify task shape and risk
- decide direct execution vs delegation
- select role(s)
- select semantic compute profile
- allocate context budget
- enforce concurrency/write ownership
- evaluate evidence and escalate when necessary

The orchestrator owns integration. Workers do not silently expand scope.

### 2. Core role layer

Core roles are intentionally generic and small. Domain specialization is introduced through specialist roles or skills only when repeated evidence shows a benefit.

### 3. Compute profile layer

Roles reference semantic profiles (`cheap`, `standard`, `deep`, `critical`) rather than provider model names. Provider adapters resolve these profiles to available models and reasoning settings.

### 4. Policy layer

Policies define delegation, escalation, context limits, write ownership and quality gates. Policies are independent from individual role prose.

### 5. Provider-neutral runtime resolution layer

For **stack-controlled delegation**, the recommended executable path is:

```text
classified task
    -> routing decision
    -> delegation preflight
    -> resolved execution plan
    -> provider adapter
    -> execution
    -> agent status / observed telemetry
    -> quality gate
```

`scripts/resolve_delegation.py` is the executable boundary for this contract. Preflight emits `PASS`, `REJECT`, or `ESCALATE` with structured reasons; only `PASS` can produce a resolved plan. The plan records role/profile/provider/model resolution, permissions/write ownership, recursion metadata, review requirement, and context budget. Provider-specific reasoning overrides remain in adapter metadata.

This layer is **not a transparent hook inside provider-native runtimes**. Installing the Codex role files/config does not cause this Python preflight to intercept every native child-agent call. A parent/orchestrator that wants the stronger contract must invoke the resolver (or equivalent library API) before dispatch and then translate the approved plan through the provider adapter. Provider-native sandbox/tool controls remain the security boundary.

The lightweight agent registry is observability, not orchestration authority. Unknown provider telemetry stays unknown.

### 6. Evaluation layer

Evals answer: "Does this routing/role/prompt preserve required quality?"

Benchmarks answer: "At what token, latency and cost budget?"

The v0.2 context-packet experiment compares a full evidence set with a bounded packet that must retain required evidence. Character count and a deterministic token proxy establish the harness; real provider token/latency evidence is added only when observed.

## Default execution topology

```text
Task
 |
 v
Classify
 |
 +-- trivial / obvious ----------------------> direct execution -> verify
 |
 +-- read-heavy discovery --> scout/researcher --+
 |                                                |
 +-- bounded implementation --> implementer -----+--> targeted tests
 |                                                |
 +-- difficult root cause --> debugger -----------+
                                                  |
                                                  v
                                        risk-based review
                                                  |
                                    +-------------+-------------+
                                    |                           |
                                  pass                      uncertain
                                    |                           |
                                  done                      escalate
```

## Concurrency and lifecycle

Parallelism is valuable mainly for independent, read-heavy work. Concurrent write assignments require disjoint path ownership. Shared-file work is serialized unless a future transactional mechanism proves safe.

The default lifecycle policy is resume-before-spawn: at most three read-only children in parallel, one writer scope owner, a soft reconciliation point at eight child assignments per goal, and an ordinary hard spawn ceiling at twelve. Architect is normally one consultation per goal and reviewer one independent worker per meaningful change-set; follow-up/resume is preferred when continuity is useful. These are orchestration-policy limits, not a claim that provider-native spawn APIs are automatically intercepted. See `policies/agent-lifecycle.md`.

## Escalation

Escalation is based on evidence, not prestige. Typical triggers:

- low confidence after bounded investigation
- conflicting evidence
- concurrency/realtime/memory-safety complexity
- public API/data compatibility decisions
- security or release-critical changes
- failed targeted re-check

## Provider adapters

Provider adapters translate semantic concepts into tool-specific configuration. A provider adapter must not redefine the canonical meaning of a role or policy.

## Memory authority

Persistent project memory is future work, not part of the v0.2 execution authority. If introduced later, memory is heuristic context only: current repository state and freshly verified external evidence take precedence over remembered summaries.
