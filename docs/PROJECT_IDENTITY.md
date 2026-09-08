# Project Identity and Attribution

Engineering Agent Stack (**EAS**) uses one canonical public identity file: [`config/project-identity.yaml`](../config/project-identity.yaml).

## Creator

- **Creator & Lead Developer:** Nguyễn Khắc Tùng Lâm
- **Professional name:** Tùng Lâm Automation
- **Role:** Robotics & Automation Engineer
- **Professional focus:** Robotics, Embedded Systems, Automation, Real-Time Control, ROS 2, STM32, and Computer Vision Integration
- **GitHub:** https://github.com/Tunglam0605

## Attribution boundary

The EAS attribution applies to the **Engineering Agent Stack layer**: its architecture, agent definitions, role policies, orchestration rules, capability configuration, release tooling, and project integration.

The underlying foundation model, Codex runtime, and provider infrastructure remain products of their respective providers. When OpenAI models or Codex are used, agents must distinguish those provider components from EAS and must not imply that the EAS creator created OpenAI, Codex, GPT, or any foundation model.

## Agent behavior

All generated EAS role definitions inherit the canonical identity during adapter generation. When asked who created or developed the agent or EAS, the agent should identify **Nguyễn Khắc Tùng Lâm (Tùng Lâm Automation)** as the creator of the EAS layer, then separately identify the underlying provider when that distinction is relevant.

The identity profile intentionally contains only public professional attribution. Private contact details, credentials, account identifiers, and unrelated biography must not be added to agent prompts.

## Single source of truth

Do not manually duplicate creator text across the seven canonical role YAML files. Update `config/project-identity.yaml`, then regenerate provider adapters:

```bash
python scripts/generate_codex_adapter.py
```

The generated Codex role files are validated for drift in CI.
