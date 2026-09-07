# Changelog

All notable project changes will be documented here.

## [Unreleased]

### Added
- Research Wave 2 analysis covering OpenAI Agents SDK, Microsoft Agent Framework, AutoGen, LangGraph, Deep Agents, CrewAI, smolagents and OpenHands.
- Authoritative `openai/codex` implementation/public-contract research note.
- Current official Codex subagent and OpenAI model-palette source notes.
- Research Wave 2 synthesis and over-orchestration anti-pattern guidance.
- Seven provider-neutral core role definitions.
- Semantic core-agent and role/profile compatibility validator.
- Executable deterministic routing-policy evaluator with critical-risk precedence cases.
- Deterministic Codex adapter generator with `--check` drift mode.
- Codex role-to-semantic-profile mapping separate from canonical roles.
- `benchmark-result-v1` contract for repeatable token/latency/quality records.
- Machine-readable benchmark experiment plan with role-specific quality rubrics.
- Point-in-time OpenAI pricing snapshot used only as a normalized cost proxy.
- Benchmark plan/fixture validator and quality-gated aggregate report.
- Synthetic benchmark fixture that is explicitly ineligible for model-default decisions.
- Two-stage screening/confirmation benchmarking protocol.

### Changed
- Repository comparison matrix expanded to fifteen sources.
- `config/model-profiles.yaml` uses the explicit `gpt-5.6-sol` model ID for the critical candidate while retaining Astra as benchmark-only.
- Codex adapter follows current public standalone custom-agent discovery rather than internal/undocumented role-registration mechanisms.
- Scout and researcher keep the Luna cost tier but default to medium reasoning in the Codex adapter as a quality floor.
- Routing fixtures contain explicit classified signals; policy routing and natural-language classifier evaluation are separated.
- Critical risk is gated before ordinary task-shape routing; independent critical review stays with Reviewer at the critical profile.
- CI validates structure, canonical agent semantics, routing behavior, generated-adapter drift, benchmark contracts, and benchmark-report execution.
- Roadmap advances into v0.2 real measurement campaigns while keeping specialist creation benchmark-gated.

## [0.0.1] - 2026-09-07

### Added
- Initial GitHub repository, MIT license and Python `.gitignore`.
- Research-first repository architecture.
- Initial source repository comparison matrix.
- Provider-neutral model profile and routing policy drafts.
- Delegation, context, escalation and verification policies.
- Core agent contract schema and result contract schema.
- Repository structure validator and CI workflow.
