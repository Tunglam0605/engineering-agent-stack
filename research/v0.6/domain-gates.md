# Candidate domain gates

Status: **candidates only; not implemented, configured, or activated**. Proposed checks are **EAS inference** from cited sources and current policy. `embedded`, `ros2`, and `release` are the only recommended initial presets. Security remains universal; a separate security preset can wait.

## Common candidate contract

A future check needs scope, severity, enforcement class (`guidance`, `validator`, `gate`), controlling boundary, input revision, evidence, and exception/escalation path. A validator is not a gate unless it controls a transition. Missing tooling, stale results, and unsupported targets are **unknown/unverified**, never passing. Human judgment needs recorded rationale. This extends the [existing quality policy](../../policies/quality-gates.md) conceptually without changing it.

Classes/severities below are proposed deployment classifications. None names an installed v0.6 enforcer. A gate candidate blocks only when later wired to a stack-owned boundary; until then it is a review requirement.

## Embedded

Basis: Zephyr relates coding guidance to external standards; west represents workspace dependencies and schema/version requirements. [Guidance][ZG] [Schema][WS] [Manifest][ZM]

| Candidate / scope | Proposed class; severity | Evidence to require | Unknown / exception handling |
|---|---|---|---|
| E1: selected standard and deviations / changed C/C++ | guidance; high for safety-sensitive code | Project-selected standard/version, review, applicable static-analysis configuration, deviation rationale. | No MISRA compliance claim from a preset or clean linter. Review applicability. |
| E2: dependency context / workspace | validator feeding pre-build gate; error | Manifest validation, resolved revisions/imports, active groups, local modifications, tool version. | Parse success is insufficient; unresolved imports or absent evidence blocks the candidate. |
| E3: compile/diagnostics / named firmware target | validator feeding acceptance gate; error | Project build command, board/toolchain/config, revision, exit result and diagnostics. | Host build cannot replace target evidence. Project selects warning policy. |
| E4: target risk / affected subsystem | guidance feeding review gate; high | Requirements and project tests for identified timing, memory, concurrency or hardware assumptions. | No generic thresholds. Require target evidence or explicit unverified status and escalation. |

E1-E4 are derived evidence requirements, not transcriptions of Zephyr/MISRA rules. E4 specifically needs target-repository corroboration. Do not reproduce proprietary MISRA text or Zephyr's rule table, or claim certification. This research cannot qualify a device.

## ROS2

Basis: [REP-2004][RQ], Package Requirements categories 1-7 and quality-level comparison. Select the package's intended quality level first; requirements vary. No target ROS2 repository/distribution was supplied, so these are evidence questions, not commands or proven gates.

| Candidate / REP category | Proposed class; severity | Target-repository evidence / acceptance question |
|---|---|---|
| R1: versioning / 1 | guidance plus validator where possible; error | Version policy, public API/ABI boundary, release history, distribution constraints. Does the change satisfy declared stability? |
| R2: change control / 2 | gate candidate; error | Change request, applicable contributor-origin evidence, peer review, CI and documentation policy for the selected level. |
| R3: documentation / 3 | validator plus review; error | README-linked quality declaration, feature/API docs, license/attribution and justification of claims. Existence alone does not establish quality. |
| R4: testing / 4 | validators feeding acceptance gate; error | Project commands/results covering documented features/API, coverage policy, applicable performance/static-analysis evidence. Review exceptions; invent no percentages. |
| R5: dependencies / 5 | inventory validator plus review; high | Direct runtime ROS dependency declarations, optional-dependency conditions, non-ROS dependency justifications, assessed against selected level. |
| R6: platforms / 6 | CI/target gate candidate; error | Declared distribution, applicable support tiers, repository CI and required-platform results. Verify current definitions before choosing a matrix. |
| R7: security / 7 | guidance plus release review; high | Disclosure policy, applicable response expectations and project evidence. A scanner alone cannot establish adherence. |

These categories are **ADAPT**, not an EAS Quality Level certificate. Missing/inapplicable items need reasons and review. Do not assume a middleware, simulator, coverage tool, timing threshold, or hardware test without package evidence.

## Release

Basis: REP-2004's evidence approach plus this repository's actual [release workflow](../../.github/workflows/release.yml), [distribution release gate](../../docs/DISTRIBUTION.md#release-gate), [provenance policy](../../docs/PROVENANCE.md), and [quality policy](../../policies/quality-gates.md). Local sources define EAS-specific checks, not universal ROS2 requirements. [REP-2004][RQ]

| Candidate / scope | Proposed class; severity | Evidence to require |
|---|---|---|
| L1: identity / candidate revision | validator feeding release gate; error | Tag/version agreement, changelog and exact validated revision; current release-tag validator is an existing example. |
| L2: reproducibility / distribution | validators feeding release gate; error | Repository checks, generated-adapter drift, applicable tests, Python compatibility floor and Linux/Windows package/recovery smoke evidence from existing workflow. |
| L3: origin / changed material | validator plus review; high | Canonical source, generator and drift evidence; licenses and file-specific adaptation/vendoring records. Hashes do not replace attribution/trust. |
| L4: review / release transition | gate candidate; critical | Independent review for release-critical behavior, unresolved findings and required authorization tied to the candidate. Preserve existing boundaries. |

No release was executed. The existing workflow shows configured checks, not proof that a release passed them. Generalizing `release` requires the target project's platform, packaging and release policy.

## Research needed before activation

Use a representative embedded repository and ROS2 package to map candidates to actual files, tools, quality targets and exceptions. Inspect the relevant distribution's current support definition rather than guessing from REP-2004. Test absent tools, stale evidence, skipped jobs, unsupported targets, contradictory declarations and deviations. A candidate may remain guidance when no reliable check or controlling gate exists.

[RQ]: https://github.com/ros-infrastructure/rep/blob/11ca24a41f31480dfb9562ba99f2a5b93d3ebda5/rep-2004.rst
[WS]: https://github.com/zephyrproject-rtos/west/blob/df990f0e0893d64e0600cbd2965ae45e39990f86/src/west/manifest-schema.yml
[ZG]: https://github.com/zephyrproject-rtos/zephyr/blob/bc2caf20dd0c7ca6c95c0dae66fd1ccb0e7e6147/doc/contribute/coding_guidelines/index.rst
[ZM]: https://github.com/zephyrproject-rtos/zephyr/blob/bc2caf20dd0c7ca6c95c0dae66fd1ccb0e7e6147/west.yml
