# langchain-ai/langgraph

Source: https://github.com/langchain-ai/langgraph

## Focus

Low-level orchestration for long-running, stateful agents.

## Useful patterns

- **ADAPT — durable state machine:** explicit state transitions are preferable to hidden conversational state for long workflows.
- **ADAPT — interrupt/human-in-the-loop:** pauses should be modeled as workflow state, not ad-hoc chat messages.
- **ADAPT — persistence/checkpointing:** useful for long runs and recovery.
- **ADOPT — observability/evaluation mindset:** complex agent behavior must be traceable and testable.

## Project consequence

The initial stack remains file/config driven, but any future runtime should model orchestration state explicitly and support resumable execution rather than relying on a single growing chat transcript.
