# EAS v0.6 extension/preset gap analysis

Research date: 2026-09-08. Status: **candidate design, research/synthesis only**.

Inspected baseline: `v0.5.0`, commit `779ea5ac076bad39016fd248aac3ca6b2f65ed6d`; package version `0.5.0`. Runtime, schema, policy, CLI, adapter, test and packaging findings refer to this checkout, not to a live provider or an implemented v0.6 feature.

The recommended insertion is a provider-neutral, declarative composition layer that produces a validated configuration snapshot before stack-controlled decisions. Keep exactly seven canonical roles: scout, researcher, implementer, debugger, test-engineer, reviewer and architect. Packages specialize their context and evidence requirements; they do not introduce role identities, execution engines, model mappings or authority.

## Reading order

1. [Gap analysis and exact insertion points](gap-analysis.md): current behavior, limitations, affected symbols and decisions.
2. [Five candidate contracts](candidate-contracts.md): extension-manifest, skill, rule, preset and project-profile.
3. [Resolution and enforcement](resolution-and-enforcement.md): deterministic discovery, precedence, compatibility, protected fields and recovery binding.
4. [Validation and provenance](validation-and-provenance.md): existing evidence, proposed acceptance cases, source lineage and remaining decisions.

All serialized shapes, new paths and CLI surfaces discussed here are proposals. Markdown examples are illustrative data contracts, not files to install or schemas consumed by v0.5.0. No runtime, generator, package, policy or test code is implemented by this study.

## Scope and provenance

This study inspects EAS itself and uses the existing local [v0.6 architecture synthesis](../architecture-synthesis.md) and [domain-gate candidates](../domain-gates.md) as prior research. Those working-tree documents are proposals, not release behavior. Their upstream source assessments are not independently reverified here. No new third-party source, copied prompt, vendored material or current provider claim is introduced. See the [provenance record](validation-and-provenance.md#provenance-record).

Existing changes in `ACKNOWLEDGEMENTS.md`, `docs/ROADMAP.md`, `research/README.md`, `research/matrix/repository-comparison.yaml` and existing `research/v0.6/` material predated this work. They are outside its write scope.

## Key decisions

| Decision | Recommendation |
| --- | --- |
| Package model | Declarative local content; no imports, hooks, commands, dependency installation or native tool registration. |
| Composition | One selected preset; explicit package-qualified references and field-specific merge rules. |
| Enforcement | Mandatory stack constraints surround composition; prose and manifests never grant permissions. |
| Reproducibility | Resolve exact package versions/content hashes, keep per-value lineage, bind decisions to the resolved snapshot. |
| Recovery | Retain v0.5 approval, revision, lock and receipt semantics; no implicit re-resolution of running work. |
| Distribution | Preserve seven canonical generated role files; project-specific material needs separate ownership and drift records. |

These are candidate contracts for review, not approval to ship v0.6. The existing checks validate the v0.5 working tree; they do not validate an extension implementation. Results and limitations are recorded in the validation document.
