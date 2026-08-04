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

# sk-team-help - Multi-Agent Team Documentation

<sk-team-help>

Display the following help documentation to the user:

---

# Multi-Agent Development Team

A structured workflow system with specialized agents for software development.

## Skills

| Skill | Description |
|---------|-------------|
| `sk-team-feature <description>` | Full workflow for new features |
| `sk-team-quick <description>` | Quick workflow for bugfixes |
| `sk-team-status` | Show status of active workflows |
| `sk-team-help` | Show this help |

Claude invokes skills as `/skill-name`, Codex as `$skill-name` or through
`/skills`, Kimi as `/skill:skill-name`, and Cursor through its slash menu.

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

## Agents (delegated subagent roles)

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

### Full Workflow (`sk-team-feature`)

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
8. Orchestrator → Archive to openspec/completed/<feature-name>/
```

**Approval is required between every phase** — the orchestrator stops after each phase
and waits for explicit user approval before continuing.

**Example:**
```
Invoke sk-team-feature with: Add user authentication with OAuth2
```

### Quick Workflow (`sk-team-quick`)

For bugfixes, typos, small changes (four phases):

```
1. sk-architect → Brief design note (quick mode)
2. sk-developer → Fix + Tests
3. sk-review-orchestrator → Quality check (all applicable review lenses)
4. sk-acceptance-reviewer → Verify fix + write docs (quick mode)
```

**Example:**
```
Invoke sk-team-quick with: Fix null pointer in calculateTotal function
```

## Artifacts

Durable, version-controlled decisions use OpenSpec:

```
openspec/changes/<feature-name>/
├── proposal.md       # Request, acceptance criteria, scope, non-goals
├── RESEARCH.md       # Optional research
├── design.md         # Approved design + Scope Delta decisions
├── tasks.md          # Required/explicitly approved work only
├── adr/              # Optional significant decisions
├── DOC_REVIEW.md     # Optional alignment review
├── CODE_REVIEW.md    # Compact feature verdict + Review Triage
├── REVIEW.md         # Quick-mode equivalent (quick workflow only)
├── VERIFICATION.md   # Acceptance evidence
├── DEFERRED.md       # Optional change-local proposal staging
└── RETROSPECTIVE.md  # Lessons + scope-control outcome
```

After final approval, the complete directory moves from `openspec/changes/` to
`openspec/completed/`.

Heavy runtime data is not committed:

```text
$(git rev-parse --git-path sk-workflow)/<feature-name>/
├── state.json                    # phase, approvals, cycles, agent/wait counters
├── checkpoints/ and logs/
└── review/<snapshot>/            # evidence, map, ledger, scopes, lenses, full report
```

`DEFERRED.md` stages `candidate | deferred | rejected | promoted` proposals; it is
not automatically the backlog. At archive, user-selected items go to the repository's
tracker or the `openspec/backlog/<slug>.md` fallback. Scope is not duplicated in
`SCOPE.md`, triage is not duplicated in another summary, and exact subagent call logs
remain host session data rather than project artifacts.

## Scope Control

Planning shows required work, explicit non-goals, and every material proposed
addition as a separately approved `SD-*` item. New queues/storage/workers, telemetry
or rollout systems, broader threat models, extra public contracts, cross-system
finality, and broad refactors cannot enter tasks through a generic approval.

All seven review lenses remain strict. Each finding receives a risk severity plus a
separate disposition: `required_fix`, `user_decision`, `backlog`, or `baseline`.
Only required fixes and explicitly selected decision IDs enter remediation. Stack
review still reports long/complex touched functions; unchanged debt is classified
rather than silently forcing a broad refactor. Final review keeps catching
regressions and proven critical defects, while new non-critical ideas are deferred
instead of starting an unbounded loop.

`CHANGES REQUESTED` means required work remains; `TRIAGE REQUIRED` means only a
scope decision remains; backlog/baseline observations may stay visible under an
`APPROVED` current-scope verdict.

## TDD Approach

The system enforces Test-Driven Development:

1. **Red Phase** (sk-tester): Write failing tests based on requirements
2. **Green Phase** (sk-developer): Write minimum code to pass tests
3. **Refactor** (sk-developer): Clean up while keeping tests green

## Agent Invocation

The orchestrator uses the host's subagent/delegation mechanism. For example:

```
Delegation request:
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

- **Scope governance.** Planning uses a Scope Delta Gate. Review uses one compact
  mandatory/user-decision/backlog triage and remediation receives only approved
  finding IDs. The canonical installed policy is
  `~/.claude/agents/shared/scope-governance.md` (or the source-repository
  equivalent).

- **Clarification (handoff protocol).** Subagents cannot reach the user directly. When one
  hits a genuine blocker it returns a compact `## NEEDS USER INPUT` block; the
  orchestrator surfaces it and never answers on your behalf. Complete reports and
  logs stay in shared artifacts; mailbox messages contain decisions, paths, and
  fingerprints. New phases/remediation use clean children, while one short
  clarification may reuse the same bounded thread.

- **Context and nesting.** Codex children use `fork_turns="none"` and inherit the
  parent's model/reasoning. Nesting is capped at depth 2 and only an orchestrator
  with an explicit child budget may delegate. Kimi stable children cannot nest, so
  its generated root team dispatches the seven review leaves directly.

- **Efficient waiting.** Work launches in concurrency-aware waves. The orchestrator
  prefers one long host-supported wait and otherwise uses a persisted finite budget:
  at most 15 minutes/15 empty wake-ups per wave and 30 idle wake-ups per workflow.
  It never lists, nudges, or chatters between empty returns. `BACKGROUND WORK ACTIVE`
  plus manual `continue` is used only after budget exhaustion. Ready results are
  drained before new work starts; unbounded polling is never enabled.

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
Invoke sk-team-feature with <describe your feature>

# Fix a bug
Invoke sk-team-quick with <describe the bug>

# Check workflow status
Invoke sk-team-status
```

</sk-team-help>
