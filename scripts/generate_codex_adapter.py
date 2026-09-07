#!/usr/bin/env python3
"""Generate Codex role files from provider-neutral canonical agent definitions."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import sys
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility for Windows acceptance.
    import tomli as tomllib

import yaml

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "agents" / "core"
MODEL_PROFILES_PATH = ROOT / "config" / "model-profiles.yaml"
ROLE_PROFILES_PATH = ROOT / "adapters" / "codex" / "role-profiles.yaml"
OUTPUT_DIR = ROOT / "adapters" / "codex" / "agents"
CONFIG_EXAMPLE_PATH = ROOT / "adapters" / "codex" / "config.toml.example"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_agents() -> dict[str, dict[str, Any]]:
    agents: dict[str, dict[str, Any]] = {}
    for path in sorted(CORE_DIR.glob("*.yaml")):
        agent = load_yaml(path)
        role_id = agent.get("id")
        if not isinstance(role_id, str) or not role_id:
            raise ValueError(f"{path} has no valid id")
        if role_id in agents:
            raise ValueError(f"duplicate role id: {role_id}")
        agents[role_id] = agent
    if not agents:
        raise ValueError("no canonical core agents found")
    return agents


def sandbox_for(access: dict[str, Any]) -> str:
    return "read-only" if access.get("write", False) is False else "workspace-write"


def sentence(text: str) -> str:
    return text.rstrip(".") + "."


def build_instructions(agent: dict[str, Any]) -> str:
    output_contract = agent["output_contract"]
    lines = [
        f"Role: {agent['id']}.",
        f"Mission: {agent['mission']}",
        "",
        "Boundaries:",
    ]
    lines.extend(
        f"- Out of scope: {sentence(item)}" for item in agent.get("non_goals", [])
    )
    lines.extend(
        [
            "",
            "Execution rules:",
            "- Stay inside the assigned scope and do not silently broaden it.",
            "- Do not spawn or orchestrate child agents unless the parent explicitly authorizes delegation.",
            "- Prefer targeted evidence and the narrowest meaningful validation.",
            "- Return concise evidence; do not dump raw transcripts, full source files, or repetitive logs.",
            "",
            f"Result contract: {output_contract.get('format', 'assignment-result-v1')}.",
            f"Summary budget: at most {output_contract.get('max_summary_tokens', 'bounded')} tokens.",
            "Report confidence, evidence, changed paths (if any), validation performed, and escalation/blockers.",
            "",
            "Escalate when:",
        ]
    )
    lines.extend(f"- {sentence(item)}" for item in agent.get("escalation", []))
    lines.extend(["", "Completion requires:"])
    lines.extend(
        f"- {sentence(item)}" for item in agent.get("completion_evidence", [])
    )
    return "\n".join(lines)


def resolve_role_compute(
    role_id: str,
    agent: dict[str, Any],
    role_map: dict[str, Any],
    model_profiles: dict[str, Any],
) -> tuple[str, str, str]:
    role_cfg = role_map["roles"].get(role_id)
    if not isinstance(role_cfg, dict):
        raise ValueError(f"missing Codex profile mapping for role {role_id!r}")

    profile_name = role_cfg["profile"]
    if profile_name not in agent["compatible_profiles"]:
        raise ValueError(
            f"role {role_id!r} maps to incompatible profile {profile_name!r}; "
            f"allowed={agent['compatible_profiles']!r}"
        )

    profile = model_profiles["profiles"][profile_name]
    model = profile["candidate_models"]["openai"]
    reasoning = role_cfg.get("reasoning_override", profile["reasoning"])
    return profile_name, model, reasoning


def render_role(
    agent: dict[str, Any],
    role_map: dict[str, Any],
    model_profiles: dict[str, Any],
) -> str:
    _, model, reasoning = resolve_role_compute(
        agent["id"], agent, role_map, model_profiles
    )
    content = "\n".join(
        [
            "# GENERATED FILE — edit canonical YAML/config, then run scripts/generate_codex_adapter.py.",
            f"name = {json.dumps(agent['id'])}",
            f"description = {json.dumps(agent['mission'])}",
            f"model = {json.dumps(model)}",
            f"model_reasoning_effort = {json.dumps(reasoning)}",
            f"sandbox_mode = {json.dumps(sandbox_for(agent['access']))}",
            f"developer_instructions = {json.dumps(build_instructions(agent), ensure_ascii=False)}",
            "",
        ]
    )
    tomllib.loads(content)
    return content


def render_config_example(
    agents: dict[str, dict[str, Any]], model_profiles: dict[str, Any]
) -> str:
    _ = agents
    default_profile = model_profiles["profiles"]["standard"]
    content = "\n".join(
        [
            "# GENERATED EXAMPLE — merge this global block into `.codex/config.toml` or `~/.codex/config.toml`.",
            "# Custom roles are discovered from sibling `agents/*.toml` files by current public Codex releases.",
            "# Multi-Agent V2 is explicit because current public Codex releases keep that feature disabled by default.",
            "# Named custom-role routing also requires V2 spawn metadata to expose the agent_type selector.",
            "",
            "[agents]",
            "enabled = true",
            "max_concurrent_threads_per_session = 4",
            f"default_subagent_model = {json.dumps(default_profile['candidate_models']['openai'])}",
            f"default_subagent_reasoning_effort = {json.dumps(default_profile['reasoning'])}",
            "interrupt_message = true",
            "",
            "[features.multi_agent_v2]",
            "enabled = true",
            "max_concurrent_threads_per_session = 4",
            "wait_agent_enabled = true",
            "non_code_mode_only = true",
            "hide_spawn_agent_metadata = false",
            "expose_spawn_agent_model_overrides = true",
            "",
            "# Recursive delegation is constrained by role instructions and repository policy.",
            "# Do not rely on legacy/V1 depth controls for current V2 behavior.",
            "",
        ]
    )
    tomllib.loads(content)
    return content


def expected_outputs() -> dict[Path, str]:
    agents = load_agents()
    model_profiles = load_yaml(MODEL_PROFILES_PATH)
    role_map = load_yaml(ROLE_PROFILES_PATH)

    missing_roles = sorted(set(agents) - set(role_map.get("roles", {})))
    extra_roles = sorted(set(role_map.get("roles", {})) - set(agents))
    if missing_roles or extra_roles:
        raise ValueError(
            f"Codex role map drift: missing={missing_roles!r}, extra={extra_roles!r}"
        )

    outputs = {
        OUTPUT_DIR / f"{role_id}.toml": render_role(
            agent, role_map, model_profiles
        )
        for role_id, agent in agents.items()
    }
    outputs[CONFIG_EXAMPLE_PATH] = render_config_example(agents, model_profiles)
    return outputs


def check(outputs: dict[Path, str]) -> int:
    failures = 0
    expected_paths = set(outputs)
    actual_paths = set(OUTPUT_DIR.glob("*.toml"))
    unexpected = sorted(actual_paths - expected_paths)
    for path in unexpected:
        print(f"DRIFT: unexpected generated role file: {path.relative_to(ROOT)}")
        failures += 1

    for path, expected in sorted(outputs.items()):
        if not path.exists():
            print(f"DRIFT: missing {path.relative_to(ROOT)}")
            failures += 1
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"DRIFT: {path.relative_to(ROOT)}")
            diff = difflib.unified_diff(
                actual.splitlines(),
                expected.splitlines(),
                fromfile="committed",
                tofile="generated",
                lineterm="",
            )
            for line in list(diff)[:80]:
                print(line)
            failures += 1

    if failures:
        print(f"FAIL: {failures} generated Codex artifact(s) drifted.")
        print("Run: python scripts/generate_codex_adapter.py")
        return 1

    print(f"PASS: {len(outputs)} generated Codex artifacts are in sync.")
    return 0


def write(outputs: dict[Path, str]) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"WROTE: {path.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if committed Codex artifacts differ from canonical generation",
    )
    args = parser.parse_args()

    try:
        outputs = expected_outputs()
    except (KeyError, TypeError, ValueError, yaml.YAMLError, tomllib.TOMLDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2

    return check(outputs) if args.check else write(outputs)


if __name__ == "__main__":
    sys.exit(main())
