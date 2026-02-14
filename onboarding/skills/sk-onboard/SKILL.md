---
name: sk-onboard
version: 1.0.0
description: Full project onboarding - discover structure + generate navigation rules
license: MIT
platforms:
  codex: true
  cursor: true
  kimi: true
---

# /sk-onboard - Full Project Onboarding

<sk-onboard>

Run both discovery skills to generate complete project documentation for AI agents and developers.

## Process

### 1. Run discover-project

Execute `/sk-discover-project` to generate `.claude/docs/project-map.md`:
- Tech stack detection
- Domain discovery
- API endpoints mapping
- Key files identification

### 2. Run explore-codebase

Execute `/sk-explore-codebase` to generate `.claude/rules/codebase-navigation.md`:
- Check-before-create rules
- Naming conventions
- Project structure patterns

### 3. Summary

Display combined results:
- Tech stack summary
- Number of domains, endpoints, services discovered
- Paths to both generated files
- Reminder about auto-loading rules

## Modes

**`full` (default):**
- Complete API endpoint extraction with schemas and auth info
- Detailed domain feature analysis
- Full check-before-create rules

**`quick`:**
- Skip detailed endpoint extraction
- Focus on high-level structure
- Faster execution for large codebases

## Output Files

| File | Purpose | Auto-loads |
|------|---------|------------|
| `.claude/docs/project-map.md` | Project overview for onboarding | No |
| `.claude/rules/codebase-navigation.md` | Navigation rules for AI | Yes |

## When to Use

- **New to project:** Run `/sk-onboard` once
- **After major changes:** Re-run to update both files
- **Just need navigation:** Run `/sk-explore-codebase` only
- **Just need overview:** Run `/sk-discover-project` only

## Your Task

1. Run `sk-discover-project` workflow
2. Run `sk-explore-codebase` workflow  
3. Report results to user

</sk-onboard>
