# Candidate domain catalog

Status: candidates pending representative-repository experiments.

## Embedded

**Skills:** build/link triage; hard-fault root cause; ISR/RTOS/DMA concurrency review; bootloader/linker/flash/OTA review.

**Rules:** resolved dependency/workspace evidence; selected target build under project warning policy; interrupt/RTOS constraints reviewed when affected; target/hardware evidence when the claim depends on hardware; selected coding/safety standard and deviations documented when required. Missing target evidence is UNKNOWN/unverified, not PASS.

**Config:** MCU/board, toolchain/version, RTOS, build target/config, linker/map inputs, hardware test target, warning policy, project coding standard/deviation process.

## ROS2

**Skills:** interface/QoS impact; launch/parameter integration; topic/TF/odom debugging; quality-declaration review.

**Rules:** adapt REP-2004 categories for versioning, change control, docs, testing, dependencies, platforms and security according to the project's declared quality target. No universal numeric coverage default.

**Config:** ROS distribution, package/build system, quality target, supported platforms, test/static-analysis commands/policy, dependency policy, expected interfaces/QoS.

## Release

**Skills:** candidate audit; provenance review; CI/publish failure triage.

**Rules:** revision/version/tag identity; required tests/generated-drift checks; independent review for release-critical/high-risk changes; artifact verification; provenance/license evidence for changed third-party/generated material.

**Config:** version source, tag pattern, required CI jobs/platforms, package outputs, artifact/signing/attestation policy, dependency-review severity/policy. Action names/versions are CONFIG, not universal RULES.

## Universal security baseline

No extension-granted permissions or arbitrary package code/hooks/commands; no secrets in snapshots/traces; strict containment/collision checks; fail closed on unsupported required capability; preserve provider-native security and EAS write/review/recovery invariants.
