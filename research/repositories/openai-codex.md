# openai/codex

Source: https://github.com/openai/codex

Primary public documentation: https://developers.openai.com/codex/subagents

Reviewed: 2026-09-07

## Focus

Authoritative implementation and public configuration behavior for Codex subagents/custom agents.

## Findings used by this project

- Current public Codex guidance discovers standalone custom-agent TOML files from `.codex/agents/` (project) or `~/.codex/agents/` (personal).
- A standalone custom agent requires `name`, `description`, and `developer_instructions`.
- Agent files can also override normal session settings such as `model`, `model_reasoning_effort`, and `sandbox_mode`.
- Global controls live under `[agents]`, including `enabled`, `max_concurrent_threads_per_session`, default subagent model/reasoning, and interruption-message behavior.
- Custom-agent model/reasoning settings take precedence over explicit spawn/default/parent values after the documented resolution sequence.
- Parent live runtime permission/sandbox overrides are reapplied when spawning children, so a role file is not an independent security boundary.
- Public examples use narrow agents and commonly place read-heavy mapping/research work on lower-cost models while using higher reasoning for review/debug roles.
- Current Codex source still contains legacy/V1 depth configuration, but `agents.max_depth` is documented in source as ignored by V2. This project therefore does not rely on it to block recursive delegation.
- Internal source paths expose additional role-loading mechanisms. The adapter follows the public standalone-agent contract rather than depending on undocumented/internal registration behavior.

## Decisions

| Pattern | Decision |
|---|---|
| Standalone custom-agent files | ADOPT |
| Public `[agents]` global controls | ADOPT |
| Role-specific model/reasoning overrides | ADAPT through semantic compute profiles |
| Parent-owned permission boundary | ADOPT as an explicit limitation |
| Narrow/opinionated custom agents | ADOPT |
| Legacy/V1 depth controls for recursion safety | REJECT |
| Internal-only role registration mechanisms | REJECT for public adapter surface |

## Local consequences

- `adapters/codex/agents/*.toml` is generated from canonical provider-neutral YAML.
- `adapters/codex/config.toml.example` contains only public global `[agents]` controls.
- Recursive-delegation limits remain policy/instruction constraints until a current runtime-enforced V2 control is documented and verified.
- Adapter compatibility must be rechecked against current public Codex docs before release.
