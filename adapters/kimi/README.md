# Kimi Code CLI Adapter

## Overview

Kimi Code CLI supports these skills through the standard Agent Skills format.

## Installation

```bash
./scripts/install-kimi.sh
```

This will:
1. Render all complete skill directories to `~/.config/agents/skills/`
2. Generate thin agent definitions from the canonical manifest
3. Use the canonical `sk-team-feature` prompt as the team system prompt

The installer no longer embeds a second hard-coded workflow.
Generated subagent definitions target the current `Agent` tool introduced in Kimi
1.25. Upgrade older Kimi installations before using the team agent. The installer
verifies rendered files and warns when a detected local CLI is older than 1.25; it
does not upgrade Kimi itself.

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
- `review-orchestrator` → Review
- `acceptance-reviewer` → QA

Kimi subagents have isolated context and return their final result to the root.
Stable Kimi CLI does not allow a subagent to create another subagent, so the
generated root team registers all seven review lenses directly. During full review
the root dispatches those leaf reviewers over one shared evidence snapshot; this
keeps independent review without nested-agent support. Large reports live in
git-local workflow artifacts, while the Agent mailbox returns compact receipts.

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

### Option 3: Project-Level Skills

For project-specific usage, create `.kimi/skills/` or `.agents/skills/`:

```bash
mkdir -p .kimi/skills
cp -r workflow/skills/sk-team-feature .kimi/skills/
```

This copies one directly invocable skill only. Use `install-kimi.sh` for the full
team plus all internal resources.

## Available Skills

### Standard Skills

| Skill | Description |
|-------|-------------|
| `sk-team-feature` | Full multi-agent feature development |
| `sk-team-quick` | Quick fix workflow |
| `sk-team-status` | Check workflow status |
| `sk-team-help` | Show documentation |
| `sk-code-review` | Review committed, staged, unstaged, and untracked changes |
| `sk-explore-codestyle` | Generate code style guidelines |
| `sk-plan-mode` | Structured planning with file-based plan storage |
| `sk-onboard` | Full project onboarding |
| `sk-discover-project` | Discover project structure |
| `sk-explore-codebase` | Generate navigation rules |
| `sk-copy-context` | Copy context to clipboard |

## Architecture

```
~/.config/agents/
├── skills/                    # Manifest-rendered complete skill directories
│   ├── sk-team-feature/
│   ├── sk-code-review/
│   └── ...
└── agents/
    ├── sk-team.yaml          # Main agent with subagents
    ├── sk-product-analyst.yaml
    ├── sk-architect.yaml
    ├── sk-tester.yaml
    ├── sk-developer.yaml
    ├── sk-review-orchestrator.yaml
    ├── sk-review-security.yaml
    ├── sk-review-architecture.yaml
    ├── ...                    # Seven root-dispatchable leaf review lenses
    ├── sk-acceptance-reviewer.yaml
    └── references/           # Agent prompts and shared resources
        ├── sk-team-feature.md # Generated prompt with embedded phase prompts
        ├── sk-product-analyst.md
        └── ...
```

## Compatibility

| Feature | Support | Notes |
|---------|---------|-------|
| Skills | ✓ Full | All 11 manifest catalog/onboarding skills work |
| Subagents | ✓ Full | Via the current `Agent` tool |
| Nested subagents | Root-owned | Review lenses are registered at root because stable Kimi children cannot nest |
| Slash commands | ✓ Full | `/skill:name` syntax |

## Limitations

- **AGENTS.md context** — the generated team prompt includes `${KIMI_AGENTS_MD}`
- **Different paths** — Uses `~/.config/agents/` instead of `~/.claude/`
- **No hard-coded Kimi plan path** — `sk-plan-mode` reuses an existing host plan
  directory, otherwise defaults to `.agents/plans/<slug>.md`

## See Also

- [Kimi CLI Agents Docs](https://moonshotai.github.io/kimi-cli/en/customization/agents.html)
- [Kimi CLI Skills Docs](https://moonshotai.github.io/kimi-cli/en/customization/skills.html)
