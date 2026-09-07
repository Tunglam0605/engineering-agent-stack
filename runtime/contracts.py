from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List, Optional

SUPPORTED_AGENT_STATES = {"pending", "running", "completed", "failed", "blocked"}


@dataclass(frozen=True)
class ContextBudget:
    max_input_tokens: int
    estimated_input_tokens: int

    def __post_init__(self) -> None:
        if not isinstance(self.max_input_tokens, int) or isinstance(self.max_input_tokens, bool):
            raise ValueError("max_input_tokens must be an integer")
        if not isinstance(self.estimated_input_tokens, int) or isinstance(self.estimated_input_tokens, bool):
            raise ValueError("estimated_input_tokens must be an integer")
        if self.max_input_tokens < 0 or self.estimated_input_tokens < 0:
            raise ValueError("context token estimates must be non-negative")


@dataclass(frozen=True)
class WriteLease:
    owner: str
    scope: List[str]

    def __post_init__(self) -> None:
        if not isinstance(self.owner, str) or not self.owner.strip():
            raise ValueError("owner must be a non-empty string")
        if not isinstance(self.scope, list) or not self.scope or not all(
            isinstance(item, str) and item.strip() for item in self.scope
        ):
            raise ValueError("scope must be a list of strings")


@dataclass(frozen=True)
class DelegationRequest:
    task: str
    route_mode: str
    role: str
    profile: str
    provider: str
    child_agent_capable: bool
    write_owner: Optional[str]
    write_scope: List[str]
    parent_role: Optional[str]
    recursion_depth: int
    context_budget: ContextBudget
    review_required: bool
    review_planned: bool
    risk_class: str = "normal"

    def __post_init__(self) -> None:
        for field_name in ("task", "route_mode", "role", "profile", "provider", "risk_class"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if type(self.child_agent_capable) is not bool:
            raise ValueError("child_agent_capable must be a boolean")
        if type(self.review_required) is not bool:
            raise ValueError("review_required must be a boolean")
        if type(self.review_planned) is not bool:
            raise ValueError("review_planned must be a boolean")
        if not isinstance(self.recursion_depth, int) or isinstance(self.recursion_depth, bool):
            raise ValueError("recursion_depth must be an integer")
        if not isinstance(self.context_budget, ContextBudget):
            raise ValueError("context_budget must be a ContextBudget")
        for field_name in ("write_owner", "parent_role"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{field_name} must be null or a non-empty string")
        if not isinstance(self.write_scope, list) or not all(
            isinstance(item, str) and item.strip() for item in self.write_scope
        ):
            raise ValueError("write_scope must be a list of strings")


@dataclass(frozen=True)
class PreflightReason:
    code: str
    message: str
    severity: str


@dataclass(frozen=True)
class PreflightSummary:
    decision: str
    reasons: List[PreflightReason] = field(default_factory=list)


@dataclass(frozen=True)
class RouteResolution:
    mode: str
    role: str
    profile: str


@dataclass(frozen=True)
class ComputeResolution:
    provider: str
    model: Optional[str]
    reasoning_effort: Optional[str]


@dataclass(frozen=True)
class PermissionResolution:
    write_owner: Optional[str]
    write_scope: List[str]


@dataclass(frozen=True)
class RecursionResolution:
    parent_role: Optional[str]
    depth: int
    recursive_delegation_allowed: bool


@dataclass(frozen=True)
class ReviewResolution:
    required: bool
    planned: bool


@dataclass(frozen=True)
class ResolvedExecutionPlan:
    assignment_id: str
    task: str
    route: RouteResolution
    compute: ComputeResolution
    permissions: PermissionResolution
    recursion: RecursionResolution
    review: ReviewResolution
    context_budget: ContextBudget
    preflight: PreflightSummary

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionTelemetry:
    duration_ms: Optional[int] = None
    tokens: Optional[int] = None
    latency_ms: Optional[int] = None

    def __post_init__(self) -> None:
        for field_name in ("duration_ms", "tokens", "latency_ms"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
                raise ValueError(f"{field_name} must be an integer or null")
            if isinstance(value, int) and value < 0:
                raise ValueError(f"{field_name} must be non-negative")


@dataclass
class AgentStatus:
    assignment_id: str
    task: str
    state: str
    role: str
    profile: str
    provider: Optional[str]
    model: Optional[str]
    parent_assignment_id: Optional[str]
    write_owner: Optional[str]
    write_scope: List[str]
    telemetry: ExecutionTelemetry = field(default_factory=ExecutionTelemetry)

    def __post_init__(self) -> None:
        for field_name in ("assignment_id", "task", "role", "profile"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.state, str) or self.state not in SUPPORTED_AGENT_STATES:
            raise ValueError("unsupported agent state: " + str(self.state))
        for field_name in ("provider", "model", "parent_assignment_id", "write_owner"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{field_name} must be null or a non-empty string")
        if not isinstance(self.write_scope, list) or not all(
            isinstance(item, str) and item.strip() for item in self.write_scope
        ):
            raise ValueError("write_scope must be a list of strings")
        if not isinstance(self.telemetry, ExecutionTelemetry):
            raise ValueError("telemetry must be an ExecutionTelemetry")

    def as_dict(self) -> dict:
        return {
            "assignment_id": self.assignment_id,
            "state": self.state,
            "task": self.task,
            "role": self.role,
            "profile": self.profile,
            "provider": self.provider,
            "model": self.model,
            "parent_assignment_id": self.parent_assignment_id,
            "write": {"owner": self.write_owner, "scope": list(self.write_scope)},
            "telemetry": asdict(self.telemetry),
        }
