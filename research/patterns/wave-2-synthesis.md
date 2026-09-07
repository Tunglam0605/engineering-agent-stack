# Research Wave 2 Synthesis

Date: 2026-09-07

This synthesis combines current Codex guidance with patterns from specialist catalogs, coding-agent orchestrators and general multi-agent frameworks.

## Architecture invariants

1. **Control plane != worker role.** The orchestrator owns decomposition, routing, integration, stopping and final verification.
2. **Role != compute profile != provider.** Expertise, budget and runtime are independently replaceable dimensions.
3. **Direct-first.** Delegation is justified only by parallelism, specialization, context isolation or independent assurance.
4. **Read parallel; write partition or serialize.** Parallel readers are cheap to coordinate. Writers require disjoint ownership or explicit ordering.
5. **Isolate context.** Child agents receive task-local evidence and return distilled results, not parent-context clones or transcripts.
6. **Deterministic coordination, bounded autonomy.** Prefer explicit workflow state/edges for orchestration; use model autonomy inside bounded assignments.
7. **Evidence-based completion.** A model claim does not close work; the narrowest sufficient test/check must support it.
8. **Runtime-enforced boundaries.** Sandbox/tool permissions are security controls; prompt instructions are not.
9. **Observability and evals are first-class.** Routing quality, latency, token usage and failures need traceable evidence.
10. **Small core, on-demand specialization.** Keep the default role catalog small and load skills/specialists only when repeated evals show benefit.

## Efficiency model

The project optimizes:

```text
quality / (cost × latency)
```

subject to a task-specific minimum quality threshold. This means the cheapest model is not automatically preferred, and the strongest model is not automatically justified.

## Default topology

```text
Task
 |
 +-- obvious + low risk -----------------> direct -> targeted verify
 |
 +-- independent discovery --------------> scout/researcher --+
 |                                                             |
 +-- bounded change ----------------------> implementer --------+--> verify
 |                                                             |
 +-- uncertain root cause ----------------> debugger -----------+
                                                               |
                                                      risk-based review
                                                               |
                                                  pass / escalate / block
```

## Model-routing hypothesis for Codex

This is a benchmark hypothesis, not a permanent mapping:

- Luna: narrow repeatable scanning/classification and inexpensive supporting work.
- Terra medium: ordinary implementation, testing and research.
- Terra high: difficult debugging and independent review.
- GPT-5.6: architecture, release-critical, realtime/safety/security-sensitive decisions.
- GPT-6 Astra: exceptional benchmark candidate only when measurable quality gain justifies substantially higher cost.

## What we deliberately do not adopt

- large default catalogs
- recursive child spawning without a parent-owned budget
- group chat as the normal execution primitive
- raw transcript aggregation
- model-enforced permissions
- automatic expensive-model escalation without evidence
- infinite review/fix/re-review loops
