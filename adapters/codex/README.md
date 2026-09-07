# Codex Adapter

Status: **experimental v0.1 candidate**

Last checked against official Codex subagent documentation: **2026-09-07**.

## Purpose

Translate provider-neutral roles and semantic compute tiers into Codex custom-agent configuration without making Codex-specific model names part of canonical role identity.

## Current files

- `config.toml.example` — conservative project-level `[agents]` baseline.
- `agents/*.toml` — seven experimental custom-agent definitions matching the canonical core roles.

Codex supports project-scoped custom agents under `.codex/agents/` and personal custom agents under `~/.codex/agents/`. Each custom agent currently requires `name`, `description`, and `developer_instructions`; normal session settings such as `model`, `model_reasoning_effort` and `sandbox_mode` may also be overridden.

## Installation for a project

Do not copy these blindly into production. Review model availability and permissions first.

```bash
mkdir -p .codex/agents
cp adapters/codex/agents/*.toml .codex/agents/
# Merge the [agents] block from adapters/codex/config.toml.example
# into the project's .codex/config.toml.
```

## Routing posture

The existence of seven custom agents does **not** mean seven agents run per task.

- trivial/reversible work: main agent executes directly
- repository discovery: `scout`
- external/versioned facts: `researcher`
- bounded ordinary edits: `implementer`
- uncertain root cause: `debugger`
- targeted validation: `test_engineer`
- independent assurance: `reviewer`
- high-risk architecture: `architect`

The parent/main agent owns decomposition, integration, stop/escalate decisions, and final verification.

## Model choices

The TOML files are adapter defaults, not canonical role identities. They currently bias toward Luna for narrow read-heavy roles, Terra for ordinary/deep worker roles, and GPT-5.6 for architecture. These mappings remain benchmark-gated.

## Security boundary

Read-only roles explicitly request `sandbox_mode = "read-only"`. Write-capable roles use workspace write access only because Codex permissions are enforced by the runtime/sandbox, not by prompt text alone. The effective parent runtime policy can still constrain children; always inspect current Codex permission behavior before relying on an adapter setting.

## Compatibility rule

Before changing Codex configuration keys, model names, reasoning levels, custom-agent schema, sandbox settings, or subagent behavior, re-check the current official documentation:

https://developers.openai.com/codex/subagents
