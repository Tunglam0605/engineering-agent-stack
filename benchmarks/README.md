# Benchmarks

Benchmarks compare compute profiles and orchestration choices under repeatable tasks.

Minimum record:

```text
case_id
role / workflow
provider + model
reasoning tier
input tokens
output tokens
latency
estimated cost
quality score
pass/fail
notes
```

Key experiments:

- Luna vs Terra for repository scanning
- Terra medium vs high for implementation/debugging
- Terra high vs Sol high for review on high-risk cases
- single-agent vs delegated discovery
- full-context vs bounded-context delegation
- generic core role vs domain specialist

No default routing change should be justified by cost alone if quality falls below the task threshold.
