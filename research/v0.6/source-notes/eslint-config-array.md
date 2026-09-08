# ESLint `@eslint/config-array`

Pinned upstream commits (2026-09-08): `eslint/rewrite` **81b5f1bf24fa1e59865ce08070054043eb1c2754**; `eslint/eslint` **c8326608e710e670beaf982501aed80ea104919a**. Sources: https://github.com/eslint/rewrite and https://github.com/eslint/eslint. The repositories were cloned and implementation plus tests inspected.

## Problem and evidence

`@eslint/config-array` resolves an ordered array of config objects into deterministic, file-aware results. Matching and order are implemented in `packages/config-array/src/config-array.js` (`ConfigArray#isRoot`, `#getConfigWithStatus`, criteria matching, ignore handling, and cache/index logic); `packages/config-array/tests/config-array.test.js` covers precedence, matching, ignores, and errors. Object validation and merge semantics are schemas in `packages/config-array/src/base-schema.js` and `src/files-and-ignores-schema.js`: schemas validate keys/types and define field-specific merge/normalize behavior instead of generic overwrite. Types are in `src/types.ts`, with tests in `tests/types/`.

ESLint flat-config integration and migration are in `lib/config/config-loader.js`, `lib/config/config.js`, and `lib/config/flat-config-array.js`; tests under `tests/lib/config/` cover loading, composition, and legacy-to-flat migration. Resolution is ordered and base-path aware, and migration translates legacy concepts without executable match callbacks.

## EAS decisions

**ADAPT** explicit field-specific merge/validation and deterministic ordered matching. EAS packages should declare provider-neutral fields, schemas, and precedence, exposing which entries matched and why.

**REJECT** generic “later file wins”: matching scope, ignores, and field semantics mean blind replacement can erase capabilities or safety policy. **REJECT** executable match functions/plugins and remote loading because they make resolution non-reproducible and widen the execution boundary. EAS uses declarative predicates and bounded adapters.

Local artifact affected: `research/v0.6/contract-freeze.md`. No code or prompts copied; concepts are paraphrased. `@eslint/config-array` is MIT licensed (`packages/config-array/LICENSE`); provenance is recorded here.
