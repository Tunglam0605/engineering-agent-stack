# OpenAI Codex Subagents — official source note

Retrieved: 2026-09-07

Primary source: https://developers.openai.com/codex/subagents

## Current facts used by this project

- Current Codex releases enable subagent workflows by default.
- Each subagent performs its own model and tool work, so delegation can consume more tokens than comparable single-agent work.
- Parallel subagents are a strong fit for independent, read-heavy work such as exploration, tests, triage, log analysis and summarization.
- Parallel write-heavy work needs more caution because coordination and edit conflicts can erase the benefit of concurrency.
- The parent/main thread should retain requirements and decisions while child agents return distilled evidence rather than raw logs.
- If model or reasoning effort is not configured, a child can inherit the parent settings.
- The current guidance positions `gpt-5.6` for demanding multi-step agents, `gpt-5.6-terra` for efficient supporting/read-heavy agents, and `gpt-5.6-luna` for narrow, repeatable, high-volume work.
- Higher reasoning effort increases latency and token usage and should be justified by task complexity.
- Project custom agents live under `.codex/agents/`; personal agents live under `~/.codex/agents/`.
- Each custom agent file requires `name`, `description`, and `developer_instructions`; supported session config such as `model`, `model_reasoning_effort` and `sandbox_mode` can also be set.
- Global subagent controls live under `[agents]`, including `max_concurrent_threads_per_session`, `default_subagent_model`, and `default_subagent_reasoning_effort`.
- Codex ships built-in `default`, `worker`, and `explorer` agents.

## Design consequence

This project treats subagents as a bounded optimization primitive, not a mandatory pipeline. The default remains direct execution; delegation must earn its token and coordination overhead through specialization, context isolation, parallelism, or independent verification.

## Source hygiene

Codex evolves quickly. Provider-specific files under `adapters/codex/` must be rechecked against current official documentation before a release that changes configuration fields, model IDs, sandbox behavior, or subagent controls.
