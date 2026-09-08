# Five candidate contracts

Status: research proposal; no schema or parser has been implemented. MUST/MUST NOT below specify proposed v0.6 acceptance requirements. They do not describe existing support.

## Shared conventions

Package manifests and skill/rule/preset descriptors are single UTF-8 YAML mappings using a restricted JSON-compatible value model. Project profiles use TOML, which is already available through the Python 3.9-compatible dependency path. Parsers must reject duplicate keys, aliases/merge keys, custom tags, implicit timestamps, non-finite numbers, invalid scalar types and unknown fields. No YAML constructor, remote schema fetch, interpolation or expression evaluation is allowed.

Every descriptor has `schema_version` (integer `1`), `kind` (one of the five exact names below), `id` and bounded `description`. Package/export descriptors additionally have a package-owned `version` expressed as a SemVer string; project-profile uses the profile file digest instead of a release version. This draft is the candidate meaning of schema version 1, not an assertion that EAS v0.5 supports it.

Package IDs have two lowercase ASCII segments, `publisher/name`; each segment matches `[a-z][a-z0-9-]{0,63}`. Export IDs are one such segment, unique per kind inside a package. The fully qualified reference is `publisher/package#kind/export-id`, where kind is `skill`, `rule` or `preset`. Core IDs and the `eas` publisher namespace are reserved to the stack distribution; local authors cannot acquire trust merely by choosing that namespace. Project IDs are a single lowercase segment with the same grammar. Display names never participate in resolution.

Every package-owned descriptor version must equal its enclosing package version in the first contract. Independent skill/rule release versioning is deferred. `schema_version`, package `version`, `requires.eas`, provider capability compatibility and durable-state version are distinct axes. See [version rules](resolution-and-enforcement.md#compatibility-and-versioning).

All relative content paths use `/`, are relative to the declaring package or selected project root, and must resolve within it. Reject parent traversal, absolute/drive/UNC paths, Windows-reserved names, case-fold collisions, ambiguous trailing dots/spaces, symbolic links/junctions/reparse-point traversal and special files. No wildcard content exports. URLs are inert attribution references, not paths to fetch.

Candidate resource ceilings: 64 KiB per descriptor/profile; 100 exports per package; 64 selected packages; 256 KiB per skill body; 1 MiB per individual reference; 10 MiB total declared package content; 32 mapping levels. These are parser/resource safety proposals, not measured optimal context budgets. UTF-8 byte counts apply before parsing; report limit errors explicitly. Context loading remains subject to tighter per-assignment bounds and the required-evidence exception.

## 1. `extension-manifest`

Purpose: identify a declarative bundle and enumerate its inspectable content, compatibility and lineage. Candidate filename: `extension.yaml` at an explicitly selected package root. It is not a Python package, native provider plugin or execution authority.

| Field | Type / requirement | Meaning and validation |
| --- | --- | --- |
| `schema_version`, `kind`, `id`, `version`, `description` | Required shared fields; kind `extension-manifest` | Stable package identity and parser/release identity. Duplicate identities reject even if discovered in different roots. |
| `license` | Required nonempty string | Declared license identifier/expression or local license reference; no legal conclusion from syntactic validity. Per-file exceptions belong in provenance. |
| `provenance` | Required nonempty list of origin records | Record form below. Must cover all exported and referenced files; original local material is explicitly recorded as original. |
| `requires.eas` | Required bounded version constraint | Supported EAS release range, independent of schema version. |
| `requires.capabilities` | Required list, may be empty | Versioned, stack-registered capabilities needed for activation, e.g. declarative skill context or a named rule boundary. Unknown required capability blocks activation. Not provider tools to install. |
| `effect` | Required `read-only` or `read-write` | Maximum declared workflow effect across exports. Discovery is always read-only. `read-write` does not confer permission. Underdeclared effects reject. |
| `provides.skills`, `provides.rules`, `provides.presets` | Required lists, may be empty | Entries `{id, path}`. Manifest ID/kind/version must match descriptor. Each referenced descriptor and body must be in inventory. At least one export is required. |
| `content` | Required list of `{path, sha256, media_type}` | Closed inventory of manifest-reachable descriptors, skill bodies, references and notices. SHA-256 is 64 lowercase hex digits over raw file bytes. Manifest itself is hashed by the resolver, not self-listed. Reject missing/mismatched/duplicate entries. |
| `settings` | Optional mapping of package-local setting names to constrained declarations | Allowed types: boolean, integer, string, homogeneous string list. Declaration contains type and optional default, enum, minimum/maximum or maximum length/items as appropriate. Unknown declaration fields and unbounded strings/lists reject. No remote `$ref`, executable validation or arbitrary object schemas. |
| `conflicts` | Optional list of package IDs | Symmetric activation conflict: either party declaring a conflict is sufficient. All installed-but-unselected packages are irrelevant. |
| `detection_hints` | Optional bounded list | Entries with `id`, project-relative literal `path`, and explanatory `rationale`; file-existence hints only. Report a suggestion with evidence, never auto-select. No commands, glob walkers or file-content regex execution. |

Origin record fields: `class` (`original`, `conceptual`, `adapted`, `vendored`, `generated`), `source` (repository/document URL or local origin label), `revision` (exact upstream commit/tag when applicable), `source_paths`, `local_paths`, `license`, `notice_paths`, `changes`. Use empty lists only when genuinely inapplicable, and explain applicability in `changes`. Adapted/vendored records require exact source files and a pinned revision plus required license/notice evidence before activation; generated records additionally require `generator` and `input_refs`. Conceptual attribution does not imply copied material. Digests prove identity, never authorship, license permission or approval.

Only declarative text/data and license notices are eligible for the content inventory. Reject executable scripts, binaries, custom commands, hooks, dynamic modules, MCP server definitions or install actions in the selected inventory; unlisted files are not exports and must never be loaded, copied or executed by EAS. A package containing an upstream skill script therefore needs an explicitly curated declarative subset before activation. Do not claim full compatibility with every upstream skill package.

No transitive extension dependencies in the initial contract. Presets may reference exports only from their own package. A project may explicitly select several independent packages and their exports. `conflicts` detects incompatibility; it does not launch a dependency solver or install missing packages. Unsupported `dependencies`, `entrypoint`, `hooks`, `agents` or provider model fields reject as unknown fields.

## 2. `skill`

Purpose: supply bounded domain/workflow expertise to an existing role for an assigned task. Candidate descriptor location: `skills/<id>/skill.yaml`, with body in `SKILL.md`. Body markdown is content; EAS activation is governed by the descriptor, not any frontmatter that claims authority.

| Field | Type / requirement | Meaning and validation |
| --- | --- | --- |
| Shared fields | Required; kind `skill` | Export ID and enclosing package version. |
| `roles` | Required nonempty list of core role IDs | Applicability only; must not change mission, access or compatible profiles. |
| `purpose`, `non_goals` | Required bounded string and nonempty string list | What expertise the skill supplies and where it stops. |
| `inputs` | Required nonempty list of `{id, description, required}` | Bounded facts/references needed before use. Missing required input yields blocked/escalation, not invented context. |
| `activation` | Required mapping | `mode` is `explicit` or `suggest`; optional lists of task domains and stages are exact metadata matches. No auto-dispatch. Suggestions include rationale and need controller/task selection before loading. |
| `body` | Required package-relative markdown path | Hash-bound through manifest inventory; load only after selection/applicability validation. |
| `references` | Required list, may be empty | `{id, path, required}` records for declared local text resources. URLs may appear as evidence in prose but are never fetched during discovery. |
| `effect` | Required `read-only` or `read-write` | Declared skill effect must fit package effect and each applicable role's canonical boundary. A read-write skill cannot target a read-only role. Test-artifact-only remains a narrower restriction. |
| `requires.capabilities` | Required list, may be empty | All requirements must be met by an already trusted stack/adapter; not requests to enable tools. |
| `output_additions` | Required list, may be empty | Named, namespaced evidence descriptions added to the base assignment result. Cannot remove or rename required base fields. |
| `completion_evidence`, `escalation` | Required nonempty string lists | Additional domain evidence and handoff conditions; additive to core contract. |
| `evaluation_refs` | Optional list of declared local evidence paths | Trigger/near-miss and quality evidence, explicitly unverified if absent. Metadata does not establish readiness. |

No `model`, `reasoning_effort`, sandbox, tool grant, spawn budget, command or role-definition field is allowed. A skill may describe the need for a project test, but loading it does not run that test or authorize a write. Mandatory instructions in prose remain subordinate to stack/assignment authority; contradictory prose makes the skill ineligible after review. Static validation cannot prove prose harmless, so it must not become an executable policy channel.

Selection is not proof of use: trace selected, loaded and observed use separately. Required resources that do not fit the assignment's evidence budget block/escalate; optional resources may be omitted with a reason. Do not silently replace core instructions with the skill or concatenate unrelated complete skill catalogs.

## 3. `rule`

Purpose: declare a scoped requirement with an honest enforcement class and evidence contract. It neither adds routing code nor provides executable validators.

| Field | Type / requirement | Meaning and validation |
| --- | --- | --- |
| Shared fields | Required; kind `rule` | Stable requirement identity, package-owned release. |
| `requirement` | Required bounded string | The condition to establish; no shell/expression DSL. |
| `scope` | Required mapping | Optional nonempty lists `roles`, `domains`, `stages`, `paths`; omitted dimension means all. Values OR within a dimension, dimensions AND together. Path entries are normalized repository-relative literal subtrees; no glob semantics. Unknown role/stage names reject. |
| `severity` | Required `info`, `warning`, `error` or `critical` | Importance, independent of enforcement class. Raising severity never fabricates a gate. |
| `enforcement` | Required `guidance`, `validator` or `gate` | Supported activation requires the class to be available; never downgrade gate to guidance silently. |
| `check_ref` | Required for validator/gate; forbidden for guidance | ID and version of a trusted, pre-registered stack check, with typed parameters constrained by that check's own schema. No executable path/argv/import supplied by package. |
| `boundary` | Required for gate; forbidden otherwise | A registered stack-controlled action boundary with matching supported check/evidence capability. Future candidates are delegation admission and acceptance/release admission. Naming one here does not create it in v0.5. |
| `evidence` | Required nonempty list of `{id, description}` | Checker outcomes must bind rule/check versions, target revision, effective resolution, scope, timestamp and evidence references. |
| `on_missing` | Required `block` or `escalate` | For unavailable/stale/unknown evidence; neither is PASS. Validator can report it; gate must prevent the covered action. |
| `exception_policy` | Required `none` or `stack-controlled` | No inline waivers or alternate approval authority. Stack-controlled means only an independently defined stack exception path, if one exists. |

Guidance requires recorded judgment; validators return findings but cannot claim to stop execution. A gate needs an implemented caller that checks completed evidence before its named side effect. A post-work validator cannot claim to have prevented writes. Unknown boundary/check IDs or unsupported versions make required activation fail closed.

All rules required by the active preset are mandatory for that selection. The project may add required rules but cannot disable, replace or weaken preset/core rules. Rule ID collisions reject; higher-precedence files cannot redefine a rule's severity, scope, evidence, check or exception semantics. Scope that does not apply yields `not_applicable` with explanation, not a passing observation.

Project-specific executable check registration is deliberately outside extension-manifest and project-profile v1. Until a vetted check is registered through a separate reviewed stack mechanism, a domain gate remains a candidate and cannot be activated as enforced. Prose guidance can still be selected under an explicitly guidance-only rule.

## 4. `preset`

Purpose: choose a coherent default skill/rule/settings bundle for a domain or stage without introducing an agent, compute tier or runtime.

| Field | Type / requirement | Meaning and validation |
| --- | --- | --- |
| Shared fields | Required; kind `preset` | Qualified selection identity, not a role alias. |
| `domain` | Required bounded lowercase string | Domain label; candidate initial built-ins are embedded, ros2 and release. Domain labels do not supply task risk. |
| `skills` | Required list, may be empty | Same-package fully qualified skill references, unique. Default active skill set, subject to role/task applicability. |
| `required_rules` | Required list, may be empty | Same-package rule references, unique. Additive to core; all applicable rule requirements must be supported before activation. |
| `defaults` | Required mapping, may be empty | Package-owned settings only, keyed by declared setting name and validated against manifest `settings`. No arbitrary core config paths. |
| `requires.capabilities` | Required list, may be empty | Union with selected rules/skills' capability requirements; cannot hide an unmet child requirement. |
| `evidence_expectations` | Required list, may be empty | Additional bounded completion evidence descriptions. These do not attest that evidence exists. |

Choose at most one preset. No `extends`, `include`, nesting, prepend/append/wrap, executable template, condition expression, provider override or cross-package preset references. One preset plus explicit extra rule/skill references in project-profile is the proposed answer to embedded/ROS2 plus release work. It needs acceptance scenarios before being called sufficient.

The absence of a preset is valid and preserves core-only behavior. Selecting a preset does not activate every export in its package. Replacing a preset for a new goal is an explicit selection change, not an exception to required checks on existing work. Active work is pinned as described in [recovery binding](resolution-and-enforcement.md#binding-to-plans-goals-and-recovery).

## 5. `project-profile`

Purpose: declare a project's reproducible selections, bounded facts and package settings. Candidate tracked path: `.eas/project.toml`. Optional developer-local overlay: `.eas/project.local.toml`, which should be ignored by the project if adopted. No files at these locations are created by this research.

| Field | Type / requirement | Meaning and validation |
| --- | --- | --- |
| `schema_version`, `kind`, `id`, `description` | Required in tracked profile; kind `project-profile` | Project identity does not replace Git-root identity. Overlay declares schema/kind but cannot redefine project ID or description. |
| `requires.eas` | Required in tracked profile | Intersect with package compatibility and actual stack version. |
| `extensions` | Required list, may be empty | Each record has package `id`, project-relative `path`, exact `version`, raw `manifest_sha256`. Path may name a project-local vendored declarative bundle. No URLs or fetch behavior. |
| `preset` | Optional qualified preset reference | At most one from selected packages; omission means none. Resolve before merging selected preset defaults. |
| `skills` | Optional unique list of qualified skill references | Explicit default skill set; replaces preset's default skill list when present, subject to required rule/evidence constraints. Empty list disables optional skills, not rules or evidence. |
| `required_rules` | Optional unique list of qualified rule references | Adds to preset/core requirements. Cannot remove a lower layer's mandatory rule. |
| `settings` | Optional mapping `package-id -> declared setting -> value` | Only selected packages' declared settings; no arbitrary role/policy/provider objects. Each typed leaf replaces a lower value. |
| `facts` | Optional bounded mapping of namespaced string facts | Project-declared board, toolchain, distribution, quality target, etc.; context only, never observed evidence or trusted task-risk classification. No secrets. |

The local overlay is a closed subset: it may set `preset`, `skills`, `settings`, `facts` and add `required_rules`. It cannot edit package pins/roots, project identity, EAS requirements or protected core fields. Changing a package pin requires explicit tracked profile change and a new resolution. A null/tombstone deletion syntax is not supported by this TOML contract; absent leaves inherit and lists have the field-specific semantics above.

Candidate CLI overrides permit only the same selectable leaves and additive required rules, plus explicit profile-file selection anchored to the chosen project root. They cannot alter installed package identity, core role/profile compatibility or trusted validator registration. File selection replaces implicit profile selection; it does not add another ancestor cascade. A profile can be absent for core-only operation; malformed, explicitly missing or incompatible selected input is an error, never ignored.

Precedence controls defaults, not permission: profile facts cannot grant network/write access, issue approvals, select native sandbox modes, lower risk, waive mandatory checks, set active leases or certify completion. Unknown keys fail rather than becoming provider configuration.

## Cross-contract validation requirements

1. Manifest export identity, descriptor kind/version, content digest and provenance coverage agree.
2. All selected references resolve exactly once within explicitly selected packages; no same-name shadowing, cross-package preset dependency or implicit fallback.
3. Skill effect/roles fit canonical access; selected settings fit closed package declarations. Effects and capabilities are declared needs, not grants.
4. All applicable required rules have available check/boundary support and additive evidence requirements; contradictions produce diagnostics, not precedence-based rule replacement.
5. All selected versions satisfy the engine/schema/capability contracts; effective configuration and content hashes form one immutable resolution identity.
6. Parse/discover/validate/explain only read declared data. No package-supplied command is run and no active goal, adapter artifact or project instruction is mutated by selection inspection.
