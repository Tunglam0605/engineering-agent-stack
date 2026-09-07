# Codex Adapter

Status: **v0.1 candidate — generated, drift-checked, and installable**

Last checked against current public Codex subagent documentation and `openai/codex` source: **2026-09-07**.

## Purpose

Translate provider-neutral canonical roles plus semantic compute profiles into Codex custom-agent TOML without making provider model names part of role identity.

## Source of truth

Do **not** hand-edit `agents/*.toml` or `config.toml.example`.

Canonical inputs:

```text
agents/core/*.yaml
config/model-profiles.yaml
adapters/codex/role-profiles.yaml
```

Generated outputs:

```text
adapters/codex/agents/*.toml
adapters/codex/config.toml.example
```

Generate/check:

```bash
python scripts/generate_codex_adapter.py
python scripts/generate_codex_adapter.py --check
```

CI runs `--check` and fails on drift.

## Current public Codex layout

Current public Codex documentation discovers standalone agent files from:

```text
.codex/agents/*.toml     project-scoped
~/.codex/agents/*.toml   personal
```

Every standalone file requires:

```text
name
description
developer_instructions
```

Normal session settings such as `model`, `model_reasoning_effort`, and `sandbox_mode` can also be set in the role file.

Global subagent controls remain under `[agents]` in `.codex/config.toml` or the personal config. The example intentionally contains only those public global controls; it does not depend on internal role-registration mechanisms.

## Safe installation

Recommended first trial:

```bash
python scripts/install_codex.py --project /path/to/project --dry-run
python scripts/install_codex.py --project /path/to/project
python scripts/install_codex.py --project /path/to/project --check
```

After project-scoped validation, personal installation is available with:

```bash
python scripts/install_codex.py --personal
```

The installer refuses to overwrite differing role files unless `--force` is supplied; forced replacement creates `.bak` files. Existing `config.toml` files are never rewritten automatically.

See [`../../docs/INSTALL_CODEX.md`](../../docs/INSTALL_CODEX.md).

## Routing posture

Seven available roles do not imply seven child runs.

```text
trivial/reversible       -> direct
repository discovery     -> scout
external/versioned facts -> researcher
bounded ordinary edit    -> implementer
uncertain root cause     -> debugger
targeted validation      -> test-engineer
independent assurance    -> reviewer
high-risk architecture   -> architect
```

The parent owns decomposition, context allocation, integration, escalation and final completion.

## Candidate model mapping

| Role | Semantic profile | Current Codex candidate |
|---|---|---|
| Scout | cheap + medium reasoning override | GPT-5.6 Luna / medium |
| Researcher | cheap + medium reasoning override | GPT-5.6 Luna / medium |
| Implementer | standard | GPT-5.6 Terra / medium |
| Debugger | deep | GPT-5.6 Terra / high |
| Test Engineer | standard | GPT-5.6 Terra / medium |
| Reviewer | deep | GPT-5.6 Terra / high |
| Architect | critical | GPT-5.6 Sol / high |

These are benchmark candidates, not permanent role identities.

## Permission caveat

A custom-agent file is not an independent security boundary. Current Codex behavior reapplies the parent's live runtime permission/sandbox choices when spawning a child. Set parent permissions deliberately and treat role `sandbox_mode` as a default within the effective runtime policy.

The adapter also does not rely on legacy `agents.max_depth` to stop recursive delegation; current Codex V2 does not use that legacy/V1 depth field. Recursive delegation is therefore prohibited by this project's role instructions/policy unless explicitly authorized.

## Compatibility rule

Before a release that changes Codex keys, model IDs, reasoning levels, sandbox behavior, custom-agent schema, or subagent controls, re-check:

- https://developers.openai.com/codex/subagents
- https://github.com/openai/codex

See also [`research/repositories/openai-codex.md`](../../research/repositories/openai-codex.md).
