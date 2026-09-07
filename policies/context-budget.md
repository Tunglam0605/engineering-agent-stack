# Context Budget Policy

## Inputs

Workers receive only the context needed to perform their assignment. Prefer repository references and explicit constraints over copied history.

## Outputs

Workers return concise evidence. Suggested default soft limits:

- scout: <= 800 tokens
- researcher: <= 1200 tokens
- test engineer: <= 1000 tokens plus essential failing output
- reviewer: <= 1500 tokens unless a high-risk audit requires more

These are starting hypotheses, not hard product limits. Benchmarks may change them.

## Prohibited defaults

- full parent conversation cloning
- full source-tree dumps
- repeated logs already available to the parent
- restating the complete plan in every worker result
