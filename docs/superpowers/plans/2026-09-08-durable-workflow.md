# Durable Workflow & Recovery v0.5.0

Goal: resume parent workflow and reconcile interrupted assignments without duplicate execution authorization.

Architecture: extend the existing Git-metadata snapshot under its exclusive lock and revision CAS. Store checkpoint, approvals and recovery receipts in that atomic snapshot. Keep JSONL as nontransactional observations; export both with explicit completeness semantics. No rollback from checkpoints: corrupt state requires operator investigation, never guessed reconstruction.

Constraints: Python 3.9+, seven unchanged roles, unchanged model mappings, stack-controlled enforcement only. No commit until independent read-only review returns PASS_FOR_COMMIT and all local gates pass.

Design:
- Checkpoint records stage plus bounded verification/review/provider evidence references; it does not authorize work or rewind assignment state.
- Pending/running assignments become suspect after policy-defined inactivity or total age. Status is read-only. Suspects continue reserving capacity.
- Recover plans reference current revision and checkpoint. Applying recovery renews the same assignment to pending only with explicit operator approval including old-executor-stopped evidence. No native process termination or dispatch.
- Approval binds action, target, revision, approver, reason, evidence and expiry. Consumption and mutation are atomic; receipts make retries idempotent. Any intervening mutation invalidates unused approval.
- Risky lifecycle transitions (active to failed/blocked, failed/blocked reactivation) require the same approval mechanism. Ordinary completion and existing CLI syntax remain supported.
- State writes flush/fsync before replacement; POSIX also fsyncs the metadata directory. Crash-left locks are never automatically stolen.

Implementation and gates:
- [x] Add failing recovery/checkpoint/approval/export tests, including concurrent processes and corruption.
- [x] Implement runtime workflow module, state validation/durability and lifecycle integration; run focused tests.
- [x] Extend goal CLI, policy/schema/docs/version and cross-platform clean-wheel smoke.
- [x] Run Python 3.9 and available current Python tests, all validators, adapter drift, YAML checks, offline acceptance, diff check and clean-wheel smoke.
- [x] Independent read-only reviewer; resolve every High/Medium blocker and obtain PASS_FOR_COMMIT.
- [ ] Commit/push main; await Linux/Windows validate, then annotated v0.5.0 tag; await release jobs and verify assets.
- [ ] Safe-update personal managed checkout; verify version/doctor/check and installed goal smoke.

Alternatives considered: separate checkpoint/approval files introduce partial multi-file commits; replaying the existing JSONL would overstate its durability. Both rejected in favor of extending the existing snapshot transaction.

Local execution evidence: Python 3.9 full suite 116 tests OK (one POSIX-only skip on Windows); Python 3.11 full suite 115 tests plus the final 24-test workflow suite OK. All validators, adapter drift, YAML/installer syntax, offline acceptance, diff check and rebuilt clean Python 3.9 wheel recovery smoke passed. Independent read-only review found one Medium missing-v2-revision defect, resolved with a failing-then-passing read/write corruption regression; follow-up returned PASS_FOR_COMMIT.
