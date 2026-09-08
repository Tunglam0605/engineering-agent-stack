# Distribution model

Engineering Agent Stack v0.3 uses a **source-managed distribution model**. The CLI is intentionally small; the managed source checkout remains the canonical home for generated roles, policies, schemas, benchmarks, and provider adapters.

## Managed locations

Default personal layout:

```text
~/.codex/
├── config.toml
├── agents/
│   ├── architect.toml
│   ├── debugger.toml
│   ├── implementer.toml
│   ├── researcher.toml
│   ├── reviewer.toml
│   ├── scout.toml
│   └── test-engineer.toml
└── engineering-agent-stack/
    ├── managed Git checkout
    └── .venv/       # isolated EAS Python runtime

~/.local/bin/
└── eas        # POSIX
   or eas.cmd  # Windows
```

The bootstrap never deletes or blindly replaces an incompatible existing `~/.codex/config.toml`.

## Bootstrap responsibilities

`install.ps1` and `install.sh`:

1. require Git and Python 3.9+;
2. clone or safely update the official repository;
3. create/reuse `~/.codex/engineering-agent-stack/.venv` as an isolated EAS runtime;
4. install the EAS package into that runtime (including PyYAML and `tomli` on Python 3.9/3.10);
5. run the existing Codex installer in dry-run mode;
6. install the seven generated roles;
7. run installer verification;
8. create a launcher under `~/.local/bin`;
9. leave PATH unchanged.

On an existing v0.3+ managed checkout, the bootstrap delegates update safety to the existing `eas update` command. The pre-v0.3 upgrade path refuses to change source unless the existing generated-role installation passes the old installer check.

## Why source-managed?

The stack contains more than a Python CLI. It includes generated Codex role files, policies, schemas, benchmark fixtures, research provenance, and provider adapters. A versioned source checkout keeps those artifacts inspectable and gives `eas update` both the old and new canonical role sets required for drift-aware upgrades.

## Upgrade safety

`eas update` is intentionally conservative. It refuses:

- dirty source checkouts;
- source checkouts not on `main`;
- locally ahead or diverged `main`;
- managed personal role files changed relative to the pre-update canonical source;
- incompatible personal Codex configuration.

A successful update uses `git merge --ff-only origin/main`, checks generated adapter drift, refreshes only personal roles that matched the pre-update canonical artifacts, and reruns the installer check.

## Uninstall safety

`eas uninstall` is ownership-aware:

- it removes only EAS role files that still byte-match canonical generated roles;
- any drifted managed role causes a full refusal before deletion;
- unrelated custom agents are preserved;
- `config.toml` is always preserved;
- the project `AGENTS.md` managed block is removed only when explicitly requested.

## Package installation

`pyproject.toml` exposes:

```text
eas = eas_cli.cli:main
```

Developers may install the CLI with `pip install .`. The managed/package runtime includes PyYAML for adapter generation; Python 3.9/3.10 additionally installs `tomli` because `tomllib` is standard-library only from Python 3.11. The one-line bootstrap remains the recommended full-stack installation because it also manages the source checkout and generated Codex artifacts.

The v0.5.0 wheel includes `runtime.workflow` and snapshot validation. Goal commands still require a canonical source checkout (`EAS_REPO` or the managed checkout) for role/policy data. Release smoke runs installed goal recovery outside the source tree on Linux and Windows. Version 2 goal snapshots are not writable by older releases; see [workflow migration and durability](WORKFLOW.md).

## Release gate

A stable release is not tagged until:

- Python 3.9 full tests pass;
- repository/provenance/agent/routing/benchmark validators pass;
- generated adapter drift is clean;
- Linux and Windows CI pass;
- package install smoke succeeds;
- installer/project lifecycle smoke succeeds;
- stack-owned acceptance passes;
- independent read-only review reports no blocking findings;
- `main` and `origin/main` are synchronized.

Provider child-agent health is a separate diagnostic and is not a deterministic release invariant.
