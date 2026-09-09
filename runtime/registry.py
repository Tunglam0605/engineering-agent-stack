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

    @staticmethod
    def _validate_limit(name: str, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(name + " must be a positive integer")

    def summary(
        self,
        *,
        soft_limit: int = 6,
        hard_limit: int = 8,
        goal_id: Optional[str] = None,
    ) -> dict:
        self._validate_limit("soft_limit", soft_limit)
        self._validate_limit("hard_limit", hard_limit)
        if hard_limit < soft_limit:
            raise ValueError("hard_limit must be greater than or equal to soft_limit")
        if goal_id is not None and (not isinstance(goal_id, str) or not goal_id.strip()):
            raise ValueError("goal_id must be null or a non-empty string")

        all_agents = list(self._agents.values())
        observed_goals = sorted(
            {item.parent_assignment_id for item in all_agents if item.parent_assignment_id is not None}
        )
        if goal_id is None and len(observed_goals) > 1:
            raise ValueError("goal_id is required when registry contains multiple parent goals")
        if goal_id is not None and goal_id not in observed_goals:
            raise ValueError("goal_id was not found in registry: " + goal_id)
        effective_goal = goal_id if goal_id is not None else (observed_goals[0] if observed_goals else None)
        agents = (
            [item for item in all_agents if item.parent_assignment_id == effective_goal]
            if effective_goal is not None
            else all_agents
        )
        active_states = {"pending", "running"}
        terminal_states = {"completed", "failed", "blocked"}
        by_role: Dict[str, int] = {}
        for item in agents:
            by_role[item.role] = by_role.get(item.role, 0) + 1

        total = len(agents)
        if total >= hard_limit:
            budget_state = "hard_limit"
        elif total >= soft_limit:
            budget_state = "soft_limit"
        else:
            budget_state = "within_budget"

        return {
            "goal_id": effective_goal,
            "total_assignments": total,
            "active_assignments": sum(item.state in active_states for item in agents),
            "terminal_assignments": sum(item.state in terminal_states for item in agents),
            "completed_assignments": sum(item.state == "completed" for item in agents),
            "failed_assignments": sum(item.state == "failed" for item in agents),
            "blocked_assignments": sum(item.state == "blocked" for item in agents),
            "by_role": {key: by_role[key] for key in sorted(by_role)},
            "soft_limit": soft_limit,
            "hard_limit": hard_limit,
            "budget_state": budget_state,
        }

    def summary_text(
        self,
        *,
        soft_limit: int = 6,
        hard_limit: int = 8,
        goal_id: Optional[str] = None,
    ) -> str:
        summary = self.summary(soft_limit=soft_limit, hard_limit=hard_limit, goal_id=goal_id)
        roles = ",".join(
            key + "=" + str(value) for key, value in summary["by_role"].items()
        ) or "none"
        return (
            "SUMMARY goal={goal} total={total_assignments} active={active_assignments} "
            "completed={completed_assignments} failed={failed_assignments} blocked={blocked_assignments} "
            "terminal={terminal_assignments} budget={budget_state} "
            "soft={soft_limit} hard={hard_limit} roles={roles}"
        ).format(goal=summary["goal_id"] or "?", roles=roles, **summary)

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
