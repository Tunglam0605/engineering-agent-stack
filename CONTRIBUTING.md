# Contributing

Engineering Agent Stack is research-driven. Contributions should improve measurable quality, efficiency, safety, maintainability, or provenance clarity.

## Preferred contribution types

- structured analysis of an agent/orchestration repository
- reproducible benchmark cases
- improvements to role/result schemas
- routing and escalation experiments
- provider adapters that preserve provider-neutral contracts
- specialist roles justified by repeated use cases
- attribution/provenance corrections

## Avoid

- large prompt dumps without rationale
- unbounded agent catalogs
- hard-coding a role to one model without a policy reason
- claims such as "best", "production-ready", or "cheapest" without evidence
- introducing runtime dependencies when a standard-library solution is sufficient
- copying third-party prompts/code/configuration without checking the upstream license and recording provenance

## Third-party research and reuse

Conceptual research should cite the upstream repository in the research matrix/notes and acknowledgements. Direct adaptation or vendoring must follow [`docs/PROVENANCE.md`](docs/PROVENANCE.md) before merge.

Do not assume that a public GitHub repository is permission to copy arbitrary material without preserving its license/notice requirements.

## Pull request checklist

- [ ] Scope is narrow and reviewable.
- [ ] Research sources are linked where relevant.
- [ ] New research sources are added to `ACKNOWLEDGEMENTS.md`.
- [ ] Directly adapted/vendored material records upstream revision, path, license, local path, and modifications.
- [ ] Role/model/policy separation is preserved.
- [ ] `python scripts/validate_structure.py` passes.
- [ ] `python scripts/validate_provenance.py` passes.
- [ ] New behavior includes an evaluation plan or evidence.
- [ ] Risks and trade-offs are documented.
