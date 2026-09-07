# Windows Codex Acceptance Test

This is the recommended first real-machine acceptance path for Engineering Agent Stack.

The harness is project-scoped and disposable: it creates a temporary Git repository, installs the seven custom agents there, validates the parent orchestration instructions, and only then invokes Codex.

## Prerequisites

On Windows:

- Git available on `PATH`
- Python **3.9 or newer** available as `py` or `python`
- Codex CLI available as `codex`
- Codex authenticated through its normal CLI flow
- development dependencies installed with `py -m pip install -r requirements-dev.txt`

Python 3.9/3.10 are supported through the conditional `tomli` compatibility dependency; Python 3.11+ uses the standard-library `tomllib` module. Python 3.11/3.12 is still recommended for a fresh machine, but upgrading an existing Python 3.9 installation is not required just to run this acceptance harness.

Before a live run, these commands should succeed:

```powershell
py --version
Get-Command codex
codex --version
```

A typical npm Codex installation on Windows may resolve `codex` to a PowerShell launcher such as `codex.ps1`. The acceptance harness prefers the adjacent npm `codex.cmd` launcher when present so `codex exec ... -` receives its stdin marker without PowerShell parameter-binding interference.

If `Get-Command codex` cannot resolve anything, the live acceptance cannot invoke Codex. Install/configure the Codex CLI or pass its exact executable/script path with `-CodexBin`.

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

The harness prints live progress markers before Scout, direct-first, and Implementer so a slow model call is distinguishable from a frozen wrapper. A single Codex call timing out is recorded as a failed test case instead of aborting the entire report.

## Codex V2 ephemeral delegation compatibility

Current Codex releases have a known upstream issue in `codex exec --ephemeral` when a V2 child spawn tries to inherit/fork parent history. The root thread exists in memory, but an ephemeral run intentionally has no persisted parent history, so the history-fork path can fail with:

```text
collab spawn failed: no thread with id: <root-thread-id>
```

Upstream tracking: <https://github.com/openai/codex/issues/41474>

The acceptance harness therefore makes the intended Engineering Agent Stack context policy explicit: delegated smoke tests request `fork_turns = "none"` and put the complete bounded assignment in the child message. This is both a runtime compatibility measure and the desired minimal-context behavior for normal role delegation.

If a real task genuinely requires inherited parent history, do not silently classify an ephemeral history-fork failure as an agent-quality failure. Use a persistent Codex session or wait for the upstream ephemeral fork path to be fixed, then test that history-dependent workflow separately.

Some affected Codex V2 releases also reject short explicit `wait_agent` values with an error such as:

```text
timeout_ms must be at least 10000
```

The managed parent instructions and acceptance prompts therefore tell Codex to omit `timeout_ms` or use at least `10000` ms.

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

If Codex is installed but is not exposed as `codex` on `PATH`, pass its exact executable or script path:

```powershell
.\scripts\acceptance-test.ps1 -CodexBin "C:\path\to\codex.cmd"
```

The harness supports normal executables plus Windows npm launchers such as `.cmd`, `.bat`, and `.ps1`.

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
    +-- explicit Scout -------> fresh bounded child, no tracked file changes
    |
    +-- explicit Implementer -> fresh bounded child, bounded write
```

Current Codex `exec --json` serializes collaboration activity as `collab_tool_call` items. Older/experimental traces may use `collab_agent_tool_call`; the parser accepts both so CLI-version differences do not create false zero-spawn results.

For a current `spawn_agent` item, the JSONL payload exposes receiver thread IDs, prompt/state, and status. It does **not** currently expose child model, reasoning effort, or custom role metadata in the `CollabToolCallItem` payload. The harness therefore records:

- `agent_spawns`
- `agent_spawn_thread_ids`
- input/output/reasoning token usage
- latency
- timeout state
- model/role/reasoning metadata only when the CLI actually emits those optional fields

Missing model/role fields are reported as `WARN`, not guessed and not treated as proof that delegation failed. A successful spawn plus the behavioral checks is enough for the basic acceptance path; exact child model/role verification requires a runtime telemetry surface that exposes those fields.

## Safety

The harness:

- never tests against your production project
- uses a disposable temporary Git repository
- does not install agents globally
- does not overwrite your personal Codex configuration
- does not copy raw Codex transcripts into the final Markdown report
- resets write-test workspaces after each case
- keeps live Codex runs ephemeral while avoiding inherited-history forks for normal bounded delegation

Use `--keep-sandbox` with the Python entry point only when you intentionally want to inspect the disposable repository after the run.

## If PowerShell blocks local scripts

Run the Python entry point directly:

```powershell
py scripts\acceptance_test_codex.py --live
```

No permanent PowerShell execution-policy change is required.
