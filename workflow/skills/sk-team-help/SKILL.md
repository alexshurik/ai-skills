---
name: sk-team-help
version: 1.0.0
description: Show help and documentation for multi-agent team workflow
license: MIT

# Cross-platform hints
platforms:
  codex: true
  cursor: true
  kimi: true
---

# /sk-team-help - Multi-Agent Team Documentation

<sk-team-help>

Display the following help documentation to the user:

---

# Multi-Agent Development Team

A structured workflow system with specialized agents for software development.

## Commands

| Command | Description |
|---------|-------------|
| `/sk-team-feature <description>` | Full workflow for new features |
| `/sk-team-quick <description>` | Quick workflow for bugfixes |
| `/sk-team-status` | Show status of active workflows |
| `/sk-team-help` | Show this help |

## Architecture

```
                       ORCHESTRATOR
     (skill: sk-team-feature / sk-team-quick / sk-team-status)
        Routes tasks, controls workflow, tracks state
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
    DISCOVERY             PLANNING            EXECUTION
         │                    │                    │
         ▼                    ▼               ┌────┴────┐
  sk-product-          sk-architect           ▼         ▼
  analyst                                  sk-       sk-
  (PM + BA)                               tester   developer
                                           (TDD)
                                             │
                                       ┌─────┴─────┐
                                       ▼           ▼
                                   sk-code-    sk-acceptance-
                                   reviewer    reviewer
```

## Agents (subagent_type for Task tool)

| Agent | Role | Purpose |
|-------|------|---------|
| `sk-product-analyst` | Discovery | WHAT & WHY - requirements, acceptance criteria |
| `sk-architect` | Planning | HOW - system design, task breakdown |
| `sk-tester` | TDD Red | Write failing tests before code |
| `sk-developer` | TDD Green | Implement code to pass tests |
| `sk-code-reviewer` | Review | Code quality, security, patterns |
| `sk-acceptance-reviewer` | Acceptance | Verify business requirements met |

## Workflows

### Full Workflow (`/sk-team-feature`)

For new features, significant changes, complex work:

```
1. sk-product-analyst → proposal.md (vision + requirements)
2. sk-architect → design.md + tasks.md (system design)
3. sk-tester → Tests (failing - TDD red phase)
4. sk-developer → Code (tests pass - TDD green phase)
5. sk-code-reviewer → Quality check (may loop to Developer)
6. sk-acceptance-reviewer → VERIFICATION.md (final check)
```

**Example:**
```
/sk-team-feature Add user authentication with OAuth2
```

### Quick Workflow (`/sk-team-quick`)

For bugfixes, typos, small changes:

```
1. sk-developer → Fix + Tests
2. sk-code-reviewer → Quick review
```

**Example:**
```
/sk-team-quick Fix null pointer in calculateTotal function
```

## Artifacts

All artifacts stored in OpenSpec structure:

```
openspec/changes/<feature-name>/
├── proposal.md      # Vision, requirements, acceptance criteria
├── design.md        # System design, architecture decisions
├── tasks.md         # Implementation task breakdown
└── VERIFICATION.md  # Final acceptance verification
```

## TDD Approach

The system enforces Test-Driven Development:

1. **Red Phase** (sk-tester): Write failing tests based on requirements
2. **Green Phase** (sk-developer): Write minimum code to pass tests
3. **Refactor** (sk-developer): Clean up while keeping tests green

## Agent Invocation

Orchestrator uses Task tool to invoke agents:

```
Task tool:
  subagent_type: "sk-product-analyst"
  prompt: |
    Feature: <description>
    ...
```

Each agent runs in isolated context with specific tools.

## Agent Colors (UI)

| Agent | Color |
|-------|-------|
| sk-product-analyst | Blue |
| sk-architect | Green |
| sk-tester | Yellow |
| sk-developer | Cyan |
| sk-code-reviewer | Orange |
| sk-acceptance-reviewer | Purple |

## Best Practices

### When to Use Full Workflow
- New features
- Complex changes
- Multiple components affected
- Design decisions needed

### When to Use Quick Workflow
- Bug fixes
- Typos
- Single-file changes
- Clear, simple tasks

### Tips
- Let the Product Analyst ask questions
- Don't skip phases for "simple" features
- Trust the TDD process
- Review Code Reviewer feedback carefully

## Getting Started

```
# Start a new feature
/sk-team-feature <describe your feature>

# Fix a bug
/sk-team-quick <describe the bug>

# Check workflow status
/sk-team-status
```

</sk-team-help>
