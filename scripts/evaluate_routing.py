#!/usr/bin/env python3
"""Evaluate deterministic routing-policy fixtures.

This tests the policy layer after task classification. It deliberately does not
pretend that keyword matching is an LLM routing benchmark; natural-language
classifier quality belongs in a separate eval suite.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "routing-policy.yaml"
CASES_PATH = ROOT / "evals" / "routing-cases.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def rule_matches(when: dict[str, Any], signals: dict[str, Any]) -> bool:
    for key, expected in when.items():
        observed = signals.get(key)
        if isinstance(expected, list):
            if observed not in expected:
                return False
        elif observed != expected:
            return False
    return True


def review_required(policy: dict[str, Any], signals: dict[str, Any]) -> bool:
    review_class = signals.get("review_class")
    if review_class is None:
        return False
    required = policy.get("quality_gate", {}).get("review_required_for", [])
    return review_class in required


def resolve(policy: dict[str, Any], signals: dict[str, Any]) -> dict[str, Any]:
    route: dict[str, Any] = {
        "action": policy.get("default", "direct"),
        "review_required": review_required(policy, signals),
    }

    for rule in policy.get("rules", []):
        when = rule.get("when", {})
        if rule_matches(when, signals):
            route["matched_rule"] = rule.get("id")
            route["action"] = rule["action"]
            if "role" in rule:
                route["role"] = rule["role"]
            if "profile" in rule:
                route["profile"] = rule["profile"]
            break

    if route["action"] == "direct":
        route["max_parallel_agents"] = 0

    return route


def compare_expected(case_id: str, actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if actual_value != expected_value:
            failures.append(
                f"{case_id}: {key}: expected {expected_value!r}, got {actual_value!r}"
            )
    return failures


def main() -> int:
    policy = load_yaml(POLICY_PATH)
    suite = load_yaml(CASES_PATH)

    failures: list[str] = []
    cases = suite.get("cases", [])
    if not cases:
        print("ERROR: no routing cases defined")
        return 2

    for case in cases:
        case_id = case["id"]
        actual = resolve(policy, case.get("signals", {}))
        failures.extend(compare_expected(case_id, actual, case["expected"]))

    if failures:
        print(f"FAIL: {len(failures)} routing expectation(s) did not match.")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS: {len(cases)} deterministic routing-policy cases.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
