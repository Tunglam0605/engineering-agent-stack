# EAS v0.6 normative contract freeze

Status: **FROZEN / IMPLEMENTATION CONTRACT**. Research is closed for v0.6. Runtime changes must conform to this document. If implementation evidence contradicts a frozen invariant, implementation stops and the architecture must be explicitly revised; no silent widening is permitted.

Normative words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are used intentionally.

## 1. Release objective

v0.6 adds a small declarative capability layer above the stable v0.5 runtime. It does not replace the seven-role orchestration model, provider adapters, delegation preflight, goal lifecycle, workflow recovery, write leases, approval evidence, or model routing.

The capability layer answers five bounded questions:

1. What reusable declarative capability package is available?
2. Which preset is explicitly active for this project?
3. Which validated rules and skills are relevant to the current task?
4. Which values won after deterministic configuration resolution, and where did each value come from?
5. Which immutable capability snapshot is the current runtime operation bound to?

## 2. Protected v0.5 invariants

The following are protected and MUST NOT be weakened by any v0.6 extension, preset, profile, or CLI override:

- exactly seven core roles: `scout`, `researcher`, `implementer`, `debugger`, `test-engineer`, `reviewer`, `architect`;
- role identity is separate from semantic compute profile, provider, concrete model, and reasoning effort;
- direct-first routing and explicit delegated-route preflight;
- provider/model mapping remains owned by canonical config plus provider adapters;
- recursive delegation remains disabled unless the canonical v0.5 policy is explicitly changed outside extension resolution;
- one active writer ownership model and bounded write scopes;
- goal-level soft/hard fan-out limits and resume-before-spawn lifecycle policy;
- revision-checked goal state and explicit approval for risky recovery/transition;
- recovery preserves assignment identity and never silently replaces a suspect executor;
- unavailable telemetry remains unknown rather than fabricated;
- extension data cannot create, rename, delete, or change permissions of core roles;
- extension data cannot select or authorize a model/provider.

A v0.6 resolver encountering a field that attempts to affect any protected surface MUST fail closed.

## 3. Trust boundary

### 3.1 Declarative only

v0.6 extension packages are data. They MUST NOT contain or activate:

- executable Python/JavaScript/shell code;
- hooks or lifecycle callbacks;
- entrypoints;
- arbitrary commands;
- dynamic imports;
- `eval` or template evaluation;
- remote code loading;
- remote schema loading;
- MCP server auto-launch;
- credential-bearing executable actions;
- dependency installation as a side effect of loading a package.

Markdown skill bodies are instructions/reference content, not an execution authority.

### 3.2 Trusted checkers

A package MAY reference a checker ID only when the checker is implemented and registered by EAS core. Package content never supplies checker code.

Rule classes:

| Class | Meaning | Automatic execution claim |
|---|---|---|
| `guidance` | Human/agent judgment requirement | None |
| `validator` | References a trusted EAS checker | Only that checker |
| `gate` | Trusted checker result may block a stack-controlled operation | Only that checker at the documented insertion point |

The initial trusted checker registry is intentionally small:

- `core.contract-shape`
- `core.clean-tree`
- `core.version-consistency`

A rule referencing any other checker ID MUST fail validation.

## 4. Public contract kinds

Exactly five public contract kinds exist in v0.6:

1. `extension-manifest`
2. `skill`
3. `rule`
4. `preset`
5. `project-profile`

`ResolvedCapabilitySnapshot` is internal runtime state, not an extension kind.

Unknown `kind` values MUST fail closed.

## 5. Common grammar

### 5.1 IDs

IDs MUST match:

```text
[a-z0-9][a-z0-9._-]{0,63}
```

Additional rules:

- IDs are lowercase ASCII only;
- Windows reserved device names are rejected;
- ID comparisons that can map to filesystem resources are case-fold conservative;
- duplicate IDs fail;
- case-fold collisions fail even on a case-sensitive host.

### 5.2 Versions

Contract versions MUST be SemVer 2.0 strings.

`schema_version` MUST be an integer. v0.6 supports only `schema_version = 1` for the five public contracts and the internal capability snapshot.

Unknown schema versions MUST fail closed. There is no best-effort downgrade.

### 5.3 `requires_eas`

The v0.6 range grammar is deliberately smaller than a general package-manager grammar.

A range consists of one or two comma-separated comparator clauses:

```text
>=0.6.0,<0.7.0
==0.6.0
>=0.6.0
```

Allowed comparators are `>=`, `<=`, `>`, `<`, `==`. Each target is SemVer 2.0.

Caret, tilde, wildcard, OR, exclusion, named-channel and implicit-version syntax are unsupported and MUST fail closed.

### 5.4 Paths

Package paths MUST:

- be relative to the package root;
- normalize separators to `/` for comparison;
- reject `..` parent traversal;
- reject absolute POSIX paths;
- reject drive-qualified Windows paths;
- reject Windows-reserved names;
- reject trailing dot/space components;
- reject cross-platform ambiguous characters;
- reject symlink/reparse traversal from package root;
- reject case-fold collisions.

Filesystem enumeration order MUST NOT determine a winner.

## 6. Serialization formats

### 6.1 YAML

Extension manifests, skills, rules and presets use a strict JSON-compatible YAML subset.

Loader MUST reject:

- duplicate mapping keys;
- unknown contract keys;
- aliases;
- anchors;
- explicit/custom tags;
- implicit date/time objects;
- non-finite floating values;
- non-string mapping keys;
- unsupported object types.

No interpolation or environment expansion occurs while parsing.

### 6.2 TOML

`.eas/project.toml` uses strict TOML parsing.

Loader MUST reject:

- malformed TOML;
- duplicate keys/tables;
- unknown contract fields;
- secret-like fields;
- unsupported configuration sections/fields.

`.eas/project.local.toml` is not part of v0.6 and MUST NOT be loaded.

## 7. `extension-manifest`

### 7.1 Required fields

- `kind = extension-manifest`
- `schema_version`
- `id`
- `version`
- `description`
- `requires_eas`
- `provenance`
- `provides`

Optional:

- `defaults`

`provenance` requires:

- `source`
- `revision`
- `license`

`provides` contains exactly:

- `skills`: list of package-relative descriptor paths
- `rules`: list of package-relative descriptor paths
- `presets`: list of package-relative descriptor paths

No `dependencies`, `extends`, `include`, agent/model/provider fields, or executable fields exist.

### 7.2 Example

```yaml
kind: extension-manifest
schema_version: 1
id: embedded
version: 0.6.0
description: Embedded engineering capability pack.
requires_eas: ">=0.6.0,<0.7.0"
provenance:
  source: eas-builtin
  revision: v0.6.0
  license: MIT
provides:
  skills: [skills/realtime-control.yaml]
  rules: [rules/realtime-budget.yaml]
  presets: [presets/embedded.yaml]
defaults: {}
```

## 8. `skill`

### 8.1 Required fields

- `kind = skill`
- `schema_version`
- `id`
- `version`
- `summary`
- `roles`
- `task_tags`
- `body`
- `context_cost`

Optional:

- `triggers`
- `references`

`roles` MUST contain only the seven core role IDs. A skill grants no role permission.

`body` and `references` are package-relative resources. They MUST NOT be read during catalog discovery.

`context_cost` is a bounded declared cost used by selection before loading body content.

### 8.2 Example

```yaml
kind: skill
schema_version: 1
id: embedded.realtime-control
version: 0.6.0
summary: Analyze bounded realtime MCU control work.
roles: [implementer, debugger, test-engineer, architect]
task_tags: [embedded, realtime, stm32]
triggers: [stm32, freertos, interrupt]
body: bodies/realtime-control.md
references: []
context_cost: 1100
```

## 9. `rule`

### 9.1 Required fields

- `kind = rule`
- `schema_version`
- `id`
- `version`
- `classification`
- `scope`
- `severity`
- `evidence`
- `text`

Optional:

- `checker_id`

Allowed classifications: `guidance`, `validator`, `gate`.

Allowed severities: `info`, `warning`, `error`.

A `guidance` rule MUST NOT have a checker ID. `validator` and `gate` MUST reference a trusted EAS checker ID.

### 9.2 Example

```yaml
kind: rule
schema_version: 1
id: release.clean-tree
version: 0.6.0
classification: gate
scope: [release]
severity: error
evidence: [git-status]
text: A release gate requires a clean source tree.
checker_id: core.clean-tree
```

## 10. `preset`

### 10.1 Required fields

- `kind = preset`
- `schema_version`
- `id`
- `version`
- `description`
- `skills`
- `required_rules`
- `defaults`
- `detection_hints`

v0.6 ships exactly three built-ins:

- `embedded`
- `ros2`
- `release`

Only one preset may be active for a resolved project snapshot.

Preset inheritance and dependencies do not exist. Fields such as `extends`, `include`, `dependencies`, or graph edges MUST fail validation. A cycle test demonstrates rejection; it does not imply a cycle solver.

### 10.2 Example

```yaml
kind: preset
schema_version: 1
id: embedded
version: 0.6.0
description: STM32, FreeRTOS and realtime firmware work.
skills: [embedded.realtime-control]
required_rules: [embedded.realtime-budget]
defaults:
  selection:
    max_skills: 3
    context_budget_tokens: 6000
  skills:
    enabled: [embedded.realtime-control]
  rules:
    required_rules: [embedded.realtime-budget]
  domain:
    target: embedded
detection_hints: [stm32-ioc, freertos-config]
```

## 11. `project-profile`

### 11.1 Location and ownership

The only v0.6 project profile is:

```text
.eas/project.toml
```

It is intended to be tracked in Git. It MUST NOT contain secrets.

Runtime state remains under `.git/eas/...` and is not stored in the tracked profile.

### 11.2 Required fields

- `kind = project-profile`
- `schema_version`
- `id`
- `preset`

Optional:

- `values`
- `required_rules`
- `skills`

The profile cannot lower protected v0.5 policy/risk. The allowed configuration tree is closed and contains no lifecycle/model/provider/permission fields.

### 11.3 Example

```toml
kind = "project-profile"
schema_version = 1
id = "robot-base"
preset = "embedded"

[values]
```

`eas init --preset embedded` MUST refuse if `.eas/project.toml` already exists. `--force` MUST NOT override this ownership rule.

## 12. Built-in wheel layout

Built-in resources are packaged inside `runtime.capabilities`:

```text
runtime/capabilities/
  resources/extensions/
    embedded/
      manifest.yaml
      presets/
      skills/
      rules/
      bodies/
    ros2/
      manifest.yaml
      presets/
      skills/
      rules/
      bodies/
    release/
      manifest.yaml
      presets/
      skills/
      rules/
      bodies/
```

A clean wheel installed outside the source tree MUST load all three presets without referring back to the repository checkout.

## 13. Configuration tree

The initial configurable leaves are deliberately small:

```text
selection.max_skills
selection.context_budget_tokens
skills.enabled
rules.required_rules
domain.target
domain.mcu_family
domain.ros_distro
release.require_clean_tree
release.require_tests
```

Unknown sections/fields fail closed.

Protected paths such as lifecycle, recovery, fanout, write lease, approval, model, provider, routing, role and permission configuration are outside this tree.

## 14. Precedence

The precedence chain is exact:

```text
core defaults
  < extension defaults
  < active preset defaults
  < tracked .eas/project.toml
  < explicit CLI override
```

No other layer exists in v0.6.

### 14.1 Merge table

| Field shape | Merge behavior |
|---|---|
| typed scalar leaf | higher precedence replaces lower |
| ordinary list | higher precedence replaces entire list |
| `rules.required_rules` | deterministic additive union |
| mapping | schema container only; no generic recursive/deep merge |
| `null` | unsupported; fail closed |
| unknown field | fail closed |

For `required_rules`, duplicate/case-fold collisions inside one source fail. Exact repetition across precedence sources is idempotent; case-fold aliases fail. Each source that contributes to the final union is retained in lineage.

### 14.2 Equal-precedence extension conflict

Extension defaults share one precedence level. If two loaded extension defaults set different values for the same ordinary leaf/list, resolution fails rather than choosing by filesystem order.

v0.6 built-ins are self-contained per preset, so ordinary project resolution does not require a multi-extension dependency graph.

## 15. CLI override boundary

Only the following explicit override paths are accepted:

- `selection.max_skills`
- `selection.context_budget_tokens`
- `skills.enabled`
- `rules.required_rules`

All other CLI override paths fail.

Protected prefixes are explicitly forbidden, including:

- `lifecycle.*`
- `recovery.*`
- `fanout.*`
- `write_lease.*`
- `approval.*`
- `model.*` / `models.*`
- `provider.*` / `providers.*`
- `routing.*`
- `roles.*`
- `permissions.*`

The CLI cannot be used as an escape hatch to weaken v0.5 protections.

## 16. Resolver algorithm

For one project resolution:

1. Parse and validate built-in manifest/catalog resources in canonical ID order.
2. Validate the active extension `requires_eas` range against the running EAS version.
3. Select exactly one active preset from explicit input or tracked profile.
4. Reject explicit preset/profile disagreement.
5. Resolve core defaults.
6. Resolve extension defaults; reject equal-precedence conflicts.
7. Apply preset defaults.
8. Apply tracked project values.
9. Apply validated CLI overrides.
10. Validate resulting enabled skill IDs against active preset.
11. Validate resulting rule IDs against the trusted catalog.
12. Record lineage for every resolved leaf.
13. Collect immutable source identities/digests.
14. Attach read-only detection evidence.
15. Canonicalize and hash the `ResolvedCapabilitySnapshot`.

No step depends on directory enumeration order.

## 17. Detection contract

Detection is recommendation only. It never changes the active preset.

The result includes:

- `status`: `RECOMMENDED`, `AMBIGUOUS`, or `NONE`;
- `confidence`: `HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN`;
- optional `recommended_preset`;
- evidence entries with paths, score, rationale and missing evidence;
- contradiction text;
- deterministic evidence revision hash;
- `release_ready = false` always.

### 17.1 Embedded evidence

Strong examples:

- STM32CubeMX `.ioc` file;
- `FreeRTOSConfig.h`;
- STM32 marker in CMake;
- `Core/Inc` + `Core/Src` layout.

### 17.2 ROS 2 evidence

Strong examples:

- `package.xml`;
- ament/rclcpp markers in CMake;
- colcon metadata.

### 17.3 Release-context evidence

Examples:

- release workflow file;
- changelog;
- package version metadata.

Release detection means only "this repository has release-process context". It MUST NOT imply tests passed, the tree is clean, a tag is valid, credentials exist, or the repository is release-ready.

### 17.4 Ambiguity

Competing strong evidence within the bounded scoring window produces `AMBIGUOUS/UNKNOWN` and no recommendation. A tracked project profile remains authoritative and the conflict is reported.

## 18. Skill discovery and lazy loading

Catalog discovery loads only validated metadata.

Selection inputs:

- active preset;
- role;
- task tags;
- trigger matches in task text;
- optional explicit skill IDs that are still constrained to the active preset;
- maximum selected skill count;
- context budget.

Default maximum selected skills is **3**.

Tie order:

1. evidence score descending;
2. declaration order in active preset;
3. skill ID.

Body/reference resources are read only after selection.

If an explicitly requested skill does not fit role/context constraints, selection fails rather than silently omitting it.

## 19. `ResolvedCapabilitySnapshot`

The internal snapshot contains exactly:

- `schema_version`
- `eas_version`
- `project_id`
- `active_preset`
- source identities and SHA-256 digests
- resolved values
- per-field lineage
- selected/enabled skill IDs
- selected rule IDs
- detection evidence/revision
- snapshot `digest`

### 19.1 Canonicalization

Digest body is UTF-8 JSON with:

- sorted keys;
- compact separators;
- no non-finite numbers;
- no insignificant whitespace dependency.

SHA-256 is calculated over the canonical body without the `digest` field.

### 19.2 Persistence

Project binding lives at:

```text
.git/eas/capabilities/snapshot.json
```

Writes use temp file + flush/fsync + atomic replace, matching the existing durable-state philosophy.

Corrupted JSON, duplicate JSON keys, shape mismatch or digest mismatch fails closed.

### 19.3 Drift and migration

If a persisted digest differs from the currently resolved digest, stack-controlled configured operations refuse and request explicit migration.

There is no silent rebind.

`eas project migrate-snapshot` is the explicit project-level operation. An optional expected-old-digest provides a compare-and-swap guard.

## 20. Goal lifecycle binding and v0.5 migration

Projects without `.eas/project.toml` retain v0.5 behavior and goal-state version 2.

A configured v0.6 project creates new goals with goal-state version 3 containing `capability_snapshot_digest`.

For a configured project:

- `goal gate` MUST verify project snapshot is bound and current;
- goal state MUST contain the same digest;
- transitions, checkpoints, approvals, recovery and export pass through the same binding check;
- drift requires explicit project snapshot migration, followed by explicit goal capability migration;
- goal capability migration is revision-checked;
- goal capability migration is refused while an assignment is active.

Legacy goal state is not silently upgraded merely because a profile appears.

`eas goal bind-capabilities GOAL_ID --revision N` is the explicit goal migration operation.

## 21. Delegation preflight binding

`DelegationRequest` and `ResolvedExecutionPlan` may carry `capability_snapshot_digest`.

A caller that controls configured-project dispatch SHOULD supply the current resolved digest as `required_capability_snapshot_digest` to the provider-neutral preflight. Preflight rejects a mismatch with `capability_snapshot_mismatch`.

This insertion does not change role/model/provider resolution. It only binds the resolved plan to the already selected capability state.

## 22. CLI contract

Required v0.6 surfaces:

```text
eas preset list
eas preset show PRESET
eas preset detect [--project PATH]
eas preset check [PRESET] [--project PATH] [--override PATH=JSON]
eas project status [--project PATH]
eas init [PROJECT] --preset PRESET
```

Explicit migration surfaces:

```text
eas project migrate-snapshot [--expected-old-digest DIGEST]
eas goal bind-capabilities GOAL_ID --revision N
```

Machine-readable commands support stable JSON where the command already exposes `--json`.

`eas preset detect` is read-only.

`eas project status` is read-only and reports `UNBOUND`, `BOUND`, `DRIFT`, or `CORRUPT` snapshot state as applicable.

`eas init --preset` preflights profile non-overwrite before writing project-managed role artifacts.

## 23. Runtime insertion points

The implementation is additive:

```text
user / project
  -> .eas/project.toml
  -> strict contract loader
  -> built-in catalog
  -> deterministic resolver
  -> read-only detector
  -> ResolvedCapabilitySnapshot
       |-> lazy skill selector
       |-> trusted rule checker references
       |-> delegation preflight digest
       `-> .git/eas/capabilities/snapshot.json
               |
               `-> goal lifecycle binding
                    -> gate / transition
                    -> checkpoint / approval
                    -> recovery / export
```

Existing provider adapters and role definitions remain downstream and unchanged.

## 24. Release/package requirements

A v0.6 release candidate MUST prove:

- exactly seven core role descriptors remain;
- built-in resources are present in a clean wheel;
- wheel import and preset list work outside source checkout;
- Python 3.9 syntax compatibility;
- Windows and Linux path assumptions are conservative;
- existing v0.5 tests remain green;
- adapter generation remains deterministic;
- structure/provenance/agent/routing/task/benchmark validators remain green;
- version metadata and CLI version match;
- Git diff has no whitespace errors.

## 25. TDD acceptance matrix

| Area | Required positive evidence | Required negative evidence |
|---|---|---|
| manifest | valid built-in manifest | invalid/unknown schema, unknown key |
| YAML | valid JSON-compatible subset | duplicate key, alias, anchor, tag, implicit date, non-finite |
| TOML | valid tracked profile | malformed/duplicate key, secret-like/unknown field |
| IDs | canonical lowercase IDs | duplicate and case-fold collision |
| paths | package-relative path | traversal, absolute, reserved/ambiguous component, symlink/reparse escape |
| versions | supported SemVer/range | wildcard/caret/unsupported range, incompatible EAS |
| dependencies | no dependency metadata | dependencies/extends/include/cycle constructs rejected |
| resolver | exact five-level precedence | equal extension conflict, unknown/deep/null field |
| lists | ordinary atomic replacement | no undocumented append/deep merge |
| required rules | deterministic additive union | duplicate/case-fold collision rejection |
| CLI override | four allowlisted paths | lifecycle/recovery/write/model/provider/role override rejected |
| detection embedded | STM32/FreeRTOS evidence | false positive/no evidence |
| detection ROS2 | package.xml + ament evidence | false positive/no evidence |
| detection release | workflow/process context | never reports release readiness |
| detection ambiguity | one clear recommendation | competing strong evidence -> AMBIGUOUS/UNKNOWN |
| skills | metadata-first selection | body unavailable before/after loading boundary tested |
| skill bounds | max <= 3 and context budget | max > 3 / explicit skill budget failure |
| snapshot | deterministic canonical hash | corruption/digest mismatch/drift refusal |
| migration | explicit CAS migration | silent rebind forbidden |
| project init | creates profile + snapshot | existing profile non-overwrite |
| goal binding | v3 goal carries digest | legacy goal not silently rebound; active migration refused |
| preflight | matching digest passes | required digest mismatch rejects |
| wheel | installed built-ins available | no source-tree dependency |
| regression | v0.5 suites green | protected semantics unchanged |

## 26. Architecture decision

The research evidence supports a bounded declarative capability layer and does not justify a general plugin runtime, dependency solver, executable marketplace, extra agent roles, or a new orchestration engine in v0.6.

The frozen implementation direction is therefore:

```text
7 roles stay fixed
+ declarative extension descriptors
+ 3 built-in presets
+ deterministic config resolution
+ read-only capability detection
+ lazy skill loading
+ trusted checker references
+ canonical capability snapshot
+ explicit lifecycle binding/migration
```

No unresolved architecture blocker remains within the v0.6 scope.

**ARCHITECTURE_READY_FOR_IMPLEMENTATION**
