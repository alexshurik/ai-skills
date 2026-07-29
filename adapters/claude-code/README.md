# Claude Code Adapter

## Installation

Run the installation script:

```bash
./scripts/install-claude-code.sh
```

This creates symlinks in `~/.claude/`:
- `~/.claude/skills/sk-*` - Slash commands
- `~/.claude/agents/sk-*` - Subagents launched through the Agent tool (`Task` alias)
- `~/.claude/commands/sk-*` - Additional commands

The manifest also links review evidence, workflow references, templates, and other
internal resources required by the skills. Run `scripts/validate-skills.sh` before
installation and `scripts/verify-installation.sh claude ~/.claude` to verify it.

## Usage

After installation, restart Claude Code and use:

```
/sk-team-help       # Show documentation
/sk-team-feature    # Start full feature workflow
/sk-team-quick      # Quick fix workflow
/sk-team-status     # Check workflow status
/sk-onboard         # Project onboarding
/sk-code-review     # Review committed, staged, unstaged, and untracked changes
```

## How It Works

### Skills (Slash Commands)

Skills are stored in `~/.claude/skills/<name>/SKILL.md` and invoked with `/name`.

Format:
```yaml
---
name: sk-team-feature
description: Full workflow for new features
allowed-tools: Task, Read, Write, Glob, Grep, Bash
---

# Instructions...
```

### Agents (Agent Tool)

Agents are stored in `~/.claude/agents/<name>.md` and invoked through Claude
Code's subagent tool. Current releases call it Agent; `Task` remains an alias:

```
Agent tool:
  subagent_type: "sk-product-analyst"
  prompt: "..."
```

Format:
```yaml
---
name: sk-product-analyst
description: Transform ideas into requirements
tools: WebSearch, Read, Write, AskUserQuestion
color: blue
---

# Agent instructions...
```

### Commands

Commands are stored in `~/.claude/commands/<name>.md` and work like skills but with different format.

## Uninstallation

```bash
./scripts/uninstall.sh
```

## Updating

To update to latest version:

```bash
cd /path/to/skills
git pull
./scripts/install-claude-code.sh
```

Existing symlinked content updates after `git pull`; rerun the installer when the
manifest adds or removes an owned path.
