#!/usr/bin/env python3
"""Validate benchmark plans, pricing snapshots, schemas, and synthetic fixtures."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "benchmarks" / "experiment-plan.yaml"
PRICING_PATH = ROOT / "benchmarks" / "pricing" / "openai-2026-09-07.yaml"
SCHEMA_PATH = ROOT / "schemas" / "benchmark-result.yaml"
FIXTURE_PATH = ROOT / "benchmarks" / "fixtures" / "sample-results.jsonl"
CORE_DIR = ROOT / "agents" / "core"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return value


def parse_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must be a JSON object")
            value["_line_number"] = line_number
            records.append(value)
    return records


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record_types(
    record: dict[str, Any],
    required_fields: list[str],
    failures: list[str],
) -> None:
    label = f"fixture line {record['_line_number']} ({record.get('run_id', 'unknown')})"

    missing = [field for field in required_fields if field not in record]
    if missing:
        failures.append(f"{label}: missing required field(s): {', '.join(missing)}")
        return

    for field in (
        "run_id",
        "stack_commit",
        "case_id",
        "variant_id",
        "provider",
        "model",
        "reasoning",
    ):
        if not non_empty_string(record.get(field)):
            failures.append(f"{label}: {field} must be a non-empty string")

    if not parse_timestamp(record.get("timestamp_utc")):
        failures.append(f"{label}: timestamp_utc must be ISO-8601")

    if not isinstance(record.get("case_version"), int) or record["case_version"] <= 0:
        failures.append(f"{label}: case_version must be a positive integer")

    for field in ("input_tokens", "output_tokens"):
        value = record.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            failures.append(f"{label}: {field} must be a non-negative integer")

    latency = record.get("latency_ms")
    if not isinstance(latency, (int, float)) or isinstance(latency, bool) or latency <= 0:
        failures.append(f"{label}: latency_ms must be a positive number")

    for field in ("quality_score", "quality_threshold"):
        value = record.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
            failures.append(f"{label}: {field} must be between 0 and 1")

    for field in ("validation_passed", "synthetic"):
        if not isinstance(record.get(field), bool):
            failures.append(f"{label}: {field} must be boolean")

    for field in ("delegated_agents", "peak_parallel_agents", "tool_calls"):
        if field in record:
            value = record[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                failures.append(f"{label}: {field} must be a non-negative integer")

    if "actual_cost_usd" in record:
        value = record["actual_cost_usd"]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            failures.append(f"{label}: actual_cost_usd must be non-negative")


def main() -> int:
    plan = load_yaml(PLAN_PATH)
    pricing = load_yaml(PRICING_PATH)
    schema = load_yaml(SCHEMA_PATH)
    fixtures = load_jsonl(FIXTURE_PATH)

    failures: list[str] = []
    required_fields = schema.get("required_fields")
    if not isinstance(required_fields, list) or not required_fields:
        failures.append("benchmark-result schema must define non-empty required_fields")
        required_fields = []

    pricing_models = pricing.get("models")
    if not isinstance(pricing_models, dict) or not pricing_models:
        failures.append("pricing snapshot must define models")
        pricing_models = {}

    for model, rates in pricing_models.items():
        if not isinstance(rates, dict):
            failures.append(f"pricing {model}: rates must be a mapping")
            continue
        for key in ("input_per_unit", "output_per_unit"):
            value = rates.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                failures.append(f"pricing {model}: {key} must be non-negative")

    core_roles = {
        path.stem
        for path in CORE_DIR.glob("*.yaml")
        if path.is_file()
    }

    cases = plan.get("cases")
    if not isinstance(cases, list) or not cases:
        failures.append("experiment plan must contain cases")
        cases = []

    case_map: dict[str, dict[str, Any]] = {}
    variant_map: dict[tuple[str, str], dict[str, Any]] = {}

    for case in cases:
        if not isinstance(case, dict):
            failures.append("experiment plan case must be a mapping")
            continue
        case_id = case.get("id")
        if not non_empty_string(case_id):
            failures.append("experiment plan case id must be non-empty")
            continue
        if case_id in case_map:
            failures.append(f"duplicate benchmark case id: {case_id}")
        case_map[case_id] = case

        version = case.get("version")
        if not isinstance(version, int) or isinstance(version, bool) or version <= 0:
            failures.append(f"{case_id}: version must be a positive integer")

        role = case.get("role")
        if role not in core_roles:
            failures.append(f"{case_id}: unknown core role {role!r}")

        threshold = case.get("quality_threshold")
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0 <= threshold <= 1:
            failures.append(f"{case_id}: quality_threshold must be between 0 and 1")

        if case.get("risk") == "critical" and case.get("hard_fail_on_safety_violation") is not True:
            failures.append(
                f"{case_id}: critical cases must set hard_fail_on_safety_violation: true"
            )

        rubric = case.get("rubric")
        if not isinstance(rubric, dict) or not rubric:
            failures.append(f"{case_id}: rubric must be a non-empty mapping")
        else:
            weights = list(rubric.values())
            if any(
                not isinstance(weight, (int, float))
                or isinstance(weight, bool)
                or weight <= 0
                for weight in weights
            ):
                failures.append(f"{case_id}: rubric weights must be positive numbers")
            elif abs(sum(weights) - 1.0) > 1e-9:
                failures.append(
                    f"{case_id}: rubric weights must sum to 1.0; got {sum(weights):.6f}"
                )

        variants = case.get("variants")
        if not isinstance(variants, list) or len(variants) < 2:
            failures.append(f"{case_id}: define at least two benchmark variants")
            continue

        seen_variants: set[str] = set()
        for variant in variants:
            if not isinstance(variant, dict):
                failures.append(f"{case_id}: variant must be a mapping")
                continue
            variant_id = variant.get("id")
            if not non_empty_string(variant_id):
                failures.append(f"{case_id}: variant id must be non-empty")
                continue
            if variant_id in seen_variants:
                failures.append(f"{case_id}: duplicate variant id {variant_id}")
            seen_variants.add(variant_id)
            variant_map[(case_id, variant_id)] = variant

            if variant.get("provider") != "openai":
                failures.append(
                    f"{case_id}/{variant_id}: current pricing harness only covers provider=openai"
                )
            model = variant.get("model")
            if model not in pricing_models:
                failures.append(
                    f"{case_id}/{variant_id}: model {model!r} missing from pricing snapshot"
                )
            if not non_empty_string(variant.get("reasoning")):
                failures.append(
                    f"{case_id}/{variant_id}: reasoning must be a non-empty string"
                )

    if not fixtures:
        failures.append("synthetic benchmark fixture must contain records")

    for record in fixtures:
        validate_record_types(record, required_fields, failures)
        if record.get("synthetic") is not True:
            failures.append(
                f"fixture line {record['_line_number']}: sample-results.jsonl must stay synthetic"
            )

        case_id = record.get("case_id")
        variant_id = record.get("variant_id")
        case = case_map.get(case_id)
        variant = variant_map.get((case_id, variant_id))
        if case is None:
            failures.append(
                f"fixture line {record['_line_number']}: unknown case {case_id!r}"
            )
            continue
        if variant is None:
            failures.append(
                f"fixture line {record['_line_number']}: unknown variant {case_id}/{variant_id}"
            )
            continue

        if record.get("case_version") != case.get("version"):
            failures.append(
                f"fixture line {record['_line_number']}: case_version does not match plan"
            )
        if record.get("quality_threshold") != case.get("quality_threshold"):
            failures.append(
                f"fixture line {record['_line_number']}: quality_threshold does not match plan"
            )
        for field in ("provider", "model", "reasoning"):
            if record.get(field) != variant.get(field):
                failures.append(
                    f"fixture line {record['_line_number']}: {field} does not match variant"
                )

    if failures:
        print(f"FAIL: {len(failures)} benchmark contract violation(s).")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        f"PASS: benchmark plan has {len(case_map)} cases and "
        f"{len(variant_map)} variants; {len(fixtures)} synthetic fixture runs are valid."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
