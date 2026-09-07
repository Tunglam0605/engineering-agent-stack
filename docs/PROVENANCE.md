# Provenance and Third-Party Attribution Policy

Engineering Agent Stack is research-driven. Provenance is part of correctness: if an upstream project influenced a local design, readers should be able to trace that influence without guessing.

## Provenance classes

### Conceptual reference

An upstream project is studied for architecture, workflow, policy, evaluation, or operational lessons. Local implementation is independently written and the source is cited in research notes and acknowledgements.

Required record:

- upstream repository/documentation URL
- problem/pattern studied
- local `ADOPT` / `ADAPT` / `EXPERIMENT` / `REJECT` decision
- affected local design artifact when applicable

### Adapted material

Text, prompt language, configuration structure, algorithmic structure, or code is materially transformed from an upstream artifact rather than merely inspired by the idea.

Required record before merge:

- upstream repository and exact file/document
- upstream commit/tag/version when practical
- upstream license
- local destination path
- summary of modifications
- any attribution or notice required by the upstream license

### Vendored material

An upstream file or substantial portion is copied into this repository with limited modification.

Required record before merge:

- all fields required for adapted material
- preserved copyright/license notice when required
- explicit reason vendoring is preferable to a dependency/reference
- update/removal strategy

Vendoring prompts, agent catalogs, source trees, or configuration packs is **not** the default for this project.

### Generated material

Provider-specific files generated from canonical local definitions must identify their local source-of-truth and generator. They should not be treated as independent authored sources.

Current example:

```text
agents/core/*.yaml
config/model-profiles.yaml
adapters/codex/role-profiles.yaml
        |
        v
scripts/generate_codex_adapter.py
        |
        v
adapters/codex/agents/*.toml
```

## Current repository posture

The upstream repositories listed in [`ACKNOWLEDGEMENTS.md`](../ACKNOWLEDGEMENTS.md) are currently treated as conceptual research inputs unless a local file explicitly records otherwise. The project does not intentionally vendor upstream source trees or wholesale agent prompt collections.

If a future audit identifies material that should be classified as adapted or vendored, add the required provenance record and license notice before the next release rather than relying on this general statement.

## Contribution rule

Do not copy third-party code, prompts, documentation, configuration, or generated artifacts into this repository without checking its license and recording provenance first.

A contribution that directly reuses third-party material should include a provenance block in the relevant research note or a dedicated notice with:

```text
upstream_repository:
upstream_revision:
upstream_path:
upstream_license:
local_path:
reuse_class: adapted | vendored
modifications:
notice_requirements:
```

## Research citation rule

Conceptual influence still deserves credit even when copyright attribution is not legally required. Add every studied repository to the research matrix and acknowledgements so that design lineage remains visible.

## No endorsement

References to OpenAI, Microsoft, AWS, LangChain, CrewAI, Hugging Face, OpenHands, or other upstream projects are descriptive. This repository is independent and does not imply endorsement, sponsorship, or affiliation.
