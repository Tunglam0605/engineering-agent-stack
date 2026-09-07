# Install into Codex

The Codex adapter is generated from provider-neutral roles and semantic compute profiles. Do not hand-edit generated role TOMLs in `adapters/codex/agents/`.

## 1. Generate and validate

```powershell
py scripts\generate_codex_adapter.py
py scripts\generate_codex_adapter.py --check
```

On Linux/macOS, use `python` instead of `py`.

## 2. Project-scoped installation

Recommended for the first real-world trial.

Windows PowerShell:

```powershell
py scripts\install_codex.py --project C:\path\to\your\project --dry-run --project-instructions
py scripts\install_codex.py --project C:\path\to\your\project --project-instructions
py scripts\install_codex.py --project C:\path\to\your\project --project-instructions --check
```

This installs generated roles into `<project>/.codex/agents/*.toml` and, with `--project-instructions`, manages one clearly marked Engineering Agent Stack block inside `<project>/AGENTS.md`.

The parent-orchestration block is important: child roles alone do not teach the parent Codex session the direct-first, selective-delegation, independent-review, and write-ownership policy.

If `<project>/.codex/config.toml` does not exist, the installer creates it from the generated example. If a config already exists, the installer does not rewrite it; it prints the generated `[agents]` reference that must be merged/reviewed manually.

If `AGENTS.md` already exists, only the managed Engineering Agent Stack block is added or refreshed. The original file is preserved and a backup named `AGENTS.md.engineering-agent-stack.bak` is created before a managed-block write.

## 3. Windows one-command acceptance

After installing development dependencies:

```powershell
py -m pip install -r requirements-dev.txt
.\scripts\acceptance-test.ps1
```

No-model/offline mode:

```powershell
.\scripts\acceptance-test.ps1 -Offline
```

Extended live role coverage:

```powershell
.\scripts\acceptance-test.ps1 -Extended
```

See [`ACCEPTANCE_WINDOWS.md`](ACCEPTANCE_WINDOWS.md).

## 4. Personal installation

Only after project-scoped smoke tests pass:

```powershell
py scripts\install_codex.py --personal --dry-run
py scripts\install_codex.py --personal
py scripts\install_codex.py --personal --check
```

Project orchestration instructions are intentionally not installed for personal scope because each target repository may already have different project constraints.

## Safe overwrite behavior

Existing differing role files cause installation to stop before writes. Use `--force` only after reviewing local differences. Forced replacement creates a `.bak` copy of every differing agent file first.

The installer never force-merges an existing `config.toml` because silently rewriting unrelated Codex configuration is unsafe.

The managed `AGENTS.md` block uses explicit markers so stack instructions can be refreshed without replacing unrelated project instructions.

## Automated smoke-test sequence

The Windows acceptance test checks:

1. repository validators and generated adapter drift
2. seven project-scoped custom-agent files
3. parent orchestration instructions
4. project-scoped installer consistency
5. explicit Scout invocation with read-only behavior
6. trivial direct-first edit with zero expected child spawns
7. explicit Implementer invocation with bounded write scope
8. token, latency, and observable subagent-spawn telemetry

Extended mode additionally invokes Researcher, Debugger, Test Engineer, Reviewer, and Architect.

## Current candidate mapping

| Role | Candidate |
|---|---|
| Scout | GPT-5.6 Luna / medium |
| Researcher | GPT-5.6 Luna / medium |
| Implementer | GPT-5.6 Terra / medium |
| Debugger | GPT-5.6 Terra / high |
| Test Engineer | GPT-5.6 Terra / medium |
| Reviewer | GPT-5.6 Terra / high |
| Architect | GPT-5.6 Sol / high |

These are benchmark candidates, not permanent role identities.
