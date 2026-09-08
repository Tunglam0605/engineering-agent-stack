"""Create and verify the exact wheel/sdist bundle promoted by release CI."""
from __future__ import annotations

import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "release-manifest.json"
RESOURCE_PREFIX = "runtime/capabilities/resources/extensions/"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def filenames(version: str) -> set:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("expected stable package version")
    return {"engineering_agent_stack-{}-py3-none-any.whl".format(version),
            "engineering_agent_stack-{}.tar.gz".format(version)}


def inventory(dist: Path, expected: set) -> None:
    if {p.name for p in dist.iterdir()} != expected:
        raise ValueError("artifact file inventory differs: missing, extra or renamed file")
    if any(p.is_symlink() or not p.is_file() for p in dist.iterdir()):
        raise ValueError("artifacts must be regular files")


def inspect_archives(dist: Path, version: str) -> None:
    root = ROOT / RESOURCE_PREFIX
    expected = {RESOURCE_PREFIX + p.relative_to(root).as_posix(): p.read_bytes()
                for p in root.rglob("*") if p.is_file()}
    if len(expected) != 24:
        raise ValueError("expected 24 canonical capability resources")
    for filename in sorted(filenames(version)):
        members = {}

        def add(name, data):
            path = PurePosixPath(name)
            if (name in members or path.as_posix() != name or path.is_absolute()
                    or ".." in path.parts or "\\" in name):
                raise ValueError("unsafe or duplicate archive member: " + name)
            members[name] = data

        if filename.endswith(".whl"):
            with zipfile.ZipFile(dist / filename) as archive:
                for entry in archive.infolist():
                    if not entry.is_dir():
                        add(entry.filename, archive.read(entry))
            metadata_name = "engineering_agent_stack-{}.dist-info/METADATA".format(version)
        else:
            prefix = "engineering_agent_stack-{}/".format(version)
            with tarfile.open(dist / filename, "r:gz") as archive:
                for entry in archive.getmembers():
                    if entry.isdir():
                        continue
                    if not entry.isfile() or not entry.name.startswith(prefix):
                        raise ValueError("unexpected sdist member: " + entry.name)
                    add(entry.name[len(prefix):], archive.extractfile(entry).read())
            metadata_name = "PKG-INFO"
        metadata = BytesParser().parsebytes(members.get(metadata_name, b""))
        if metadata.get_all("Name") != ["engineering-agent-stack"] or metadata.get_all("Version") != [version]:
            raise ValueError("archive package metadata differs from candidate: " + filename)
        version_text = members.get("eas_cli/version.py", b"").decode("utf-8")
        if not re.fullmatch(r'__version__ = "' + re.escape(version) + r'"\s*', version_text):
            raise ValueError("archive CLI version differs from candidate: " + filename)
        resources = {name: data for name, data in members.items() if name.startswith(RESOURCE_PREFIX)}
        if resources != expected:
            raise ValueError("archive capability resources differ from canonical inventory: " + filename)


def create_manifest(dist: Path, version: str, commit: str) -> str:
    names = filenames(version)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("expected full Git commit SHA")
    inventory(dist, names)
    inspect_archives(dist, version)
    manifest = {"schema": 1, "version": version, "commit": commit, "files": {
        name: {"sha256": sha256((dist / name).read_bytes()), "size": (dist / name).stat().st_size}
        for name in sorted(names)
    }}
    data = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (dist / MANIFEST).write_bytes(data)
    return sha256(data)


def verify_manifest(dist: Path, version: str, commit: str, digest: str) -> dict:
    names = filenames(version)
    inventory(dist, names | {MANIFEST})
    data = (dist / MANIFEST).read_bytes()
    if not re.fullmatch(r"[0-9a-f]{64}", digest) or sha256(data) != digest:
        raise ValueError("manifest SHA-256 differs from independent build digest")

    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate manifest key")
            result[key] = value
        return result

    manifest = json.loads(data, object_pairs_hook=unique_pairs)
    if not isinstance(manifest, dict) or set(manifest) != {"schema", "version", "commit", "files"}:
        raise ValueError("invalid manifest fields")
    if (type(manifest["schema"]) is not int or manifest["schema"] != 1
            or manifest["version"] != version or manifest["commit"] != commit
            or not re.fullmatch(r"[0-9a-f]{40}", commit)):
        raise ValueError("manifest identity differs from candidate")
    if not isinstance(manifest["files"], dict) or set(manifest["files"]) != names:
        raise ValueError("invalid manifest file inventory")
    for name, record in manifest["files"].items():
        if (not isinstance(record, dict) or set(record) != {"sha256", "size"}
                or type(record["size"]) is not int or not isinstance(record["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])):
            raise ValueError("invalid file hash record")
        payload = (dist / name).read_bytes()
        if len(payload) != record["size"] or sha256(payload) != record["sha256"]:
            raise ValueError("artifact SHA-256/size mismatch: " + name)
    inspect_archives(dist, version)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("create", "verify"))
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "create":
            digest = create_manifest(args.dist, args.version, args.commit)
            if args.github_output:
                with args.github_output.open("a", encoding="utf-8") as output:
                    output.write("manifest-sha256=" + digest + "\n")
            print("manifest-sha256=" + digest)
        else:
            if args.manifest_sha256 is None:
                raise ValueError("verify requires --manifest-sha256 from the build")
            manifest = verify_manifest(args.dist, args.version, args.commit, args.manifest_sha256)
            print(json.dumps(manifest, indent=2, sort_keys=True))
    except (ValueError, OSError, tarfile.TarError, zipfile.BadZipFile) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
