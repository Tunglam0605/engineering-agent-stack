# OpenAI model routing source snapshot — 2026-09-23

Status: verified against OpenAI public documentation on 2026-09-23.

## Primary sources

- OpenAI API changelog: https://developers.openai.com/api/docs/changelog
- GPT-6 Sol model page: https://developers.openai.com/api/docs/models/gpt-6-sol
- GPT-6 Luna model page: https://developers.openai.com/api/docs/models/gpt-6-luna
- GPT-6 model migration guidance: https://developers.openai.com/api/docs/guides/latest-model
- OpenAI API pricing: https://developers.openai.com/api/docs/pricing

## Verified facts used by EAS

- GPT-6 Sol model ID: `gpt-6-sol`.
- GPT-6 Luna model ID: `gpt-6-luna`.
- Both support reasoning efforts from `none` through `max`, including `medium`, `high`, and `xhigh`.
- GPT-6 Sol is positioned for complex coding and agentic workflows.
- GPT-6 Luna is positioned for focused, high-volume work.
- Standard short-context pricing published for prompts up to 272K input tokens is $2 input / $10 output per 1M tokens for GPT-6 Sol and $0.10 input / $0.50 output for GPT-6 Luna.
- OpenAI released GPT-6 Sol and GPT-6 Luna on 2026-09-22.

## EAS routing interpretation

The provider facts above do not by themselves prove a best role mapping. EAS therefore keeps role identity separate from model identity and uses a quality-gate-first migration:

- `cheap` -> GPT-6 Luna.
- `standard`, `deep`, `critical` -> GPT-6 Sol for the initial migration.
- GPT-6 Luna remains a benchmark candidate for wider standard/deep use.
- GPT-6 Astra remains a critical benchmark candidate.
- GPT-5.6 models remain only as migration baselines until repeated controlled runs establish the new quality/cost/latency envelope.

No routing default should be changed from price alone when the task quality threshold is not met.
