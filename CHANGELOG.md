# Changelog

All notable project changes will be documented here.

## [Unreleased]

No unreleased changes.

## [0.6.6] - 2026-09-09

### Added

- Add persisted per-goal efficiency evidence for spawned assignments, reuse decisions, resume/retry attempts, replacement assignments and peak active children. Provider token, cost and latency fields remain explicitly `null` unless externally evidenced.
- Add read-only `eas goal efficiency GOAL_ID [--json]` reporting. Goal trace export and status include the same deterministic efficiency summary.
- Add regression coverage for budget 6/8, conservative default concurrency, reuse-before-spawn persistence, corruption retry/replacement idempotency and efficiency CLI behavior.

### Changed

- Change `auto` reader scheduling from `balanced=3` to `conservative=2`; `balanced=3` and `read-heavy=4` remain explicit opt-in ceilings for genuinely independent work. Writer ownership remains serialized at one.
- Tighten durable fan-out from soft/hard `8/12` to `6/8` and strengthen native Codex guidance to inspect/reuse existing specialists instead of creating retry/round2/final-retry workers.
- Preserve the v0.6.5 Codex-native stable path and exactly seven canonical roles; v0.6.6 reduces agent proliferation rather than adding agents or another runtime.

## [0.6.5] - 2026-09-08

### Added

- Add a canonical public project identity and attribution contract for Engineering Agent Stack, with creator attribution to Nguyễn Khắc Tùng Lâm (Tùng Lâm Automation) and an explicit provider/foundation-model boundary.
- Inject the canonical EAS identity into all seven generated Codex roles and the parent orchestration policy, without duplicating unrelated private biography.
- Add adaptive child concurrency profiles: `conservative=2`, `balanced=3`, and `read-heavy=4`; `auto` selects conservative for write-capable work and balanced for read-only work.

### Changed

- Restore the Codex-native subagent path as the default execution baseline: Codex owns spawn/wait/follow-up/transport; EAS durable goal, approval and recovery services are opt-in for explicitly initialized durable workflows.
- Reduce generated child instruction size and parent orchestration prompt size while preserving all seven role boundaries, creator attribution, provider separation, evidence discipline and release-critical review guidance.
- Raise the Codex session ceiling to four children so EAS can use adaptive 2/3/4 advisory scheduling while keeping writer ownership serialized at one; this is a configured ceiling, not a guarantee that provider-native four-way streams are healthy in every session, and normal work should prefer 1-2 children.
- Tighten encrypted-output recovery guidance: one same-child resume attempt, then replacement/fallback instead of repeated retries of a corrupted stream.
- Persist the resolved concurrency mode with goal assignments and preserve it across replacement/recovery.
- Publish canonical package/license authorship for Nguyễn Khắc Tùng Lâm (Tùng Lâm Automation).

## [0.6.4] - 2026-09-08

### Fixed

- Stop generating or forcing the experimental `features.multi_agent_v2` Codex table. Live A/B acceptance on Codex 0.153.4 reproduced `Encrypted function output content could not be decrypted or decoded` with V2 enabled while the same custom `scout` child completed through the public `[agents]` surface.
- Align Codex and EAS child concurrency at two active children per session, preserving the seven generated roles and v0.6.3 bounded recovery behavior.
- Make installer validation reject `features.multi_agent_v2.enabled=true`, while tolerating an explicitly disabled legacy table so existing users can migrate without destructive config rewrites.
- Update provider probes to exercise native public subagent routing instead of masking failures by forcing experimental feature flags.

## [0.6.3] - 2026-09-08

### Hardened

- Classify transient transport, encrypted-output corruption and agent failures separately in durable assignment recovery evidence.
- Resume before replacement with at most two resumes and one replacement per lineage; retain stopped-executor approvals, revision checks, fanout limits and reconnect capacity reservations.
- Default to two active children total (existing routing policy permits 1..4); unresolved recovery creates a scheduling barrier.
- Require bounded summary/evidence/files/commands/risks/next-action handoffs for replacement, referencing large logs by artifact or path.
- Add goal transport/replacement operations and installed-wheel transport recovery smoke coverage.

This hardens EAS orchestration contracts. It does not intercept Codex App reconnects or repair upstream encrypted stream decoding. Exactly seven core roles and the frozen runtime/capability architecture remain; no personal managed-install changes are required or performed.

## [0.6.2] - 2026-09-08

### Hardened

- Build wheel and sdist once per CI/release run; Linux and Windows validate the exact downloaded bundle, and publish promotes that same bundle without rebuilding.
- Bind the immutable workflow artifact ID to a strict SHA-256 manifest and an independent build-job manifest digest. Reject missing, extra, renamed and altered files; inspect both archives for candidate metadata and all 24 canonical capability resources.
- Preserve clean installed-wheel import/version/preset and goal checkpoint/approval/recovery/export smoke; verify bundle identity before and after it.
- Pin official checkout, setup-python, upload-artifact and download-artifact Actions to verified release commit SHAs, all using Node 24. Make download digest mismatches fatal and close Windows command-failure masking gaps.

Runtime and capability architecture are unchanged: seven core roles, declarative data-only extensions, and the frozen v0.6 safety contracts. Unchanged built-in capability packs remain at 0.6.0. This release guarantees exact-artifact promotion, not deterministic independent rebuilds or locked dependencies.

## [0.6.1] - 2026-09-08

### Changed
- Upgrade official GitHub checkout/setup-python actions to Node 24-based v7 on hosted Linux and Windows runners.
- Share clean-wheel smoke between main CI, release validation and local checks: isolated virtual environment and working directory, installed import origins, version agreement, all three preset CLI views, and byte-for-byte verification of every built-in capability resource.
- Preserve installed goal recovery smoke and fail immediately on Windows release-tag validation errors.

### Tests
- Cover extension-order-independent resolver/snapshot results, recommendation/resolution without activation, and preservation of snapshot bindings after rejected drift or migration.

### Compatibility
- All v0.6 frozen boundaries and seven core roles remain unchanged; built-in declarative pack versions remain 0.6.0. No v0.7 features or research-history changes.

## [0.6.0] - 2026-09-08

### Added
- Strict declarative v0.6 contracts for extension manifests, skills, rules, presets and tracked project profiles.
- Built-in `embedded`, `ros2`, and `release` capability packs packaged inside the Python wheel.
- Deterministic five-level configuration resolver with per-value lineage, atomic list replacement and additive `required_rules`.
- Read-only evidence-based preset detection with bounded confidence, explicit ambiguity and no automatic activation.
- Metadata-first lazy skill discovery/selection with a default maximum of three skills and explicit context budget.
- Trusted core checker registry so declarative packages can reference checks without shipping executable validators.
- Canonical SHA-256 `ResolvedCapabilitySnapshot` state under `.git/eas/capabilities/` with corruption/drift refusal.
- `eas preset list/show/detect/check`, `eas project status/migrate-snapshot`, `eas init --preset`, and explicit `eas goal bind-capabilities`.
- v0.6 negative-first regression coverage for parser/schema/path/merge/detection/skill/snapshot/profile/CLI boundaries.

### Changed
- Delegation requests and resolved execution plans can carry an optional capability snapshot digest; preflight can require an exact current digest.
- Configured v0.6 goals use version 3 durable state containing the capability digest, while legacy/unconfigured projects retain v0.5 version-2 behavior.
- Stack-controlled goal gate/transition/workflow paths require the configured project and goal snapshot bindings to agree.
- Python packaging includes `runtime.capabilities` and all built-in declarative resources for source-independent wheel installs.

### Safety boundary
- v0.6 extensions are data only: scripts, hooks, entrypoints, dynamic import/eval, dependency solving, preset inheritance, remote code/schema loading and MCP auto-launch are unsupported and fail closed.
- Presets/extensions cannot add roles or modify protected lifecycle/recovery/write-lease/approval/model/provider/routing semantics.
- Release detection identifies process context only and never claims release readiness.
- Capability drift is never silently rebound; project and goal migration are explicit revision/digest-checked operations.

## [0.5.0] - 2026-09-08

### Added
- Durable workflow checkpoints with bounded verification, review and provider evidence references.
- `eas goal checkpoint`, `plan`, `approve`, `recover`, and machine-readable `export`.
- Revision-scoped explicit approval evidence, expiry, atomic consumption and idempotent receipts for recovery and risky lifecycle transitions.
- Policy-defined stale/timeout suspicion that retains capacity and requires evidence the prior executor stopped before recovery of the same assignment ID.
- Concurrency, corruption, crash-boundary, approval, export and installed-package recovery coverage.

### Changed
- Version 2 goal snapshots include workflow evidence; valid v1 snapshots migrate on their next mutation.
- Snapshot writes flush/fsync before atomic replacement and sync the directory on POSIX; crash-left locks remain operator-controlled.
- Export explicitly distinguishes authoritative durable evidence from nontransactional JSONL observations, including parse warnings and completeness limits.
- Release package smoke exercises recovery on Linux and Windows outside the source tree.

### Safety boundary
- Enforcement covers stack-controlled goal operations only. Approval is a local operator attestation, not identity authentication or native process verification. No native spawn interception, process termination, or automatic dispatch is claimed.

## [0.4.0] - 2026-09-08

### Added
- Executable per-goal lifecycle gate with `REUSE / SPAWN / ESCALATE / REJECT` decisions.
- `eas goal init`, `goal gate`, `goal transition`, and `goal status`.
- Atomic goal state and append-only JSONL lifecycle events under Git metadata.
- Enforcement for soft/hard child budgets, reader/writer capacity, and architect/reviewer reuse policy.
- Goal lifecycle schema and Python runtime contracts.

### Changed
- `eas status` now reads canonical routing/lifecycle limits instead of reporting hard-coded stale values.
- Python distribution now packages the provider-neutral `runtime` module required by lifecycle CLI commands.
- Roadmap prioritizes durable workflow/recovery before domain presets.

### Fixed
- Lifecycle state no longer dirties a project worktree; operational state is stored under `.git/eas/goals/`.
- Concurrent goal commits are serialized and revision-checked so stale callers cannot lose assignments or bypass writer limits.
- Fresh-context requests cannot duplicate an already-active same role/domain/scope assignment, and lifecycle override reasons are persisted in event evidence.
- Corrupted goal-state shapes and cross-platform-unsafe goal IDs fail closed with bounded CLI errors.

## [0.3.1] - 2026-09-08

### Added
- Goal-level fan-out guidance with an 8-assignment soft reconciliation point and 12-assignment ordinary hard ceiling.
- Resume-before-spawn lifecycle policy and stable role/domain assignment naming.
- Agent-registry fan-out summary with active/terminal/per-role counts and budget state.

### Changed
- Default parallel read-only children reduced from 4 to 3; writer ownership remains 1 scope owner.
- Architect defaults to one consultation per goal and reviewer to one independent worker per meaningful change-set, with follow-up reuse preferred.
- Parent Codex instructions now explicitly reconcile existing children before spawning more work.

## [0.3.0] - 2026-09-08

### Added
- Stable `eas` distribution CLI with `version`, `doctor`, `status`, `install`, `init`, `check`, `update`, and `uninstall`.
- Windows PowerShell and POSIX one-line bootstrap installers using a managed source checkout under `~/.codex/engineering-agent-stack`.
- Python package metadata and the `eas = eas_cli.cli:main` console entry point with a Python 3.9 compatibility floor and PyYAML as the adapter-generation runtime dependency and `tomli` conditionally on Python <3.11.
- Read-only structured health/status output with provider health explicitly left unknown unless probed separately.
- Drift-aware lifecycle tests for project initialization, update refusal, and ownership-safe uninstall.
- `docs/CLI.md`, `docs/DISTRIBUTION.md`, and tagged-release workflow.
- Research Wave 2 analysis covering OpenAI Agents SDK, Microsoft Agent Framework, AutoGen, LangGraph, Deep Agents, CrewAI, smolagents and OpenHands.
- Authoritative `openai/codex` implementation/public-contract research notes.
- Seven provider-neutral core role definitions and semantic contract validation.
- Executable deterministic routing-policy evaluator.
- Deterministic Codex adapter generator with drift checking.
- Codex role-to-semantic-profile mapping separate from canonical roles.
- Normalized benchmark/run-capture contracts and Codex JSONL capture pipeline.
- `controlled-v1` benchmark suite with deterministic text/test graders.
- Safe Codex installer with project/personal scope, dry-run, drift check, conflict refusal, and backup behavior.
- Managed parent-orchestration block for target-project `AGENTS.md`.
- `ACKNOWLEDGEMENTS.md` with explicit credit to all repositories currently in the research matrix.
- `docs/PROVENANCE.md` and provenance validation.
- Windows Codex installation/acceptance documentation.
- Stack-owned acceptance core covering repository validation, isolated installation, direct-first behavior, and exact bounded-write scope.
- Separate Codex provider/runtime probe for `spawn_agent`, custom-role selection, Multi-Agent V2 behavior, and child-model telemetry.
- Locale-independent UTF-8 subprocess capture with Windows regression coverage.
- Offline Windows GitHub Actions acceptance job.
- Provider-neutral v0.2 runtime contracts for delegation preflight, resolved execution plans, agent status/registry, and bounded context packets.
- Lightweight `scripts/agent_status.py` renderer for human-readable or JSON registry snapshots.
- Executable `scripts/resolve_delegation.py` preflight/planning gate plus strict `delegation-request` schema/example.
- Controlled `context-packet-synthetic-001` task and `context-packet-full-vs-bounded` experiment foundation.
- `can1357/oh-my-pi` conceptual research note and provenance entry for runtime-resolution/observability patterns.

### Changed
- README is now product-oriented: one-line installation and first-use workflow come before internal architecture/research details.
- v0.3 keeps the seven core roles stable and moves domain presets/extensions to the next roadmap phase.
- Managed upgrades require clean `main`, fast-forward only, adapter drift verification, compatible personal configuration, and no locally modified managed roles.
- Bootstrap installers do not silently modify PATH and delegate v0.3+ updates to `eas update`.
- Repository comparison matrix remains the source-of-truth list for acknowledged research inputs.
- `config/model-profiles.yaml` uses `gpt-5.6-sol` for the critical candidate while retaining Astra as benchmark-only.
- Scout and researcher retain the Luna cost tier but use medium reasoning as the current quality-floor candidate.
- Context budgeting is adaptive across input context, work budget, and result budget rather than a hard total-token quota.
- Stack-controlled delegated routes now have an explicit provider-neutral preflight/resolution path; hard violations reject and unresolved quality/budget gates escalate rather than silently falling back. The Python gate does not claim to transparently intercept provider-native child calls.
- Codex runtime identity (`openai-codex`) is separated from model-provider identity (`openai`), and role-specific reasoning overrides resolve from adapter metadata.
- Project-scoped installation can now install/refresh only the managed Engineering Agent Stack block inside an existing `AGENTS.md`.
- README now makes Windows + Codex project-scoped acceptance the primary quick-start path and retains explicit upstream acknowledgements.
- CI asserts synthetic subagent telemetry, project parent instructions, Windows offline acceptance, and locale-independent UTF-8 subprocess handling.
- Stack-owned release acceptance no longer forces or gates on Codex child-agent spawning/model routing; those provider capabilities are observed by a separate diagnostic command.
- Legacy `scripts/acceptance_test_codex.py` is now a compatibility entry point for the stack-owned acceptance core.
- Generated Codex installations enable Multi-Agent V2 collaboration in code mode (`non_code_mode_only = false`), matching this engineering stack's intended execution surface.
- Provider failure reports now preserve concise final-provider-message evidence and collaboration-call counts when public JSONL contains no observed spawn event.
- Windows acceptance, installation, roadmap, and adapter documentation now reflect the split live-test architecture and the 2026-09-07 `codex-cli 0.153.4` results.

### Fixed
- Windows bootstrap keeps detected Python commands array-safe even when only `python`/`python3` is available.
- Bootstrap creates a managed `.venv`, supplies PyYAML for adapter generation, and supplies `tomli` on Python 3.9/3.10, so a clean supported interpreter is sufficient.
- `eas init` resolves nested invocation paths to the Git repository root.
- Invalid explicit `EAS_REPO` values refuse instead of falling back to another checkout.
- v0.3 bootstrap ref behavior is intentionally main-only; unsupported refs are rejected instead of being inconsistently updated.
- Release tags must match the package version and pass Python 3.9 Linux + Windows gates before the publish job receives write permission.
- Linux and Windows release gates now build the distribution, install the wheel into a clean Python 3.9 venv, run `eas version`, and execute adapter generation before publish.
- Update rollback failures are surfaced explicitly instead of being silently ignored.
- Uninstall preserves unrelated `AGENTS.md` indentation/whitespace outside the managed block.
- `eas update` refuses incomplete personal role installations instead of creating missing managed roles.
- Project instruction install/uninstall preserves mixed LF/CRLF user-owned `AGENTS.md` bytes outside the managed block.
- Generated installations no longer hide `spawn_agent` from code-mode sessions through `non_code_mode_only = true`.
- Spawn telemetry and reports no longer treat zero public JSONL `spawn_agent` items as proof that no child was spawned.
- The installation guide no longer directs extended provider coverage through the stack-owned acceptance wrapper.
- Exact write-scope checks now include unstaged, staged, and untracked paths and fully clean disposable sandboxes between cases.
- Installer and acceptance checks now parse TOML and reject preserved configurations that disable required Multi-Agent V2 custom-role delegation, including code-mode delegation.

### Removed
- The temporary acceptance normalization gate that downgraded provider failures after the fact; release/provider scope is now separated before execution.

## [0.0.1] - 2026-09-07

### Added
- Initial GitHub repository, MIT license and Python `.gitignore`.
- Research-first repository architecture.
- Initial source repository comparison matrix.
- Provider-neutral model profile and routing policy drafts.
- Delegation, context, escalation and verification policies.
- Core agent contract schema and result contract schema.
- Repository structure validator and CI workflow.
