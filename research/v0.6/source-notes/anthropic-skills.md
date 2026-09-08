# anthropics/skills

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

The collection demonstrates task-specific skills; its README distinguishes open-source examples from source-available document skills. The creator describes always-visible metadata, a body loaded on triggering, and resources loaded as needed; framework variants belong in focused references. It recommends a body below 500 lines, paired baseline/skill evaluations, and trigger-positive and near-miss queries. [Collection][S1] [Creator][S2]

## Decisions and limitations

- **ADAPT** disclosure and variant references, keeping common procedure in one small body.
- **ADOPT** evaluation against a baseline and testing false triggers.
- **REJECT** importing the catalog or treating all repository content as uniformly licensed.

EAS inference: retain clear task triggers without the creator's broad, deliberately aggressive triggering style. Do not equate its approximate metadata word budget with the Agent Skills token recommendation. Demonstration guidance is not measured EAS performance.

## Local impact

[Architecture synthesis](../architecture-synthesis.md): authoring quality, metadata budget, and script boundary. Future skills need their own evaluations.

## Source record

- Repository: https://github.com/anthropics/skills; inspected revision `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f`.
- S1: `README.md` - [requested branch URL](https://github.com/anthropics/skills/blob/main/README.md); [inspected snapshot][S1].
- S2: `skills/skill-creator/SKILL.md` - [requested branch URL](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md); [inspected snapshot][S2].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- The inspected creator has an [Apache-2.0 license](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/skill-creator/LICENSE.txt); the [README][S1] identifies mixed licensing elsewhere. Do not assume repository-wide permission.

[S1]: https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/README.md

[S2]: https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/skill-creator/SKILL.md
