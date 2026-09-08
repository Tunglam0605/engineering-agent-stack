#!/usr/bin/env python3
"""Evaluate one provider-neutral delegation request and emit preflight evidence."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.contracts import ContextBudget, DelegationRequest, WriteLease
from runtime.preflight import DelegationPreflight


def load_request(path: Path) -> Dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("request must be a YAML/JSON mapping")
    return value


def require_string(payload: Dict[str, Any], field: str, *, allow_none: bool = False) -> Any:
    value = payload.get(field)
    if allow_none and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def require_boolean(payload: Dict[str, Any], field: str, *, default: Any = None) -> bool:
    value = payload[field] if field in payload else default
    if type(value) is not bool:
        raise ValueError(f"{field} must be a boolean")
    return value


def require_integer(payload: Dict[str, Any], field: str) -> int:
    value = payload.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    return value


def require_string_list(payload: Dict[str, Any], field: str, *, default: Any = None) -> List[str]:
    value = payload[field] if field in payload else default
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field} must be a list of strings")
    return [item.strip() for item in value]


def build_request(payload: Dict[str, Any]) -> DelegationRequest:
    budget = payload.get("context_budget")
    if not isinstance(budget, dict):
        raise ValueError("context_budget must be a mapping")
    return DelegationRequest(
        task=require_string(payload, "task"),
        route_mode=require_string(payload, "route_mode"),
        role=require_string(payload, "role"),
        profile=require_string(payload, "profile"),
        provider=require_string(payload, "provider"),
        child_agent_capable=require_boolean(payload, "child_agent_capable"),
        write_owner=require_string(payload, "write_owner", allow_none=True),
        write_scope=require_string_list(payload, "write_scope", default=[]),
        parent_role=require_string(payload, "parent_role", allow_none=True),
        recursion_depth=require_integer(payload, "recursion_depth"),
        context_budget=ContextBudget(
            max_input_tokens=require_integer(budget, "max_input_tokens"),
            estimated_input_tokens=require_integer(budget, "estimated_input_tokens"),
        ),
        review_required=require_boolean(payload, "review_required", default=False),
        review_planned=require_boolean(payload, "review_planned", default=False),
        risk_class=require_string(payload, "risk_class") if "risk_class" in payload else "normal",
        capability_snapshot_digest=require_string(
            payload, "capability_snapshot_digest", allow_none=True
        ),
    )


def build_leases(payload: Dict[str, Any]) -> List[WriteLease]:
    raw = payload["active_write_leases"] if "active_write_leases" in payload else []
    if not isinstance(raw, list):
        raise ValueError("active_write_leases must be a list")
    leases: List[WriteLease] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("active_write_leases entries must be mappings")
        leases.append(
            WriteLease(
                owner=require_string(item, "owner"),
                scope=require_string_list(item, "scope"),
            )
        )
    return leases


def result_payload(payload: Dict[str, Any]) -> tuple:
    request = build_request(payload)
    disabled = require_string_list(payload, "disabled_roles", default=[])
    result = DelegationPreflight.from_repository(ROOT).evaluate(
        request,
        disabled_roles=set(disabled),
        active_write_leases=build_leases(payload),
    )
    plan = None
    if result.decision == "PASS":
        assignment_id = require_string(payload, "assignment_id")
        plan = result.to_execution_plan(assignment_id=assignment_id).as_dict()
    body = {
        "preflight": {
            "decision": result.decision,
            "reasons": [asdict(reason) for reason in result.reasons],
        },
        "resolved": {
            "model": result.resolved_model,
            "reasoning_effort": result.resolved_effort,
            "review_required": result.effective_review_required,
            "capability_snapshot_digest": result.capability_snapshot_digest,
        },
        "execution_plan": plan,
    }
    exit_code = {"PASS": 0, "REJECT": 3, "ESCALATE": 4}[result.decision]
    return body, exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()
    try:
        body, exit_code = result_payload(load_request(args.request))
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        if args.format == "json":
            print(json.dumps({"error": str(exc)}, sort_keys=True))
        else:
            print("ERROR: " + str(exc))
        return 2

    if args.format == "json":
        print(json.dumps(body, sort_keys=True))
    else:
        preflight = body["preflight"]
        print("decision=" + preflight["decision"])
        for reason in preflight["reasons"]:
            print("reason=" + reason["code"] + ": " + reason["message"])
        resolved = body["resolved"]
        print("model=" + str(resolved["model"]))
        print("reasoning_effort=" + str(resolved["reasoning_effort"]))
        print("execution_plan=" + ("ready" if body["execution_plan"] is not None else "none"))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
