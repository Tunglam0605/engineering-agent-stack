# OpenAI Codex exec JSONL capture

Checked: 2026-09-07

Primary implementation references:

- `openai/codex/codex-rs/exec/src/cli.rs`
- `openai/codex/sdk/typescript/src/events.ts`
- `openai/codex/sdk/typescript/src/items.ts`

## Observed public contract

Current Codex `exec` supports `--json` (with `--experimental-json` retained as an alias) and emits one JSON object per line.

Relevant top-level events include:

- `thread.started`
- `turn.started`
- `turn.completed`
- `turn.failed`
- `item.started`
- `item.updated`
- `item.completed`
- `error`

`turn.completed` carries a `usage` object with:

- `input_tokens`
- `cached_input_tokens`
- `cache_write_input_tokens`
- `output_tokens`
- `reasoning_output_tokens`

Completed items include command execution, file changes, MCP tool calls, web searches, agent messages, reasoning and errors.

## Local decision

**ADOPT** the JSONL event stream as the initial Codex measurement source for token usage and coarse execution evidence.

**ADAPT** it through a provider-specific normalization layer. Canonical benchmark records must not depend directly on Codex event names.

**DO NOT** commit raw traces by default. Tool outputs, commands, paths and agent messages can expose repository or environment information.

## Limits

The normalized capture counts top-level completed item/tool events and sums usage reported on `turn.completed`. It does not assume that every hidden/internal subagent action is separately observable in the public exec stream. Agent-count experiments therefore need explicit topology metadata and, where available, additional runtime evidence.
