from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, Iterable, List, Optional, Set

import yaml

from .contracts import (
    ComputeResolution,
    DelegationRequest,
    PermissionResolution,
    PreflightReason,
    PreflightSummary,
    RecursionResolution,
    ResolvedExecutionPlan,
    ReviewResolution,
    RouteResolution,
    WriteLease,
)


@dataclass(frozen=True)
class ProviderPolicy:
    provider: str
    model_provider: str
    roles: Dict[str, dict]


@dataclass(frozen=True)
class PreflightResult:
    request: DelegationRequest
    decision: str
    reasons: List[PreflightReason]
    resolved_model: Optional[str]
    resolved_effort: Optional[str]
    recursive_delegation_allowed: bool
    effective_review_required: bool
    capability_snapshot_digest: Optional[str] = None

    def to_execution_plan(self, assignment_id: str) -> ResolvedExecutionPlan:
        if self.decision != "PASS":
            raise ValueError("execution plan requires a PASS preflight decision")
        if not isinstance(assignment_id, str) or not assignment_id.strip():
            raise ValueError("assignment_id must be a non-empty string")
        return ResolvedExecutionPlan(
            assignment_id=assignment_id,
            task=self.request.task,
            route=RouteResolution(
                mode=self.request.route_mode,
                role=self.request.role,
                profile=self.request.profile,
            ),
            compute=ComputeResolution(
                provider=self.request.provider,
                model=self.resolved_model,
                reasoning_effort=self.resolved_effort,
            ),
            permissions=PermissionResolution(
                write_owner=self.request.write_owner,
                write_scope=list(self.request.write_scope),
            ),
            recursion=RecursionResolution(
                parent_role=self.request.parent_role,
                depth=self.request.recursion_depth,
                recursive_delegation_allowed=self.recursive_delegation_allowed,
            ),
            review=ReviewResolution(
                required=self.effective_review_required,
                planned=self.request.review_planned,
            ),
            context_budget=self.request.context_budget,
            preflight=PreflightSummary(decision=self.decision, reasons=[]),
            capability_snapshot_digest=self.capability_snapshot_digest,
        )


def _load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected mapping in " + str(path))
    return value


def _load_provider_policies(root: Path) -> Dict[str, ProviderPolicy]:
    policies: Dict[str, ProviderPolicy] = {}
    adapters_root = root / "adapters"
    if not adapters_root.is_dir():
        return policies
    for path in sorted(adapters_root.glob("*/role-profiles.yaml")):
        data = _load_yaml(path)
        provider = data.get("provider")
        roles = data.get("roles")
        if not isinstance(provider, str) or not provider:
            continue
        if not isinstance(roles, dict):
            continue
        model_provider = data.get("model_provider", provider)
        if not isinstance(model_provider, str) or not model_provider:
            raise ValueError(f"{path}: model_provider must be a non-empty string")
        policies[provider] = ProviderPolicy(
            provider=provider,
            model_provider=model_provider,
            roles=dict(roles),
        )
    return policies


def _canonical_scope(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("write scope must be a string")
    if value != value.strip():
        raise ValueError("write scope must not have leading or trailing whitespace")
    raw = value.replace("\\", "/")
    if not raw:
        raise ValueError("write scope must be non-empty")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise ValueError("write scope must be repository-relative")
    parts: List[str] = []
    for part in raw.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("write scope must not contain parent traversal")
        if part.endswith((".", " ")):
            raise ValueError("write scope components must not end with dot or space")
        if re.search(r'[<>:"|?*\x00-\x1f]', part):
            raise ValueError("write scope contains a platform-ambiguous path character")
        parts.append(part)
    if not parts:
        return "."
    # Conflict detection is deliberately conservative across case-sensitive and
    # case-insensitive hosts so a plan cannot become unsafe when moved between them.
    return "/".join(parts).casefold()


def _scopes_overlap(left: str, right: str) -> bool:
    a = _canonical_scope(left)
    b = _canonical_scope(right)
    if a == "." or b == ".":
        return True
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


class DelegationPreflight:
    def __init__(
        self,
        *,
        agents: Dict[str, dict],
        profiles: Dict[str, dict],
        recursive_delegation_allowed: bool,
        review_required_for: Set[str],
        provider_policies: Optional[Dict[str, ProviderPolicy]] = None,
    ) -> None:
        self.agents = agents
        self.profiles = profiles
        self.recursive_delegation_allowed = recursive_delegation_allowed
        self.review_required_for = review_required_for
        self.provider_policies = provider_policies or {}

    @classmethod
    def from_repository(cls, root: Path) -> "DelegationPreflight":
        agents: Dict[str, dict] = {}
        for path in sorted((root / "agents" / "core").glob("*.yaml")):
            data = _load_yaml(path)
            agent_id = data.get("id")
            if isinstance(agent_id, str):
                agents[agent_id] = data
        profiles_doc = _load_yaml(root / "config" / "model-profiles.yaml")
        routing_doc = _load_yaml(root / "config" / "routing-policy.yaml")
        quality_gate = routing_doc.get("quality_gate") or {}
        review_required_for = quality_gate.get("review_required_for") or []
        return cls(
            agents=agents,
            profiles=dict(profiles_doc.get("profiles") or {}),
            recursive_delegation_allowed=bool(
                (routing_doc.get("limits") or {}).get("recursive_delegation", False)
            ),
            review_required_for={str(item) for item in review_required_for},
            provider_policies=_load_provider_policies(root),
        )

    def evaluate(
        self,
        request: DelegationRequest,
        *,
        disabled_roles: Optional[Set[str]] = None,
        active_write_leases: Optional[Iterable[WriteLease]] = None,
        required_capability_snapshot_digest: Optional[str] = None,
    ) -> PreflightResult:
        if not isinstance(request, DelegationRequest):
            raise ValueError("request must be a DelegationRequest")
        if disabled_roles is None:
            disabled_roles = set()
        elif not isinstance(disabled_roles, set) or not all(
            isinstance(item, str) and item for item in disabled_roles
        ):
            raise ValueError("disabled_roles must be a set of non-empty strings")
        if active_write_leases is None:
            active_write_leases = []
        else:
            if isinstance(active_write_leases, (str, bytes, dict)):
                raise ValueError("active_write_leases must be an iterable of WriteLease")
            try:
                active_write_leases = list(active_write_leases)
            except TypeError as exc:
                raise ValueError("active_write_leases must be an iterable of WriteLease") from exc
        rejects: List[PreflightReason] = []
        escalations: List[PreflightReason] = []

        if required_capability_snapshot_digest is not None:
            if (
                not isinstance(required_capability_snapshot_digest, str)
                or not re.fullmatch(r"[0-9a-f]{64}", required_capability_snapshot_digest)
            ):
                raise ValueError("required_capability_snapshot_digest must be lowercase SHA-256 hex")
            if request.capability_snapshot_digest != required_capability_snapshot_digest:
                rejects.append(PreflightReason(
                    code="capability_snapshot_mismatch",
                    message="delegation request is not bound to the current capability snapshot",
                    severity="error",
                ))

        def reject(code: str, message: str) -> None:
            rejects.append(PreflightReason(code=code, message=message, severity="error"))

        def escalate(code: str, message: str) -> None:
            escalations.append(PreflightReason(code=code, message=message, severity="escalate"))

        agent = self.agents.get(request.role)
        if agent is None:
            reject("role_not_found", "requested role is not registered")
        elif request.role in disabled_roles:
            reject("role_disabled", "requested role is disabled")

        if request.route_mode != "delegate":
            reject("route_not_delegated", "delegation preflight only accepts delegated routes")
        if not request.child_agent_capable:
            reject("child_agent_unavailable", "provider runtime does not expose child-agent capability")

        profile = self.profiles.get(request.profile)
        if profile is None:
            reject("profile_not_found", "requested compute profile is not registered")
        elif agent is not None:
            compatible = agent.get("compatible_profiles") or []
            if request.profile not in compatible:
                reject("role_profile_incompatible", "role does not permit the requested compute profile")

        provider_policy = self.provider_policies.get(request.provider)
        model_provider = provider_policy.model_provider if provider_policy else request.provider
        resolved_model: Optional[str] = None
        resolved_effort: Optional[str] = None
        if profile is not None:
            candidates = profile.get("candidate_models") or {}
            if isinstance(candidates, dict):
                candidate = candidates.get(model_provider)
                if isinstance(candidate, str) and candidate:
                    resolved_model = candidate
            reasoning = profile.get("reasoning")
            if isinstance(reasoning, str):
                resolved_effort = reasoning
            if provider_policy is not None:
                role_policy = provider_policy.roles.get(request.role)
                if isinstance(role_policy, dict) and role_policy.get("profile") == request.profile:
                    override = role_policy.get("reasoning_override")
                    if isinstance(override, str) and override:
                        resolved_effort = override
            if resolved_model is None:
                reject("model_resolution_unavailable", "provider has no model mapping for the requested profile")

        if not isinstance(request.recursion_depth, int) or isinstance(request.recursion_depth, bool) or request.recursion_depth < 0:
            reject("invalid_recursion_depth", "recursion depth must be a non-negative integer")
        elif request.recursion_depth > 0 and not self.recursive_delegation_allowed:
            reject("recursive_delegation_forbidden", "recursive delegation is disabled by repository policy")
        if request.parent_role and request.parent_role == request.role:
            reject("self_recursion_forbidden", "a role may not delegate to itself without an explicit contract")

        access = (agent or {}).get("access") or {}
        write_capable = bool(access.get("write", False))
        request_scopes_valid = True
        if request.write_scope:
            for scope in request.write_scope:
                try:
                    _canonical_scope(scope)
                except ValueError as exc:
                    reject("invalid_write_scope", str(exc))
                    request_scopes_valid = False
                    break
        if request.write_scope and agent is not None and not write_capable:
            reject("write_scope_forbidden", "read-only role may not receive a write scope")
        if write_capable and not request.write_scope:
            reject("write_scope_required", "write-capable delegation requires a non-empty approved write scope")
        if write_capable and not request.write_owner:
            reject("write_owner_required", "write-capable delegation requires an explicit write owner")

        leases_valid = True
        for lease in active_write_leases:
            if not isinstance(lease, WriteLease):
                reject("invalid_active_write_lease", "active write lease must use the WriteLease contract")
                leases_valid = False
                break
            if not lease.owner.strip() or not lease.scope:
                reject("invalid_active_write_lease", "active write lease must have an owner and non-empty scope")
                leases_valid = False
                break
            for scope in lease.scope:
                try:
                    _canonical_scope(scope)
                except ValueError as exc:
                    reject("invalid_active_write_lease", str(exc))
                    leases_valid = False
                    break
            if not leases_valid:
                break

        if request.write_scope and request_scopes_valid and leases_valid:
            for lease in active_write_leases:
                if lease.owner == request.write_owner:
                    continue
                if any(
                    _scopes_overlap(scope, leased)
                    for scope in request.write_scope
                    for leased in lease.scope
                ):
                    reject("write_scope_conflict", "requested write scope overlaps an active writer lease")
                    break

        if request.context_budget.estimated_input_tokens > request.context_budget.max_input_tokens:
            escalate("context_budget_exceeded", "estimated input exceeds the approved context budget")
        effective_review_required = (
            request.review_required or request.risk_class in self.review_required_for
        )
        if effective_review_required and not request.review_planned:
            escalate("required_review_unplanned", "independent review is required but not planned")

        if rejects:
            decision = "REJECT"
            reasons = rejects + escalations
        elif escalations:
            decision = "ESCALATE"
            reasons = escalations
        else:
            decision = "PASS"
            reasons = []

        return PreflightResult(
            request=request,
            decision=decision,
            reasons=reasons,
            resolved_model=resolved_model,
            resolved_effort=resolved_effort,
            recursive_delegation_allowed=self.recursive_delegation_allowed,
            effective_review_required=effective_review_required,
            capability_snapshot_digest=request.capability_snapshot_digest,
        )
