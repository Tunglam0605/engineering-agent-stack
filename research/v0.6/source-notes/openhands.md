# OpenHands extensions, registry, and runtime research (v0.6)

## Pinned provenance

- `OpenHands/extensions` `main`: `39fc25a91749fe248db391315c2c4eb2c74655a6` (resolved 2026-09-08): https://github.com/OpenHands/extensions/tree/39fc25a91749fe248db391315c2c4eb2c74655a6
- `OpenHands/OpenHands` `main`: `f7fb0c4b21f5ed726edbba8a6309634ef434b004` (resolved 2026-09-08): https://github.com/OpenHands/OpenHands/tree/f7fb0c4b21f5ed726edbba8a6309634ef434b004

## Findings

The registry contract is documented in `OpenHands/extensions/AGENTS.md`: `skills/<id>/SKILL.md` is one skill per stable directory, with optional `README.md` and `references/`; `plugins/<id>/SKILL.md` may also contain executable `hooks/` and `scripts/`. Marketplace declarations live in `marketplaces/openhands-extensions.json`; generated indexes are maintained by `scripts/sync_extensions.py`. These are registry facts, not proof of execution isolation.

Runtime evidence is separate. The pinned `OpenHands/OpenHands` tree contains browser-level skill coverage at `tests/e2e/mock-llm/skills/mock-llm-skills.spec.ts` and helpers at `tests/e2e/mock-llm/utils/skill-test-helpers.ts`; orchestration and sandbox ownership are explicitly assigned by the extensions contract to the SDK/application/automation repositories, not this registry. No pinned OpenHands path inspected here establishes a plugin sandbox or permission enforcement contract. Therefore registry metadata must not be treated as runtime isolation evidence.

## Decisions for EAS v0.6

- **ADOPT:** directory-per-skill `SKILL.md`, stable identifiers, progressive disclosure, optional references, and catalog metadata separated from runtime behavior.
- **ADAPT:** use keyword/triggers and marketplace categories only as advisory, provider-neutral routing metadata; retain canonical-source and generated-artifact traceability.
- **REJECT:** executable plugins, hooks, scripts, credential-dependent actions, and plugin loading as an EAS v0.6 extension mechanism. They require separately pinned SDK/runtime loader code, sandbox and permission tests, and a security review. EAS v0.6 remains declarative Markdown/configuration only.

## Source paths

- Registry rules: `OpenHands/extensions/AGENTS.md`, `skills/`, `plugins/`, `marketplaces/openhands-extensions.json`, `scripts/sync_extensions.py`.
- Runtime-adjacent tests inspected: `OpenHands/tests/e2e/mock-llm/skills/mock-llm-skills.spec.ts`, `OpenHands/tests/e2e/mock-llm/utils/skill-test-helpers.ts`.
- Docs: https://docs.openhands.dev/overview/skills and https://docs.openhands.dev/sdk/guides/skill
