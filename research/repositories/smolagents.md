# huggingface/smolagents

Source: https://github.com/huggingface/smolagents

## Focus

Minimal, model-agnostic agent library with code agents and sandbox integrations.

## Useful patterns

- **ADOPT — minimal core:** orchestration infrastructure should remain understandable and small before abstractions are added.
- **ADOPT — model/tool agnosticism:** roles should not encode vendor assumptions.
- **ADAPT — sandbox-first execution:** code/tool execution requires an enforceable environment boundary.
- **EXPERIMENT — code actions:** letting a model express tool actions as code can be efficient, but is outside the initial stack scope.

## Project consequence

Prefer small explicit contracts and plain configuration over a large framework inside this repository. Add runtime machinery only after a concrete eval requires it.
