# OpenAI Codex Adapter

## Installation

Run the installation script:

```bash
./scripts/install-codex.sh
```

By default, this copies skills to `~/.codex/skills/`.

To use a different location:
```bash
CODEX_SKILLS_DIR=/custom/path ./scripts/install-codex.sh
```

## Usage

After installation, use the skills in Codex:

```
/sk-team-help       # Show documentation
/sk-team-feature    # Start full feature workflow
/sk-team-quick      # Quick fix workflow
/sk-onboard         # Project onboarding
```

## Skill Format

Codex uses the same SKILL.md format as Claude Code:

```yaml
---
name: sk-team-feature
description: Full workflow for new features
allowed-tools: Task, Read, Write
---

# Instructions...
```

## Agent Usage

In Codex, agents are invoked similarly:

```
Use the sk-product-analyst agent to gather requirements.
```

## Updating

Unlike Claude Code (which uses symlinks), Codex uses copied files. To update:

```bash
cd /path/to/skills
git pull
./scripts/install-codex.sh
```

## Compatibility Notes

- Most skills work identically in Codex
- Some tools may have different names or capabilities
- Context management skills (`sk-pass-to-*`) are macOS-specific
