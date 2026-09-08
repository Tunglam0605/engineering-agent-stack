"""Release transport must reject altered payloads before package execution."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class ReleaseArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.dist = Path(self.temporary.name)
        self.version = "0.6.2"
        self.commit = "a" * 40
        self.wheel = self.dist / "engineering_agent_stack-0.6.2-py3-none-any.whl"
        self.sdist = self.dist / "engineering_agent_stack-0.6.2.tar.gz"
        resources = ROOT / "runtime/capabilities/resources/extensions"
        self.members = {
            "runtime/capabilities/resources/extensions/" + p.relative_to(resources).as_posix(): p.read_bytes()
            for p in resources.rglob("*") if p.is_file()
        }
        self.members["eas_cli/version.py"] = b'__version__ = "0.6.2"\n'
        self.metadata = b"Name: engineering-agent-stack\nVersion: 0.6.2\n"
        self.write_archives()

    def write_archives(self):
        with zipfile.ZipFile(self.wheel, "w") as archive:
            for name, data in self.members.items():
                archive.writestr(name, data)
            archive.writestr("engineering_agent_stack-0.6.2.dist-info/METADATA", self.metadata)
        with tarfile.open(self.sdist, "w:gz") as archive:
            for name, data in dict(self.members, **{"PKG-INFO": self.metadata}).items():
                entry = tarfile.TarInfo("engineering_agent_stack-0.6.2/" + name)
                entry.size = len(data)
                archive.addfile(entry, io.BytesIO(data))

    def command(self, mode, digest=None):
        command = [sys.executable, str(ROOT / "scripts/release_artifacts.py"), mode,
                   "--dist", str(self.dist), "--version", self.version, "--commit", self.commit]
        if digest is not None:
            command += ["--manifest-sha256", digest]
        return subprocess.run(command, capture_output=True, text=True)

    def create(self):
        result = self.command("create")
        self.assertEqual(result.returncode, 0, result.stderr)
        return hashlib.sha256((self.dist / "release-manifest.json").read_bytes()).hexdigest()

    def test_round_trip_binds_both_files_and_candidate(self):
        digest = self.create()
        manifest = json.loads((self.dist / "release-manifest.json").read_text())
        self.assertEqual(set(manifest["files"]), {self.wheel.name, self.sdist.name})
        self.assertEqual(manifest["commit"], self.commit)
        self.assertEqual(manifest["version"], self.version)
        self.assertEqual(self.command("verify", digest).returncode, 0)

    def test_tampered_payload_fails(self):
        digest = self.create()
        self.wheel.write_bytes(self.wheel.read_bytes() + b"tampered")
        self.assertNotEqual(self.command("verify", digest).returncode, 0)

    def test_replaced_manifest_and_payload_fail_independent_digest(self):
        digest = self.create()
        path = self.dist / "release-manifest.json"
        manifest = json.loads(path.read_text())
        self.wheel.write_bytes(self.wheel.read_bytes() + b"tampered")
        manifest["files"][self.wheel.name]["sha256"] = hashlib.sha256(self.wheel.read_bytes()).hexdigest()
        manifest["files"][self.wheel.name]["size"] = self.wheel.stat().st_size
        path.write_text(json.dumps(manifest))
        self.assertNotEqual(self.command("verify", digest).returncode, 0)

    def test_missing_extra_renamed_and_directory_fail(self):
        digest = self.create()
        original = self.wheel.read_bytes()
        for change in ("missing", "extra", "renamed", "directory"):
            with self.subTest(change=change):
                extra = self.dist / "unexpected"
                if change == "missing":
                    self.wheel.unlink()
                elif change == "renamed":
                    self.wheel.rename(extra)
                elif change == "directory":
                    extra.mkdir()
                else:
                    extra.write_bytes(b"extra")
                self.assertNotEqual(self.command("verify", digest).returncode, 0)
                if extra.is_dir():
                    extra.rmdir()
                elif extra.exists():
                    extra.unlink()
                self.wheel.write_bytes(original)

    def test_wrong_commit_version_or_empty_digest_fail(self):
        digest = self.create()
        self.commit = "b" * 40
        self.assertNotEqual(self.command("verify", digest).returncode, 0)
        self.commit = "a" * 40
        self.version = "0.6.3"
        self.assertNotEqual(self.command("verify", digest).returncode, 0)
        self.version = "0.6.2"
        self.assertNotEqual(self.command("verify", "").returncode, 0)
        self.assertNotEqual(self.command("verify").returncode, 0)

    def test_unknown_manifest_fields_fail_even_with_matching_digest(self):
        self.create()
        path = self.dist / "release-manifest.json"
        manifest = json.loads(path.read_text())
        manifest["unexpected"] = True
        path.write_text(json.dumps(manifest))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertNotEqual(self.command("verify", digest).returncode, 0)

    def test_bad_archive_version_fails_before_manifest_creation(self):
        self.create()
        (self.dist / "release-manifest.json").unlink()
        self.metadata = b"Name: engineering-agent-stack\nVersion: 0.6.1\n"
        self.write_archives()
        self.assertNotEqual(self.command("create").returncode, 0)
        self.assertFalse((self.dist / "release-manifest.json").exists())

    def test_missing_or_altered_canonical_resource_fails(self):
        self.create()
        (self.dist / "release-manifest.json").unlink()
        name = next(iter(self.members))
        for change in ("alter", "remove"):
            with self.subTest(change=change):
                if change == "alter":
                    self.members[name] = b"altered"
                else:
                    del self.members[name]
                self.write_archives()
                self.assertNotEqual(self.command("create").returncode, 0)

    def test_smoke_rejects_tampered_artifact_before_install(self):
        digest = self.create()
        self.wheel.write_bytes(self.wheel.read_bytes() + b"tampered")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/smoke_package.py"), "--dist", str(self.dist),
             "--commit", self.commit, "--manifest-sha256", digest], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("artifact SHA-256/size mismatch", result.stderr)
        self.assertNotIn("PASS: clean installed wheel", result.stdout)

    def test_duplicate_manifest_key_and_malformed_records_fail(self):
        self.create()
        path = self.dist / "release-manifest.json"
        original = path.read_text()
        candidates = [original.replace('"schema": 1', '"schema": 1, "schema": 1')]
        for value in (True, "100", -1):
            manifest = json.loads(original)
            manifest["files"][self.wheel.name]["size"] = value
            candidates.append(json.dumps(manifest))
        for candidate in candidates:
            with self.subTest(candidate=candidate[:30]):
                path.write_text(candidate)
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertNotEqual(self.command("verify", digest).returncode, 0)

    def test_sdist_only_resource_tampering_is_rejected(self):
        self.create()
        (self.dist / "release-manifest.json").unlink()
        wheel_bytes = self.wheel.read_bytes()
        self.members[next(iter(self.members))] = b"tampered sdist only"
        self.write_archives()
        self.wheel.write_bytes(wheel_bytes)
        result = self.command("create")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive capability resources differ", result.stderr)

    def test_duplicate_wheel_member_is_rejected(self):
        self.create()
        (self.dist / "release-manifest.json").unlink()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.wheel, "a") as archive:
                archive.writestr("eas_cli/version.py", self.members["eas_cli/version.py"])
        result = self.command("create")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate archive member", result.stderr)

    def test_archive_resource_aliases_are_rejected(self):
        resource = next(iter(self.members))
        original = dict(self.members)
        for alias in ("./" + resource, resource.replace("runtime/", "runtime//", 1)):
            with self.subTest(alias=alias):
                self.members = dict(original)
                manifest = self.dist / "release-manifest.json"
                if manifest.exists():
                    manifest.unlink()
                self.members[alias] = b"altered alias would overwrite canonical resource"
                self.write_archives()
                result = self.command("create")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("unsafe or duplicate archive member", result.stderr)


if __name__ == "__main__":
    unittest.main()
