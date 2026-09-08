# LangGraph source study

Pinned upstream commit: `81bf17b23123e4ef8b9d5f49fa09a0122fc2edd1` (clone of `langchain-ai/langgraph` main). Source: https://github.com/langchain-ai/langgraph

## Inspected paths and observed semantics

- `libs/langgraph/langgraph/graph/state.py`: `StateGraph` accepts typed `state_schema`; channels and reducers are inferred from annotations. `context_schema` defines run-scoped context and replaces deprecated `config_schema`; nodes may receive `Runtime[Context]`.
- `libs/langgraph/langgraph/types.py`: `Runtime` carries context, store, stream writer and execution metadata; `Command` carries updates, routing (`goto`) and resume values.
- `libs/langgraph/langgraph/_internal/_scratchpad.py`, `libs/langgraph/langgraph/errors.py`: interrupts suspend execution with a payload; resume supplies a value through `Command(resume=...)`.
- `libs/langgraph/langgraph/pregel/__init__.py`: Pregel execution coordinates supersteps, node writes and checkpoint integration; execution identity is supplied through `RunnableConfig`.
- `libs/checkpoint/langgraph/checkpoint/base/__init__.py`: checkpointers persist versioned channel state and require `thread_id`; without one, state cannot be saved or resumed.
- `libs/checkpoint/langgraph/checkpoint/memory/__init__.py`: `InMemorySaver` is configured at compile time for thread-scoped persistence.
- `libs/langgraph/tests/test_interruption.py`: verifies interrupt payloads, suspension, `Command` resume, repeated execution and checkpoint-backed continuation.
- `libs/langgraph/tests/test_interrupt_migration.py`: covers interrupt representation migration compatibility.
- `libs/langgraph/tests/test_parent_command.py`, `test_parent_command_async.py`: verify command navigation between parent and child graphs, sync and async.
- `libs/checkpoint/tests/test_conformance_delta.py`: exercises saver conformance across implementations.

## EAS decisions

**ADOPT** typed state/context separation, bounded command routing, explicit execution identity, checkpoint interfaces, and tests for suspend/resume and persistence.

**ADAPT** channels/reducers into provider-neutral EAS schemas with deterministic merges; map `Runtime` to EAS execution context while keeping role, compute profile, provider, execution policy and provenance separate.

**REJECT** executable nodes/plugins as agent identity, implicit configuration inheritance, remote loading, and unbounded parent/child navigation. Durable execution remains an implementation pattern; EAS requires explicit boundaries, escalation and completion evidence.

Local design impact: `research/v0.6/contract-freeze.md`. No source code or prompts were copied; findings are paraphrased and provenance is recorded here.
