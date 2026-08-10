# Kimi Code CLI Adapter

## Overview

The adapter targets the current standalone Kimi Code CLI. It installs standard
Agent Skills and Markdown agent profiles; the retired Python `kimi-cli` YAML format
is not supported.

## Install

Install or upgrade Kimi Code with the official installer, then render this suite:

```bash
curl -fsSL https://code.kimi.com/kimi-code/install.sh | bash
./scripts/install-kimi.sh
```

The SK installer writes receipt-owned files under `~/.kimi-code/`, which Kimi
discovers natively. If an older SK adapter receipt exists under
`~/.config/agents/`, the installer removes only those receipt-owned legacy files.
It checks capabilities (`--agent-file` with Markdown support) instead of comparing
version numbers from the unrelated legacy release line.

## Full team

```bash
kimi --agent-file ~/.kimi-code/agents/sk-team.md
```

The main profile may delegate to the eight workflow roles. Ordinary roles are
leaves. `sk-review-orchestrator` alone may delegate one level deeper to exactly
three leaf reviewers: architecture-design, correctness-safety, and
engineering-quality. Current Kimi returns background subagent results to the parent
automatically, so the workflow does not poll task status.

## Individual skills

Start Kimi normally and invoke any installed public skill:

```text
/skill:sk-team-feature Add user authentication
/skill:sk-team-quick Fix the failing login test
/skill:sk-code-review
/skill:sk-onboard
```

Installed public skills are:

- `sk-team-feature`, `sk-team-quick`, `sk-team-status`, `sk-team-help`
- `sk-code-review`, `sk-explore-codestyle`, `sk-copy-context`
- `sk-onboard`, `sk-discover-project`, `sk-explore-codebase`

Use Kimi's native `/plan`, Shift+Tab plan toggle, or `kimi --plan` for standalone
planning. The feature workflow still keeps durable approved requirements and design
under `openspec/changes/<name>/`; a separate SK planning skill is unnecessary.

## Installed tree

```text
~/.kimi-code/
├── skills/                      # Standard Agent Skills
└── agents/
    ├── sk-team.md               # Main workflow profile
    ├── sk-product-analyst.md
    ├── sk-architect.md
    ├── sk-tester.md
    ├── sk-developer.md
    ├── sk-review-orchestrator.md
    ├── sk-review-architecture-design.md
    ├── sk-review-correctness-safety.md
    ├── sk-review-engineering-quality.md
    ├── sk-acceptance-reviewer.md
    └── references/              # Shared policies, templates, and tooling
```

The generated main profile includes `${base_prompt}`, so Kimi retains its native
workspace instructions, skills, tools, and plugin context. Platform-specific paths
inside role prompts are rendered to `~/.kimi-code/agents/references/`.

## Official documentation

- [Getting started](https://www.kimi.com/code/docs/en/kimi-code-cli/guides/getting-started.html)
- [Agents and sub-agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html)
- [Agent Skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html)
- [Migrating from kimi-cli](https://www.kimi.com/code/docs/en/kimi-code-cli/guides/migration.html)
