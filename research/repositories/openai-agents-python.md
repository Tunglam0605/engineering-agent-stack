# openai/openai-agents-python

Source: https://github.com/openai/openai-agents-python

## Focus

Lightweight multi-agent runtime with agents, tools, handoffs, guardrails, sessions, sandboxes and tracing.

## Useful patterns

- **ADOPT — explicit handoff semantics:** delegation is a first-class transition rather than implicit prompt convention.
- **ADOPT — guardrails:** validation belongs around agent execution, not only in role prose.
- **ADOPT — tracing:** orchestration needs observable runs to debug routing and cost.
- **ADAPT — agents as tools:** useful when the parent should retain control, but should not become the only orchestration shape.
- **ADAPT — provider-agnostic runtime:** canonical roles should stay provider-neutral while adapters handle runtime details.

## Project consequence

Our canonical role/result contracts should remain independent from a specific orchestration library, while preserving concepts equivalent to explicit handoff, guardrail, session state and trace evidence.
