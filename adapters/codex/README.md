# OpenAI Codex Adapter

## Installation

Run the installation script:

```bash
./scripts/install-codex.sh
```

By default, this copies skills to `~/.agents/skills/` — the location Codex scans for
user-level skills (the agent-agnostic open standard, shared with other agents). The
older `~/.codex/skills/` path is no longer scanned per current Codex docs.

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

## Catalog vs. internal resources

Only **user-invocable** skills (the `sk-team-*`, `sk-onboard`, `sk-code-review`, … )
are installed as catalog entries that Codex surfaces for routing. The workflow
**agents** (`sk-product-analyst`, `sk-developer`, …), review sub-passes, shared docs,
and best-practice profiles are copied as internal **resource files** (under
`agents/`, `review-steps/`, `shared/`, `best-practices/` — no `SKILL.md`), so they do
**not** clutter the skill catalog. The orchestrator skills reference them by path.

## Agent Usage

Agents are internal sub-roles the workflow skills drive; you normally start a workflow
skill rather than invoking an agent directly:

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
