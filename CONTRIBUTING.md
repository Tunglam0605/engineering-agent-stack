# Contributing

Engineering Agent Stack is research-driven. Contributions should improve measurable quality, efficiency, safety, or maintainability.

## Preferred contribution types

- structured analysis of an agent/orchestration repository
- reproducible benchmark cases
- improvements to role/result schemas
- routing and escalation experiments
- provider adapters that preserve provider-neutral contracts
- specialist roles justified by repeated use cases

## Avoid

- large prompt dumps without rationale
- unbounded agent catalogs
- hard-coding a role to one model without a policy reason
- claims such as "best", "production-ready", or "cheapest" without evidence
- introducing runtime dependencies when a standard-library solution is sufficient

## Pull request checklist

- [ ] Scope is narrow and reviewable.
- [ ] Research sources are linked where relevant.
- [ ] Role/model/policy separation is preserved.
- [ ] `python scripts/validate_structure.py` passes.
- [ ] New behavior includes an evaluation plan or evidence.
- [ ] Risks and trade-offs are documented.
