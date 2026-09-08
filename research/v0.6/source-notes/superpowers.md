# obra/superpowers

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

The authoring guide treats skills as reusable techniques, patterns, tools, or references. It excludes one-off narratives, project conventions, and constraints better automated. It uses baseline failure, skill-enabled success, and loophole-closing pressure tests. It reports workflow-summary metadata causing agents to shortcut body instructions; that observation is not an EAS benchmark. Its word-count targets are under 150 for startup workflows, 200 for frequent skills, and 500 for others. [Writing skills][S1]

## Decisions and limitations

- **ADAPT** RED/GREEN/refactor pressure testing to an EAS evidence contract, including negative triggers.
- **ADOPT** separating project rules and mechanical validation from reusable judgment.
- **REJECT** workflow summaries in trigger metadata and treating upstream word targets as proven universal optima.

EAS inference: a failed baseline must expose the intended weakness, not an unrelated tool failure. Keep necessary correctness evidence even when it exceeds a size target. No pressure tests were run in this research phase because no skills were created.

## Local impact

[Architecture synthesis](../architecture-synthesis.md): skill admission and evaluation requirements; future evaluation fixtures, not changes to core roles.

## Source record

- Repository: https://github.com/obra/superpowers; inspected revision `b36e0829c6d0140e93cfef2ca599b1b07d4a7797`.
- S1: `skills/writing-skills/SKILL.md` - [requested branch URL](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md); [inspected snapshot][S1].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- obra/superpowers: root [MIT license](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/LICENSE) inspected; nested or third-party material still needs its own check.

[S1]: https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-skills/SKILL.md
