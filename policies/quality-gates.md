# Quality Gates

## Universal gate

No change is complete without fresh validation or an explicit, documented validation gap.

## Risk tiers

### Low

Targeted validation by the executing lane is sufficient.

### Normal

Targeted tests/build plus review when behavior crosses module boundaries.

### High

Independent reviewer required. Validate integration and regression risks.

### Critical

Independent high-capability review plus the strongest practical verification available for the domain. Hardware/release/security evidence may be mandatory.

## Retry bound

One automatic remediation and one targeted re-check is the default. A second failure or broader causal layer escalates rather than looping indefinitely.
