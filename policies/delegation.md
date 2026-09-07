# Delegation Policy

1. Default to direct execution.
2. Delegate only when it improves quality, speed, safety or context isolation enough to justify overhead.
3. Child work must be bounded by objective, scope and stop condition.
4. Parallel read-heavy tasks are preferred over parallel write-heavy tasks.
5. Concurrent writers require disjoint path ownership.
6. Workers do not recursively delegate by default.
7. The orchestrator owns integration and final completion claims.
