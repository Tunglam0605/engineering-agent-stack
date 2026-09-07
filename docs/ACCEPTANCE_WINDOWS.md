# Windows Codex Acceptance Test

This is the recommended first real-machine acceptance path for Engineering Agent Stack.

The harness is project-scoped and disposable: it creates a temporary Git repository, installs the seven custom agents there, validates the parent orchestration instructions, and only then invokes Codex.

## Prerequisites

On Windows:

- Git available on `PATH`
- Python **3.10 or newer** available as `py` or `python`
- Codex CLI available as `codex`
- Codex authenticated through its normal CLI flow
- development dependencies installed with `py -m pip install -r requirements-dev.txt`

Python 3.10 is supported through the conditional `tomli` compatibility dependency; Python 3.11+ uses the standard-library `tomllib` module.

Before a live run, these two commands should succeed:

```powershell
py --version
Get-Command codex
```

If `Get-Command codex` cannot resolve an executable, the live acceptance cannot invoke Codex. Install/configure the Codex CLI or pass its exact executable path with `-CodexBin`.

## One-command live acceptance

From the Engineering Agent Stack repository in PowerShell:

```powershell
.\scripts\acceptance-test.ps1
```

This performs:

1. repository validators
2. generated-adapter drift check
3. isolated sandbox creation
4. project-scoped installation of all seven custom-agent TOMLs
5. managed parent orchestration block installation into the sandbox `AGENTS.md`
6. installation consistency check
7. live Scout invocation
8. direct-first trivial edit check
9. live Implementer invocation
10. token/latency/subagent-spawn telemetry capture
11. Markdown acceptance report generation

The basic live acceptance intentionally avoids invoking every role because repeated child-agent calls consume model tokens.

## Offline acceptance

Use this first when you only want to verify Windows compatibility and installation logic without consuming model tokens:

```powershell
.\scripts\acceptance-test.ps1 -Offline
```

The Python entry point defaults to offline mode:

```powershell
py scripts\acceptance_test_codex.py
```

## Extended live acceptance

After the basic test passes:

```powershell
.\scripts\acceptance-test.ps1 -Extended
```

This additionally invokes Researcher, Debugger, Test Engineer, Reviewer, and Architect. Architect currently maps to the critical Sol candidate, so extended acceptance costs more than the basic test.

## Custom Codex executable path

If Codex is installed but is not exposed as `codex` on `PATH`, pass its exact executable path:

```powershell
.\scripts\acceptance-test.ps1 -CodexBin "C:\path\to\codex.exe"
```

The PowerShell wrapper performs this preflight before starting a live run and reports a focused error instead of a generic Windows process-launch failure.

## Report

By default reports are written under:

```text
acceptance-reports/acceptance-<UTC timestamp>.md
```

The directory is ignored by Git.

Statuses mean:

- `PASS`: required condition observed
- `WARN`: non-blocking telemetry difference/incomplete field
- `SKIP`: intentionally not exercised
- `FAIL`: blocking acceptance condition not met

A basic live acceptance should not be called stable if it has any `FAIL`.

## What the live test proves

```text
parent Codex
    |
    +-- trivial edit ----------> direct, expected 0 child spawns
    |
    +-- explicit Scout -------> custom child spawn, read-only
    |
    +-- explicit Implementer -> custom child spawn, bounded write
```

Current Codex completed collaboration items can expose `collab_agent_tool_call` events. When available, the harness records:

- `agent_spawns`
- child `model`
- child `reasoning_effort`
- child role metadata
- input/output/reasoning token usage
- latency

If a Codex build omits optional model/role fields, the harness reports `WARN` rather than inventing evidence.

## Safety

The harness:

- never tests against your production project
- uses a disposable temporary Git repository
- does not install agents globally
- does not overwrite your personal Codex configuration
- does not copy raw Codex transcripts into the final Markdown report
- resets write-test workspaces after each case

Use `--keep-sandbox` with the Python entry point only when you intentionally want to inspect the disposable repository after the run.

## If PowerShell blocks local scripts

Run the Python entry point directly:

```powershell
py scripts\acceptance_test_codex.py --live
```

No permanent PowerShell execution-policy change is required.
