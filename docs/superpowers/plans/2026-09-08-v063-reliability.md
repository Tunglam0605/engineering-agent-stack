# v0.6.3 reliability hotfix

Goal: bound the impact of reported transport/session failures in existing EAS orchestration.
Architecture: extend durable assignment evidence and Workflow transactions; no native dispatch,
new role, provider configuration, or capability architecture changes. User authorized direct
implementation and release on clean main; execute inline with an independent read-only review.

- [x] Inspect lifecycle, approvals, dispatch, context bounds, adapters and release workflows.
- [x] Write and run failing transport/recovery, concurrency and handoff regressions.
- [x] Implement classification and validated assignment recovery evidence in runtime/reliability.py.
- [x] Extend Workflow with revision-checked observations, bounded resumes and one approved replacement.
  Preserve stopped-executor attestations, assignment scope, fanout limits and capability binding.
- [x] Add combined active-child capacity (default 2, allowed 1..4) to existing routing policy;
  reconnecting children reserve capacity, and unresolved recovery creates a scheduling barrier.
- [x] Expose operations through existing goal CLI; document bounded result/handoff fields and limits.
- [x] Update version/docs/generated adapter instructions; keep exactly seven roles.
- [x] Run Python 3.9 suite, validators, drift, compileall, workflow syntax, diff checks and independent review.
- [ ] Commit/push main, wait for CI, annotate/push v0.6.3, verify tag CI/release and exact artifact bytes.

Recovery states: failure -> resume-ready -> resuming -> healthy on verified success;
failed resume -> resume-ready until two resumes, or replacement-ready immediately for corruption.
Replacement needs a bounded handoff and fresh stopped-executor approval, passes ordinary lifecycle
limits, inherits cumulative budgets, and retires the old assignment. Replacement failure escalates.
Missing handoff/approval or exhausted budget never authorizes dispatch. Repeated observations
cannot reset budgets. Persist reason and bounded evidence; raw logs remain artifact references.

## Local release evidence

- Python 3.9: 172 tests passed, two Windows platform skips. Thirteen transport regressions
  cover classification, resume success, corruption replacement, retry budgets, duplicate
  observations, concurrent reservations, handoff bounding and transition/budget bypasses.
- All seven repository checks, compileall, actionlint 1.7.12, tag/version validation and diff checks passed.
- Offline acceptance installed exactly seven generated roles plus parent instructions into a temporary
  project. Personal managed checkout/install was not modified.
- Fresh wheel/sdist manifest verification and isolated installed-wheel smoke passed, including
  transport observation/resume/result, installed module origins and all 24 capability resources.
- Independent read-only review reproduced barrier, retirement and terminal reconciliation gaps.
  Failing regressions preceded fixes. Re-review found historical same-task reactivation; that
  regression now passes. Final review reported no blocking findings and independently verified
  the regression fails with the guard removed in memory. Filesystem/concurrency evidence came
  from the full local suite; the reviewer used a validating in-memory store.
- The legacy capacity CLI test now uses the configured cap instead of hard-coded three; existing
  reader/writer tests remain intact. Release artifact fixtures now use the package version so the
  tamper-before-install regression remains valid after version bumps.
- Local bundles are development evidence, not release assets. Main/tag CI and publication evidence
  will be recorded in immutable GitHub run/release records without amending tagged source.
