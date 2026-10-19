---
name: sk-team-help
description: Show help and documentation for multi-agent team workflow
license: MIT
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
| `sk-team <description>` | Recommended entry: choose Micro, Quick, or Full and how far to finish |
| `sk-team-feature <description>` | Full workflow for new features |
| `sk-team-quick <description>` | Quick workflow for bugfixes |
| `sk-team-status` | Show status of active workflows |
| `sk-team-help` | Show this help |

Claude invokes skills as `/skill-name`, Codex as `$skill-name` or through
`/skills`, Kimi as `/skill:skill-name`, and Cursor through its slash menu.

## Architecture

```
                       ORCHESTRATOR
     (skill: sk-team / sk-team-feature / sk-team-quick / sk-team-status)
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

## Start Charter

`sk-team` recommends a complete charter and asks once when choices are missing:

1. **Path:** Pick for me | Super-short | Short | Full
2. **Control:** Every phase | Important checkpoints | YOLO
3. **Workspace:** Current | Separate | Choose safely
4. **Finish:** Diagnose only | Leave changes | Commit | PR | Merge | Deploy
5. **Checks:** Standard | Elevated

The Russian UI labels are: `Подбери сам`, `Суперкороткий`, `Короткий`, `Полный`;
`Каждый этап`, `Только важное`, `YOLO`; `Текущая`, `Отдельная`,
`Выбрать безопасно`; `Только разобраться`, `Оставить правки`, `Коммит`, `PR`,
`Merge`, `Deploy`; `Обычные`, `Усиленные`.

YOLO continues through phase ceremony, in-scope implementation, checks, review, and
approved-design remediation. It still stops for material product/scope choices,
missing external access, destructive or live-value actions, unverifiable evidence,
budget exhaustion, or a finish beyond the selected destination. YOLO lasts for one
objective only.

Visual quality is mandatory for every route that changes rendered UI; it is not an
extra mode or another startup question. Micro uses root visual inspection, Quick
uses an early/final render plus its fresh combined reviewer, and Full adds the
independent rendered UI/UX lens. YOLO skips ceremony, never the visual gate.

## Agents (delegated subagent roles)

| Agent | Role | Purpose |
|-------|------|---------|
| `sk-product-analyst` | Discovery | WHAT & WHY - requirements, acceptance criteria |
| `sk-researcher` | Research (optional) | Investigate unknown domains, APIs, best practices |
| `sk-architect` | Planning | HOW - system design, task breakdown |
| `sk-doc-reviewer` | Doc Review (optional) | Consistency & alignment check before testing |
| `sk-tester` | Risk-routed TDD Red | Independent failing tests for high-risk/explicitly requested work |
| `sk-developer` | TDD Green | Implement code to pass tests |
| `sk-review-orchestrator` | Review | Dispatches three core lenses plus conditional rendered UI/UX |
| `sk-acceptance-reviewer` | Acceptance | Verify business requirements met |

## Workflows

### Full Workflow (`sk-team-feature`)

For new features, significant changes, complex work:

```
1. sk-product-analyst → proposal.md (vision + requirements)
   1.5 sk-researcher → RESEARCH.md (optional — unknown domains/APIs)
2. sk-architect → design.md + tasks.md (system design)
   2.5 sk-doc-reviewer → DOC_REVIEW.md (optional — alignment check)
3. [sk-tester] → Independent Red only when risk-routed
4. sk-developer → Integrated or Tester-backed Red→Green implementation
5. sk-review-orchestrator → Quality check (may loop to Developer)
6. sk-acceptance-reviewer → VERIFICATION.md (final check)
7. Orchestrator → RETROSPECTIVE.md (lesson disposition)
8. Orchestrator → Archive to openspec/completed/<feature-name>/
```

Phase gates follow the charter: Manual asks after each phase, Checkpoints asks at
Scope Lock and Execution, and YOLO continues across ceremony. All modes still stop
at genuine authority or safety boundaries.

**Example:**
```
Invoke sk-team-feature with: Add user authentication with OAuth2
```

### Quick Workflow (`sk-team-quick`)

For bugfixes, bounded features, coherent multi-screen UI polish, and small changes,
quick mode uses two bounded threads:

```
1. sk-developer → Diagnosis + brief design gate + implementation/tests
2. fresh non-delegating reviewer → Three owner dimensions + acceptance verdict
```

The root retains the execution checkpoint when the charter requires it and always
keeps fresh independent review without launching the full feature role sequence.

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
├── events.jsonl                  # authoritative semantic transition history
├── state.json                    # derived schema-v3 charter/stage/task/delivery projection
├── checkpoints/ and logs/
└── review/<snapshot>/            # evidence, map, scopes, provenance, lenses, full report
```

The global root owns the journal/projection; only the named nested-review lease may
record leaf attempts through the same helper. Gates belong to stages, attempts belong
to logical tasks, and transport-only wait timeouts do not produce events.
`sk-team-status` validates the projection and can show every agent attempt without
reading host transcripts. Python 3.10+ is required; resolve `python3`, `python`, or
`py -3` before invoking the helper. See the shared `runtime-state-policy.md` for the
authoritative command, lease, recovery, and migration protocol.

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

All three core review dimensions remain strict, and user-visible frontend changes
also receive an independent rendered UI/UX lens; quick mode may combine required
dimensions for a truly small change. Each finding receives
a risk severity plus a separate disposition: `required_fix`, `user_decision`,
`backlog`, or `baseline`, plus `required_outcome` and a separate remedy authority:

| Remedy authority | Route |
|---|---|
| `within_approved_design` | Developer |
| `architecture_decision_required` | Architect replan and design approval |
| `scope_decision_required` | Scope Triage and user decision |
| `investigation_required` | Bounded read-only investigation |

Only required fixes and explicitly selected decision IDs enter the allowlist, and
only Developer-routed IDs enter source remediation. The allowlist authorizes an
outcome, not a new design. Stack review still reports long/complex touched
functions; unchanged debt is classified rather than silently forcing a broad
refactor. Final review keeps catching regressions and proven critical defects, while
new non-critical ideas are deferred instead of starting an unbounded loop.

`CHANGES REQUESTED` means required work remains; `TRIAGE REQUIRED` means only a
scope decision remains; backlog/baseline observations may stay visible under an
`APPROVED` current-scope verdict.

Review uses one full round, then at most one targeted remediation verification with
exact receipt reuse. An unresolved allowlisted or newly critical defect may receive
one bounded focused recovery without restarting the full review; in YOLO this
continues automatically when it stays inside approved design, scope, safety, and
destination. A normative design/ADR amendment exits targeted mode and returns to
its authority gate. Remaining blockers return the exact IDs and boundary.

For user-visible UI, review reports `CONTRACT` and `VISUAL` separately. Approval
requires both PASS; a screen can satisfy the written layout contract and still fail
for weak hierarchy, grouping, density, rhythm, alignment, or product fit.

## TDD Approach

The system enforces Red→Green→Refactor, but separates roles by risk. A clean Tester
runs for auth/authz, payments, destructive data, migrations/public contracts,
concurrency/idempotency, complex external integrations, a new reusable harness, or
explicit user request. Otherwise Developer writes proportionate tests and code in
one bounded phase. Prefer lowest-faithful bug regressions, component/browser tests
for UI states, boundary integration/contract tests, and a few critical E2E journeys;
use unit tests only for non-trivial logic.

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
  models, reuse decisions, abstraction budget, conditional mechanism budget,
  state/coordination invariant alignment, module-growth forecast, and infrastructure
  non-goals. Developer re-checks these before the first edit.

- **Independent review.** Review includes complete tracked/untracked scope and three
  owners: architecture-design (shape/ownership), correctness-safety (semantics/risk),
  and engineering-quality (implementation/tool evidence). Baseline debt is separate
  from change-caused findings.

- **Scope governance.** Planning uses a Scope Delta Gate. Review uses one compact
  mandatory/user-decision/backlog triage and remediation receives approved finding
  IDs with per-ID remedy authority. Only `within_approved_design` work goes directly
  to Developer; other routes return to Architecture, Scope Triage, or Investigation.
  The canonical installed policy is
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
  with an explicit child budget may delegate. Current Kimi supports the same
  review-orchestrator → three leaf-reviewers shape.

- **Efficient waiting.** Work launches in concurrency-aware waves. Required children
  stay in a foreground join using the longest host-permitted event-driven mailbox
  wait; transport-only timeouts do not become workflow counters. The orchestrator
  never lists, nudges, or chatters between routine returns. It detaches only when the
  user requests background work, the host forces the turn to end, or waiting is
  unavailable/failing, and records the reason. Notifications report activity but do
  not resume mailbox aggregation. Ready results are drained before new work starts.

## Best Practices

### When to Use Full Workflow
- Material product or architecture decisions
- Public/data/trust-boundary changes
- High-risk migrations, concurrency, payments, destructive data, or deployment
- Multiple components with genuinely non-obvious ownership

### When to Use Super-short Workflow
- Tiny localized fixes or text/config edits
- One clear owner and no unresolved design decision
- Focused checks are sufficient

### When to Use Quick Workflow
- Bug fixes
- Bounded features with clear behavior
- Related multi-screen UI polish using established owners
- Changes needing one implementer and one independent combined review

### Tips
- Route by product and boundary risk, not bullet/file/test count
- Use focused checks while iterating and one content-addressed broad receipt
- Reuse unchanged receipts during review, remediation, and acceptance
- Keep the visual gate mandatory for rendered UI without promoting UI polish to Full

## Getting Started

```
# Recommended: choose a route and settings interactively
Invoke sk-team with <describe the objective>

# Start a new feature
Invoke sk-team-feature with <describe your feature>

# Fix a bug
Invoke sk-team-quick with <describe the bug>

# Check workflow status
Invoke sk-team-status
```

</sk-team-help>
