# Proposed v0.6 architecture synthesis

Status: **research/architecture audit in progress; not implemented**. Recommendations below are **EAS inference**, informed by linked evidence. This is not a schema, loader contract, CLI specification, or replacement for [current architecture](../../docs/ARCHITECTURE.md).

## Conceptual model

Keep all seven roles unchanged. A role owns an engineering responsibility; a compute profile selects a resource class; a provider supplies execution; execution policy governs permitted work; provenance identifies origin and transformation. Packages must not collapse these dimensions or change model mappings.

| Concept | Proposed EAS meaning | Example / boundary |
|---|---|---|
| **SKILL** | Reusable procedure, judgment, or reference loaded on demand. | Analyze dependency compatibility using project versions as inputs. It grants no permissions. |
| **RULE** | Constraint or requirement, preferably executable when mechanical. | Require API-change evidence; validate a parseable manifest. |
| **CONFIG** | Parameter/value source. | Target board, ROS distribution, selected coverage policy; not workflow instructions. |
| **PRESET** | Curated composition of skills, rules, and config defaults for a domain or process. | Explicitly selected `embedded`, `ros2`, or `release`. |
| **EXTENSION** | Versioned capability package providing skills, rules, config schemas, detection hints, and/or presets. | Declarative distribution unit, never an agent or new executable runtime. |

Procedure versus mechanical constraint is informed by [Superpowers][SW]; separating workflow surfaces from canonical rules by [oh-my-codex][OT]. A project-only convention belongs in project rules, not a new skill. EAS v0.6 manifests/config/presets are not implemented.

## Progressive disclosure and skill quality

**ADAPT** Agent Skills compatibility: discover `skills/<name>/SKILL.md`, expose validated `name`/`description`, load the body when triggered, and retrieve heavy references/scripts/assets only when needed. Prefer shallow resource pointers and variant-specific references. Discovery, not the trigger, determines which source won. [Agent Skills][AS] [Anthropic creator][AC] [oh-my-pi skills][OS]

Draft EAS admission policy:

- Keep always-visible metadata small; budget the aggregate catalog too. Describe capability and triggering conditions without a workflow summary that substitutes for the body. Upstream line/word/token targets are different heuristics, not interchangeable limits. [Superpowers][SW]
- Require bounded purpose, inputs, output/evidence expectations, failure/escalation behavior, and focused references in the body. Avoid duplicating canonical rules.
- Record a pressure scenario exposing the intended weakness without the skill (**RED**); rerun with a versioned skill and acceptance evidence (**GREEN**); add adversarial variants to close loopholes (**refactor**). Include time pressure, incomplete evidence, tempting shortcuts, positive triggers, and near-miss negative triggers. This adapts [pressure testing][SW] and [baseline/trigger evaluations][AC].
- Compare equivalent tasks/environments; record skill revision, provider/compute profile, outcome, omissions, and context cost. An unrelated tool failure does not establish RED. Claim no superiority or readiness without recorded results.

These are future evaluation requirements; no skill or pressure test is implemented here.

## Rules, enforcement, and security

**ADOPT** enforcement classification. Each rule needs an ID, canonical source, scope (project/path/task/stage), severity, and evidence expectations. Severity describes importance; it does not make text enforceable.

| Class | Meaning | Evidence needed before claiming enforcement |
|---|---|---|
| guidance | Instruction requiring judgment/cooperation. | Review rationale or reported adherence; no automatic prevention claim. |
| validator | Executable check returning findings at a known invocation point. | Check identity/version, inputs/revision, result, diagnostic reference. |
| gate | Boundary blocking a defined transition/action on failed or missing required checks. | Controlling executor, pre-action check, negative test, covered/bypassed paths. |

A validator participates in a gate only when the transition consults it. Missing support must report unavailable enforcement; never silently downgrade a required gate to guidance. Mechanical checks should reference vetted stack/project validators, not arbitrary commands supplied by packages.

Input, output, and tool boundaries differ. Output checks follow work; parallel input checks may permit work before rejection. An EAS gate preventing a side effect must finish before that effect at a stack-controlled boundary. No transparent interception of native provider calls is claimed. [SDK guardrails][AG] [Current EAS architecture](../../docs/ARCHITECTURE.md)

Capability metadata is untrusted input, not authority. MCP's prompt/resource/tool control owners and negotiation illustrate why discovery, availability, consent, and execution need separate treatment. [Overview][MI] [Prompts][MP] [Resources][MR] [Tools][MT] [Lifecycle][ML]

## Declarative extension boundary

**ADAPT** multi-capability packaging; **REJECT** oh-my-pi's executable factory/module runtime for v0.6. Its bundling/loading behavior motivates this boundary, not implementation reuse. [Authoring][OE] [Loading][OL]

Proposed restrictions for later design:

- Loading validates/reads data only: no import-time code, hooks, installers, custom tool/command registration, detection scripts, network callbacks, or automatic `.mcp.json` server launch.
- Agent Skills permits bundled scripts; compatibility does not require EAS execution. Extension-supplied executables are ineligible for execution through the v0.6 package mechanism. References to approved project tools remain subject to existing execution policy. Decide later whether inert scripts are retained or rejected at validation.
- Resolve resources inside the declared package root; reject traversal/symlink escapes. Use no shell evaluation, dynamic schema code, or remote schema fetching to interpret data.
- `effect` is declared intent requiring verification, not a sandbox. `read-write` can describe eventual workflow or managed materialization; discovery itself remains read-only. Reject unsupported capabilities.
- Provider discovery/rendering belongs in adapters. Generated content records canonical source, generator, revision, and hash. Hashes detect drift, not publisher trust.

### Manifest concepts for the later schema phase

**ADOPT** versioning/compatibility, informed by [Spec Kit manifests][PE] and [west schema][WS]. Recommend these concepts without choosing serialized shape or creating a schema:

| Concept | Purpose |
|---|---|
| `schema_version` | Parser contract; reject unsupported versions explicitly. |
| `id`, `version`, `description` | Stable identity, package release, concise discovery. |
| `license`, `provenance`, `source` | Origin/revision, reuse/notice records, file-specific exceptions. |
| `requires.eas` version range | EAS compatibility, distinct from package/schema versions. |
| `effect` (`read-only` / `read-write`) | Declared maximum workflow effect, not authorization. |
| `capabilities` | Explicit capability needs; report unavailable needs. |
| `provides.skills`, `rules`, `presets`, `config-schema`, `detection-hints` | Declarative contents and bounded local references. |
| managed-content hashes/provenance | Source/generator lineage, ownership and drift evidence. |
| dependencies/conflicts, only if needed | Explicit incompatibility; no automatic dependency installation or general solver initially. |

This field set, including `effect`, is an EAS recommendation, not attributed wholesale to Spec Kit or west.

## Deterministic configuration and composition

**ADOPT** deterministic precedence; **ADAPT** Ruff's explicit-selection principle and Spec Kit's project/local separation. Ruff's closest-file behavior is evidence against implicit cascading, not the EAS algorithm. [Ruff][RC] [Spec Kit API][PE]

Recommended order, lowest to highest priority:

```text
core defaults
  < extension defaults
  < preset
  < project profile (.eas/project.toml)
  < local project override (.eas/project.local.toml, gitignored)
  < explicit CLI override
```

Those files and CLI options are not created here. Environment variables should supply only named secrets or ephemeral integration values, with redacted reporting; reject a broad hidden environment cascade.

Resolution recommendations:

1. Select one project root. Do not merge all ancestor/user configs implicitly. Future explicit inheritance needs a concrete use case and cycle/path validation.
2. Validate types/known keys per participating schema. Keep per-value source and override history; explain winners without exposing secrets. Precedence selects permitted values, not permission to weaken mandatory policy or expand a role's boundary.
3. Prefer atomic replacement for lists and named leaf values; no prompt concatenation or undocumented deep merge. Map/deletion semantics need fixtures before schema design is final.
4. Default to one selected preset. Allow multiple installed packages but reject ambiguous same-layer definitions rather than use filesystem order. Stable package-qualified IDs avoid accidental shadowing. Add no dependency/conflict solver without demonstrated need.
5. Config layering, provider skill discovery, and content composition are separate decisions. Reject recursive prepend/append/wrap composition initially. [Preset architecture][PA]

For embedded quality plus release checks, evaluate whether a phase parameter or explicit rule selection suffices before adding preset stacking. Recommend only `embedded`, `ros2`, and `release` initially. A security preset/extension is future work; universal security constraints still apply.

## Detection and observability

**ADAPT** evidence/confidence reporting from [oh-my-codex analyze][OA]. Detection should read bounded repository evidence and return suggested preset, confidence with rationale, evidence paths/observations, contradictions, and missing facts. Confidence is not a calibrated probability unless evaluated as one.

A `west.yml` may suggest embedded context but cannot prove the target; a package manifest cannot establish ROS distribution or quality level. Recommendations must not silently activate high-impact capabilities, install packages, invoke build systems, or rewrite config. Conflicting evidence yields explicit ambiguity.

**ADAPT** workflow/trace/span grouping for bounded evidence, preserving v0.5 durable-state authority and observational-log separation. Record selection/resolution/check IDs, input revision, outcomes, and evidence references; redact secrets and avoid whole transcripts. Traces are observations, not approval or enforcement. [SDK tracing][AT] [EAS workflow](../../docs/WORKFLOW.md)

## Alternatives and v0.6 non-goals

- **Recommended:** declarative packages, a small curated preset set, explainable composition, no new runtime.
- **Deferred alternative:** loose skills/project rules only; simpler distribution but weaker package identity/compatibility and repeatability.
- **Rejected alternative:** executable plugins, recursive composition and specialist catalogs; larger trust/routing/maintenance burden without local evidence of need.

This audit implements none of these. Out of scope: loader/runtime, commands/schemas, marketplace/install/update system, dependency solver, new agents/compute mappings, superiority claims, safety certification, automatic domain activation.

## Open decisions and next evidence

| Question requiring further evidence | Starting recommendation | Evidence needed before later design approval |
|---|---|---|
| Retain inert upstream scripts or reject them? | No extension execution. | Representative skill packages and adapter cases proving the packaging boundary. |
| Map replacement, deletion, duplicate IDs? | Explicit leaf/list replacement; fail ambiguous collisions. | Nested-map, duplicate-package, local-override, unknown-key and policy-weakening fixtures. |
| One preset for domain plus release work? | One active preset; no recursive composition. | Embedded/ROS2 release scenarios testing explicit rule selection. |
| What can a domain gate execute? | Vetted project/stack checks only. | Target embedded repo/board/toolchain and ROS2 package/distribution, quality declaration, CI and dependencies. |
| Useful metadata budget/detection confidence? | Small metadata; explained confidence. | Trigger/near-miss and mixed-monorepo cases; context cost and false-positive measurements. |
| Managed-content ownership/trust? | Source/generator/hash lineage; no silent overwrite. | Drift, uninstall, path/symlink, publisher provenance and cross-platform cases against the current installer. |

These gaps do not reopen the seven-role or declarative-only decisions. They block implementation-ready contract, calibrated detection, or domain-qualification claims.

[AC]: https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/skill-creator/SKILL.md
[AG]: https://github.com/openai/openai-agents-python/blob/02c205f9574c765a265ce102dc55da81cdd74b89/docs/guardrails.md
[AS]: https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx
[AT]: https://github.com/openai/openai-agents-python/blob/02c205f9574c765a265ce102dc55da81cdd74b89/docs/tracing.md
[MI]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/index.mdx
[ML]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/basic/lifecycle.mdx
[MP]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/server/prompts.mdx
[MR]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/server/resources.mdx
[MT]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/server/tools.mdx
[OA]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/skills/analyze/SKILL.md
[OE]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/skills/authoring-extensions.md
[OL]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/extension-loading.md
[OS]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/skills.md
[OT]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/skills/team/SKILL.md
[PA]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/presets/ARCHITECTURE.md
[PE]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/extensions/EXTENSION-API-REFERENCE.md
[RC]: https://github.com/astral-sh/ruff/blob/e7adf82ff005f3ab3051c363464cf65bf8a6e2f3/docs/configuration.md
[SW]: https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-skills/SKILL.md
[WS]: https://github.com/zephyrproject-rtos/west/blob/df990f0e0893d64e0600cbd2965ae45e39990f86/src/west/manifest-schema.yml
