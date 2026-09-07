# awslabs/cli-agent-orchestrator

Source: https://github.com/awslabs/cli-agent-orchestrator

## Focus

Supervisor-oriented orchestration of multiple coding CLIs with provider-specific workers, profiles, skills and isolated terminal sessions.

## Inspected surfaces

- project README and runtime overview
- `docs/agent-profile.md`
- built-in agent store (supervisor, developer, reviewer, scout, memory manager, retrospector)

## Useful patterns

- **ADOPT — role/provider/tool separation:** a profile distinguishes its purpose, provider choice and tool restrictions.
- **ADOPT — explicit provider precedence:** launch-time and profile-level overrides have documented resolution rules.
- **ADAPT — capability/tag discovery:** metadata can help route specialists without loading all prompt bodies.
- **ADAPT — workspace/session isolation:** concurrent workers should have isolated execution surfaces where practical.
- **ADAPT — supervisor topology:** a single integration authority is useful, but external CLI process orchestration is not required for our first Codex adapter.
- **EXPERIMENT — persistent memory/self-learning:** useful only with provenance, bounded retention and regression protection.
- **ADOPT — untrusted metadata rule:** discovered profile metadata is routing data, not executable instruction authority.

## Project consequence

Canonical roles remain provider-neutral. Provider selection, tool permissions and launch behavior belong in adapters. Discovery metadata must never be allowed to override higher-level policy.
