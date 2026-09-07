# infiquetra/infiquetra-codex-plugins

Source: https://github.com/infiquetra/infiquetra-codex-plugins

## Focus

Verified Codex workflows with explicit execution contracts, managed compute profiles, independent review and runtime/result validation.

## Useful patterns

- Logical role is separated from compute profile.
- One maintained mapping resolves semantic execution classes to model/reasoning settings.
- Independent reviewer is not the implementation agent or its descendant.
- Concurrent writers must have disjoint write sets.
- Results are typed/bounded rather than free-form orchestration transcripts.
- Automatic remediation/recheck loops are bounded.

## Risks for this project

- Full workflow-contract infrastructure is heavy for small tasks.
- Provider-runtime verification details should remain inside adapters, not canonical roles.

## Decisions

- **ADOPT:** role/compute separation, independent review, disjoint write ownership, bounded result contracts.
- **ADAPT:** workflow contracts into a lighter default policy with strict mode available for high-risk changes.
