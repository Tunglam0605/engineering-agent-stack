# Benchmarking Protocol

## Objective

The benchmark program is designed to answer:

> What is the least expensive/slowest-acceptable compute path that preserves the engineering quality required by the task risk?

This is a **quality-constrained optimization** problem, not a cheapest-model contest.

```text
first:  satisfy correctness / safety / evidence threshold
then:   minimize token cost and latency among qualified variants
```

## Why two stages

Benchmarking itself can waste tokens. The protocol therefore uses **sequential screening**:

### Stage A — screening

Run a small repeat count (`experiment-plan.yaml`, currently 3) for each candidate.

Stop a variant early when:

- it triggers a hard safety failure;
- it repeatedly misses the quality threshold;
- evidence shows it is clearly unsuitable for the role.

This prevents spending confirmation-level tokens on obvious failures.

### Stage B — confirmation

Only screening-qualified contenders advance to the larger repeat count (currently 10).

A routing/model default may be reconsidered only after confirmation runs preserve the required quality and show a material cost or latency advantage.

The repeat counts are candidate protocol values, not statistical guarantees. They can be revised as variance data accumulates.

## Fair comparison controls

For model/profile comparisons, hold constant as much as practical:

- task fixture and case version
- repository/commit under test
- parent instructions and role contract
- tool availability and sandbox permissions
- context supplied to the worker
- acceptance criteria and scoring rubric
- timeout policy
- provider endpoint/billing mode

Record any unavoidable difference.

## Quality scoring

Every benchmark case defines:

- a required `quality_threshold`
- a weighted rubric whose weights sum to 1.0
- a risk class
- whether a safety violation is a hard failure

The final `quality_score` must come from that versioned rubric or an independent evaluator. Cost does not change the score.

For critical cases, a hard safety failure disqualifies the run regardless of weighted score.

## Cost measurement

Preferred order:

1. actual trustworthy per-run billed cost, if the provider exposes it;
2. actual input/output token counts;
3. normalized cost estimate using the dated pricing snapshot.

The current OpenAI pricing file is a normalized API-price proxy. It must **not** be presented as the actual charge for a ChatGPT/Codex subscription run.

## Required comparisons

Initial core campaigns:

| Role | Main comparison |
|---|---|
| Scout | Luna low vs Luna medium vs Terra medium |
| Researcher | Luna medium vs Terra medium |
| Implementer | Terra medium vs Terra high |
| Debugger | Terra high vs Sol high |
| Reviewer | Terra high vs Sol high |
| Architect / critical | Sol high vs Astra high |

The purpose is not to force every higher tier into use. The test asks whether the cheaper tier already clears the quality gate.

## Context experiments

After model-tier baselines, measure context policy independently:

```text
full parent context
vs
bounded task packet
vs
bounded task packet + targeted evidence
```

Track both quality and input-token reduction. Context compression is accepted only if evidence fidelity remains above the case threshold.

## Orchestration experiments

Compare:

```text
single main agent
vs
main + one narrow worker
vs
bounded parallel read workers
```

Record delegated-agent count and peak parallelism where available. A multi-agent topology must earn its coordination/token overhead.

## Promotion rule

No automatic script changes `config/model-profiles.yaml`.

A proposed default change needs:

1. confirmation-quality evidence;
2. no new critical failure mode;
3. documented cost/latency delta;
4. review of variance and task coverage;
5. a normal repository change with CI.

Synthetic fixtures are categorically ineligible as promotion evidence.
