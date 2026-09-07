# Yeachan-Heo/oh-my-codex

Source: https://github.com/Yeachan-Heo/oh-my-codex

## Focus

Codex-oriented orchestration layer with explicit leader/worker responsibilities, specialist routing and workflow modes.

## Useful patterns

- Direct execution is the default; delegate only when it materially improves outcome.
- Bounded subtask delegation with a leader responsible for integration and final verification.
- Specialist routing separates repository exploration, external research, implementation and review concerns.
- Concurrency is bounded rather than open-ended.

## Risks for this project

- A feature-rich orchestration framework can become more complex than the engineering task itself.
- Workflow-specific modes may be too provider/tool-specific for a canonical cross-provider layer.

## Decisions

- **ADOPT:** direct-first delegation philosophy and leader-owned verification.
- **ADAPT:** specialist routing into provider-neutral role contracts.
- **REJECT:** making complex orchestration modes mandatory for ordinary work.
