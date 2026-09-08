# astral-sh/ruff

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

Ruff makes configuration selection predictable: each file uses its closest applicable configuration; parent configurations are not implicitly merged. `extend` requests inheritance explicitly, and supported command-line options override resolved configuration. There are documented exceptions, including explicit-config path behavior and a user-config fallback. [Configuration][S1]

## Decisions and limitations

- **ADOPT** deterministic selection and explicit override explanations.
- **ADAPT** the anti-cascade principle to EAS's declared layers.
- **REJECT** a hidden ancestor/environment cascade or conflating file discovery with config merging.

EAS inference: EAS should select one project root and apply a fixed layer order; this is not Ruff's per-file algorithm. Keep each value's source, reject invalid values, and avoid silently concatenating lists. Cross-project inheritance is unnecessary initially; if later justified, make references explicit and cycle-checked.

## Local impact

[Architecture synthesis](../architecture-synthesis.md): parameter precedence and resolution diagnostics. No config resolver is implemented by this audit.

## Source record

- Repository: https://github.com/astral-sh/ruff; inspected revision `e7adf82ff005f3ab3051c363464cf65bf8a6e2f3`.
- S1: `docs/configuration.md` - [requested branch URL](https://github.com/astral-sh/ruff/blob/main/docs/configuration.md); [inspected snapshot][S1].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- astral-sh/ruff: root [MIT license](https://github.com/astral-sh/ruff/blob/e7adf82ff005f3ab3051c363464cf65bf8a6e2f3/LICENSE) inspected; nested or third-party material still needs its own check.

[S1]: https://github.com/astral-sh/ruff/blob/e7adf82ff005f3ab3051c363464cf65bf8a6e2f3/docs/configuration.md
