from __future__ import annotations

import json
from typing import Dict, Optional

from .contracts import AgentStatus, ExecutionTelemetry, SUPPORTED_AGENT_STATES


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, AgentStatus] = {}

    def add(self, status: AgentStatus) -> None:
        if status.assignment_id in self._agents:
            raise ValueError("duplicate assignment id: " + status.assignment_id)
        self._agents[status.assignment_id] = status

    def transition(
        self,
        assignment_id: str,
        state: str,
        *,
        telemetry: Optional[ExecutionTelemetry] = None,
    ) -> None:
        if state not in SUPPORTED_AGENT_STATES:
            raise ValueError("unsupported agent state: " + state)
        if assignment_id not in self._agents:
            raise KeyError(assignment_id)
        status = self._agents[assignment_id]
        status.state = state
        if telemetry is not None:
            if not isinstance(telemetry, ExecutionTelemetry):
                raise ValueError("telemetry must be an ExecutionTelemetry")
            status.telemetry = telemetry

    @classmethod
    def from_dict(cls, payload: dict) -> "AgentRegistry":
        agents = payload.get("agents")
        if not isinstance(agents, list):
            raise ValueError("status snapshot must contain an agents list")
        registry = cls()
        for raw in agents:
            if not isinstance(raw, dict):
                raise ValueError("agent status entry must be an object")
            write = raw.get("write")
            telemetry = raw.get("telemetry")
            if not isinstance(write, dict):
                raise ValueError("write must be an object")
            if not isinstance(telemetry, dict):
                raise ValueError("telemetry must be an object")
            registry.add(
                AgentStatus(
                    assignment_id=raw["assignment_id"],
                    task=raw["task"],
                    state=raw["state"],
                    role=raw["role"],
                    profile=raw["profile"],
                    provider=raw.get("provider"),
                    model=raw.get("model"),
                    parent_assignment_id=raw.get("parent_assignment_id"),
                    write_owner=write.get("owner"),
                    write_scope=write.get("scope"),
                    telemetry=ExecutionTelemetry(
                        duration_ms=telemetry.get("duration_ms"),
                        tokens=telemetry.get("tokens"),
                        latency_ms=telemetry.get("latency_ms"),
                    ),
                )
            )
        return registry

    def as_dict(self) -> dict:
        return {"agents": [self._agents[key].as_dict() for key in sorted(self._agents)]}

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _known(value: object) -> str:
        return "?" if value is None else str(value)

    def to_text(self) -> str:
        lines = []
        for key in sorted(self._agents):
            item = self._agents[key]
            provider_model = (item.provider or "?") + ":" + (item.model or "?")
            telemetry = item.telemetry
            lines.append(
                f"{item.assignment_id} {item.state} {item.role}/{item.profile} {provider_model} "
                f"tokens={self._known(telemetry.tokens)} "
                f"latency={self._known(telemetry.latency_ms)} "
                f"duration={self._known(telemetry.duration_ms)}"
            )
        return "\n".join(lines)
