# can1357/oh-my-pi

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

The runtime integrates discoverable capabilities. Skills expose small metadata and on-demand `skill://` content. Provider/custom-directory scanning is one level below a skills root. Provider priority, custom-directory overrides, and authored-over-managed resolution affect collisions; these are different resolution passes. [Skills][S1]

Extension packages can bundle skills, hooks, tools, commands, rules, prompts, and `.mcp.json`. Their factories register executable behavior. Module discovery/import is a separate subsystem; disabling it is not a universal capability-isolation switch. The SDK embeds session/tool/event control in a Bun process. [Authoring][S2] [Runtime][S3] [Loading][S4] [SDK][S5]

## Decisions and limitations

- **ADAPT** one-level discovery, staged loading, package composition, and visible source provenance.
- **ADOPT** explicit collision handling as a requirement, without copying provider priority numbers.
- **REJECT** full runtime/plugin execution, automatic hook/module loading, and a second provider tool runtime in v0.6.

EAS inference: a capability package is not an agent. Provider discovery belongs in adapters; package metadata cannot grant tool authority. Separate discovery, selection, validation, and execution so disabling one is never advertised as disabling all.

## Local impact

[Architecture synthesis](../architecture-synthesis.md): extension boundary, discovery, and compatibility. Existing core roles and provider mappings remain unchanged.

## Source record

- Repository: https://github.com/can1357/oh-my-pi; inspected revision `daf07999c2fee9b22edc7bf8fea1fb6272e0df5e`.
- S1: `docs/skills.md` - [requested branch URL](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md); [inspected snapshot][S1].
- S2: `docs/skills/authoring-extensions.md` - [requested branch URL](https://github.com/can1357/oh-my-pi/blob/main/docs/skills/authoring-extensions.md); [inspected snapshot][S2].
- S3: `docs/extensions.md` - [requested branch URL](https://github.com/can1357/oh-my-pi/blob/main/docs/extensions.md); [inspected snapshot][S3].
- S4: `docs/extension-loading.md` - [requested branch URL](https://github.com/can1357/oh-my-pi/blob/main/docs/extension-loading.md); [inspected snapshot][S4].
- S5: `docs/sdk.md` - [requested branch URL](https://github.com/can1357/oh-my-pi/blob/main/docs/sdk.md); [inspected snapshot][S5].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- can1357/oh-my-pi: root [MIT license](https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/LICENSE) inspected; nested or third-party material still needs its own check.

[S1]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/skills.md

[S2]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/skills/authoring-extensions.md

[S3]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/extensions.md

[S4]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/extension-loading.md

[S5]: https://github.com/can1357/oh-my-pi/blob/daf07999c2fee9b22edc7bf8fea1fb6272e0df5e/docs/sdk.md
