# v0.6 research checkpoint

Status: **CLOSED — architecture frozen; v0.6.0 implementation validated against the frozen contract.**

## Recommended architecture

`EAS core (7 roles + v0.5 lifecycle/recovery) -> declarative resolver -> ResolvedCapabilitySnapshot -> selected skills/rules/settings/preset/project profile`.

The same snapshot is pinned to stack-controlled preflight, lifecycle admission, goal state and recovery so a preset/config edit cannot silently change an active assignment.

## Decisions ready for approval

1. Keep exactly seven core roles; extensions never define agents/models.
2. v0.6 packages are local/declarative: no arbitrary executable plugin/hook/installer/command/MCP-server mechanism.
3. Separate SKILL, RULE, CONFIG, PRESET and EXTENSION contracts.
4. One active preset initially; explicit extra skills + additive required rules. First candidates: `embedded`, `ros2`, `release`; security is universal.
5. Deterministic closed config resolution with lineage; no hidden ancestor/environment cascade.
6. Immutable/hashable `ResolvedCapabilitySnapshot`, pinned to active work/recovery.
7. Protected core invariants are outside override scope.
8. Guidance, validator and real gate stay distinct; descriptors cannot fabricate enforcement.
9. Detection recommends with evidence/rationale only; no silent activation.
10. Missing/unsupported/stale required evidence remains UNKNOWN/unverified and blocks/escalates as declared.

## Implemented sequence

A. closed schemas + strict parser + deterministic resolver + canonical snapshot; B. tracked project profile + built-in declarative `embedded/ros2/release` packages and recommendation-only detection; C. explicit snapshot binding to preflight/lifecycle/goal/recovery with state migration; D. trusted checker registry and stack-controlled validation boundaries; E. metadata-first lazy skill loading, Python 3.9 regression coverage, and clean-wheel release hardening.

Non-goals: extra role catalog, full runtime/marketplace/dependency solver, package code execution, custom provider permissions/model maps, silent auto-activation, compliance certification, or transparent interception of native Codex child calls.

Research execution note: Codex hit quota after collecting substantial evidence and Claude fallback could not establish a usable API session; artifacts were completed locally from retained evidence. No runtime files were modified by this checkpoint.

## Freeze handoff

Research questions required for v0.6 implementation are closed. The normative handoff is [`contract-freeze.md`](contract-freeze.md). No source study identified a need for additional core roles, executable extensions, dependency solving, preset inheritance, or implicit activation. Any implementation deviation from the freeze requires an explicit architecture revision rather than a silent compatibility shim.
