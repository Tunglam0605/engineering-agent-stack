# langchain-ai/deepagents

Source: https://github.com/langchain-ai/deepagents

## Focus

Opinionated long-horizon agent harness built on LangGraph.

## Useful patterns

- **ADOPT — isolated subagent context:** delegated work should not inherit more context than necessary.
- **ADOPT — tool-output offload:** noisy command output can be stored outside the main reasoning context and summarized.
- **ADOPT — on-demand skills:** load specialist instructions only when relevant instead of carrying a huge static prompt catalog.
- **ADAPT — filesystem abstraction:** useful for sandbox/remote providers, but should live behind adapters/runtime.
- **ADAPT — persistent memory:** valuable only with explicit scope, retention and provenance rules.
- **REJECT — relying on the model to self-enforce permissions:** security boundaries must be tool/sandbox enforced.

## Project consequence

Context isolation and on-demand skills become first-class efficiency mechanisms. Prompt discipline is not treated as a substitute for runtime permissions.
