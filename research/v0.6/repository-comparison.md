# v0.6 repository comparison

All decisions are **EAS design recommendations**, not implementation status. Evidence links identify inspected snapshots; [source notes](README.md#source-set) preserve requested URLs, revisions and license records. The existing [canonical matrix](../matrix/repository-comparison.yaml) remains the repository-wide provenance index.

| Source / problem | Evidence-backed pattern | Decision and reason | Risk / limitation | Local audit artifact affected |
|---|---|---|---|---|
| Agent Skills: portable procedure | Directory contract and staged loading. [Spec][AS] | **ADAPT** compatibility and disclosure; **ADOPT** required metadata. | Format does not authorize scripts/tools. | architecture-synthesis.md: disclosure, packages |
| Anthropic: skill authoring | Variant references, baseline comparisons, trigger evaluation. [Creator][AC] | **ADAPT** bounded bodies and focused references; **ADOPT** negative-trigger tests. | Aggressive triggers may over-activate; mixed licenses. | architecture-synthesis.md: quality |
| oh-my-pi: discovery | One-level skills, source/priority resolution, on-demand URLs. [Skills][OS] | **ADAPT** discovery and provenance; avoid provider priorities in core. | Multiple passes can obscure collisions. | architecture-synthesis.md: discovery |
| oh-my-pi: runtime extensibility | Packages bundle surfaces; module loading executes factories. [Authoring][OE] [Loading][OL] | **ADAPT** declarative bundles; **REJECT** full runtime/plugin execution. | Disabling modules does not disable all discovery surfaces. | architecture-synthesis.md: security |
| Superpowers: reliable skills | Baseline failure, success with skill, loophole tests; automate mechanical constraints. [Guide][SW] | **ADAPT** pressure tests; **REJECT** project-convention skills and workflow-summary metadata. | Guidance is not measured EAS benefit. | architecture-synthesis.md: quality |
| oh-my-codex: coordination | Canonical durable rules, explicit runtime, scoped skills and analysis. [Team][OT] [Skills][OK] [Analyze][OA] [Template][OC] | **ADOPT** single rule source; **ADAPT** scopes; **REJECT** specialist catalog expansion. | Workflow/role proliferation increases overlap. | architecture-synthesis.md: taxonomy |
| Spec Kit: customization | Versioned manifests, configuration layers, composition, catalogs. [Architecture][PA] [API][PE] [Extensions][PX] | **ADOPT** versioning/precedence; **ADAPT** presets; **REJECT** recursive composition and broad environment cascade initially. | Hook consumers differ; a dependency solver is not established by these docs. | architecture-synthesis.md: composition |
| Agents SDK: checks | Input/output/function-tool boundaries; traces and spans. [Guardrails][AG] [Tracing][AT] | **ADOPT** named boundaries; **ADAPT** bounded tracing. | Post-effect checks cannot prevent earlier effects; some tools are outside coverage. | architecture-synthesis.md: enforcement |
| MCP: capabilities | Distinct control owners and negotiated features. [Prompts][MP] [Resources][MR] [Tools][MT] [Lifecycle][ML] | **ADOPT** advertisement versus authorization distinction; **ADAPT** capability declarations. | Untrusted metadata and consent remain host concerns. | architecture-synthesis.md: security |
| west: dependencies | Versioned typed manifest with revisions/imports/groups. [Schema][WS] | **ADOPT** version checks; **ADAPT** inventory; **REJECT** recursive solver initially. | Structural validity is not full semantic validity. | architecture-synthesis.md; domain-gates.md |
| Zephyr: embedded quality | External-standard references and dependency revisions/groups. [Guidelines][ZG] [Manifest][ZM] | **ADAPT** standards/evidence discipline. | No copied MISRA text or certification. | domain-gates.md: embedded |
| REP-2004: package quality | Quality-level-specific policies with justification. [REP][RQ] | **ADOPT** evidence declarations; **ADAPT** domain candidates. | No automatic certification or universal numeric threshold. | domain-gates.md: ros2, release |
| Ruff: config predictability | Closest applicable config, explicit extend, CLI override. [Config][RC] | **ADOPT** determinism; **ADAPT** fixed EAS layers; **REJECT** hidden cascades. | EAS layers differ from per-file selection. | architecture-synthesis.md: config |

## Disagreements resolved for this draft

- **Skill scope:** oh-my-codex permits codebase-specific skill capture; Superpowers excludes project conventions. EAS chooses reusable procedures with project parameters, keeping project-only requirements in rules/config. This is a local choice, not consensus. [Skills][OK] [Guide][SW]
- **Trigger content:** Agent Skills describes what a skill does and when to use it; Superpowers warns against workflow summaries. EAS can satisfy both with a short capability statement and trigger conditions, omitting procedural steps. [Spec][AS] [Guide][SW]
- **Precedence:** Ruff selects file configuration; Spec Kit composes packages/templates; oh-my-pi resolves provider discovery. EAS must distinguish these problems instead of using one ambiguous priority number. [Config][RC] [Architecture][PA] [Skills][OS]
- **Enforcement:** hook declarations, guidance, advertisements, and traces are not gates. EAS requires a named executor and evidence of coverage. [Extensions][PX] [Guardrails][AG] [Tools][MT]

`EXPERIMENT` remains valid in the repository-wide vocabulary, but this package makes no measured-benefit claim. Later trigger, collision, and pressure fixtures must test recommendations before promotion.

[AC]: https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/skill-creator/SKILL.md
[AG]: https://github.com/openai/openai-agents-python/blob/02c205f9574c765a265ce102dc55da81cdd74b89/docs/guardrails.md
[AS]: https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx
[AT]: https://github.com/openai/openai-agents-python/blob/02c205f9574c765a265ce102dc55da81cdd74b89/docs/tracing.md
[ML]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/basic/lifecycle.mdx
[MP]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/server/prompts.mdx
[MR]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/server/resources.mdx
[MT]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/server/tools.mdx
[OA]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/skills/analyze/SKILL.md
[OC]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/templates/AGENTS.md
[OE]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/skills/authoring-extensions.md
[OK]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/skills/skill/SKILL.md
[OL]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/extension-loading.md
[OS]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/skills.md
[OT]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/skills/team/SKILL.md
[PA]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/presets/ARCHITECTURE.md
[PE]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/extensions/EXTENSION-API-REFERENCE.md
[PX]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/docs/reference/extensions.md
[RC]: https://github.com/astral-sh/ruff/blob/e7adf82ff005f3ab3051c363464cf65bf8a6e2f3/docs/configuration.md
[RQ]: https://github.com/ros-infrastructure/rep/blob/11ca24a41f31480dfb9562ba99f2a5b93d3ebda5/rep-2004.rst
[SW]: https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-skills/SKILL.md
[WS]: https://github.com/zephyrproject-rtos/west/blob/df990f0e0893d64e0600cbd2965ae45e39990f86/src/west/manifest-schema.yml
[ZG]: https://github.com/zephyrproject-rtos/zephyr/blob/bc2caf20dd0c7ca6c95c0dae66fd1ccb0e7e6147/doc/contribute/coding_guidelines/index.rst
[ZM]: https://github.com/zephyrproject-rtos/zephyr/blob/bc2caf20dd0c7ca6c95c0dae66fd1ccb0e7e6147/west.yml
