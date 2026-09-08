# Agent Lifecycle and Fan-Out Policy

The objective is to keep multi-agent work useful, bounded, and legible. More child assignments are not evidence of better engineering. The parent remains responsible for decomposition, reuse, integration, and stopping conditions.

## Resume before spawn

Before creating a new child, the parent should first ask whether an existing child with the same role and problem domain can receive a follow-up. Reuse is preferred when the prior evidence is still relevant and the scope is materially the same.

A fresh child is justified when:

- independent parallel read work materially reduces elapsed time;
- independent review requires a separate context; or
- the previous child context is stale, wrong, or materially mismatched to the new scope.

Do not spawn a second worker merely because the first worker completed one turn. Current Codex V2 follow-up/resume behavior can continue a bounded investigation without paying for a fresh context every time.

## Goal fan-out budget

Default orchestration guidance:

```text
parallel readers                    <= 3
parallel writers                    <= 1 scope owner
soft child-assignment budget        = 8 per goal
hard ordinary-spawn ceiling         = 12 per goal
same role + same scope active       <= 1
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

## Observability

The agent registry may summarize total, active, completed/failed/blocked, terminal, and per-role assignment counts. Unknown provider telemetry remains unknown. Fan-out warnings are policy signals, not fabricated provider measurements.

Example for one goal snapshot:

```bash
python scripts/agent_status.py --input status.json --summary --goal-id root-1
```

If a snapshot contains multiple parent goals and no `--goal-id` is supplied, summary generation refuses rather than combining unrelated work into one budget.

## Provider boundary

These rules are parent-orchestration policy. They do not claim that EAS transparently intercepts every provider-native `spawn_agent` call. Strong stack-controlled delegation still requires the parent/provider adapter to honor the policy and preflight contract explicitly.
