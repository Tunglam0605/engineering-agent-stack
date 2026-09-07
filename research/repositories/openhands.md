# OpenHands/OpenHands

Source: https://github.com/OpenHands/OpenHands

## Focus

Self-hosted control center that can operate multiple coding-agent backends and isolate runtime responsibilities across services.

## Useful patterns

- **ADOPT — control-plane/runtime separation:** UI/orchestration, agent runtime and automation scheduling are separate responsibilities.
- **ADOPT — sandbox backends:** local, container, VM and remote execution need explicit isolation boundaries.
- **ADAPT — multi-backend adapter design:** one control surface can route to different agent providers without redefining role semantics.
- **ADAPT — automation separation:** scheduled/webhook dispatch is a separate service concern from agent reasoning.

## Project consequence

Provider adapters must not become the canonical role source. A future runtime should separate orchestration/control-plane concerns from execution backends and automation triggers.
