# OpenAI Codex Adapter

## Installation

Run the installation script:

```bash
./scripts/install-codex.sh
```

By default, this installs skills to `~/.agents/skills/`. Some environments may
still discover legacy user entries under `~/.codex/skills/`; duplicate names can
therefore load conflicting instructions.

The installer validates and verifies the current target, then runs the installation
doctor. If legacy duplicates remain, inspect the report and migrate only this
repository's entries:

```bash
./scripts/migrate-legacy-codex.sh
```

The migration preserves `~/.codex/skills/.system` and unrelated skills.

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

Codex uses manifest-rendered copied directories, including skill references,
scripts, and UI metadata. To update:

```bash
cd /path/to/skills
git pull
./scripts/install-codex.sh
```

Verify or diagnose:

```bash
./scripts/validate-skills.sh
./scripts/doctor-installation.sh
./scripts/verify-installation.sh codex ~/.agents/skills
```

## Compatibility Notes

- Most skills work identically in Codex
- Some tools may have different names or capabilities
- Context management skills (`sk-pass-to-*`) are macOS-specific
