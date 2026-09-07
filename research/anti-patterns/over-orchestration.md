# Anti-pattern: Over-Orchestration

Over-orchestration occurs when the coordination system becomes more expensive or less reliable than the engineering task it was intended to help.

## Failure modes

### Agent-for-everything

Spawning a specialist for a trivial one-file change adds launch/context/synthesis cost without meaningful quality gain.

**Rule:** direct execution remains the default.

### Recursive fan-out

A child spawns more children, which spawn more children, and the root loses budget and ownership visibility.

**Rule:** recursive delegation is disabled by default; only the root/orchestrator can authorize deeper topology.

### Context cloning

Every worker receives the full parent conversation or repository dump.

**Rule:** send bounded task context and references; let workers retrieve only what they need.

### Transcript aggregation

Workers return logs, source dumps and chain-of-actions rather than evidence.

**Rule:** return structured summaries, file/symbol evidence, validation results and confidence.

### Reviewer inflation

Every change receives multiple expensive reviewers regardless of risk.

**Rule:** review depth is risk-adjusted; low-risk reversible work may need only targeted verification.

### Writer collision

Parallel workers edit overlapping paths and create merge/conflict overhead.

**Rule:** serialize writers by default or assign disjoint write sets.

### Infinite convergence loop

Review -> fix -> review repeats without a bounded stop criterion.

**Rule:** limit automatic remediation/recheck cycles; escalate unresolved uncertainty to the orchestrator/user.

### Frontier-everywhere

The most expensive model is used for search, formatting, routine tests and simple changes.

**Rule:** start with the lowest compute profile that meets the required quality threshold, then escalate on evidence.
