#!/usr/bin/env python3
"""Backward-compatible entry point for the stack-owned acceptance gate.

Provider-specific child-agent spawning and model-routing experiments moved to
`scripts/provider_probe_codex.py` / `scripts/provider-probe.ps1` so upstream
Codex runtime behavior cannot block the stack-owned release gate.
"""

from acceptance_core import main


if __name__ == "__main__":
    raise SystemExit(main())
