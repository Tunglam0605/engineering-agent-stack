# Anti-patterns

The stack explicitly guards against:

- **Agent-for-everything:** spawning workers for trivial tasks.
- **Frontier-everywhere:** assigning the strongest compute tier to routine work.
- **Recursive fan-out:** workers spawning more workers without bounded workflow authority.
- **Context cloning:** giving each worker the full parent context by default.
- **Transcript return:** flooding the parent with raw logs/source instead of evidence.
- **Writer collision:** multiple agents editing the same paths concurrently.
- **Self-review:** implementer acting as the only authority on its own change.
- **Infinite convergence:** review/fix/review loops without retry limits.
- **Role-model coupling:** defining a role by a permanent model name.
- **Catalog inflation:** adding specialists without evidence they improve outcomes.
