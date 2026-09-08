# Domain Skills / Rules / Config audit

Status: **research only; no preset/gate is active**. `source-index.json` records commit-pinned source evidence from Zephyr/west, FreeRTOS, STM32CubeH7, ROS2/REP-2004, GitHub release/security tooling, attestations, dependency review and Scorecard.

Classification is strict: **SKILL** = procedure/judgment; **RULE** = requirement with `guidance/validator/gate`; **CONFIG** = project parameter. Config never grants authority.

Evidence limits: do not reproduce proprietary MISRA text or claim certification; host tests do not replace target evidence for hardware-sensitive claims; FreeRTOS diagnostics are not complete safety proofs; REP-2004 does not justify an invented universal coverage threshold; dependency-review `warn-only`/unknown-license states are not equivalent to a clean blocking policy; attestations/Scorecard are evidence signals, not correctness certification.

See [candidate catalog](candidates.md).
