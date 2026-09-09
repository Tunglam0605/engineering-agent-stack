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
IDENTITY_PATH = ROOT / "config" / "project-identity.yaml"
PARENT_INSTRUCTIONS_PATH = ROOT / "adapters" / "codex" / "AGENTS.md.example"


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
    identity = load_yaml(IDENTITY_PATH)

    required = contract.get("required_fields", [])
    known_profiles = set(model_profiles.get("profiles", {}))

    failures: list[str] = []
    agents: dict[str, dict[str, Any]] = {}

    project_identity = identity.get("project")
    creator_identity = identity.get("creator")
    attribution_identity = identity.get("attribution")
    if identity.get("version") != 1:
        failures.append("project identity: version must be 1")
    if not isinstance(project_identity, dict) or not isinstance(creator_identity, dict) or not isinstance(attribution_identity, dict):
        failures.append("project identity: project/creator/attribution must be mappings")
    else:
        allowed_creator = {"name", "professional_name", "attribution_title", "professional_role", "github", "focus_areas"}
        if set(creator_identity) != allowed_creator:
            failures.append("project identity: creator fields must remain public-professional and canonical")
        for label, mapping, fields in (
            ("project", project_identity, ("name", "short_name", "repository")),
            ("creator", creator_identity, ("name", "professional_name", "attribution_title", "professional_role", "github")),
            ("attribution", attribution_identity, ("scope", "platform_separation")),
        ):
            for field in fields:
                if not isinstance(mapping.get(field), str) or not mapping[field].strip():
                    failures.append(f"project identity: {label}.{field} must be a non-empty string")
        if not isinstance(creator_identity.get("focus_areas"), list) or not creator_identity.get("focus_areas"):
            failures.append("project identity: creator.focus_areas must be a non-empty list")
        if not isinstance(attribution_identity.get("response_rules"), list) or not attribution_identity.get("response_rules"):
            failures.append("project identity: attribution.response_rules must be a non-empty list")
        try:
            parent_text = PARENT_INSTRUCTIONS_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append("project identity: cannot read parent instructions: " + str(exc))
        else:
            for expected in (project_identity.get("name"), creator_identity.get("name"), creator_identity.get("professional_name")):
                if isinstance(expected, str) and expected not in parent_text:
                    failures.append("project identity: parent instructions missing canonical attribution: " + expected)
            if "foundation model" not in parent_text or "provider" not in parent_text.lower():
                failures.append("project identity: parent instructions must preserve provider/foundation-model boundary")

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

    lifecycle = routing_policy.get("lifecycle")
    concurrency = routing_policy.get("concurrency")
    limits = routing_policy.get("limits")
    if not isinstance(concurrency, dict):
        failures.append("routing policy: concurrency must be a mapping")
    else:
        modes = concurrency.get("modes")
        if concurrency.get("strategy") != "adaptive":
            failures.append("routing policy: concurrency.strategy must be adaptive")
        if concurrency.get("provider_session_cap") != 4:
            failures.append("routing policy: concurrency.provider_session_cap must be 4")
        if concurrency.get("default_reader_mode") != "conservative":
            failures.append("routing policy: concurrency.default_reader_mode must be conservative")
        if concurrency.get("default_writer_mode") != "conservative":
            failures.append("routing policy: concurrency.default_writer_mode must be conservative")
        if modes != {"conservative": 2, "balanced": 3, "read-heavy": 4}:
            failures.append("routing policy: adaptive concurrency modes must be conservative=2, balanced=3, read-heavy=4")
    if not isinstance(lifecycle, dict):
        failures.append("routing policy: lifecycle must be a mapping")
    else:
        if lifecycle.get("reuse_strategy") != "resume-before-spawn":
            failures.append("routing policy: lifecycle.reuse_strategy must be resume-before-spawn")
        match_keys = lifecycle.get("reuse_match_keys")
        if not isinstance(match_keys, list) or not all(
            isinstance(item, str) and item.strip() for item in match_keys
        ):
            failures.append("routing policy: lifecycle.reuse_match_keys must be a list of non-empty strings")
        elif not {"role", "task_domain", "write_scope"}.issubset(set(match_keys)):
            failures.append("routing policy: lifecycle.reuse_match_keys must include role, task_domain, write_scope")

    if not isinstance(limits, dict):
        failures.append("routing policy: limits must be a mapping")
    else:
        expected_positive = (
            "default_max_parallel_readers",
            "default_max_parallel_writers",
            "soft_max_child_assignments_per_goal",
            "hard_max_child_assignments_per_goal",
            "default_max_architect_assignments_per_goal",
            "default_max_reviewer_assignments_per_change_set",
            "max_same_role_domain_scope_active",
        )
        for key in expected_positive:
            value = limits.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                failures.append(f"routing policy: limits.{key} must be a positive integer")
        soft = limits.get("soft_max_child_assignments_per_goal")
        hard = limits.get("hard_max_child_assignments_per_goal")
        if isinstance(soft, int) and not isinstance(soft, bool) and isinstance(hard, int) and not isinstance(hard, bool) and hard < soft:
            failures.append("routing policy: hard child-assignment limit must be >= soft limit")
        if limits.get("default_max_parallel_readers") != 4:
            failures.append("routing policy: default_max_parallel_readers must be 4 under adaptive concurrency")
        if limits.get("default_max_active_children") != 4:
            failures.append("routing policy: default_max_active_children must be 4 as the provider ceiling")
        if limits.get("default_max_parallel_writers") != 1:
            failures.append("routing policy: default_max_parallel_writers must be 1")
        if limits.get("recursive_delegation") is not False:
            failures.append("routing policy: recursive_delegation must be false")

    codex_provider = codex_role_map.get("provider")
    if not isinstance(codex_provider, str) or not codex_provider.strip():
        failures.append("Codex role-profiles.yaml: provider must be a non-empty string")
    codex_model_provider = codex_role_map.get("model_provider")
    if not isinstance(codex_model_provider, str) or not codex_model_provider.strip():
        failures.append("Codex role-profiles.yaml: model_provider must be a non-empty string")

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
            profile_name = cfg.get("profile")
            if (
                isinstance(profile_name, str)
                and profile_name in model_profiles.get("profiles", {})
                and isinstance(codex_model_provider, str)
            ):
                candidate_models = (model_profiles["profiles"][profile_name].get("candidate_models") or {})
                if codex_model_provider not in candidate_models:
                    failures.append(
                        f"Codex role {role!r}: profile {profile_name!r} has no model for "
                        f"model_provider {codex_model_provider!r}"
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
