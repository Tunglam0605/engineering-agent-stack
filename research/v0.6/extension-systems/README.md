# Extension systems deep audit

Status: **research only; no implementation**.

Deeper source inspection used these pinned snapshots: oh-my-pi `daf07999c2fee9b22edc7bf8fea1fb6272e0df5e`, Superpowers `b36e0829c6d0140e93cfef2ca599b1b07d4a7797`, oh-my-codex `304fb3b4825c4132c273732b14d2d5e86b54f8e3`, Spec Kit `4a7341a93d944d6efe153b71da4a1adb9c2b578c`, OpenAI Agents SDK `02c205f9574c765a265ce102dc55da81cdd74b89`, MCP `e76e9c572c6f2bfcb730357101acc90f2f802e02`, Ruff `e7adf82ff005f3ab3051c363464cf65bf8a6e2f3`.

## Normalized findings

- **ADAPT** oh-my-pi's separation of capability discovery from executable extension loading; **REJECT** its executable plugin runtime for v0.6.
- **ADAPT** Superpowers-style composable skills and trigger/pressure evaluation; do not load an entire catalog by default.
- **ADAPT** OMX managed ownership/collision discipline; a child process inheriting environment is process isolation, **not a sandbox**.
- **ADOPT/ADAPT** Spec Kit manifest compatibility, path/archive safety and explicit config layers; its instruction-returning hooks are **not enforcement gates**.
- **ADOPT** OpenAI Agents SDK's collision/path checks and boundary-specific guardrail semantics; metadata/tool availability never grants EAS authority.
- **ADOPT** MCP's advertisement-versus-authorization distinction.
- **ADOPT** Ruff-style deterministic resolution/cycle diagnostics; **REJECT** hidden broad config cascades.

## v0.6 consequence

The evidence favors a **declarative local capability package**, not a general plugin runtime. Initial flow should be `discover -> parse -> validate -> resolve -> explain/hash`. Packages may describe skills/rules/settings/presets and requirements, but cannot define agents, models, permissions, commands, hooks, installers or MCP servers. See [comparison matrix](comparison-matrix.md).
