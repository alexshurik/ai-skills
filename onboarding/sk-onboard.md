---
name: sk-onboard
version: 1.0.0
description: Discover a project and generate its map, navigation rules, and authoritative convention profiles
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

Execute `sk-discover-project` to generate `.claude/docs/project-map.md`:
- Tech stack detection
- Domain discovery
- API endpoints mapping
- Key files identification

### 2. Run explore-codebase

Execute `sk-explore-codebase` to generate navigation rules AND the project
convention profile:
- `.claude/rules/codebase-navigation.md` — check-before-create rules, structure
- `.agents/best-practices/project/{coder,reviewer}.md` — Enforced and Approved
  project conventions loaded by `sk-*` implementation/review agents
- `.agents/best-practices/project/evidence.md` — Observed and Legacy/uncertain
  source patterns that are evidence, not automatic instructions

### 3. Summary

Display combined results:
- Tech stack summary
- Number of domains, endpoints, services discovered
- Paths to all generated artifacts
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
| `.agents/best-practices/project/coder.md` | Project code-style conventions | Loaded by sk-* agents |
| `.agents/best-practices/project/reviewer.md` | Same rules as review checks | Loaded by sk-* agents |
| `.agents/best-practices/project/evidence.md` | Non-normative observations and legacy patterns | No |

## When to Use

- **New to project:** Run `sk-onboard` once
- **After major changes:** Re-run to update the project map, navigation, and profiles
- **Just need navigation/profiles:** Run `sk-explore-codebase` only
- **Just need overview:** Run `sk-discover-project` only

## Example Output

After running, you'll have:

```
.claude/
├── docs/
│   └── project-map.md        # "Here's what the project does"
└── rules/
    └── codebase-navigation.md # "Check here before creating X"
.agents/
└── best-practices/
    └── project/
        ├── coder.md           # Enforced and Approved coding rules
        ├── reviewer.md        # Matching review checks
        └── evidence.md        # Observed and Legacy/uncertain evidence
```

The Claude rule auto-loads in new Claude Code sessions. The `sk-*` implementation
and review agents load the project convention profiles on every supported host.
