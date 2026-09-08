# modelcontextprotocol/modelcontextprotocol

Reviewed: 2026-09-08. Reuse class: **Conceptual reference**. Status: source inspection complete; EAS decisions are proposals.

## Problem and evidence

MCP separates interoperable context and action surfaces: prompts are user-controlled, resources application-driven, and tools model-controlled. These describe interaction ownership, not independent authority to access data or act. Initialization exchanges protocol version and capabilities; operation must respect negotiated features. The security guidance makes consent and host controls explicit and treats tool annotations as untrusted absent a trusted source. [Overview][S1] [Tools][S2] [Prompts][S3] [Resources][S4] [Lifecycle][S5]

## Decisions and limitations

- **ADOPT** separating capability advertisement, compatibility, and authorization.
- **ADAPT** explicit capability declarations to declarative extension metadata.
- **REJECT** interpreting capability presence or a read-only annotation as permission or enforcement.

EAS inference: no `.mcp.json` server launch on discovery; any later integration must name its controlling host and consent boundary. A skill is neither an MCP tool nor automatically an MCP prompt. The audit studies the requested 2025-11-25 specification, not a claim about the latest protocol revision.

## Local impact

[Architecture synthesis](../architecture-synthesis.md): capabilities, effect claims, and provider integration boundaries.

## Source record

- Repository: https://github.com/modelcontextprotocol/modelcontextprotocol; inspected revision `e76e9c572c6f2bfcb730357101acc90f2f802e02`.
- S1: `docs/specification/2025-11-25/index.mdx` - [requested branch URL](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/index.mdx); [inspected snapshot][S1].
- S2: `docs/specification/2025-11-25/server/tools.mdx` - [requested branch URL](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/server/tools.mdx); [inspected snapshot][S2].
- S3: `docs/specification/2025-11-25/server/prompts.mdx` - [requested branch URL](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/server/prompts.mdx); [inspected snapshot][S3].
- S4: `docs/specification/2025-11-25/server/resources.mdx` - [requested branch URL](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/server/resources.mdx); [inspected snapshot][S4].
- S5: `docs/specification/2025-11-25/basic/lifecycle.mdx` - [requested branch URL](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/lifecycle.mdx); [inspected snapshot][S5].

## License and provenance

All analysis is independently paraphrased; no upstream code, prompts, templates, or rule tables are vendored or materially adapted. Before future direct reuse, record file-level license, revision, destination, modifications, and required notices under [EAS provenance policy](../../../docs/PROVENANCE.md).

- The [license notice](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/LICENSE) describes an MIT-to-Apache-2.0 transition, with CC-BY-4.0 for non-specification documentation and unconsented older contributions remaining MIT. File/history review is required before direct reuse; do not flatten this to a single license.

[S1]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/index.mdx

[S2]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/server/tools.mdx

[S3]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/server/prompts.mdx

[S4]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/server/resources.mdx

[S5]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/e76e9c572c6f2bfcb730357101acc90f2f802e02/docs/specification/2025-11-25/basic/lifecycle.mdx
