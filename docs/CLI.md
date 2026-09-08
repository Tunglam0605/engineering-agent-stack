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
## Goal lifecycle commands (v0.4)

Long-running goals may use an executable lifecycle registry stored outside the worktree under `.git/eas/goals/`.

### `eas goal init GOAL_ID [--project PROJECT] [--json]`

Initializes atomic goal state and an append-only JSONL event stream. Goal IDs are lowercase/path-safe, reject Windows-reserved names, and cannot contain traversal.

### `eas goal gate GOAL_ID --role ROLE --domain DOMAIN [options]`

Returns one lifecycle action before a child dispatch:

- `REUSE` — continue an existing matching assignment;
- `SPAWN` — a new assignment is within policy;
- `ESCALATE` — reconciliation/serialization/operator justification is needed;
- `REJECT` — the ordinary hard ceiling forbids another child.

Writer roles require one or more `--scope PATH`. Use `--commit` to persist a `SPAWN` decision as a pending assignment or record a non-spawn gate decision. Use `--fresh-context --reason TEXT` only when a matching child is stale/wrong and a new context is materially justified. At/above the soft budget, `--reconciled --reason TEXT` records why another spawn is justified. Hard-ceiling exceptions are restricted to acceptance diagnostics and required safety/release review.

Exit codes: `0 = SPAWN/REUSE`, `4 = ESCALATE`, `3 = REJECT`, `2 = invalid input/runtime error`.

### `eas goal transition GOAL_ID ASSIGNMENT_ID STATE`

Transitions a committed assignment among `pending`, `running`, `completed`, `failed`, and `blocked`, updating atomic state and the event stream.

### `eas goal status GOAL_ID [--json]`

Shows total/active assignments, reader/writer concurrency, per-role counts, soft/hard budget state, and assignment details.

Committed mutations use a per-goal transaction lock plus state revision/CAS, so concurrent callers cannot silently lose assignments or bypass writer capacity. A lock timeout fails closed and does not auto-delete a possibly live lock.

The goal gate is opt-in stack-controlled enforcement. Native provider child calls that bypass the EAS gate remain outside this enforcement boundary.

## Durable workflow commands (v0.5.0)

All accept `--project PATH` and `--json`. See [WORKFLOW.md](WORKFLOW.md) for evidence semantics and the complete recovery sequence.

| Command | Required arguments |
|---|---|
| `eas goal checkpoint GOAL` | `--stage TEXT --revision N` (optional `--evidence JSON_OBJECT`) |
| `eas goal plan GOAL` | none; read-only checkpoint, revision and suspicion |
| `eas goal approve GOAL` | `--action ACTION --target ASSIGNMENT --revision N --approver TEXT --reason TEXT --executor-stopped-evidence TEXT` |
| `eas goal recover GOAL ASSIGNMENT` | `--approval ID` |
| `eas goal export GOAL` | none; always emits machine-readable JSON |

Risky `goal transition` calls additionally require `--approval ID` bound to `transition:STATE`. Stale/timeout suspicion is not proof an executor stopped and never frees capacity. Recovery consumes explicit approval atomically and preserves assignment identity. Retries return historical receipts without reapplying mutations. Approval is a local attestation, not authenticated identity or automatic evidence verification.
