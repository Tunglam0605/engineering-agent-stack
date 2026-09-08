# Acknowledgements

Engineering Agent Stack is an original synthesis built from public documentation, source code, design discussions, and community experiments across the agent ecosystem. It would not exist without the maintainers and contributors who made those systems available for study.

This project does **not** claim ownership of upstream projects, their names, documentation, prompts, or implementation ideas. We study them, record what we learned, and re-express selected patterns in a smaller provider-aware engineering stack.

## Primary research sources

| Upstream project | What it contributed to our research |
|---|---|
| [openai/codex](https://github.com/openai/codex) | Authoritative Codex runtime/custom-agent behavior, public configuration surface, and execution telemetry. |
| [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | Specialist-role design, explicit mission/deliverable framing, and role taxonomy ideas. |
| [Yeachan-Heo/oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex) | Direct-first delegation, leader-owned verification, and specialist routing patterns. |
| [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) | Runtime role/model resolution, delegation preflight, agent status observability, and bounded context-management patterns studied for v0.2. |
| [infiquetra/infiquetra-codex-plugins](https://github.com/infiquetra/infiquetra-codex-plugins) | Separation of logical role from compute profile, independent review, typed results, and write-set discipline. |
| [trailofbits/codex-config](https://github.com/trailofbits/codex-config) | Conservative Codex configuration and the practice of checking current official docs before relying on fast-changing keys. |
| [KevinBigham/codex-safe-starter](https://github.com/KevinBigham/codex-safe-starter) | Read-only exploration/review, narrow verification, and reversible project-scoped setup. |
| [awslabs/cli-agent-orchestrator](https://github.com/awslabs/cli-agent-orchestrator) | Role/provider/tool separation, capability discovery, session isolation, and supervisor-style orchestration. |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | Explicit handoffs, guardrails, tracing, and agents-as-tools concepts. |
| [microsoft/agent-framework](https://github.com/microsoft/agent-framework) | Deterministic workflow graphs, observability, checkpointing, and human-in-the-loop patterns. |
| [microsoft/autogen](https://github.com/microsoft/autogen) | Historical multi-agent architecture and evaluation lessons, including limitations of group-chat-first designs. |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | Durable state-machine orchestration, interrupts, persistence, and evaluation/observability patterns. |
| [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) | Isolated subagent context, tool-output offloading, and on-demand skills. |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | Separation between autonomous agents and deterministic flows, plus structured collaborative task concepts. |
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | Minimal agent runtime philosophy, model/tool agnosticism, and sandbox-oriented execution ideas. |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | Coding-agent control-plane/runtime separation, sandbox backends, and multi-backend adapter concepts. |

Thank you to the maintainers and contributors of these projects for publishing work that the wider engineering community can inspect, compare, challenge, and learn from.

## v0.6 research and architecture audit sources

The [v0.6 audit](research/v0.6/README.md) additionally studies the following conceptual sources. It revisits `can1357/oh-my-pi`, `Yeachan-Heo/oh-my-codex`, and `openai/openai-agents-python` above for capability packaging, canonical workflow rules, and enforcement boundaries. Source notes record inspected revisions and file-level license concerns; no upstream material is copied.

| Upstream project | Research contribution |
|---|---|
| [agentskills/agentskills](https://github.com/agentskills/agentskills) | Portable skill format and progressive disclosure. |
| [anthropics/skills](https://github.com/anthropics/skills) | Bounded skill bodies, variant references, and evaluation. |
| [obra/superpowers](https://github.com/obra/superpowers) | Reusable skill criteria and baseline pressure testing. |
| [github/spec-kit](https://github.com/github/spec-kit) | Preset composition, manifests, compatibility, catalogs, and precedence. |
| [modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol) | Capability negotiation, control ownership, and consent boundaries. |
| [zephyrproject-rtos/west](https://github.com/zephyrproject-rtos/west) | Manifest versioning and explicit dependency evidence. |
| [zephyrproject-rtos/zephyr](https://github.com/zephyrproject-rtos/zephyr) | Embedded quality rooted in external standards; no proprietary MISRA text reused. |
| [ros-infrastructure/rep](https://github.com/ros-infrastructure/rep) | REP-2004 quality declarations and justified evidence. |
| [astral-sh/ruff](https://github.com/astral-sh/ruff) | Deterministic configuration selection and explicit inheritance. |

## Relationship to upstream projects

The entries above are **research inputs**, not dependencies by default. Decisions derived from them are tracked in [`research/matrix/repository-comparison.yaml`](research/matrix/repository-comparison.yaml) using `ADOPT`, `ADAPT`, `EXPERIMENT`, `REJECT`, or `HISTORICAL` labels.

The project intentionally avoids wholesale prompt/configuration copying. If future work directly adapts or vendors upstream material, that change must record source, revision, license, local path, and modifications according to [`docs/PROVENANCE.md`](docs/PROVENANCE.md).

No endorsement or affiliation by any upstream project is implied.
