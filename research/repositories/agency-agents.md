# msitarzewski/agency-agents

Source: https://github.com/msitarzewski/agency-agents

## Focus

Large catalog of domain-specialized agent personas with explicit expertise, workflows and deliverable orientation; includes engineering roles such as embedded firmware, architecture, code review and multi-agent systems.

## Useful patterns

- Strong role specialization and recognizable responsibilities.
- Deliverable-focused descriptions rather than generic "be an expert" prompts.
- Install/select subsets rather than requiring one monolithic team.
- Rich domain catalog is useful as a taxonomy reference.

## Risks for this project

- A very large catalog would increase routing complexity and maintenance burden.
- Personality detail can consume context without improving engineering outcomes.
- A specialist catalog alone does not solve compute-tier selection or token control.

## Decisions

- **ADOPT:** explicit mission, workflow and deliverable contracts.
- **ADAPT:** specialist taxonomy; start from a much smaller engineering set.
- **EXPERIMENT:** determine when a specialist beats a generic core role plus skill.
- **REJECT:** installing/activating the full catalog by default.
