# EAS CLI

`eas` is the distribution and lifecycle interface for Engineering Agent Stack.

## Commands

### `eas version`

Prints the CLI version.

### `eas doctor [--json]`

Read-only environment/installation diagnostic. It checks Python, Git, Codex discovery, source checkout, personal installation and the current Git project. It does not run provider probes.

### `eas status [--json]`

Read-only summary of canonical roles, personal/project installation state and policy limits.

### `eas install [--dry-run] [--force]`

Installs the seven generated roles for personal Codex. It reuses `scripts/install_codex.py`, so an incompatible existing `config.toml` is refused rather than overwritten.

Use `--force` only after reviewing a locally modified managed role.

### `eas init [PROJECT] [--dry-run] [--force]`

Initializes one Git repository with:

- `.codex/agents/*.toml`;
- `.codex/config.toml` when missing;
- one EAS-managed block in `AGENTS.md`.

Content outside the managed block is preserved.

### `eas check [--personal | --project PATH] [--project-instructions]`

Verifies generated roles/config. `--project-instructions` additionally verifies the managed `AGENTS.md` block.

### `eas update [--check]`

For a source-managed checkout:

1. require a clean Git worktree;
2. require branch `main`;
3. refuse local managed-role drift;
4. refuse incomplete personal managed-role installations rather than filling missing roles;
5. fetch `origin/main`;
6. refuse ahead/diverged state;
7. use fast-forward only;
8. verify generated adapter drift;
9. refresh only a complete personal managed-role set whose pre-update contents matched the old canonical version;
10. run the installer check.

`--check` performs the remote comparison without merging.

### `eas uninstall [--personal | --project PATH] [--project-instructions] [--dry-run]`

Removes only EAS-generated role files that still byte-match canonical generated artifacts.

It never deletes `config.toml`. Unrelated custom agents are preserved. If any managed role has local drift, the operation refuses before deleting any managed role.

## Environment variables

| Variable | Purpose |
|---|---|
| `EAS_HOME` | Override user home for tests/isolated environments |
| `EAS_REPO` | Explicit EAS source checkout |
| `EAS_REF` | POSIX bootstrap branch selector; v0.3 accepts only `main` and refuses other values |

## Exit codes

General CLI lifecycle commands use:

- `0`: success;
- `2`: invalid/refused/unsafe lifecycle action;
- downstream installer/check commands may preserve their documented nonzero result.

The delegation resolver has its own contract: `0=PASS`, `3=REJECT`, `4=ESCALATE`, `2=invalid request`.
