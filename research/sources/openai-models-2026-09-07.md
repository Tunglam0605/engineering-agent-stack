# OpenAI model palette snapshot

Retrieved: 2026-09-07

Primary sources:

- https://developers.openai.com/api/docs/models
- https://developers.openai.com/api/docs/models/gpt-5.6-terra
- https://developers.openai.com/api/docs/models/gpt-5.6-luna

## Relevant models

| Model | Positioning | Input / 1M | Output / 1M | Use in this project |
|---|---|---:|---:|---|
| `gpt-5.6-luna` | cost-sensitive, high-volume | $0.20 | $1.20 | narrow scanning/classification candidate |
| `gpt-5.6-terra` | balance intelligence and cost | $2.00 | $12.00 | ordinary work and deep supporting-agent candidate |
| `gpt-5.6-sol` (`gpt-5.6` alias) | complex professional work | $4.00 | $20.00 | critical reasoning candidate |
| `gpt-6-astra` | hardest end-to-end work | $10.00 | $50.00 | exceptional benchmark candidate, not default |

Prices are a point-in-time research input, not a contractual project constant. Provider adapters must not assume that a model remains available or that price/performance ordering remains unchanged.

## Decision

`gpt-6-astra` is intentionally not the default critical tier yet. The project optimizes quality under cost/latency constraints, so a more expensive frontier model must demonstrate measurable quality gains on critical evals before being promoted.
