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

### `eas init [PROJECT] [--dry-run] [--force] [--preset {embedded,ros2,release}]`

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


## Installed package verification

Build once into a fresh distribution directory, then create a release manifest with `scripts/release_artifacts.py create`. Run `python scripts/smoke_package.py --dist dist --commit COMMIT --manifest-sha256 DIGEST`, using the full source commit and the manifest digest recorded by the build. See [exact-artifact promotion](DISTRIBUTION.md#exact-artifact-promotion) for commands.

The smoke verifies the wheel/sdist hashes and archive metadata/resources before installation and again after testing. It creates a temporary clean virtual environment outside the checkout and verifies `eas version`, `eas preset list`, and `eas preset show embedded`, `ros2`, and `release`, plus all 24 packaged capability resources. It retains adapter validation and installed goal checkpoint/approval/recovery/export smoke. Main and release CI download the same build bundle on Linux and Windows with Python 3.9; no personal managed install is used. Runtime and capability behavior is unchanged in v0.6.2.

## Capability and preset commands (v0.6)

v0.6 adds a declarative capability layer. It does not add agents, change provider/model routing, or execute extension code.

### `eas preset list [--json]`

Lists the three built-in presets: `embedded`, `ros2`, and `release`.

### `eas preset show PRESET [--json]`

Shows one validated built-in preset, including declared skills, required rules and defaults.

### `eas preset detect [--project PATH] [--json]`

Runs a bounded **read-only** capability detector. Results are recommendation evidence only:

- `RECOMMENDED` with `HIGH|MEDIUM|LOW` confidence;
- `AMBIGUOUS/UNKNOWN` when strong evidence competes;
- `NONE/UNKNOWN` when no bounded evidence exists.

Detection never writes `.eas/project.toml` and never auto-activates a preset. Release-context detection never claims release readiness.

### `eas preset check [PRESET] [--project PATH] [--override PATH=JSON_VALUE] [--json]`

Validates the preset and runs only EAS-core trusted checker IDs referenced by validator/gate rules. Guidance is reported as guidance rather than claimed as automatic enforcement.

CLI override paths are deliberately limited to:

```text
selection.max_skills
selection.context_budget_tokens
skills.enabled
rules.required_rules
```

Protected lifecycle/recovery/write/model/provider/role fields are rejected.

### `eas project status [--project PATH] [--json]`

Reports:

- tracked `.eas/project.toml` state;
- read-only detection evidence and any conflict with the tracked profile;
- capability snapshot state: `UNBOUND`, `BOUND`, `DRIFT`, or `CORRUPT`.

The tracked profile remains authoritative; detector disagreement is surfaced, not applied.

### `eas project migrate-snapshot [--project PATH] [--expected-old-digest SHA256] [--json]`

Explicitly replaces the persisted `.git/eas/capabilities/snapshot.json` binding after configuration changes. Optional expected-old-digest gives compare-and-swap protection. No automatic drift rebind exists.

### `eas init PROJECT --preset PRESET`

Initializes the existing EAS project-managed Codex artifacts and creates tracked `.eas/project.toml` plus the initial capability snapshot. The profile non-overwrite check runs before project-role writes. Existing `.eas/project.toml` is never overwritten, including with `--force`.

### `eas goal bind-capabilities GOAL_ID --revision N [--project PATH] [--json]`

Explicitly migrates a legacy or drifted goal to the current project capability snapshot. Migration is revision-checked and refused while assignments are active.

Configured v0.6 projects require the same snapshot digest for stack-controlled goal gate/transition/checkpoint/approval/recovery/export paths. Projects without `.eas/project.toml` retain v0.5 lifecycle behavior.

## Codex subagent compatibility (v0.6.4)

EAS uses the public Codex `[agents]` configuration surface with `max_concurrent_threads_per_session = 2`. Do not enable the legacy experimental `[features.multi_agent_v2]` table: live Codex 0.153.4 A/B acceptance reproduced encrypted child-output failures when it was enabled. `eas` installation checks reject `features.multi_agent_v2.enabled=true`.

For an existing personal install, remove that experimental table (or set `enabled = false`) and verify Codex with `--strict-config` before running live subagent acceptance.

# v0.6.3 reliability operations

`eas goal transport GOAL ASSIGNMENT --event failure|resume-success|resume-failed --evidence TEXT --revision N`
records bounded failure/result evidence. `eas goal replace-child GOAL ASSIGNMENT --approval ID --handoff FILE`
reserves a single replacement after failed resume, subject to existing lifecycle checks. Neither
operation dispatches native children. See [workflow recovery](WORKFLOW.md#transport-and-session-recovery-v063).
