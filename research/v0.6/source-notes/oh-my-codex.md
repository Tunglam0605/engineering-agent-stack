# Yeachan-Heo/oh-my-codex

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

The guidance template coordinates role and workflow surfaces. The team card points to canonical durable invariants instead of duplicating them, requires the appropriate tmux/runtime environment, and forbids nested Team runs. The skill card distinguishes user and project roots; analyze calls for read-only evidence, confidence, and explicit inference. The template lists multiple specialized roles and workflow modes. [Template][S1] [Team][S2] [Skill][S3] [Analyze][S4]

## Decisions and limitations

- **ADOPT** one canonical rule source and truthful runtime availability boundaries.
- **ADAPT** scoped workflow surfaces and evidence/confidence reporting.
- **REJECT** importing the broad role/skill catalog into the seven-role EAS core.

A real disagreement: the skill card allows codebase-specific workflows, while Superpowers excludes project conventions ([comparison](../repository-comparison.md)). EAS inference: a reusable procedure may have project parameters, but a repository-only requirement belongs in rules/config. Runtime coordination remains an execution policy, not a new role identity.

## Local impact

[Architecture synthesis](../architecture-synthesis.md): taxonomy, canonical policy ownership, and read-only detection. No Team runtime adoption.

## Source record

- Repository: https://github.com/Yeachan-Heo/oh-my-codex; inspected revision `304fb3b4825c4132c273732b14d2d5e86b54f8e3`.
- S1: `templates/AGENTS.md` - [requested branch URL](https://github.com/Yeachan-Heo/oh-my-codex/blob/main/templates/AGENTS.md); [inspected snapshot][S1].
- S2: `skills/team/SKILL.md` - [requested branch URL](https://github.com/Yeachan-Heo/oh-my-codex/blob/main/skills/team/SKILL.md); [inspected snapshot][S2].
- S3: `skills/skill/SKILL.md` - [requested branch URL](https://github.com/Yeachan-Heo/oh-my-codex/blob/main/skills/skill/SKILL.md); [inspected snapshot][S3].
- S4: `skills/analyze/SKILL.md` - [requested branch URL](https://github.com/Yeachan-Heo/oh-my-codex/blob/main/skills/analyze/SKILL.md); [inspected snapshot][S4].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- Yeachan-Heo/oh-my-codex: root [MIT license](https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/LICENSE) inspected; nested or third-party material still needs its own check.

[S1]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/templates/AGENTS.md

[S2]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/skills/team/SKILL.md

[S3]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/skills/skill/SKILL.md

[S4]: https://github.com/Yeachan-Heo/oh-my-codex/blob/304fb3b4825c4132c273732b14d2d5e86b54f8e3/skills/analyze/SKILL.md
