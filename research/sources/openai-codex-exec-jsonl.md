# OpenAI Codex exec JSONL capture

Checked: 2026-09-07

Primary implementation references:

- `openai/codex/codex-rs/exec/src/cli.rs`
- `openai/codex/sdk/typescript/src/events.ts`
- `openai/codex/sdk/typescript/src/items.ts`
- `openai/codex/codex-rs/protocol/src/items.rs`
- `openai/codex/codex-rs/core/src/tools/handlers/multi_agents/spawn.rs`

## Observed public contract

Current Codex `exec` supports `--json` (with `--experimental-json` retained as an alias) and emits one JSON object per line.

Relevant top-level events include `thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.started`, `item.updated`, `item.completed`, and `error`.

`turn.completed` carries a `usage` object with `input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`, and `reasoning_output_tokens`.

Completed items include command execution, file changes, MCP tool calls, web searches, agent messages, reasoning, collaboration calls, and errors.

## Subagent telemetry

Public `codex exec --json` output observed on `codex-cli 0.153.4` represents collaboration activity as a `collab_tool_call` item. Older/experimental traces used `collab_agent_tool_call`; the normalizer accepts both. A completed `spawn_agent` item can expose:

- effective child `model`
- effective `reasoning_effort`
- receiver thread IDs
- receiver agent metadata, including `agent_role` when available

The current spawn implementation emits the effective model and reasoning effort after role/profile resolution. This makes the event useful for acceptance and routing audits.

The local parser counts collaboration calls and `spawn_agent` items observed in public JSONL and records observed child model, reasoning, and role metadata when supplied. The serialized `agent_spawns` name is retained for capture compatibility, but its value is an observed event count rather than runtime ground truth.

## Local decision

**ADOPT** the JSONL event stream as the initial Codex measurement source for token usage, coarse execution evidence, and observable subagent-spawn metadata.

**ADAPT** it through a provider-specific normalization layer. Canonical benchmark records must not depend directly on Codex event names.

**DO NOT** commit raw traces by default. Tool outputs, commands, paths, prompts, and agent messages can expose repository or environment information.

## Limits

Subagent telemetry is best-effort. Optional model/role fields may vary across Codex versions or execution modes, and not every hidden/internal action is guaranteed to be separately observable in the public exec stream. In particular, `agent_spawns = 0` means "0 spawn events observed in public JSONL"; it is not definitive proof that no child was spawned.

Acceptance therefore distinguishes:

- missing spawn evidence for an explicitly requested child -> blocking failure
- missing optional child model/role metadata -> warning
- engineering quality -> separate deterministic/manual quality gate
