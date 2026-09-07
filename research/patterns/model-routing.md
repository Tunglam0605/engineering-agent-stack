# Model Routing Pattern

## Principle

Route by task shape, risk and uncertainty—not by agent title alone.

A role may be compatible with several compute profiles. Example:

```text
Debugger + ordinary deterministic bug  -> standard
Debugger + concurrency/race condition  -> deep
Debugger + safety/release-critical     -> critical
```

## Semantic profiles

- `cheap`: scanning, classification, simple validation
- `standard`: ordinary implementation/debugging
- `deep`: complex reasoning, difficult root cause, high-confidence review
- `critical`: architecture/security/realtime/release-critical decisions

Provider-specific models are resolved later by adapters.

## Escalate instead of over-provisioning

Start at the lowest tier expected to satisfy the quality threshold, then escalate when evidence shows insufficient confidence or complexity.
