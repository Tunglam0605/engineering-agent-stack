# Verification Pattern

## Rule

A model's capability is not evidence that its output is correct.

## Verification ladder

1. Define the exact claim.
2. Run the smallest check that can prove or falsify the claim.
3. Read the result.
4. If it fails, remediate within scope and re-check once.
5. Escalate or stop if the failure exposes broader scope/risk.

## Examples

- documentation change -> link/structure validation
- parser change -> focused unit tests
- backend behavior -> targeted tests + type/lint/build as appropriate
- embedded realtime path -> static review + build + hardware/integration evidence when available
- release-critical change -> independent review plus release gate
