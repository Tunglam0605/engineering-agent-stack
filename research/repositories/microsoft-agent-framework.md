# microsoft/agent-framework

Source: https://github.com/microsoft/agent-framework

## Focus

Production-grade multi-agent framework and successor to AutoGen, with provider flexibility and durable workflow primitives.

## Useful patterns

- **ADOPT — deterministic workflow graph:** sequential, concurrent, handoff and group collaboration are explicit orchestration shapes.
- **ADOPT — observability:** OpenTelemetry-style tracing belongs in the runtime contract.
- **ADOPT — provider flexibility:** orchestration semantics should not be coupled to one model vendor.
- **ADAPT — declarative agents:** versionable declarative definitions are useful, but our canonical schema should remain smaller.
- **ADAPT — checkpointing/restartability:** important for long-running workflows; defer runtime implementation until the core stack is stable.
- **ADAPT — human-in-the-loop:** introduce approval gates where risk or irreversible effects justify them.

## Project consequence

Use deterministic control flow for coordination and allow model autonomy only inside bounded assignments. Durability and observability are future runtime requirements, not prompt features.
