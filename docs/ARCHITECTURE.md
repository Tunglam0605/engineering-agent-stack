# Architecture

## Objective

The stack optimizes engineering outcomes under three constrained resources: model capability, context/token budget and latency.

A routing decision should minimize unnecessary compute while preserving the quality threshold implied by task risk.

## Layers

### 0. Distribution layer

`eas_cli/`, `install.ps1`, and `install.sh` are the operational surface for installation, project initialization, health/status, guarded updates, and ownership-aware uninstall. This layer does not redefine role semantics or provider execution; it manages the artifacts that expose the stack to Codex.

The recommended personal distribution is source-managed under `~/.codex/engineering-agent-stack`, with seven generated role files under `~/.codex/agents/` and a launcher under `~/.local/bin/`. Update and uninstall are deliberately conservative so distribution automation never becomes an implicit overwrite mechanism.

See [`DISTRIBUTION.md`](DISTRIBUTION.md).

### 0a. Identity and attribution layer

`config/project-identity.yaml` is the canonical public identity for EAS. Provider adapters inherit this identity at generation time so all seven child roles consistently attribute the EAS layer to **Nguyễn Khắc Tùng Lâm (Tùng Lâm Automation)** while keeping foundation-model/provider authorship separate. Private contact data, credentials, account identifiers, and unrelated biography are intentionally excluded from the agent prompt surface.

See [`PROJECT_IDENTITY.md`](PROJECT_IDENTITY.md).

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

### 5a. Declarative capability layer (v0.6)

v0.6 inserts a deterministic capability-resolution layer **before** stack-controlled execution without replacing the existing preflight/lifecycle engine:

```text
tracked .eas/project.toml / explicit preset
        |
        v
strict contract loader
        |
        v
built-in declarative catalog
        |
        +--> read-only detector (recommendation only)
        |
        v
core < extension < preset < project < CLI resolver
        |
        v
ResolvedCapabilitySnapshot (canonical JSON + SHA-256)
        |
        +--> lazy bounded skill selection (max 3)
        +--> trusted checker references
        +--> delegation-plan digest
        `--> .git/eas/capabilities/snapshot.json
                 |
                 `--> goal lifecycle binding / explicit migration
```

Public declarative contracts are exactly `extension-manifest`, `skill`, `rule`, `preset`, and `project-profile`. The built-in presets are `embedded`, `ros2`, and `release`. The seven core roles remain unchanged.

The extension trust boundary is intentionally closed: no scripts, hooks, entrypoints, dynamic imports/eval, dependency solver, preset inheritance, MCP auto-launch, or remote-code/schema loading. Rules may reference only trusted EAS-core checker IDs; extension content does not supply executable validators.

Resolver precedence is exactly:

```text
core defaults < extension defaults < preset < .eas/project.toml < explicit CLI override
```

Ordinary lists replace atomically. `rules.required_rules` is the only additive list. Unknown/null/deep-merge fields and equal-precedence extension conflicts fail closed. Per-field lineage and source digests are stored in the resolved snapshot.

Detection identifies repository context, never readiness. A tracked project profile remains authoritative when detector evidence disagrees. Snapshot drift/corruption blocks configured stack-controlled operations until explicit migration; legacy projects without `.eas/project.toml` keep v0.5 semantics.

See [`../research/v0.6/contract-freeze.md`](../research/v0.6/contract-freeze.md) for the normative contract.

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

## Codex-native stable baseline (v0.6.5, retained in v0.6.6)

For ordinary Codex subagent work, the default runtime path deliberately stays close to the proven v0.3 shape:

```text
parent Codex
    -> select EAS role
    -> native spawn_agent
    -> native wait/follow-up
    -> child result
    -> parent integration
```

Codex owns child process/session lifecycle and transport. EAS does not insert checkpoint, approval, capability-snapshot or recovery machinery into every native child call. Those services remain available for stack-controlled or explicitly initialized durable goals, where their stronger audit/recovery contract is useful. This single-owner boundary avoids competing lifecycle controllers while preserving EAS role intelligence and guardrails.

## Agent efficiency layer (v0.6.6)

The native execution boundary is unchanged. v0.6.6 reduces unnecessary fan-out by making conservative two-child scheduling the `auto` default, persisting reuse/recovery efficiency counters for durable goals, and tightening durable fan-out to soft/hard 6/8. `balanced=3` and `read-heavy=4` remain explicit opt-in ceilings rather than defaults. Efficiency telemetry does not estimate provider token, cost or latency data.

## Concurrency and lifecycle

Parallelism is valuable mainly for independent, read-heavy work. Concurrent write assignments require disjoint path ownership. Shared-file work is serialized unless a future transactional mechanism proves safe.

The lifecycle policy is resume-before-spawn with **adaptive concurrency**. Codex is configured with a provider/session ceiling of four children, while EAS resolves a smaller effective cap per dispatch: `conservative=2`, `balanced=3`, and `read-heavy=4`. `auto` selects conservative scheduling for write-capable work and balanced scheduling for read-only work. If a writer is already active, a read request is downshifted to the conservative combined cap; writer scope ownership remains serialized at one. `read-heavy=4` is reserved for explicitly independent read-only work with bounded output.

The goal still has a soft reconciliation point at eight child assignments and an ordinary hard spawn ceiling at twelve. Architect is normally one consultation per goal and reviewer one independent worker per meaningful change-set; follow-up/resume is preferred when continuity is useful. These are orchestration-policy limits, not a claim that provider-native spawn APIs are automatically intercepted. See `policies/agent-lifecycle.md`.

From v0.4, stack-controlled orchestration can use `runtime/lifecycle.py` / `eas goal gate` as an executable decision boundary. Goal state and JSONL events live under Git metadata so observability does not dirty the worktree. The gate remains opt-in: native provider dispatch that bypasses it is not claimed to be intercepted.

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
