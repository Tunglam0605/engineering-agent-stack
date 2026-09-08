# openai/openai-agents-python

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

The SDK manages agent loops, checks, and observations. Input checks cover the first agent, output checks the final agent. Function-tool checks cover their own calls, not handoffs, hosted tools, or built-in execution tools. Parallel input checking may allow work before rejection; blocking input checking completes first. [Guardrails][S1]

Traces group a workflow and spans represent nested timed operations. Tracing is enabled by default and supports disabling/sensitive-data controls. The runner advances through model output, handoffs, and tool results with a turn limit. [Tracing][S2] [Running][S3]

## Decisions and limitations

- **ADOPT** named enforcement boundaries and explicit coverage limitations.
- **ADAPT** workflow/trace/span structure into bounded evidence references.
- **REJECT** claims that an output check prevents an already-completed side effect, or that a trace is approval authority.

EAS inference: gates preventing effects must run before those effects through an identified stack-owned boundary. Provider-native calls remain outside coverage unless actually integrated. Record omissions and redact evidence; do not adopt the SDK's export defaults or its runtime.

## Local impact

[Architecture synthesis](../architecture-synthesis.md): enforcement and observation model. Preserve v0.5 durable-state versus observational-log separation.

## Source record

- Repository: https://github.com/openai/openai-agents-python; inspected revision `02c205f9574c765a265ce102dc55da81cdd74b89`.
- S1: `docs/guardrails.md` - [requested branch URL](https://github.com/openai/openai-agents-python/blob/main/docs/guardrails.md); [inspected snapshot][S1].
- S2: `docs/tracing.md` - [requested branch URL](https://github.com/openai/openai-agents-python/blob/main/docs/tracing.md); [inspected snapshot][S2].
- S3: `docs/running_agents.md` - [requested branch URL](https://github.com/openai/openai-agents-python/blob/main/docs/running_agents.md); [inspected snapshot][S3].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- openai/openai-agents-python: root [MIT license](https://github.com/openai/openai-agents-python/blob/02c205f9574c765a265ce102dc55da81cdd74b89/LICENSE) inspected; nested or third-party material still needs its own check.

[S1]: https://github.com/openai/openai-agents-python/blob/02c205f9574c765a265ce102dc55da81cdd74b89/docs/guardrails.md

[S2]: https://github.com/openai/openai-agents-python/blob/02c205f9574c765a265ce102dc55da81cdd74b89/docs/tracing.md

[S3]: https://github.com/openai/openai-agents-python/blob/02c205f9574c765a265ce102dc55da81cdd74b89/docs/running_agents.md
