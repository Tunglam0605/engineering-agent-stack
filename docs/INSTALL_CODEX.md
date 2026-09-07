# Install into Codex

The Codex adapter is generated from provider-neutral roles and semantic compute profiles. Do not hand-edit generated role TOMLs in `adapters/codex/agents/`.

## 1. Generate and validate

```bash
python scripts/generate_codex_adapter.py
python scripts/generate_codex_adapter.py --check
```

## 2. Project-scoped installation

Recommended for the first real-world trial:

```bash
python scripts/install_codex.py --project /path/to/your/project --dry-run
python scripts/install_codex.py --project /path/to/your/project
python scripts/install_codex.py --project /path/to/your/project --check
```

This installs generated roles into:

```text
<project>/.codex/agents/*.toml
```

If `<project>/.codex/config.toml` does not exist, the installer creates it from the generated example. If a config already exists, the installer **does not rewrite it**; it prints the generated `[agents]` reference that must be merged/reviewed manually.

## 3. Personal installation

After project-scoped smoke tests pass:

```bash
python scripts/install_codex.py --personal --dry-run
python scripts/install_codex.py --personal
python scripts/install_codex.py --personal --check
```

This installs generated roles into `~/.codex/agents/`.

## Safe overwrite behavior

Existing differing role files cause installation to stop before writes. Use `--force` only after reviewing local differences. Forced replacement creates a `.bak` copy of every differing agent file first.

The installer never force-merges an existing `config.toml` because silently rewriting unrelated Codex configuration is unsafe.

## Smoke-test sequence

Use a non-critical repository first and check four behaviors:

1. a trivial single-file edit is handled directly without unnecessary delegation
2. repository discovery can delegate to `scout`
3. bounded implementation can delegate to `implementer` and receive targeted verification
4. high-risk review can invoke an independent `reviewer` or `architect` route

Then collect real traces with the benchmark capture tooling before changing default model mappings.

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
