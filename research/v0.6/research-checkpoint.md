# v0.6 research checkpoint

Status: **research complete enough for architecture approval; runtime implementation has not started**.

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

## Proposed implementation sequence after approval

A. closed schemas + strict parser + resolver + snapshot/explain (read-only); B. project profile + built-in declarative `embedded/ros2/release` packages and recommendation-only detection; C. bind snapshot to preflight/lifecycle/goal/recovery with state migration; D. trusted validator registry and real stack-controlled gates; E. adapter/progressive skill rendering + benchmark/release hardening.

Non-goals: extra role catalog, full runtime/marketplace/dependency solver, package code execution, custom provider permissions/model maps, silent auto-activation, compliance certification, or transparent interception of native Codex child calls.

Research execution note: Codex hit quota after collecting substantial evidence and Claude fallback could not establish a usable API session; artifacts were completed locally from retained evidence. No runtime files were modified by this checkpoint.
