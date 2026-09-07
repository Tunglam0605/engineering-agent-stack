#!/usr/bin/env python3
"""Release gate wrapper for Engineering Agent Stack acceptance.

The underlying acceptance harness records both stack-owned invariants and
provider/runtime capability probes. By default this wrapper keeps provider
child-spawn failures observable but non-blocking, so upstream Codex runtime
limitations do not falsely mark the stack itself as broken.

Use --strict-delegation when validating Codex provider behavior itself; in that
mode the underlying harness status is preserved exactly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts" / "acceptance_test_codex.py"
PROVIDER_PROBE_NAMES = {
    "Live Scout invocation",
    "Live Implementer invocation",
}
PROVIDER_PROBE_PREFIXES = ("Extended live role: ",)
TABLE_ROW = re.compile(r"^\| (PASS|FAIL|WARN|SKIP) \| (.*?) \| (.*?) \|$")


def is_provider_probe(name: str) -> bool:
    return name in PROVIDER_PROBE_NAMES or any(name.startswith(prefix) for prefix in PROVIDER_PROBE_PREFIXES)


def explicit_report(args: list[str]) -> Path | None:
    for index, arg in enumerate(args):
        if arg == "--report" and index + 1 < len(args):
            return Path(args[index + 1]).expanduser().resolve()
    return None


def default_report() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return (ROOT / "acceptance-reports" / f"acceptance-{stamp}.md").resolve()


def normalize_report(path: Path) -> tuple[int, int, int, list[tuple[str, str, str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[str, str, str]] = []
    normalized: list[str] = []

    for line in lines:
        match = TABLE_ROW.match(line)
        if not match:
            normalized.append(line)
            continue

        status, name, detail = match.groups()
        if status == "FAIL" and is_provider_probe(name):
            status = "WARN"
            suffix = "Provider/runtime delegation capability probe; non-blocking in the default release gate."
            detail = f"{detail} {suffix}".strip()
        rows.append((status, name, detail))
        normalized.append(f"| {status} | {name} | {detail} |")

    failures = sum(status == "FAIL" for status, _, _ in rows)
    warnings = sum(status == "WARN" for status, _, _ in rows)
    skips = sum(status == "SKIP" for status, _, _ in rows)
    overall = "PASS" if failures == 0 else "FAIL"

    rewritten: list[str] = []
    gate_line_written = False
    for line in normalized:
        if line.startswith("- Overall: **"):
            line = f"- Overall: **{overall}**"
        elif line.startswith("- Failures: `"):
            line = f"- Failures: `{failures}`"
        elif line.startswith("- Warnings: `"):
            line = f"- Warnings: `{warnings}`"
        elif line.startswith("- Skips: `"):
            line = f"- Skips: `{skips}`"
        elif line.startswith("- Delegation gate:"):
            line = "- Delegation gate: `provider-observational`"
            gate_line_written = True
        elif line == "- `WARN`: optional telemetry was incomplete or a non-blocking expectation differed.":
            line = "- `WARN`: optional telemetry was incomplete, a non-blocking expectation differed, or an upstream provider/runtime delegation probe did not pass."
        rewritten.append(line)
        if line.startswith("- Mode: `") and not gate_line_written:
            rewritten.append("- Delegation gate: `provider-observational` (use `--strict-delegation` to make provider child-spawn probes blocking)")
            gate_line_written = True

    path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
    return failures, warnings, skips, rows


def print_preamble(stdout: str) -> None:
    for line in stdout.splitlines():
        if line.startswith("REPORT:"):
            break
        print(line)


def main() -> int:
    strict = "--strict-delegation" in sys.argv[1:]
    forwarded = [arg for arg in sys.argv[1:] if arg != "--strict-delegation"]

    report = explicit_report(forwarded)
    if report is None:
        report = default_report()
        forwarded.extend(["--report", str(report)])

    result = subprocess.run(
        [sys.executable, str(HARNESS), *forwarded],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if strict:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode

    if not report.is_file():
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode

    failures, warnings, skips, rows = normalize_report(report)
    print_preamble(result.stdout)
    print(f"REPORT: {report}")
    print("INFO  Delegation gate: provider child-spawn probes are WARN by default; use --strict-delegation to make them blocking.")
    for status, name, detail in rows:
        print(f"{status:4}  {name}: {detail}")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if failures == 0:
        print(f"\nAcceptance release gate passed with {warnings} warning(s) and {skips} skip(s).")
        return 0
    print(f"\nAcceptance release gate found {failures} blocking failure(s).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
