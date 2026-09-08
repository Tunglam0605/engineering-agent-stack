# Install into Codex

Engineering Agent Stack v0.3 has two installation surfaces:

1. **recommended full-stack bootstrap** — clones a managed source checkout, installs the seven generated roles, verifies them, and creates an `eas` launcher;
2. **advanced source installer** — `scripts/install_codex.py`, useful for contributors, CI, and tightly controlled project installs.

Generated role TOMLs under `adapters/codex/agents/` are build artifacts. Do not hand-edit them.

## Recommended: one-line bootstrap

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/Tunglam0605/engineering-agent-stack/main/install.ps1 | iex
& "$HOME\.local\bin\eas.cmd" doctor
```

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/Tunglam0605/engineering-agent-stack/main/install.sh | sh
~/.local/bin/eas doctor
```

The bootstrap uses `~/.codex/engineering-agent-stack` as the managed checkout, `~/.codex/engineering-agent-stack/.venv` as an isolated Python runtime, and `~/.local/bin` for the launcher. The managed runtime carries PyYAML for adapter generation; Python 3.9/3.10 also gets the required `tomli` compatibility dependency there. It **does not modify PATH**.

See [`DISTRIBUTION.md`](DISTRIBUTION.md) for lifecycle and update safety.

## Initialize a project

From a Git repository:

```powershell
eas init C:\path\to\project
```

or:

```bash
cd /path/to/project
eas init
```

This installs generated roles into `<project>/.codex/agents/`, creates `<project>/.codex/config.toml` only when missing, and manages one clearly marked Engineering Agent Stack block in `<project>/AGENTS.md`.

Existing `AGENTS.md` content outside the managed block is preserved.

Verify:

```powershell
eas check --project C:\path\to\project --project-instructions
```

## Personal lifecycle

```powershell
eas install --dry-run
eas install
eas check --personal
eas doctor
```

Existing differing role files cause installation to stop before writes. `--force` is available only for deliberate replacement after reviewing local differences. The underlying installer creates backups for forced role replacement.

The installer never force-merges an existing `config.toml`; malformed or incompatible configuration is refused and must be merged manually.

## Update

```powershell
eas update --check
eas update
```

Update requires a clean managed source checkout on `main`, refuses ahead/diverged branches, refuses local managed-role drift, and uses fast-forward only.

## Uninstall

Project scope:

```powershell
eas uninstall --project C:\path\to\project --project-instructions
```

Personal scope:

```powershell
eas uninstall --personal
```

Uninstall removes only canonical EAS-managed role files. It preserves `config.toml`, unrelated custom agents, and unrelated `AGENTS.md` content. A drifted managed role causes the operation to refuse before deleting any managed role.

## Advanced source installer

Contributors can still call the lower-level installer directly:

```powershell
py -3.9 scripts\install_codex.py --project C:\path\to\project --project-instructions --dry-run
py -3.9 scripts\install_codex.py --project C:\path\to\project --project-instructions
py -3.9 scripts\install_codex.py --project C:\path\to\project --project-instructions --check
```

Personal:

```powershell
py -3.9 scripts\install_codex.py --personal --dry-run
py -3.9 scripts\install_codex.py --personal
py -3.9 scripts\install_codex.py --personal --check
```

On Linux/macOS use `python3` or `python`.

## Acceptance and provider diagnostics

Stack-owned release acceptance:

```powershell
.\scripts\acceptance-test.ps1
```

Offline:

```powershell
.\scripts\acceptance-test.ps1 -Offline
```

Provider-owned child delegation remains a separate diagnostic:

```powershell
.\scripts\provider-probe.ps1
```

A provider probe may fail because of upstream service availability while deterministic installer/routing/runtime release gates remain healthy.

## Current candidate model mapping

| Role | Candidate |
|---|---|
| Scout | GPT-5.6 Luna / medium |
| Researcher | GPT-5.6 Luna / medium |
| Implementer | GPT-5.6 Terra / medium |
| Debugger | GPT-5.6 Terra / high |
| Test Engineer | GPT-5.6 Terra / medium |
| Reviewer | GPT-5.6 Terra / high |
| Architect | GPT-5.6 Sol / high |

These are benchmark candidates, not role identities.
