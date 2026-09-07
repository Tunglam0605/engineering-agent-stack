# Architecture

## Objective

The stack optimizes engineering outcomes under three constrained resources: model capability, context/token budget and latency.

A routing decision should minimize unnecessary compute while preserving the quality threshold implied by task risk.

## Layers

### 1. Orchestration layer

Responsibilities:

- classify task shape and risk
- decide direct execution vs delegation
- select role(s)
- select semantic compute profile
- allocate context budget
- enforce concurrency/write ownership
- evaluate evidence and escalate when necessary

The orchestrator owns integration. Workers do not silently expand scope.

### 2. Core role layer

Core roles are intentionally generic and small. Domain specialization is introduced through specialist roles or skills only when repeated evidence shows a benefit.

### 3. Compute profile layer

Roles reference semantic profiles (`cheap`, `standard`, `deep`, `critical`) rather than provider model names. Provider adapters resolve these profiles to available models and reasoning settings.

### 4. Policy layer

Policies define delegation, escalation, context limits, write ownership and quality gates. Policies are independent from individual role prose.

### 5. Evaluation layer

Evals answer: "Does this routing/role/prompt preserve required quality?"

Benchmarks answer: "At what token, latency and cost budget?"

## Default execution topology

```text
Task
 |
 v
Classify
 |
 +-- trivial / obvious ----------------------> direct execution -> verify
 |
 +-- read-heavy discovery --> scout/researcher --+
 |                                                |
 +-- bounded implementation --> implementer -----+--> targeted tests
 |                                                |
 +-- difficult root cause --> debugger -----------+
                                                  |
                                                  v
                                        risk-based review
                                                  |
                                    +-------------+-------------+
                                    |                           |
                                  pass                      uncertain
                                    |                           |
                                  done                      escalate
```

## Concurrency

Parallelism is valuable mainly for independent, read-heavy work. Concurrent write assignments require disjoint path ownership. Shared-file work is serialized unless a future transactional mechanism proves safe.

## Escalation

Escalation is based on evidence, not prestige. Typical triggers:

- low confidence after bounded investigation
- conflicting evidence
- concurrency/realtime/memory-safety complexity
- public API/data compatibility decisions
- security or release-critical changes
- failed targeted re-check

## Provider adapters

Provider adapters translate semantic concepts into tool-specific configuration. A provider adapter must not redefine the canonical meaning of a role or policy.
