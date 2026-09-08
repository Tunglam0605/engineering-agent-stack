# Roadmap

Engineering Agent Stack keeps the **seven core roles stable** unless benchmark evidence shows that a new role improves engineering quality enough to justify additional routing and maintenance complexity.

## v0.1 — Core agent foundation

Status: **completed foundation.**

- seven provider-neutral core roles
- role/schema validation
- deterministic direct-vs-delegate routing fixtures
- generated Codex adapter
- safe project/personal installer
- managed project `AGENTS.md` orchestration block
- stack-owned Windows acceptance
- provider/runtime diagnostic split
- provenance and acknowledgements gates

## v0.2 — Runtime-first controls

Status: **completed foundation; empirical optimization remains continuous.**

- provider-neutral delegation preflight
- `PASS / REJECT / ESCALATE` semantics
- resolved execution-plan contract
- bounded write ownership and recursion checks
- agent registry/status
- bounded context packets
- controlled full-context vs bounded-context benchmark harness
- strict request and runtime typing
- provider/model-profile separation
- Python 3.9 compatibility floor

Ongoing evidence work:

- repeated real Codex runs
- context/token/latency measurements
- Luna/Terra/Sol task-level quality/cost comparisons
- natural-language routing/classifier evaluation
- escalation regression fixtures
- repeated experiment reports before default model/routing changes

## v0.3 — Distribution and operational safety

Status: **stable release target.**

- `eas` CLI
- Windows and POSIX one-line bootstrap
- read-only `doctor` and `status`
- safe `install`, `init`, and `check`
- drift-aware `uninstall`
- guarded fast-forward `update`
- managed source checkout
- Python package metadata and console entry point
- product-oriented README and CLI/distribution docs
- Linux/Windows distribution smoke tests
- tagged release workflow

The core remains seven roles. v0.3 is about making the existing stack easy to install, inspect, update, and remove safely.

## v0.4 — Extensions and presets

Candidates:

- extension manifest/schema
- `embedded` preset
- `ros2` / robotics preset
- security/release preset
- capability discovery
- Codex plugin/skill packaging where it adds value

A preset augments the seven core roles; it does not create a duplicate agent taxonomy by default.

## v0.5 — Team distribution

Candidates:

- version pin / lock file
- organization presets
- policy inheritance
- offline/internal mirrors
- audit/export reports
- managed team rollout

## v1.0 — Stable platform contract

- stable canonical schemas
- migration policy
- benchmark-backed routing defaults
- reproducible release/distribution process
- cross-provider compatibility contract
- third-party/provenance release checklist
