# Engineering Agent Stack

> Turn Codex into a bounded engineering team: **7 focused roles, direct-first routing, safe writes, independent verification, and a small distribution CLI.**

[![Status](https://img.shields.io/badge/status-v0.5.0%20stable-blue)](#release-status)
[![CI](https://github.com/Tunglam0605/engineering-agent-stack/actions/workflows/validate.yml/badge.svg)](https://github.com/Tunglam0605/engineering-agent-stack/actions/workflows/validate.yml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](pyproject.toml)

Engineering Agent Stack (EAS) is a compact orchestration and policy layer for Codex. It does **not** replace Codex and it does not try to maximize agent count. It gives Codex a small engineering team with explicit responsibilities, bounded write behavior, verification rules, runtime contracts, and repeatable installation.

## Install

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/Tunglam0605/engineering-agent-stack/main/install.ps1 | iex
```

Then run:

```powershell
& "$HOME\.local\bin\eas.cmd" doctor
```

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/Tunglam0605/engineering-agent-stack/main/install.sh | sh
~/.local/bin/eas doctor
```

The bootstrap installs a managed source checkout under `~/.codex/engineering-agent-stack`, creates an isolated `.venv` runtime, installs the seven generated Codex roles, validates the installation, and creates an `eas` launcher under `~/.local/bin`.

**EAS does not silently modify your PATH.** Add `~/.local/bin` to PATH yourself if you want to run `eas` from anywhere.

## Start using it

Initialize a Git repository:

```powershell
cd C:\path\to\your\project
& "$HOME\.local\bin\eas.cmd" init
codex
```

On Linux/macOS:

```bash
cd /path/to/your/project
eas init
codex
```

`eas init` installs project-scoped Codex role files and one managed orchestration block inside `AGENTS.md`. Existing project instructions outside that block are preserved.

Then give Codex the engineering task normally:

```text
Find the root cause of this failure and fix it.
Use Engineering Agent Stack policy: direct-first, bounded writes,
targeted verification, and independent review when risk requires it.
```

## The seven roles

| Role | Responsibility | Default capability | Compute candidate |
|---|---|---|---|
| **Scout** | repository discovery and call-flow mapping | read-only | Luna / medium |
| **Researcher** | current authoritative external evidence | read + network intent | Luna / medium |
| **Implementer** | smallest approved implementation | bounded write + test | Terra / medium |
| **Debugger** | evidence-first root cause and remediation | bounded write + test | Terra / high |
| **Test Engineer** | narrowest meaningful verification | test artifacts + test | Terra / medium |
| **Reviewer** | independent correctness/regression review | read + test | Terra / high |
| **Architect** | critical architecture/safety decisions | read-only | Sol / high |

A **role is not a model**. Role, compute profile, provider, and concrete model remain separate so routing can change after benchmarks without changing the engineering contract.

## Direct-first orchestration

EAS defaults to doing small, reversible work directly. Delegation is used only when task shape, uncertainty, or risk justifies the overhead.

```text
Task
 |
 +--> DIRECT ---------------------------> verify
 |
 +--> DELEGATE
        |
        v
   role + profile
        |
        v
   preflight
   PASS / REJECT / ESCALATE
        |
        v
   execution
        |
        v
   verification / review
```

Current policy keeps parallelism conservative:

```text
maximum parallel readers: 3
default parallel writer ownership: 1 scope owner
soft child-assignment budget: 8 per goal
hard ordinary-spawn ceiling: 12 per goal
resume-before-spawn: enabled
recursive delegation: disabled
```

## `eas` CLI

```text
eas version
eas doctor
eas status
eas install
eas init [PROJECT]
eas check
eas update [--check]
eas uninstall
eas goal init GOAL_ID
eas goal gate GOAL_ID --role ROLE --domain DOMAIN [--scope PATH] [--commit]
eas goal transition GOAL_ID ASSIGNMENT_ID STATE
eas goal status GOAL_ID [--json]
```

Useful examples:

```powershell
# Read-only health report
eas doctor

# Machine-readable automation output
eas doctor --json
eas status --json

# Preview a personal install
eas install --dry-run

# Initialize one repository
eas init C:\Projects\robot

# Verify project-managed roles + orchestration block
eas check --project C:\Projects\robot --project-instructions

# Check whether the managed checkout is behind
eas update --check

# Safe fast-forward update
eas update

# Remove only EAS-managed project roles/instructions
eas uninstall --project C:\Projects\robot --project-instructions
```

See [`docs/CLI.md`](docs/CLI.md) for the command contract.

## Safety model

EAS treats prompts as instructions, not security boundaries. Important constraints are represented in code/configuration and validated wherever the provider exposes an enforceable boundary.

Key guarantees in the repository tooling:

- existing incompatible Codex config is refused rather than rewritten;
- project `AGENTS.md` uses managed markers and preserves unrelated content;
- uninstall removes only role files that still match EAS-generated artifacts;
- drifted managed roles cause uninstall/update to refuse before destructive action;
- update requires a clean `main` checkout and uses fast-forward only;
- update never overwrites locally modified managed role files;
- update refuses partial personal role installations rather than creating missing managed roles;
- provider telemetry that is unavailable remains **unknown**, not fabricated;
- only `PASS` from the repository preflight API can produce a resolved execution plan.

The Python preflight gate is an explicit repository/runtime tool. It does **not** claim to transparently intercept every native Codex `spawn_agent` call.

## Provider health is separate from stack health

Codex child-agent service availability can fail independently of EAS. `eas doctor` therefore does not probe a provider by default.

```text
EAS core         HEALTHY
Codex install    HEALTHY
Provider         UNKNOWN / DEGRADED
```

Use `scripts/provider-probe.ps1` when you explicitly want provider/runtime diagnostics. A provider `502 Bad Gateway` does not invalidate deterministic repository, installer, routing, or safety tests.

## For Codex: install this repo for me

You can also give Codex the repository URL and ask it to install EAS:

```text
Install Engineering Agent Stack from:
https://github.com/Tunglam0605/engineering-agent-stack.git

Read the repository installation docs first.
Do not overwrite an incompatible ~/.codex/config.toml.
Run a dry-run before installation, then run the installer check and eas doctor.
```

## Architecture

```text
User task
   |
   v
Classification / direct-first routing
   |
   v
Delegation preflight
   |
   +-- REJECT
   +-- ESCALATE
   +-- PASS
         |
         v
Resolved execution plan
         |
         v
Provider adapter
         |
         v
Execution
         |
         +--> registry / telemetry
         |
         v
Quality gate
```

Repository layout:

```text
eas_cli/         distribution CLI: health, lifecycle, update and status
agents/          provider-neutral core role definitions
config/          semantic compute profiles and deterministic routing policy
policies/        delegation, context, escalation and quality rules
runtime/         provider-neutral preflight, plan, registry and context contracts
adapters/        provider-specific generated artifacts
benchmarks/      controlled quality/cost/latency experiments
research/        source analysis and provenance
schemas/         stable machine-readable contracts
scripts/         installer, acceptance, probes and developer utilities
tests/           deterministic regression coverage
docs/            architecture, CLI, distribution and contributor guidance
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Development

Python 3.9 is the compatibility floor.

```powershell
py -3.9 -m pip install -r requirements-dev.txt
py -3.9 -m unittest discover -s tests -v
py -3.9 scripts\validate_structure.py
py -3.9 scripts\validate_provenance.py
py -3.9 scripts\validate_agents.py
py -3.9 scripts\evaluate_routing.py
py -3.9 scripts\validate_task_suite.py
py -3.9 scripts\validate_benchmarks.py
py -3.9 scripts\generate_codex_adapter.py --check
git diff --check
```

Build/install the CLI locally:

```powershell
py -3.9 -m pip install .
eas version
eas doctor
```

Stack-owned Windows acceptance:

```powershell
.\scripts\acceptance-test.ps1
```

Provider/runtime diagnostic:

```powershell
.\scripts\provider-probe.ps1
```

## Research and benchmarks

EAS is research-driven. Routing and model mappings remain benchmark candidates rather than role identity.

The project studies and credits upstream work including OpenAI Codex, agency-agents, oh-my-codex, oh-my-pi, OpenAI Agents SDK, Microsoft Agent Framework, AutoGen, LangGraph, Deep Agents, CrewAI, smolagents, OpenHands and others.

See:

- [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md)
- [`docs/PROVENANCE.md`](docs/PROVENANCE.md)
- [`research/matrix/repository-comparison.yaml`](research/matrix/repository-comparison.yaml)
- [`benchmarks/README.md`](benchmarks/README.md)

## Executable goal lifecycle gate

For long-running multi-agent work, EAS can persist goal state under Git metadata (`.git/eas/goals/`) and make an executable lifecycle decision before dispatch:

```text
spawn request
    -> eas goal gate
    -> REUSE | SPAWN | ESCALATE | REJECT
    -> optional --commit
    -> assignment transition + JSONL event
```

Example:

```powershell
eas goal init ota-hardening
eas goal gate ota-hardening --role scout --domain gateway --commit
eas goal status ota-hardening --json
```

Writer roles require `--scope`. Use `--fresh-context --reason TEXT` only when a matching child is stale/wrong. Committed mutations are serialized by a per-goal transaction lock and protected by a state revision, preventing stale/lost updates. Exit codes follow the stack planning convention: `0` for `SPAWN/REUSE`, `4` for `ESCALATE`, and `3` for `REJECT`. This is an executable EAS gate for stack-controlled orchestration; it does **not** claim to transparently intercept arbitrary provider-native `spawn_agent` calls.

Checkpoint verification/review evidence with `eas goal checkpoint`, inspect interruption with `eas goal plan`, then record explicit stopped-executor evidence with `eas goal approve` before `eas goal recover`. Recovery preserves the assignment ID. See the [workflow and recovery guide](docs/WORKFLOW.md) for the complete sequence and enforcement boundary.

## Release status

**v0.5.0** adds durable workflow checkpoints, explicit approval evidence, and safe assignment recovery while keeping the seven-role/model map stable:

- `eas goal checkpoint/plan/approve/recover/export`;
- revision-scoped approval consumption and idempotent recovery receipts;
- stale/timeout suspicion without automatic executor replacement;
- machine-readable export separating durable state from observational JSONL;
- stable `eas` CLI;
- executable `eas goal gate` decisions (`REUSE / SPAWN / ESCALATE / REJECT`);
- atomic goal state under Git metadata with append-only JSONL events;
- goal status/assignment transition CLI;
- canonical policy-derived `eas status` instead of hard-coded limits;
- resume-before-spawn lifecycle policy;
- soft/hard per-goal child-assignment budgets;
- conservative 3-reader / 1-writer parallelism;
- architect/reviewer reuse guidance and stable assignment naming;
- fan-out summary observability in the agent registry;
- Windows and POSIX bootstrap installers;
- read-only `doctor` / `status`;
- safe project initialization;
- drift-aware uninstall;
- guarded fast-forward update;
- Python package metadata;
- CI/package smoke coverage;
- product-oriented installation documentation.

The core remains deliberately small at seven roles. Domain extensions/presets are deferred until benchmark evidence justifies their maintenance cost.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) and [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT. See [`LICENSE`](LICENSE).
