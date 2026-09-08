# Resolution and enforcement proposal

Status: research contract only.

## ResolvedCapabilitySnapshot

v0.6 should resolve one immutable/hashable snapshot containing: resolver/EAS version, project/profile digest, selected package IDs/versions/content hashes, preset/skills/required rules, effective declared settings/facts, capability availability, per-value lineage, protected-invariant version, and canonical snapshot digest.

The digest proves exact resolved content identity; it does not prove publisher trust, provider execution, authorization, compliance or correctness.

## Resolution

Resolve one project root; load explicit profile/local overlay; resolve only explicitly listed local package roots; parse closed schemas with resource/path/collision limits; verify identity/compatibility/content/provenance; resolve one preset plus explicit skills/rules/settings; verify role/effect/capability applicability; refuse a required gate without a trusted check + controlling boundary; emit deterministic snapshot and explanation.

Allowed precedence: `core defaults < extension defaults < preset < tracked project profile < local overlay < explicit CLI override`. Only declared configurable leaves participate.

## Protected invariants

Extensions cannot redefine the seven roles/access, model/provider authority, native sandbox/tool permissions, write ownership/scope safety, recursion default, mandatory review floors, lifecycle/reuse safety floors, stale/recovery approval/CAS/lock/receipt semantics, UNKNOWN telemetry, provenance classes, or what counts as a gate.

## Binding

Preflight and lifecycle admission must consume the **same snapshot digest**. A future versioned goal state records that binding. Resume/recovery keeps it. If current config resolves differently, report drift and refuse silent rebind; configuration migration requires a separate reviewed/approved operation, not ordinary recovery approval.

Rule semantics remain: `guidance` requires judgment; `validator` reports trusted structured evidence; `gate` means a stack-controlled side-effect boundary actually invokes the trusted check and blocks on failure/missing evidence. Provider-native calls bypassing EAS remain outside this guarantee.
