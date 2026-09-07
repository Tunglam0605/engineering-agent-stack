# Windows Acceptance and Codex Provider Probes

Engineering Agent Stack now separates **stack-owned release acceptance** from **Codex provider/runtime diagnostics**.

That boundary is intentional. Repository structure, routing policy, installer behavior, direct-first behavior, and bounded write scope are under this project's control. `spawn_agent`, Multi-Agent V2 role selection, child-model routing, and provider telemetry are controlled by the current Codex runtime and must not block the stack release gate.

## Prerequisites

On Windows:

- Git available on `PATH`
- Python **3.9 or newer** available as `python` or `py`
- Codex CLI available as `codex` for live checks
- Codex authenticated through its normal CLI flow
- development dependencies installed with `py -m pip install -r requirements-dev.txt`

Python 3.11/3.12 is recommended for a fresh machine, but the validation path is kept compatible with Python 3.9.

A typical npm Codex installation may expose both `codex.ps1` and `codex.cmd`. The Python launcher resolver prefers the adjacent `.cmd` shim on Windows because `codex exec ... -` is less fragile through that path.

## Release gate: stack-owned acceptance

Run this for normal project acceptance:

```powershell
.\scripts\acceptance-test.ps1
```

This validates:

1. repository structure and provenance
2. canonical agent contracts and deterministic routing policy
3. controlled benchmark contracts
4. generated Codex adapter drift
5. Git availability
6. isolated project-scoped installation of all seven role files
7. parent orchestration instructions in the sandbox `AGENTS.md`
8. installer consistency check
9. direct-first trivial one-file edit behavior
10. bounded one-file write correctness and exact scope across unstaged, staged, and untracked paths

The live release gate **does not require a child agent to spawn**. Provider-owned delegation behavior is tested separately.

Offline/no-model acceptance:

```powershell
.\scripts\acceptance-test.ps1 -Offline
```

Direct Python entry point:

```powershell
py scripts\acceptance_core.py --offline
```

The legacy Python path remains as a compatibility shim:

```powershell
py scripts\acceptance_test_codex.py --offline
```

## Provider/runtime diagnostic: child delegation

Run this only when you explicitly want to test the current Codex runtime's multi-agent behavior:

```powershell
.\scripts\provider-probe.ps1
```

The basic provider probe tests:

- Scout custom-role `spawn_agent` event observation
- Scout read-only behavior
- Implementer custom-role `spawn_agent` event observation
- Implementer bounded write scope
- child model/role telemetry when the current JSONL schema exposes it

Extended provider probe:

```powershell
.\scripts\provider-probe.ps1 -Extended
```

This additionally probes Researcher, Debugger, Test Engineer, Reviewer, and Architect.

A provider probe can FAIL while the stack-owned release gate remains PASS. That means the current Codex runtime did not satisfy the requested provider capability; it is diagnostic evidence, not proof that repository routing/installation logic is broken.

## Retained local evidence example (2026-09-07)

On Windows `10.0.26200` with Python `3.11.15` and `codex-cli 0.153.4`:

- Stack-owned live acceptance: **PASS** with 0 failures, warnings, or skips. All seven generated roles installed consistently in the disposable project. Direct-first changed only `DIRECT.md`; bounded write changed only `IMPLEMENT.md`.
- Public JSONL reported zero observed `spawn_agent` events in the direct-first case. This is observational telemetry only and does not prove that no child ran.
- Basic provider probe: **FAIL** as a provider/runtime diagnostic. Scout remained read-only. The Implementer delegation path reported an upstream `502 Bad Gateway`, the parent did not silently perform the requested edit, and `changed=[]` remained intact.
- Child role/model telemetry was unavailable in the public JSONL stream. Extended provider probing was not run because the basic probe was unhealthy.
- Collaboration-call counts, token usage, latency, and other provider telemetry vary from run to run. Treat the Markdown report emitted by the current `acceptance-test.ps1` or `provider-probe.ps1` invocation as the authoritative source for exact measurements from that run.

The generated adapter sets `non_code_mode_only = false`, so installed projects expose Multi-Agent V2 collaboration in code mode. The provider probe exercises that installation default rather than masking it with a probe-only override.

## Why the split exists

The project previously mixed two different contracts:

```text
STACK-OWNED
  repository -> roles -> routing -> installer -> direct/write invariants

PROVIDER-OWNED
  Codex runtime -> spawn_agent -> custom role selection -> child model -> telemetry
```

That made upstream Codex runtime changes look like stack release failures. The two paths are now isolated so debugging one does not repeatedly block the other.

## UTF-8 subprocess handling

Codex JSONL is UTF-8. Windows engineering environments can inherit legacy code pages such as cp1252 from Python distributions or toolchains.

All subprocess capture in the acceptance core now explicitly uses:

```python
encoding="utf-8"
errors="replace"
```

and the JSONL parser accepts `None`/empty output as a zero-event stream instead of crashing. The PowerShell wrappers also launch Python in UTF-8 mode as an additional defense.

This prevents the previous failure chain:

```text
cp1252 UnicodeDecodeError
    -> subprocess reader thread dies
    -> stdout becomes None
    -> JSONL parser crashes on splitlines()
```

CI includes Linux and Windows regression checks for UTF-8 subprocess capture.

## Reports

Release-gate reports:

```text
acceptance-reports/acceptance-<UTC timestamp>.md
```

Provider-probe reports:

```text
acceptance-reports/provider-probe-<UTC timestamp>.md
```

The report directory is ignored by Git.

Release-gate statuses:

- `PASS`: required stack-owned condition observed
- `WARN`: optional runtime telemetry was unavailable
- `SKIP`: intentionally not exercised
- `FAIL`: repository/installer/direct-write invariant failed and blocks the release gate

Provider-probe failures are intentionally separate from release-gate status.

## Safety

Both paths use disposable temporary Git repositories. They do not:

- test against your production project
- install agents globally
- overwrite personal Codex configuration
- commit raw Codex transcripts to the repository

Write tests verify the sandbox Git top level, refuse hidden `skip-worktree` or `assume-unchanged` index state during exact-scope checks, clear those flags before resetting tracked/index changes, and remove untracked or ignored content after each case.

## Custom Codex executable path

Release gate:

```powershell
.\scripts\acceptance-test.ps1 -CodexBin "C:\path\to\codex.cmd"
```

Provider probe:

```powershell
.\scripts\provider-probe.ps1 -CodexBin "C:\path\to\codex.cmd"
```

## If PowerShell blocks local scripts

Run the Python entry points directly:

```powershell
py scripts\acceptance_core.py --live
py scripts\provider_probe_codex.py
```

No permanent PowerShell execution-policy change is required.
