# Escalation Policy

Escalate compute or role authority when evidence shows the current tier is insufficient.

## Triggers

- unresolved ambiguity that affects correctness
- low confidence after bounded investigation
- contradictory evidence
- concurrency, realtime, memory-safety or data-integrity complexity
- security-sensitive or release-critical behavior
- failed targeted re-check
- architecture/public-interface/data-model decision

## Non-triggers

- the task is large only because the repository is large
- a stronger model is available
- a worker prefers more context without evidence

Escalation should preserve the existing evidence package so the stronger tier does not repeat unnecessary exploration.
