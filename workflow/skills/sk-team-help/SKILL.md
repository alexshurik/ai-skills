---
name: sk-team-help
version: 1.1.0
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
   ┌──────────────┬───────────┼──────────────┬───────────────┐
   ▼              ▼           ▼              ▼               ▼
DISCOVERY    [RESEARCH]   PLANNING     [DOC REVIEW]      EXECUTION
   │              │           │              │               │
   ▼              ▼           ▼              ▼          ┌─────┴─────┐
sk-product-  sk-          sk-architect  sk-doc-          ▼           ▼
analyst      researcher                 reviewer       sk-        sk-
(PM + BA)    (optional)                 (optional)    tester    developer
                                                       (TDD)
                                                         │
                                                   ┌─────┴─────┐
                                                   ▼           ▼
                                               sk-review-  sk-acceptance-
                                               orchestrator reviewer
```

Research and Doc Review are **optional** phases — the orchestrator offers them and
runs them only on request.

## Agents (subagent_type for Task tool)

| Agent | Role | Purpose |
|-------|------|---------|
| `sk-product-analyst` | Discovery | WHAT & WHY - requirements, acceptance criteria |
| `sk-researcher` | Research (optional) | Investigate unknown domains, APIs, best practices |
| `sk-architect` | Planning | HOW - system design, task breakdown |
| `sk-doc-reviewer` | Doc Review (optional) | Consistency & alignment check before testing |
| `sk-tester` | TDD Red | Write failing tests before code |
| `sk-developer` | TDD Green | Implement code to pass tests |
| `sk-review-orchestrator` | Review | Dispatches contract/security, architecture, abstraction, structure, imports, stack, and instruction-quality lenses |
| `sk-acceptance-reviewer` | Acceptance | Verify business requirements met |

## Workflows

### Full Workflow (`/sk-team-feature`)

For new features, significant changes, complex work:

```
1. sk-product-analyst → proposal.md (vision + requirements)
   1.5 sk-researcher → RESEARCH.md (optional — unknown domains/APIs)
2. sk-architect → design.md + tasks.md (system design)
   2.5 sk-doc-reviewer → DOC_REVIEW.md (optional — alignment check)
3. sk-tester → Tests (failing - TDD red phase)
4. sk-developer → Code (tests pass - TDD green phase)
5. sk-review-orchestrator → Quality check (may loop to Developer)
6. sk-acceptance-reviewer → VERIFICATION.md (final check)
7. Orchestrator → RETROSPECTIVE.md (lesson disposition)
```

**Approval is required between every phase** — the orchestrator stops after each phase
and waits for explicit user approval before continuing.

**Example:**
```
/sk-team-feature Add user authentication with OAuth2
```

### Quick Workflow (`/sk-team-quick`)

For bugfixes, typos, small changes (four phases):

```
1. sk-architect → Brief design note (quick mode)
2. sk-developer → Fix + Tests
3. sk-review-orchestrator → Quality check (all applicable review lenses)
4. sk-acceptance-reviewer → Verify fix + write docs (quick mode)
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
├── RESEARCH.md      # Technology findings (optional)
├── design.md        # System design, architecture decisions
├── tasks.md         # Implementation task breakdown
├── DOC_REVIEW.md    # Alignment verification (optional)
├── CODE_REVIEW.md   # Full latest review verdict + provenance
├── VERIFICATION.md  # Final acceptance verification
└── RETROSPECTIVE.md # Escaped signals + lesson disposition
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
| sk-researcher | Teal |
| sk-architect | Green |
| sk-doc-reviewer | Magenta |
| sk-tester | Yellow |
| sk-developer | Cyan |
| sk-review-orchestrator | Orange |
| sk-acceptance-reviewer | Purple |

## How Agents Stay On-Project

- **Project conventions.** `sk-developer` and `sk-review-orchestrator` load
  stack-specific profiles plus `.agents/best-practices/project/`. Generated
  `coder.md`/`reviewer.md` contain Enforced and Approved rules only;
  `evidence.md` keeps Observed and Legacy patterns non-normative. Sample frequency
  never becomes an instruction by itself.

- **Architecture gates.** Planning names one owner per concern, trust-boundary
  models, reuse decisions, abstraction budget, module-growth forecast, and
  infrastructure non-goals. Developer re-checks these before the first edit.

- **Independent review.** Review includes complete tracked/untracked scope and
  separate lenses for contract/security, layers, abstraction cost, structure,
  imports, stack rules, and applicable instruction quality. Baseline debt is shown
  separately from change-caused findings.

- **Clarification (handoff protocol).** Subagents cannot reach the user directly. When one
  hits a genuine blocker it returns a `## NEEDS USER INPUT` block; the orchestrator surfaces
  the questions verbatim, collects answers, and re-dispatches — it never answers on your
  behalf or auto-proceeds.

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
- Review code review feedback carefully

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
