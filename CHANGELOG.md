# Changelog

All notable project changes will be documented here.

## [Unreleased]

### Added
- Research Wave 2 analysis covering OpenAI Agents SDK, Microsoft Agent Framework, AutoGen, LangGraph, Deep Agents, CrewAI, smolagents and OpenHands.
- Authoritative `openai/codex` implementation/public-contract research note.
- Current official Codex subagent and OpenAI model-palette source notes.
- Research Wave 2 synthesis and over-orchestration anti-pattern guidance.
- Seven provider-neutral core role definitions.
- Semantic core-agent contract validator.
- Executable deterministic routing-policy evaluator.
- Deterministic Codex adapter generator with `--check` drift mode.
- Codex role-to-semantic-profile mapping separate from canonical roles.
- Development dependency manifest for YAML-based validation/generation.
- Normalized benchmark/run-capture contracts and Codex JSONL capture pipeline.
- `controlled-v1` benchmark suite with scout, implementer, reviewer and trivial-orchestration tasks.
- Deterministic text-evidence and command/test task graders.
- Controlled workspace materializer that generates concrete Codex run manifests.
- CI coverage for controlled task validation, preparation and grading.

### Changed
- Repository comparison matrix expanded to fifteen sources.
- `config/model-profiles.yaml` now uses the explicit `gpt-5.6-sol` model ID for the critical candidate while retaining Astra as benchmark-only.
- Codex adapter now follows current public standalone custom-agent discovery rather than internal/undocumented role-registration mechanisms.
- Scout and researcher keep the Luna cost tier but default to medium reasoning in the Codex adapter as a quality floor.
- Routing fixtures now contain explicit classified signals; policy routing and natural-language classifier evaluation are separated.
- Benchmark experiments now reference concrete controlled task IDs.
- CI now validates structure, canonical agent semantics, routing policy behavior, controlled benchmark tasks, benchmark contracts, run capture, grading, and generated-adapter drift.
- Roadmap marks v0.2 controlled-task/capture infrastructure as operational and repeated real runs as the next gate.

## [0.0.1] - 2026-09-07

### Added
- Initial GitHub repository, MIT license and Python `.gitignore`.
- Research-first repository architecture.
- Initial source repository comparison matrix.
- Provider-neutral model profile and routing policy drafts.
- Delegation, context, escalation and verification policies.
- Core agent contract schema and result contract schema.
- Repository structure validator and CI workflow.
