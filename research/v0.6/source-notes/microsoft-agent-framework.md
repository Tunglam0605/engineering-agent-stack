# microsoft/agent-framework

Reviewed: 2026-09-08. Upstream `main` pinned to `8fcb052bffb2b61836ed1b0aa15fd83eb3e97311` (resolved with `git ls-remote`; shallow clone inspected). No upstream code or prompts copied.

## Evidence inspected

- Declarative agent/workflow examples and schemas: `declarative-agents/agent-samples/**/*.yaml`, `declarative-agents/workflow-samples/*.yaml`; implementation and parsing in `python/packages/declarative/agent_framework_declarative/` with package metadata in `python/packages/declarative/pyproject.toml`.
- Workflow graph, state and checkpoint behavior: `python/packages/core/agent_framework/` (workflow abstractions), `python/packages/declarative/agent_framework_declarative/_workflows/_state.py`, `_factory.py`, and tests `python/packages/declarative/tests/test_workflow_state.py`, `test_workflow_factory.py`, `test_graph_workflow_integration.py`.
- External input/HITL boundary: `python/packages/declarative/agent_framework_declarative/_workflows/_executors_external_input.py`; workflow integration coverage in `python/packages/declarative/tests/workflows/`.
- Middleware and skills: middleware decisions and contracts in `docs/decisions/0007-agent-filtering-middleware.md` and `0016-python-context-middleware.md`; skill design and MCP references in `docs/decisions/0037-agent-skills-design.md` and `0029-mcp-skill-templates-and-direct-references.md`; concrete skills under `python/scripts/sample_validation/skills/*/SKILL.md`.
- Package/release metadata: root `python/pyproject.toml`, plus package `pyproject.toml` files; .NET projects under `dotnet/src/` and tests under `dotnet/tests/`.
- Security/execution boundary: `SECURITY.md`; declarative executors `_executors_http.py`, `_executors_mcp.py`, `_executors_tools.py` show that YAML declarations dispatch to runtime handlers, so declarations are not authority by themselves.

## EAS classification

- **ADOPT** separating declarative capability descriptions from runtime execution. Keep provider-neutral manifests under EAS declarative artifacts; adapters instantiate providers.
- **ADAPT** typed workflow graphs, explicit state/checkpoint objects, external-input approval pauses, and ordered middleware. EAS must bind pause/resume to authenticated run identity, authorization context, replay-safe effects, and bounded tokens.
- **ADAPT** skill metadata and MCP templates for discovery/provenance, with schema validation and capability/resource limits enforced by the runtime.
- **REJECT** treating YAML/skill content as execution authority, embedding provider/model names into role identity, or adopting framework-specific APIs as EAS contracts.

## Risks and limitations

Checkpoint replay may repeat side effects; tools need idempotency or effect journaling. HTTP/MCP/tool executors expand the attack surface and require allowlists, credentials isolation and resource limits. Tests demonstrate intended behavior, not production security. APIs and schemas can change as `main` evolves.

## Local impact

Informs `research/v0.6/architecture-synthesis.md` on declarative extensions, workflow state/checkpoints, HITL, middleware and provenance.

## Provenance

Repository: https://github.com/microsoft/agent-framework/tree/8fcb052bffb2b61836ed1b0aa15fd83eb3e97311. License: MIT (`LICENSE`). Findings are paraphrased; no material vendored.
