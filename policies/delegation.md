# Delegation Policy

1. Default to direct execution.
2. Delegate only when it improves quality, speed, safety or context isolation enough to justify overhead.
3. Child work must be bounded by objective, scope and stop condition.
4. Parallel read-heavy tasks are preferred over parallel write-heavy tasks.
5. Concurrent writers require disjoint path ownership.
6. Workers do not recursively delegate by default.
7. The orchestrator owns integration and final completion claims.

## Delegation preflight

Within stack-controlled orchestration, a delegated route is not approved for dispatch until provider-neutral preflight resolves it. The preflight checks role availability, semantic profile compatibility, provider child-agent capability, concrete model resolution, recursion policy, write ownership, active write-scope conflicts, context budget, and required independent review. `scripts/resolve_delegation.py` is the reference executable gate. Native provider calls that bypass this gate are outside this enforcement path and remain governed by provider runtime permissions plus parent instructions.

Decision semantics:

- `PASS` — the route may proceed to provider execution.
- `REJECT` — a hard policy/capability invariant is violated; do not silently fall back.
- `ESCALATE` — the route is structurally valid but a controller decision is required, such as exceeding the context budget or missing a required review plan.

Only `PASS` may create a resolved execution plan. The plan is evidence of what was approved; it is not a provider runtime itself.
