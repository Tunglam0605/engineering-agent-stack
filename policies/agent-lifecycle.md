# Agent Lifecycle and Fan-Out Policy

The objective is to keep multi-agent work useful, bounded, and legible. More child assignments are not evidence of better engineering. The parent remains responsible for decomposition, reuse, integration, and stopping conditions.

## Resume before spawn

Before creating a new child, the parent should first ask whether an existing child with the same role and problem domain can receive a follow-up. Reuse is preferred when the prior evidence is still relevant and the scope is materially the same.

A fresh child is justified when:

- independent parallel read work materially reduces elapsed time;
- independent review requires a separate context; or
- the previous child context is stale, wrong, or materially mismatched to the new scope.

Do not spawn a second worker merely because the first worker completed one turn. Follow-up/resume behavior should continue a bounded investigation without paying for a fresh context every time.

## Goal fan-out budget

Default orchestration guidance:

```text
parallel readers                    <= 4 hard ceiling
effective active children           = adaptive 2 / 3 / 4
  conservative                      = 2
  balanced                          = 3
  read-heavy                        = 4 (read-only only)
parallel writers                    <= 1 scope owner
soft child-assignment budget        = 8 per goal
hard ordinary-spawn ceiling         = 12 per goal
same role + same domain + same scope active       <= 1
architect consultation default      = 1 per goal
reviewer default                    = 1 per meaningful change-set
recursive delegation                = disabled
```

The soft budget is a reconciliation point, not a success target. At 8 child assignments, the parent should inspect completed/active work, merge overlapping investigations, prefer follow-up on existing children, and state why any additional spawn is still useful.

The hard ceiling applies to ordinary orchestration. At 12 child assignments, stop creating ordinary new children and integrate, serialize, or escalate. Explicit diagnostic instructions and a required independent safety/release review may override the ceiling only when the parent records the reason.

## Expensive-role reuse

Architect and reviewer calls are deliberately scarce:

- Reuse the same architect for follow-up on the same architectural decision. A second architect consultation is justified only when assumptions, interfaces, or safety constraints materially changed.
- Reuse the same independent reviewer for fix verification on one change-set. Spawn another reviewer only when a genuinely separate independent opinion is required.

## Naming

Use short stable assignment labels such as:

```text
scout: gateway
debugger: packaging
reviewer: release
architect: ota contract
```

Avoid gratuitous version suffixes such as `v030`, `retry-2`, or `final-final` when the same child can be resumed. Names should describe responsibility, not execution chronology.

## Transaction safety

Committed goal lifecycle changes are serialized by a per-goal lock under Git metadata and protected by a monotonic state revision. A stale caller must fail rather than overwrite a newer assignment registry. Lock files are not silently broken on timeout; an operator should confirm the other EAS process is gone before removing a stale lock.

## Durable recovery and approval

The canonical routing policy defines inactivity, total-attempt timeout and approval TTL in seconds. Pending/running assignments crossing either threshold become suspect, never automatically stopped or failed. They continue reserving capacity; stack-controlled dispatch escalates until reconciliation.

Recovery requires explicit operator attestation that the prior executor stopped, bound to action, assignment and the current revision, with approver, reason and expiry. Approval issuance advances the revision and binds to that resulting snapshot. Consumption and mutation share the goal transaction. Recovery preserves the assignment ID and original scope, resets the attempt clock and returns it to pending without native dispatch. Consumed approvals return historical receipts on retry and cannot rewind later execution.

Active-to-failed/blocked transitions, changes out of failed/blocked, running-to-pending reset and transitions of suspect assignments require this approval evidence. Reactivation continues to enforce capacity and scope conflicts. Nonsuspect ordinary completion remains supported. Checkpoints carry bounded parent-stage and verification/review/provider evidence references, never rollback or execution authority. Corrupt durable state fails closed; observational JSONL is not a recovery source.

These attestations are checked by stack-controlled APIs; they do not authenticate operator identity or independently prove a provider process exited. See [workflow operations and trust boundary](../docs/WORKFLOW.md).

## Observability

Transport/session recovery uses explicit reason categories and finite lineage budgets: two resumes,
then at most one replacement with bounded handoff and stopped-executor approval. Failed corruption
resume may use that replacement immediately. Missing evidence or exhausted recovery escalates to
the parent. Unresolved recovery is a dispatch barrier; reconnecting executors retain capacity.
See [transport recovery operations](../docs/WORKFLOW.md#transport-and-session-recovery-v063).

The agent registry may summarize total, active, completed/failed/blocked, terminal, and per-role assignment counts. Unknown provider telemetry remains unknown. Fan-out warnings are policy signals, not fabricated provider measurements.

Example for one goal snapshot:

```bash
python scripts/agent_status.py --input status.json --summary --goal-id root-1
```

If a snapshot contains multiple parent goals and no `--goal-id` is supplied, summary generation refuses rather than combining unrelated work into one budget.

## Provider boundary

These rules are parent-orchestration policy. They do not claim that EAS transparently intercepts every provider-native `spawn_agent` call. Strong stack-controlled delegation still requires the parent/provider adapter to honor the policy and preflight contract explicitly.
