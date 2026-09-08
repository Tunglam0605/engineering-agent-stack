# agentskills/agentskills

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

Portable procedural knowledge needs a discoverable file contract. A skill directory requires `SKILL.md` with YAML `name` and `description`; scripts, references, and assets are optional. The specification recommends staged loading, roughly 100 tokens of metadata, under 5,000 tokens of instructions, and a body under 500 lines. These are recommendations, distinct from required field constraints. `allowed-tools` is experimental. [Specification][S1]

## Decisions and limitations

- **ADAPT** the format and progressive disclosure for EAS portability; do not turn metadata into permission grants.
- **ADOPT** explicit required fields and relative resource references.
- **REJECT** automatic execution of a bundled script merely because a skill is compatible. Format compatibility is weaker than a trusted execution contract.

EAS inference: discovery should validate metadata before exposing it and explain unavailable capabilities. This audit does not certify any adapter as Agent Skills compatible.

## Local impact

[Architecture synthesis](../architecture-synthesis.md), especially disclosure and declarative packaging; future skill validation and adapter rendering, with no implementation here.

## Source record

- Repository: https://github.com/agentskills/agentskills; inspected revision `69ef37e9424c0a7ea9dd2293b559e43ec8176379`.
- S1: `docs/specification.mdx` - [requested branch URL](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx); [inspected snapshot][S1].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- agentskills/agentskills: root [Apache-2.0 license](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/LICENSE) inspected; nested or third-party material still needs its own check.

[S1]: https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx
