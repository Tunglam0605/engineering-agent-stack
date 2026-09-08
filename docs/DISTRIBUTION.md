# Distribution model

Engineering Agent Stack v0.3 uses a **source-managed distribution model**. The CLI is intentionally small; the managed source checkout remains the canonical home for generated roles, policies, schemas, benchmarks, and provider adapters.

## Managed locations

Default personal layout:

```text
~/.codex/
├── config.toml
├── agents/
│   ├── architect.toml
│   ├── debugger.toml
│   ├── implementer.toml
│   ├── researcher.toml
│   ├── reviewer.toml
│   ├── scout.toml
│   └── test-engineer.toml
└── engineering-agent-stack/
    ├── managed Git checkout
    └── .venv/       # isolated EAS Python runtime

~/.local/bin/
└── eas        # POSIX
   or eas.cmd  # Windows
```

The bootstrap never deletes or blindly replaces an incompatible existing `~/.codex/config.toml`.

## Bootstrap responsibilities

`install.ps1` and `install.sh`:

1. require Git and Python 3.9+;
2. clone or safely update the official repository;
3. create/reuse `~/.codex/engineering-agent-stack/.venv` as an isolated EAS runtime;
4. install the EAS package into that runtime (including PyYAML and `tomli` on Python 3.9/3.10);
5. run the existing Codex installer in dry-run mode;
6. install the seven generated roles;
7. run installer verification;
8. create a launcher under `~/.local/bin`;
9. leave PATH unchanged.

On an existing v0.3+ managed checkout, the bootstrap delegates update safety to the existing `eas update` command. The pre-v0.3 upgrade path refuses to change source unless the existing generated-role installation passes the old installer check.

## Why source-managed?

The stack contains more than a Python CLI. It includes generated Codex role files, policies, schemas, benchmark fixtures, research provenance, and provider adapters. A versioned source checkout keeps those artifacts inspectable and gives `eas update` both the old and new canonical role sets required for drift-aware upgrades.

## Upgrade safety

`eas update` is intentionally conservative. It refuses:

- dirty source checkouts;
- source checkouts not on `main`;
- locally ahead or diverged `main`;
- managed personal role files changed relative to the pre-update canonical source;
- incompatible personal Codex configuration.

A successful update uses `git merge --ff-only origin/main`, checks generated adapter drift, refreshes only personal roles that matched the pre-update canonical artifacts, and reruns the installer check.

## Uninstall safety

`eas uninstall` is ownership-aware:

- it removes only EAS role files that still byte-match canonical generated roles;
- any drifted managed role causes a full refusal before deletion;
- unrelated custom agents are preserved;
- `config.toml` is always preserved;
- the project `AGENTS.md` managed block is removed only when explicitly requested.

## Package installation

`pyproject.toml` exposes:

```text
eas = eas_cli.cli:main
```

Developers may install the CLI with `pip install .`. The managed/package runtime includes PyYAML for adapter generation; Python 3.9/3.10 additionally installs `tomli` because `tomllib` is standard-library only from Python 3.11. The one-line bootstrap remains the recommended full-stack installation because it also manages the source checkout and generated Codex artifacts.

The v0.5.0 wheel includes `runtime.workflow` and snapshot validation. Goal commands still require a canonical source checkout (`EAS_REPO` or the managed checkout) for role/policy data. Release smoke runs installed goal recovery outside the source tree on Linux and Windows. Version 2 goal snapshots are not writable by older releases; see [workflow migration and durability](WORKFLOW.md).

## Release gate

A stable release is not tagged until:

- Python 3.9 full tests pass;
- repository/provenance/agent/routing/benchmark validators pass;
- generated adapter drift is clean;
- Linux and Windows CI pass;
- package install smoke succeeds;
- installer/project lifecycle smoke succeeds;
- stack-owned acceptance passes;
- independent read-only review reports no blocking findings;
- `main` and `origin/main` are synchronized.

Provider child-agent health is a separate diagnostic and is not a deterministic release invariant.

## Exact-artifact promotion

v0.6.2 changes release engineering only. Runtime/capability architecture and the seven roles are unchanged; built-in capability packs remain at 0.6.0.

Each main/tag CI run and each tag release run builds a single wheel/sdist bundle on Linux. The build writes `release-manifest.json` with candidate version, source commit, exact filenames, sizes and SHA-256 values. The manifest digest and immutable GitHub artifact ID travel separately as job outputs. Python 3.9 Linux and Windows jobs download that ID, require transport digest validation, verify the manifest against the build digest, inspect both archives and smoke-test the installed wheel. Hashes are checked again after smoke. Windows and Linux checkouts retain LF bytes for canonical resources.

Release publish depends on both release validators, downloads the same artifact ID, verifies the manifest again and uploads the wheel, sdist and manifest to GitHub Release. It does not install build tooling or rebuild. The main/tag validation workflow and tag release workflow have independent bundles; the published bundle is the one built and tested in the release run. Artifact retention is 30 days; the release preserves its manifest. Rerunning failed consumer jobs reuses the original build ID/digest. Never replace an existing release or move a published tag to hide failure.

This proves promotion identity within the trusted GitHub workflow. It does not claim deterministic independent rebuilds, a dependency lock, cryptographic signing, or protection against a compromised authorized workflow. Build and runtime dependency ranges remain technical debt.

### Local verification (PowerShell, Python 3.9)

Use a fresh, empty output directory. Record the manifest digest from creation independently; do not regenerate a manifest to validate downloaded or suspect bytes.

```powershell
$candidateCommit = git rev-parse HEAD
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m build --outdir dist/candidate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/release_artifacts.py create --dist dist/candidate --version 0.6.2 --commit $candidateCommit
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
# Set $buildDigest to the manifest-sha256 printed by the preceding build step.
python scripts/smoke_package.py --dist dist/candidate --commit $candidateCommit --manifest-sha256 $buildDigest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

The equivalent commands run on Linux with the full commit and digest passed as quoted shell arguments and `set -euo pipefail`. Verification fails on missing/extra/renamed/non-regular files, invalid manifests, wrong candidate identity, or size/hash/resource/metadata disagreement. Package smoke uses a temporary venv and working directory outside the checkout; it does not change personal managed configuration.

### Verify published assets

After both tag workflows pass, download all three release assets into a fresh directory and download the release run's `release-candidate` workflow artifact separately (`gh release download v0.6.2 --dir DIRECTORY` and `gh run download RUN_ID --name release-candidate --dir OTHER_DIRECTORY`). Use the manifest digest recorded in the release build log, not a digest newly trusted from the release download:

```text
python scripts/release_artifacts.py verify --dist DIRECTORY --version 0.6.2 --commit FULL_TAG_COMMIT --manifest-sha256 BUILD_LOG_DIGEST
```

Verify the workflow bundle the same way, compare the SHA-256 of each release asset with its workflow counterpart, and confirm exactly the two distributions and manifest are attached. The verifier reads archives without extraction and checks all 24 canonical resources against the matching source checkout. GitHub's automatically generated source archives are separate from the attached Python sdist.

### Official Action pins

Verified on 2026-09-08 using each official release tag, its resolved commit and `action.yml` at that commit; all declare Node 24:

| Action release | Pinned commit |
| --- | --- |
| [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| [setup-python v7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0) | `5fda3b95a4ea91299a34e894583c3862153e4b97` |
| [upload-artifact v7.0.1](https://github.com/actions/upload-artifact/releases/tag/v7.0.1) | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |
| [download-artifact v8.0.1](https://github.com/actions/download-artifact/releases/tag/v8.0.1) | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` |

When updating a pin, resolve the official release commit again and inspect its runtime; retain the readable release-version comment. No upstream Action source is vendored.
