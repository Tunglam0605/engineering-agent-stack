# zephyrproject-rtos/west + zephyrproject-rtos/zephyr

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

West describes a multi-repository workspace with typed manifest fields, revisions, imports, and groups. Its optional `version` means the minimum manifest schema required; several nested values use permissive types, so schema shape alone cannot prove resolved import validity. Zephyr's workspace manifest records concrete dependency revisions and group filters. [West schema][S1] [Zephyr manifest][S3]

Zephyr describes its coding guidelines as a subset based on MISRA-C 2012, with external-standard references. This audit studies that relationship, not proprietary rule text. [Coding guidelines][S2]

## Decisions and limitations

- **ADOPT** explicit version compatibility and validation before use.
- **ADAPT** revision/group evidence for an embedded dependency inventory.
- **REJECT** recursive imports/groups as an initial EAS package solver and any implied MISRA certification.

EAS inference: candidate checks should identify the project's selected standard, toolchain, target, diagnostics, and justified exceptions. Actual commands and acceptance limits require a target repository. Do not copy the rule table or transcribe proprietary MISRA material.

## Local impact

[Architecture synthesis](../architecture-synthesis.md): version semantics; [domain gates](../domain-gates.md): embedded candidates. No west execution or firmware build was performed.

## Source record

- Repository: https://github.com/zephyrproject-rtos/west; inspected revision `df990f0e0893d64e0600cbd2965ae45e39990f86`.
- S1: `src/west/manifest-schema.yml` - [requested branch URL](https://github.com/zephyrproject-rtos/west/blob/main/src/west/manifest-schema.yml); [inspected snapshot][S1].
- Repository: https://github.com/zephyrproject-rtos/zephyr; inspected revision `bc2caf20dd0c7ca6c95c0dae66fd1ccb0e7e6147`.
- S2: `doc/contribute/coding_guidelines/index.rst` - [requested branch URL](https://github.com/zephyrproject-rtos/zephyr/blob/main/doc/contribute/coding_guidelines/index.rst); [inspected snapshot][S2].
- S3: `west.yml` - [requested branch URL](https://github.com/zephyrproject-rtos/zephyr/blob/main/west.yml); [inspected snapshot][S3].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- zephyrproject-rtos/west: root [Apache-2.0 license](https://github.com/zephyrproject-rtos/west/blob/df990f0e0893d64e0600cbd2965ae45e39990f86/LICENSE) inspected; nested or third-party material still needs its own check.
- zephyrproject-rtos/zephyr: root [Apache-2.0 license](https://github.com/zephyrproject-rtos/zephyr/blob/bc2caf20dd0c7ca6c95c0dae66fd1ccb0e7e6147/LICENSE) inspected; nested or third-party material still needs its own check.
- Zephyr licensing does not authorize copying the proprietary MISRA standard; no proprietary text is reproduced.

[S1]: https://github.com/zephyrproject-rtos/west/blob/df990f0e0893d64e0600cbd2965ae45e39990f86/src/west/manifest-schema.yml

[S2]: https://github.com/zephyrproject-rtos/zephyr/blob/bc2caf20dd0c7ca6c95c0dae66fd1ccb0e7e6147/doc/contribute/coding_guidelines/index.rst

[S3]: https://github.com/zephyrproject-rtos/zephyr/blob/bc2caf20dd0c7ca6c95c0dae66fd1ccb0e7e6147/west.yml
