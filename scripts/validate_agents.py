#!/usr/bin/env python3
"""Validate canonical core-agent contracts and cross-file routing/profile invariants."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "agents" / "core"
SCHEMA_PATH = ROOT / "schemas" / "agent-contract.yaml"
MODEL_PROFILES_PATH = ROOT / "config" / "model-profiles.yaml"
ROUTING_POLICY_PATH = ROOT / "config" / "routing-policy.yaml"
CODEX_ROLE_MAP_PATH = ROOT / "adapters" / "codex" / "role-profiles.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def require_list(agent_id: str, field: str, value: Any, failures: list[str]) -> None:
    if not isinstance(value, list) or not value:
        failures.append(f"{agent_id}: {field} must be a non-empty list")


def validate_role_profile_pair(
    label: str,
    role: Any,
    profile: Any,
    agents: dict[str, dict[str, Any]],
    known_profiles: set[str],
    failures: list[str],
) -> None:
    if not isinstance(role, str) or role not in agents:
        failures.append(f"{label}: unknown role {role!r}")
        return
    if not isinstance(profile, str) or profile not in known_profiles:
        failures.append(f"{label}: unknown profile {profile!r}")
        return
    compatible = agents[role].get("compatible_profiles", [])
    if profile not in compatible:
        failures.append(
            f"{label}: role {role!r} is not compatible with profile {profile!r}; "
            f"allowed={compatible!r}"
        )


def main() -> int:
    contract = load_yaml(SCHEMA_PATH)
    model_profiles = load_yaml(MODEL_PROFILES_PATH)
    routing_policy = load_yaml(ROUTING_POLICY_PATH)
    codex_role_map = load_yaml(CODEX_ROLE_MAP_PATH)

    required = contract.get("required_fields", [])
    known_profiles = set(model_profiles.get("profiles", {}))

    failures: list[str] = []
    agents: dict[str, dict[str, Any]] = {}

    agent_paths = sorted(CORE_DIR.glob("*.yaml"))
    if not agent_paths:
        print("ERROR: no canonical core agents found")
        return 2

    for path in agent_paths:
        agent = load_yaml(path)
        agent_id = agent.get("id")
        if not isinstance(agent_id, str) or not agent_id:
            failures.append(f"{path.name}: id must be a non-empty string")
            continue

        if agent_id in agents:
            failures.append(f"duplicate agent id: {agent_id}")
        agents[agent_id] = agent

        if path.stem != agent_id:
            failures.append(f"{agent_id}: filename must be {agent_id}.yaml")

        for field in required:
            if field not in agent:
                failures.append(f"{agent_id}: missing required field {field}")

        if not isinstance(agent.get("mission"), str) or not agent["mission"].strip():
            failures.append(f"{agent_id}: mission must be a non-empty string")

        for field in ("non_goals", "inputs", "escalation", "completion_evidence"):
            require_list(agent_id, field, agent.get(field), failures)

        access = agent.get("access")
        if not isinstance(access, dict):
            failures.append(f"{agent_id}: access must be a mapping")
        else:
            for key in ("read", "write", "test", "network"):
                if key not in access:
                    failures.append(f"{agent_id}: access.{key} is required")
            if access.get("read") is not True:
                failures.append(
                    f"{agent_id}: core roles must currently declare read: true"
                )

        output = agent.get("output_contract")
        if not isinstance(output, dict):
            failures.append(f"{agent_id}: output_contract must be a mapping")
        else:
            if output.get("format") != "assignment-result-v1":
                failures.append(
                    f"{agent_id}: output_contract.format must be assignment-result-v1"
                )
            budget = output.get("max_summary_tokens")
            if not isinstance(budget, int) or budget <= 0:
                failures.append(
                    f"{agent_id}: output_contract.max_summary_tokens must be a positive integer"
                )

        compatible = agent.get("compatible_profiles")
        require_list(agent_id, "compatible_profiles", compatible, failures)
        if isinstance(compatible, list):
            unknown = sorted(set(compatible) - known_profiles)
            if unknown:
                failures.append(
                    f"{agent_id}: unknown compatible profile(s): {', '.join(unknown)}"
                )

    for rule in routing_policy.get("rules", []):
        if rule.get("action") != "delegate":
            continue
        label = f"routing rule {rule.get('id', '<unnamed>')}"
        validate_role_profile_pair(
            label,
            rule.get("role"),
            rule.get("profile"),
            agents,
            known_profiles,
            failures,
        )

    codex_roles = codex_role_map.get("roles")
    if not isinstance(codex_roles, dict):
        failures.append("Codex role-profiles.yaml: roles must be a mapping")
    else:
        missing = sorted(set(agents) - set(codex_roles))
        extra = sorted(set(codex_roles) - set(agents))
        if missing:
            failures.append(f"Codex role map missing role(s): {', '.join(missing)}")
        if extra:
            failures.append(f"Codex role map has unknown role(s): {', '.join(extra)}")

        for role, cfg in codex_roles.items():
            if not isinstance(cfg, dict):
                failures.append(f"Codex role {role!r}: mapping must be an object")
                continue
            validate_role_profile_pair(
                f"Codex role {role}",
                role,
                cfg.get("profile"),
                agents,
                known_profiles,
                failures,
            )
            override = cfg.get("reasoning_override")
            if override is not None and (
                not isinstance(override, str) or not override.strip()
            ):
                failures.append(
                    f"Codex role {role!r}: reasoning_override must be a non-empty string"
                )

    if failures:
        print(f"FAIL: {len(failures)} agent/routing contract violation(s).")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        f"PASS: {len(agent_paths)} canonical core agents satisfy the contract; "
        "routing and Codex role mappings reference compatible semantic profiles."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
