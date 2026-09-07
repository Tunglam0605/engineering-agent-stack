# Adaptive Context and Result Budget Policy

The objective is to remove **wasted** context and transcript volume without starving an agent of evidence needed to produce a correct result.

Budgets are therefore adaptive guidance, not hard product token limits.

## Three separate budgets

### 1. Input context budget

Workers receive the smallest useful assignment context:

- task objective and acceptance criteria
- relevant constraints and known evidence
- file/symbol references where already known
- only the conversation history needed to avoid ambiguity

Prefer references to repository artifacts over copying full files or full parent history.

### 2. Work budget

The amount of investigation/reasoning/tool work is **not** capped to a small fixed token number by this policy.

Expected posture:

```text
simple / reversible   -> small investigation
normal engineering    -> bounded investigation
uncertain / complex   -> allow more evidence gathering
critical / safety     -> quality and required evidence override cost pressure
```

Escalate when additional low-tier work is unlikely to resolve uncertainty efficiently. Do not keep a cheap worker looping merely to avoid a justified escalation.

### 3. Result budget

Workers return distilled evidence rather than transcripts. Suggested output targets:

| Role | Simple | Normal | Complex/high-risk |
|---|---:|---:|---:|
| Scout | 300-500 | <= 800 | <= 1500 |
| Researcher | <= 600 | <= 1200 | <= 2000 |
| Test Engineer | <= 500 | <= 1000 + essential failure output | <= 2000 + essential failure output |
| Reviewer | <= 600 | <= 1500 | <= 3000 or evidence-required exception |
| Implementer | concise change/evidence summary | evidence-driven | evidence-driven |
| Debugger | concise root-cause/evidence summary | evidence-driven | evidence-driven |
| Architect | concise decision record | evidence-driven | no fixed default when critical evidence requires more |

These are starting hypotheses for benchmark validation. They are not provider-enforced quotas.

## Evidence exception

A budget must never force an agent to omit evidence required to establish correctness, safety, a blocker, or a material trade-off.

When the result exceeds the normal target, prefer:

1. concise summary
2. exact `file:line` / symbol / command evidence
3. artifact references for long logs or generated output
4. only the minimal excerpt needed for the parent decision

## Prohibited defaults

- cloning the full parent conversation into every child
- dumping full source trees into child context
- returning entire source files when `file:line` evidence is sufficient
- repeating logs already available to the parent
- restating the complete plan in every worker result
- recursively forwarding one child's full transcript to another child
- forcing a fixed total-token cap that predictably lowers task quality

## Benchmark rule

Budget changes are accepted only when repeated tasks show that the tighter budget preserves the required quality threshold. Measure input tokens, output tokens, latency, escalation rate, reviewer rejection/rework rate, and final task quality together.
