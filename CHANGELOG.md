# Changelog

All notable project changes will be documented here.

## [Unreleased]

No unreleased changes.

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
