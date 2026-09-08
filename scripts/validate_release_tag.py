#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def package_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"^version\s*=\s*[\"\']([^\"\']+)[\"\']\s*$", text, re.MULTILINE)
    if not match:
        raise ValueError("pyproject.toml project version not found")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Git release tag against the EAS package version.")
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    version = package_version()
    expected = "v{}".format(version)
    if args.tag != expected:
        print("FAIL: release tag {} does not match package version {} (expected {}).".format(args.tag, version, expected))
        return 1
    print("PASS: release tag {} matches package version {}.".format(args.tag, version))
    return 0


if __name__ == "__main__":
    sys.exit(main())
