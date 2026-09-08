# huggingface/smolagents

Pinned upstream: `30bb1161095dbae2271e6bc3cc4c219cc3897a57` (main tip inspected by cloning). Source: https://github.com/huggingface/smolagents

## Problem

smolagents is a Python framework for model-driven agents using tool calls or generated code. Roles and loops are in `src/smolagents/agents.py`; model interfaces in `models.py`; typed actions and memory in `agent_types.py` and `memory.py`.

## Exact implementation observations

- `src/smolagents/tools.py` defines tools, `ToolCollection`, loading, and schema generation; `tool_validation.py` validates signatures. Built-ins are in `default_tools.py`; MCP loading/discovery is in `mcp_client.py`.
- Execution boundaries are `local_python_executor.py` (AST validation/restricted execution) and `remote_executors.py` (E2B, Modal, Blaxel, container backends), wired by `agents.py`.
- `serialization.py` implements JSON/YAML save and reconstruction; `cli.py` and `pyproject.toml` define package/CLI metadata. Reconstruction is executable and requires trusted inputs.
- `trust_remote_code` loading paths are in `tools.py` and `mcp_client.py`. Tests cover them in `tests/test_tools.py`, `tests/test_mcp_client.py`, and `tests/test_serialization.py`.
- Agent/tool behavior: `tests/test_agents.py`, `tests/test_tools.py`; executor restrictions: `tests/test_local_python_executor.py`, `tests/test_remote_executors.py`; serialization round trips: `tests/test_serialization.py`; MCP: `tests/test_mcp_client.py`; import and CLI metadata: `tests/test_import.py`, `tests/test_cli.py`.

## Decisions for EAS v0.6

- **ADOPT:** explicit typed tool/action contracts, capability metadata, and boundary-focused tests.
- **ADAPT:** lazy/minimal tool exposure: start with a declared set, then require an auditable capability grant before loading collections. Keep role identity provider-neutral; isolate model/executor adapters.
- **EXPERIMENT:** a later adapter could run generated code under signed provenance, isolated budgets, and a separately governed executor policy.
- **REJECT:** executable extension plugins in the v0.6 contract, implicit provider/model authority, and unconstrained remote dependency solving.

Executable extension code is out of v0.6 because Python definitions, remote tools, MCP servers, and serialized classes become runnable capabilities, expanding the trust boundary. Lazy minimal exposure provides routing and review evidence before loading code; v0.6 therefore freezes declarative contracts and defers executable loading to a governed adapter.

Local impact: `research/v0.6/contract-freeze.md`. No source or prompts copied; observations are paraphrased and provenance recorded here.
