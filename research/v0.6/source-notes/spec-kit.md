# github/spec-kit

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

Spec Kit customizes workflows without a core fork. Preset resolution places project overrides above presets, extensions, and core; presets may recursively replace, prepend, append, or wrap content. Catalog priority and install trust are separate concepts. Extension manifests declare schema/package versions, compatibility, identity, and provided content; configuration has defaults, project, local, and environment layers. [Architecture][S1] [Presets][S2] [API][S3] [Extensions][S4]

The hook API describes priority sorting, while command-template behavior is documented as using configured order and skipping non-empty conditions. A documented hook does not establish uniform enforcement. [API][S3] [Extensions][S4]

## Decisions and limitations

- **ADOPT** manifest versioning, compatibility checks, and explainable precedence.
- **ADAPT** project/local separation, catalogs as discovery rather than trust, and curated presets.
- **REJECT** recursive content composition, broad environment overrides, and arbitrary hooks for initial EAS.

EAS inference: explicit effect classification is recommended for EAS, not claimed as an existing Spec Kit manifest field. The inspected pages establish composition conflict risks; they do not establish a complete preset dependency solver. Dependency/conflict graph complexity is a risk to avoid, not a capability to assume or copy.

## Local impact

[Architecture synthesis](../architecture-synthesis.md): manifest concepts, precedence, and intentionally limited composition.

## Source record

- Repository: https://github.com/github/spec-kit; inspected revision `4a7341a93d944d6efe153b71da4a1adb9c2b578c`.
- S1: `presets/ARCHITECTURE.md` - [requested branch URL](https://github.com/github/spec-kit/blob/main/presets/ARCHITECTURE.md); [inspected snapshot][S1].
- S2: `presets/README.md` - [requested branch URL](https://github.com/github/spec-kit/blob/main/presets/README.md); [inspected snapshot][S2].
- S3: `extensions/EXTENSION-API-REFERENCE.md` - [requested branch URL](https://github.com/github/spec-kit/blob/main/extensions/EXTENSION-API-REFERENCE.md); [inspected snapshot][S3].
- S4: `docs/reference/extensions.md` - [requested branch URL](https://github.com/github/spec-kit/blob/main/docs/reference/extensions.md); [inspected snapshot][S4].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- github/spec-kit: root [MIT license](https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/LICENSE) inspected; nested or third-party material still needs its own check.

[S1]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/presets/ARCHITECTURE.md

[S2]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/presets/README.md

[S3]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/extensions/EXTENSION-API-REFERENCE.md

[S4]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/docs/reference/extensions.md
