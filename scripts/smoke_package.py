"""Verify a clean wheel install outside the checkout, without managed installs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import venv

from release_artifacts import verify_manifest
from validate_release_tag import package_version


def resource_hashes(root: Path) -> dict:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    verify_manifest(args.dist, package_version(), args.commit, args.manifest_sha256)
    wheels = list(args.dist.resolve().glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("smoke requires exactly one wheel in --dist")
    with tempfile.TemporaryDirectory(prefix="eas-wheel-smoke-") as temporary:
        outside = Path(temporary).resolve()
        if repo == outside or repo in outside.parents:
            raise RuntimeError("smoke temporary directory must be outside the checkout")
        environment = outside / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        bin_dir = environment / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        eas = bin_dir / ("eas.exe" if os.name == "nt" else "eas")
        env = os.environ.copy()
        for key in ("PYTHONPATH", "PYTHONHOME", "EAS_REPO"):
            env.pop(key, None)
        env["EAS_HOME"] = str(outside / "managed-home")
        env["PYTHONNOUSERSITE"] = "1"

        def run(*command: str) -> str:
            result = subprocess.run(
                [str(part) for part in command], cwd=outside, env=env,
                check=True, capture_output=True, text=True, encoding="utf-8",
            )
            return result.stdout

        run(python, "-m", "pip", "install", "--disable-pip-version-check", wheels[0])
        # -I excludes source/PYTHONPATH/user-site imports. The console commands
        # below also run from this empty temporary directory with EAS_REPO unset.
        probe = json.loads(run(python, "-I", "-c", """
import hashlib, json
from pathlib import Path
from importlib.metadata import version
import eas_cli, runtime, runtime.capabilities
from runtime.capabilities.builtins import builtin_root, load_builtin_catalog
catalog = load_builtin_catalog()
root = builtin_root()
print(json.dumps({
    'version': eas_cli.__version__,
    'distribution_version': version('engineering-agent-stack'),
    'origins': [eas_cli.__file__, runtime.__file__, runtime.capabilities.__file__],
    'resources': {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(root.rglob('*')) if p.is_file()},
}))
"""))
        for origin in probe["origins"]:
            if environment not in Path(origin).resolve().parents:
                raise RuntimeError("import did not come from clean wheel environment: " + origin)
        expected = resource_hashes(repo / "runtime" / "capabilities" / "resources" / "extensions")
        if not expected or probe["resources"] != expected:
            raise RuntimeError("installed capability resources differ from source inventory")
        # Read the candidate version without importing its modules.
        version = re.search(r'^version = "([^"]+)"$',
                            (repo / "pyproject.toml").read_text(encoding="utf-8"), re.MULTILINE).group(1)
        if probe["version"] != version or probe["distribution_version"] != version:
            raise RuntimeError("installed wheel version differs from candidate")
        if run(eas, "version").strip() != "eas " + version:
            raise RuntimeError("installed eas version output differs from candidate")
        listed = run(eas, "preset", "list")
        presets = {"embedded", "ros2", "release"}
        if {line.split()[0] for line in listed.splitlines()} != presets:
            raise RuntimeError("installed preset list is incomplete")
        for preset in sorted(presets):
            shown = json.loads(run(eas, "preset", "show", preset))
            if shown["id"] != preset or not shown["skills"] or not shown["required_rules"]:
                raise RuntimeError("installed preset is incomplete: " + preset)
        if (outside / "managed-home").exists() or (outside / ".eas").exists():
            raise RuntimeError("read-only package commands created managed state")
        run(python, repo / "scripts" / "generate_codex_adapter.py", "--check")
        print(run(python, repo / "scripts" / "smoke_goal_recovery.py", "--repo", repo).strip())
        print("PASS: clean installed wheel {}; 5 CLI commands; {} capability resources; origins in {}".format(
            version, len(expected), environment))
    verify_manifest(args.dist, package_version(), args.commit, args.manifest_sha256)
    print("PASS: exact wheel/sdist bytes match build manifest " + args.manifest_sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
