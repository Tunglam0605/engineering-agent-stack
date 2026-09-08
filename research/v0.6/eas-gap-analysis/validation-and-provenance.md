# Validation and provenance plan

Status: research proposal. Current v0.5 validators do not validate future v0.6 contracts.

Implementation must test: closed/duplicate-safe parsing; size/depth limits; traversal/absolute/UNC/symlink/reparse/case collisions; identity/version/capability compatibility; content digests; provenance coverage; deterministic resolution/lineage; protected-field override refusal; skill role/effect/context behavior; no silent `gate` downgrade; stable snapshot hashing on Python 3.9/OSes; preflight/lifecycle digest agreement; goal-state migration and recovery drift refusal; installed-package resource smoke if built-ins enter the wheel.

Adversarial fixtures should include malicious fields (`model`, `sandbox`, `tools`, `hooks`, `command`, `agents`, `permissions`), contradictory skill prose, missing gate/check, policy-weakening overlays, config changes between spawn/recovery, stale hardware/CI evidence, false-positive detection, mixed monorepos and resource-limit boundaries.

Before stable defaults, `embedded`, `ros2`, and `release` need controlled representative repos/tasks comparing core-only vs preset quality, omissions, false positives and context cost. Embedded needs at least one hardware-sensitive case; ROS2 needs a real package/distribution + declared quality target; release needs successful and failed candidates.

Provenance stays conceptual for this audit. Future copied/adapted upstream text/code requires new file-level license/provenance review. Do not reproduce proprietary MISRA rules. Hashes prove identity/drift only.
