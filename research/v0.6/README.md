# v0.6 Research & Architecture Audit

Status: **research closed; architecture frozen; v0.6.0 implementation validated and release-ready pending repository release gates**. The normative contract is [`contract-freeze.md`](contract-freeze.md).

## Scope

This directory preserves the research and architecture evidence that preceded implementation. The shipped v0.6 runtime lives under `runtime/capabilities/`, `eas_cli/`, and `schemas/`; this research package remains evidence/provenance material rather than execution authority. The seven core roles remain scout, researcher, implementer, debugger, test-engineer, reviewer, architect.

## Method and evidence status

1. Inspect [research conventions](../README.md), the [canonical matrix](../matrix/repository-comparison.yaml), [provenance policy](../../docs/PROVENANCE.md), existing repository notes, [architecture](../../docs/ARCHITECTURE.md), [quality policy](../../policies/quality-gates.md), release workflow, and validators before editing.
2. Resolve each requested upstream branch to a commit; retrieve named files at that revision and inspect relevant sections. Notes retain requested branch URLs and immutable snapshot URLs. MCP coverage is specifically the requested 2025-11-25 specification.
3. Separate **evidence** (what inspected documentation/schema says) from **EAS inference** (proposed local choice). Compare conflicting guidance explicitly. This is a targeted documentation/schema audit, not a code audit of every upstream runtime or a test of its behavior.
4. Classify conceptual influence and record license concerns. Temporary upstream retrievals stay outside the worktree; no third-party source trees or material are copied into this package.
5. Validate local structure/provenance and inspect the diff. Existing validators do not prove source-claim accuracy or validate the proposed v0.6 design; citation and scope review are separate.

## Artifacts

- [Research checkpoint](research-checkpoint.md): architecture decisions ready for implementation planning.
- [Repository comparison](repository-comparison.md): decisions, reasons, risks, and affected local artifacts.
- [Architecture synthesis](architecture-synthesis.md): taxonomy, disclosure, precedence, enforcement, security boundaries, and open decisions.
- [Domain gates](domain-gates.md): candidates for `embedded`, `ros2`, and `release`; none is activated.
- [Extension-system deep audit](extension-systems/README.md): loader/config/enforcement findings from runtime/source inspection.
- [Domain Skills / Rules / Config deep audit](domain-rules/README.md): embedded/ROS2/release/security candidates and source index.
- [EAS v0.5 gap analysis](eas-gap-analysis/README.md): insertion points, candidate contracts, resolution/enforcement and validation plan.
- Source notes below: one per research topic/repository, with west and Zephyr grouped as related evidence.

## Source set

All 11 requested source groups (12 repositories, 30 document files) were retrieved successfully. The notes account for requested documents and supporting MCP/README files; license files were checked separately.

| Topic | Source note | Main audit question |
|---|---|---|
| Agent Skills | [agent-skills](source-notes/agent-skills.md) | Portable directory and metadata contract |
| Anthropic skills | [anthropic-skills](source-notes/anthropic-skills.md) | Disclosure, variants, evaluation, mixed licensing |
| oh-my-pi | [oh-my-pi](source-notes/oh-my-pi.md) | Discovery versus executable extension loading |
| Superpowers | [superpowers](source-notes/superpowers.md) | Skill admission and pressure testing |
| oh-my-codex | [oh-my-codex](source-notes/oh-my-codex.md) | Canonical rules, workflow scopes, runtime boundaries |
| GitHub Spec Kit | [spec-kit](source-notes/spec-kit.md) | Manifests, composition, catalogs, precedence |
| OpenAI Agents SDK | [openai-agents-sdk](source-notes/openai-agents-sdk.md) | Check boundaries and trace structure |
| MCP | [mcp](source-notes/mcp.md) | Control owners, negotiation, consent |
| Zephyr / west | [zephyr-west](source-notes/zephyr-west.md) | Standards-based quality and dependency manifests |
| ROS2 REP-2004 | [ros2-rep-2004](source-notes/ros2-rep-2004.md) | Justified quality declarations |
| Ruff | [ruff](source-notes/ruff.md) | Deterministic configuration selection |

## Provenance and completion boundary

Reuse class: **Conceptual reference** throughout. `ADAPT` denotes adapting an idea, not directly adapted material. New sources are registered in the existing canonical matrix and [acknowledgements](../../ACKNOWLEDGEMENTS.md), as required by provenance policy. Inclusion implies no dependency, endorsement, license clearance for future reuse, or benchmark superiority.

This package can be reviewed independently of implementation. No runtime demonstrations, skill pressure experiments, embedded builds, ROS2 package qualification, or release execution were performed. Future work must resolve the listed gaps before claiming those capabilities.

## Local validation record

Run on 2026-09-08 in the Windows research worktree:

| Command | Result |
|---|---|
| `python scripts/validate_structure.py` | PASS: 164 required artifacts; seven-role structure and v0.6 capability artifacts present. |
| `python scripts/validate_provenance.py` | PASS: 25 canonical research sources acknowledged. |
| `python scripts/validate_agents.py` | PASS: seven contracts and compatible routing/provider mappings. |
| `python scripts/evaluate_routing.py` | PASS: 10 deterministic cases. |
| `python scripts/validate_task_suite.py` | PASS: five controlled tasks. |
| `python scripts/validate_benchmarks.py` | PASS: five planned experiments and five tasks. |
| `python scripts/generate_codex_adapter.py --check` | PASS: eight generated artifacts in sync. |
| `git diff --check` | PASS: no whitespace errors. |
| `py -3.9 -m unittest discover -s tests -v` | PASS: 139 tests, 2 platform skips. |
| clean wheel build + isolated Python 3.9 install | PASS: v0.6.0 wheel contains all three built-in capability packs and runs `eas preset list/show` outside the source tree. |

These results validate the implemented v0.6 contract and packaging boundary. They do not certify any external embedded/ROS2 project or claim provider-native interception.

## Architecture freeze

The v0.6 implementation MUST follow [`contract-freeze.md`](contract-freeze.md): exactly seven core roles, declarative-only extensions, five public contract kinds, one active preset, deterministic precedence, read-only detection, lazy bounded skill loading, trusted checker IDs, and explicit capability-snapshot migration. Runtime implementation does not reopen the research scope unless validation exposes a material contradiction.
