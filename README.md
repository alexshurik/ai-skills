# SK-* Skills

A collection of AI coding agent skills for multi-agent development workflows.

**Compatible with:** Claude Code, OpenAI Codex, Cursor, Kimi/MiniMax

## Quick Start

### Claude Code

```bash
# Install
./scripts/install-claude-code.sh

# Use
/sk-team-help       # Show documentation
/sk-team-feature    # Start full feature workflow
/sk-team-quick      # Quick fix workflow
/sk-onboard         # Project onboarding
/sk-plan-mode      # Create plan before making changes
```

### OpenAI Codex

```bash
./scripts/install-codex.sh
```

### Cursor

```bash
./scripts/generate-cursorrules.sh
cp adapters/cursor/.cursorrules /path/to/project/
```

### Kimi/MiniMax

```bash
./scripts/install-kimi.sh
```

Use with agent team:
```bash
kimi --agent-file ~/.config/agents/agents/sk-team.yaml
```

Or invoke skills directly in Kimi:
```
/skill:sk-team-feature Add user authentication
/skill:sk-code-review
/skill:sk-onboard
```

## What's Included

### Workflow Commands

| Command | Description |
|---------|-------------|
| `/sk-team-feature` | Full workflow for new features with multi-agent team |
| `/sk-team-quick` | Quick workflow for bugfixes and small changes |
| `/sk-team-status` | Show status of active workflows |
| `/sk-team-help` | Documentation for team workflow |

### Onboarding Commands

| Command | Description |
|---------|-------------|
| `/sk-onboard` | Full project onboarding |
| `/sk-discover-project` | Discover project structure and tech stack |
| `/sk-explore-codebase` | Generate navigation rules for AI |

### Planning Commands

| Command | Description |
|---------|-------------|
| `/sk-plan-mode` | Structured planning workflow with file-based plan storage |

### Utility Commands

| Command | Description |
|---------|-------------|
| `/sk-code-review` | Review uncommitted changes |
| `/sk-explore-codestyle` | Generate code style guidelines |

### Context Commands

| Command | Description |
|---------|-------------|
| `/sk-copy-context` | Copy session context to clipboard |
| `/sk-pass-to-claude` | Switch to aclaude with context |
| `/sk-pass-to-minimax` | Switch to mclaude with context |

### Agents

| Agent | Role |
|-------|------|
| `sk-product-analyst` | Requirements gathering (PM + BA) |
| `sk-architect` | System design and task breakdown |
| `sk-tester` | TDD red phase - write failing tests |
| `sk-developer` | TDD green phase - implementation |
| `sk-code-reviewer` | Code quality review |
| `sk-acceptance-reviewer` | Business validation |

## Plan Mode Workflow

For changes that need careful planning before execution:

```
/sk-plan-mode "Refactor authentication to OAuth2"

Phase 1: Understanding → Read files, ask questions
Phase 2: Design → Create implementation plan
Phase 3: Review → Validate approach  
Phase 4: Final Plan → Write plan to .kimi/plan.md

⏸️ Waiting for approval...

User: "Approved"

Execute plan step by step...
```

## Multi-Agent Workflow

```
/sk-team-feature "Add user authentication"

        ┌─────────────────────────────────────────┐
        │              ORCHESTRATOR               │
        │    Coordinates all agents sequentially  │
        └─────────────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼
DISCOVERY              PLANNING              EXECUTION
    │                      │                      │
    ▼                      ▼                 ┌────┴────┐
sk-product-         sk-architect             ▼         ▼
analyst                                  sk-tester  sk-developer
(proposal.md)       (design.md)           (tests)     (code)
                    (tasks.md)                │
                                        ┌─────┴─────┐
                                        ▼           ▼
                                    sk-code-    sk-acceptance-
                                    reviewer    reviewer
                                               (VERIFICATION.md)
```

## Directory Structure

```
skills/
├── workflow/               # Multi-agent team workflow
│   ├── skills/             # Slash commands
│   │   ├── sk-team-feature/
│   │   ├── sk-team-quick/
│   │   ├── sk-team-status/
│   │   └── sk-team-help/
│   └── agents/             # Task tool agents
│       ├── sk-product-analyst.md
│       ├── sk-architect.md
│       ├── sk-tester.md
│       ├── sk-developer.md
│       ├── sk-code-reviewer.md
│       └── sk-acceptance-reviewer.md
│
├── onboarding/             # Project onboarding commands
│   ├── skills/             # Onboarding skills
│   │   ├── sk-discover-project/
│   │   ├── sk-explore-codebase/
│   │   └── sk-onboard/
│   ├── sk-discover-project.md
│   ├── sk-explore-codebase.md
│   └── sk-onboard.md
│
├── planning/               # Planning and analysis workflows
│   └── sk-plan-mode/       # Structured planning with approval workflow
│
├── utilities/              # Standalone tools
│   ├── sk-code-review/
│   └── sk-explore-codestyle/
│
├── context/                # Context management
│   ├── sk-copy-context/
│   ├── sk-pass-to-claude/
│   └── sk-pass-to-minimax/
│
├── shared/                 # Shared resources
│   ├── templates/          # Artifact templates
│   └── context-handoff.md
│
├── scripts/                # Installation scripts
│   ├── install-claude-code.sh
│   ├── install-codex.sh
│   ├── install-kimi.sh
│   ├── generate-cursorrules.sh
│   ├── generate-agents-md.sh
│   └── uninstall.sh
│
├── adapters/               # Platform-specific adapters
│   ├── claude-code/
│   ├── codex/
│   ├── cursor/
│   └── kimi/
│
├── AGENTS.md               # Cross-platform agent docs
├── LICENSE                 # MIT
└── README.md               # This file
```

## Artifacts

All feature development artifacts are stored in:

```
openspec/changes/<feature-name>/
├── proposal.md      # Requirements (Product Analyst)
├── design.md        # Technical design (Architect)
├── tasks.md         # Task breakdown (Architect)
└── VERIFICATION.md  # Acceptance result (Acceptance Reviewer)
```

**Note:** This directory structure is inspired by [OpenSpec](https://openspec.dev/) (Spec-Driven Development), but **you don't need to install OpenSpec** — our workflows use this as a simple convention for organizing artifacts. Directories are created automatically during workflow execution.

## Customization

### Adding New Skills

1. Create directory: `workflow/skills/sk-my-skill/`
2. Create `SKILL.md` with frontmatter
3. Run install script

### Adding New Agents

1. Create file: `workflow/agents/sk-my-agent.md`
2. Run install script

## Uninstallation

```bash
./scripts/uninstall.sh
```

## License

MIT

## Contributing

1. Fork the repository
2. Create your feature branch
3. Submit a pull request

## Related Projects

- [OpenSpec](https://openspec.dev/) - Spec-Driven Development (SDD) framework that inspired our artifact structure
