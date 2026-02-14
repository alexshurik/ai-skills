---
name: sk-onboard
version: 1.0.0
description: Full project onboarding - discover structure + generate navigation rules
argument-hint: "[optional: quick|full]"
license: MIT
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Write
  - Task
  - Skill
---

# Full Project Onboarding

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

## Example Output

After running, you'll have:

```
.claude/
├── docs/
│   └── project-map.md        # "Here's what the project does"
└── rules/
    └── codebase-navigation.md # "Check here before creating X"
```

The rules file auto-loads in new Claude Code sessions, providing context-aware assistance.
