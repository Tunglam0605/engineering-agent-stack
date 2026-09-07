#!/usr/bin/env python3
"""Summarize benchmark JSONL without auto-promoting a model/default."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRICING = ROOT / "benchmarks" / "pricing" / "openai-2026-09-07.yaml"
DEFAULT_PLAN = ROOT / "benchmarks" / "experiment-plan.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return value


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
    if not records:
        raise ValueError(f"{path} contains no benchmark records")
    return records


def normalized_cost(record: dict[str, Any], pricing: dict[str, Any]) -> tuple[float, str]:
    actual = record.get("actual_cost_usd")
    if actual is not None:
        return float(actual), "actual"

    model = record.get("model")
    rates = pricing.get("models", {}).get(model)
    if not isinstance(rates, dict):
        raise ValueError(
            f"run {record.get('run_id')}: no pricing for model {model!r} "
            "and no actual_cost_usd supplied"
        )

    unit = pricing.get("unit_tokens")
    if not isinstance(unit, (int, float)) or unit <= 0:
        raise ValueError("pricing unit_tokens must be positive")

    input_cost = (record["input_tokens"] / unit) * rates["input_per_unit"]
    output_cost = (record["output_tokens"] / unit) * rates["output_per_unit"]
    return float(input_cost + output_cost), "normalized-api-estimate"


def aggregate(
    records: list[dict[str, Any]],
    pricing: dict[str, Any],
    plan: dict[str, Any],
) -> list[dict[str, Any]]:
    screening_repeats = int(plan.get("protocol", {}).get("screening_repeats", 3))
    confirmation_repeats = int(
        plan.get("protocol", {}).get("confirmation_repeats", 10)
    )

    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = (
            str(record["case_id"]),
            str(record["variant_id"]),
            str(record["model"]),
            str(record["reasoning"]),
        )
        cost, cost_source = normalized_cost(record, pricing)
        enriched = dict(record)
        enriched["_effective_cost_usd"] = cost
        enriched["_cost_source"] = cost_source
        enriched["_quality_qualified"] = bool(record["validation_passed"]) and (
            float(record["quality_score"]) >= float(record["quality_threshold"])
        )
        grouped[key].append(enriched)

    summary: list[dict[str, Any]] = []
    any_synthetic = any(bool(record.get("synthetic")) for record in records)

    for (case_id, variant_id, model, reasoning), runs in sorted(grouped.items()):
        qualified_count = sum(1 for run in runs if run["_quality_qualified"])
        cost_sources = {run["_cost_source"] for run in runs}
        run_count = len(runs)
        qualification_rate = qualified_count / run_count

        row = {
            "case_id": case_id,
            "variant_id": variant_id,
            "model": model,
            "reasoning": reasoning,
            "runs": run_count,
            "qualified_runs": qualified_count,
            "qualification_rate": qualification_rate,
            "average_quality": statistics.fmean(
                float(run["quality_score"]) for run in runs
            ),
            "average_cost_usd": statistics.fmean(
                float(run["_effective_cost_usd"]) for run in runs
            ),
            "total_cost_usd": sum(
                float(run["_effective_cost_usd"]) for run in runs
            ),
            "average_latency_seconds": statistics.fmean(
                float(run["latency_ms"]) / 1000.0 for run in runs
            ),
            "average_input_tokens": statistics.fmean(
                int(run["input_tokens"]) for run in runs
            ),
            "average_output_tokens": statistics.fmean(
                int(run["output_tokens"]) for run in runs
            ),
            "cost_basis": next(iter(cost_sources))
            if len(cost_sources) == 1
            else "mixed",
            "screening_complete": run_count >= screening_repeats,
            "screening_quality_qualified": (
                run_count >= screening_repeats and qualification_rate == 1.0
            ),
            "confirmation_complete": run_count >= confirmation_repeats,
            "confirmation_quality_qualified": (
                not any_synthetic
                and run_count >= confirmation_repeats
                and qualification_rate == 1.0
            ),
            "synthetic": all(bool(run.get("synthetic")) for run in runs),
        }
        summary.append(row)

    return summary


def print_table(rows: list[dict[str, Any]]) -> None:
    header = (
        f"{'CASE':28} {'VARIANT':14} {'RUNS':>4} {'QUAL':>7} "
        f"{'AVG_Q':>7} {'$/RUN':>10} {'LAT_S':>8} {'SCREEN':>8} {'CONFIRM':>8}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        qual = f"{row['qualified_runs']}/{row['runs']}"
        print(
            f"{row['case_id'][:28]:28} "
            f"{row['variant_id'][:14]:14} "
            f"{row['runs']:>4} "
            f"{qual:>7} "
            f"{row['average_quality']:>7.3f} "
            f"{row['average_cost_usd']:>10.6f} "
            f"{row['average_latency_seconds']:>8.2f} "
            f"{('PASS' if row['screening_quality_qualified'] else '-'):>8} "
            f"{('PASS' if row['confirmation_quality_qualified'] else '-'):>8}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="benchmark JSONL input")
    parser.add_argument("--pricing", type=Path, default=DEFAULT_PRICING)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument(
        "--allow-synthetic",
        action="store_true",
        help="allow synthetic harness fixtures; never treat them as promotion evidence",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args()

    try:
        records = load_jsonl(args.input)
        pricing = load_yaml(args.pricing)
        plan = load_yaml(args.plan)

        synthetic_values = {bool(record.get("synthetic")) for record in records}
        if len(synthetic_values) > 1:
            raise ValueError("do not mix synthetic and real records in one report")
        if True in synthetic_values and not args.allow_synthetic:
            raise ValueError(
                "input is synthetic; pass --allow-synthetic only for harness validation"
            )

        rows = aggregate(records, pricing, plan)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print_table(rows)
        if True in synthetic_values:
            print(
                "\nSYNTHETIC FIXTURE: these rows validate the harness only and "
                "must not influence model/routing defaults."
            )
        else:
            print(
                "\nNo winner is selected automatically. Apply the quality gate first, "
                "then compare cost/latency only among confirmed qualified variants."
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
