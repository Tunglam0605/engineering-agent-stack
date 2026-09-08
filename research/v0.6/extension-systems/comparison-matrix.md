# Extension-system comparison matrix

| Concern | EAS decision | Boundary |
|---|---|---|
| package identity/version/compatibility | **ADOPT** | identity/hash supports reproducibility, not trust or permission |
| progressive skill discovery/loading | **ADAPT** | metadata first; body/resources only after applicability + budget |
| executable plugin factories/hooks | **REJECT v0.6** | discovery must not execute package code |
| config precedence | **ADOPT deterministic fixed layers** | only declared configurable leaves participate |
| recursive preset/config inheritance | **REJECT initially** | avoid ambiguous merge/cycle/policy weakening |
| path/collision/symlink safety | **ADOPT** | cross-platform containment and unique identity required |
| package-defined tools/commands | **REJECT** | descriptors may reference only trusted pre-registered checks |
| guardrails/rules | **ADAPT boundary-specific semantics** | guidance != validator != gate |
| provenance/content hashes | **ADOPT EAS provenance + hashes** | hashes detect drift; they do not prove license/trust |

Proposed allowed precedence: `core defaults < extension defaults < preset < tracked project profile < local override < explicit CLI override`. This is not a permission hierarchy; protected core invariants remain outside it.
