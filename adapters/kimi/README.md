# Kimi/MiniMax Adapter

## Overview

Kimi Code CLI supports these skills through the standard Agent Skills format.

## Installation

```bash
./scripts/install-kimi.sh
```

This will:
1. Link all skills to `~/.config/agents/skills/`
2. Create agent definitions in `~/.config/agents/agents/`

## Usage

### Option 1: Full Agent Team

Run Kimi with the multi-agent team:

```bash
kimi --agent-file ~/.config/agents/agents/sk-team.yaml
```

Then request features:
```
Add user authentication with OAuth
```

The orchestrator will coordinate subagents:
- `product-analyst` → Requirements
- `architect` → Design
- `tester` → Tests
- `developer` → Implementation
- `code-reviewer` → Review
- `acceptance-reviewer` → QA

### Option 2: Individual Skills

Use skills directly without the agent team:

```bash
kimi
```

Then invoke skills:
```
/skill:sk-team-feature Add user authentication
/skill:sk-code-review
/skill:sk-explore-codestyle
/skill:sk-onboard
/skill:sk-discover-project
/skill:sk-explore-codebase
```

### Option 3: Flow Skills (Automated Workflows)

Flow skills run multi-step workflows automatically following a diagram:

```bash
kimi
```

Then execute flow:
```
/flow:sk-team-feature-flow Add user authentication
```

**Difference:**
- `/skill:sk-team-feature` — Orchestrator controls each phase manually
- `/flow:sk-team-feature-flow` — Automatic execution through all phases

Use `/skill` for flexibility, `/flow` for hands-off automation.

### Option 4: Project-Level Skills

For project-specific usage, create `.kimi/skills/` or `.agents/skills/`:

```bash
mkdir -p .kimi/skills
cp -r workflow/skills/sk-team-feature .kimi/skills/
```

## Available Skills

### Standard Skills

| Skill | Description |
|-------|-------------|
| `sk-team-feature` | Full multi-agent feature development |
| `sk-team-quick` | Quick fix workflow |
| `sk-team-status` | Check workflow status |
| `sk-team-help` | Show documentation |
| `sk-code-review` | Review uncommitted changes |
| `sk-explore-codestyle` | Generate code style guidelines |
| `sk-onboard` | Full project onboarding |
| `sk-discover-project` | Discover project structure |
| `sk-explore-codebase` | Generate navigation rules |
| `sk-copy-context` | Copy context to clipboard |

### Flow Skills (Automated)

| Flow | Description |
|------|-------------|
| `sk-team-feature-flow` | Automated feature development (all phases auto-executed) |
| `sk-team-quick-flow` | Automated quick fixes (Developer → Reviewer only) |

## Architecture

```
~/.config/agents/
├── skills/                    # Symlinks to skill directories
│   ├── sk-team-feature/ → SKILL.md
│   ├── sk-code-review/ → SKILL.md
│   └── ...
└── agents/
    ├── sk-team.yaml          # Main agent with subagents
    ├── sk-product-analyst.yaml
    ├── sk-architect.yaml
    ├── sk-tester.yaml
    ├── sk-developer.yaml
    ├── sk-code-reviewer.yaml
    ├── sk-acceptance-reviewer.yaml
    └── references/           # Agent system prompts
        ├── sk-product-analyst.md
        └── ...
```

## Compatibility

| Feature | Support | Notes |
|---------|---------|-------|
| Skills | ✓ Full | All 12 skills work |
| Subagents | ✓ Full | Via `Task` tool |
| Flow skills | ✓ Full | Multi-turn workflows |
| Slash commands | ✓ Full | `/skill:name` syntax |

## Limitations

- **No AGENTS.md auto-loading** — Kimi uses `${KIMI_AGENTS_MD}` variable
- **Different paths** — Uses `~/.config/agents/` instead of `~/.claude/`

## See Also

- [Kimi CLI Agents Docs](https://moonshotai.github.io/kimi-cli/en/customization/agents.html)
- [Kimi CLI Skills Docs](https://moonshotai.github.io/kimi-cli/en/customization/skills.html)
