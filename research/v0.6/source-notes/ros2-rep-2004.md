# ros-infrastructure/rep

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

REP-2004 communicates package quality through declared policies and justified claims. Its categories cover versioning, change control, documentation, testing, dependencies, platform support, and security, with requirements varying by quality level. It deliberately leaves policy implementation flexible and acknowledges that judgment cannot all be automated. Testing includes feature/API evidence, coverage policy, performance policy, and applicable static analysis. [REP-2004][S1]

## Decisions and limitations

- **ADOPT** evidence and justification for a declared quality target.
- **ADAPT** its categories into candidate ROS2/release checks.
- **REJECT** treating a preset as Quality Level 1 certification or inventing a universal coverage threshold.

EAS inference: read the target package's quality declaration, manifests, CI, tests, dependency declarations, and supported distribution before choosing commands or gates. Optional dependencies and documented exceptions need review. No target ROS2 package was supplied; the audit establishes categories, not package readiness, distribution support, or hardware safety.

## Local impact

[Domain gates](../domain-gates.md): candidate evidence mapping and unresolved package validation; [architecture synthesis](../architecture-synthesis.md): rule enforcement limits.

## Source record

- Repository: https://github.com/ros-infrastructure/rep; inspected revision `11ca24a41f31480dfb9562ba99f2a5b93d3ebda5`.
- S1: `rep-2004.rst` - [requested branch URL](https://github.com/ros-infrastructure/rep/blob/master/rep-2004.rst); [inspected snapshot][S1].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- REP-2004 ends with a public-domain/CC0-1.0-Universal declaration, whichever is more permissive. [Document copyright][S1]

[S1]: https://github.com/ros-infrastructure/rep/blob/11ca24a41f31480dfb9562ba99f2a5b93d3ebda5/rep-2004.rst
