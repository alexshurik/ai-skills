# AGENTS.md

> Auto-generated. Provides context for AI coding agents.
> Compatible with: OpenAI Codex, Claude Code, Cursor, and Kimi Code CLI

## Available Commands

### Workflow (Multi-Agent Team)

- `sk-team-feature` - Run a worktree-isolated multi-agent feature workflow with explicit approval gates from discovery through retrospective and acceptance archive.
- `sk-team-help` - Show help and documentation for multi-agent team workflow
- `sk-team-quick` - Quick workflow for bugfixes, typos, and small changes
- `sk-team-status` - Show status of current team workflow

### Onboarding

- `sk-discover-project` - Discover project structure, stack, domains, and API surface for quick onboarding
- `sk-explore-codebase` - Explore a codebase and generate navigation plus authoritative project convention profiles
- `sk-onboard` - Discover a project and generate its map, navigation rules, and authoritative convention profiles

### Utilities

- `sk-code-review` - Review committed, staged, unstaged, untracked, deleted, and renamed changes through exactly three independent baseline-aware lenses without modifying source code.
- `sk-explore-codestyle` - Derive project-specific coder, reviewer, and evidence profiles from enforced tooling, approved repository guidance, and representative source samples without promoting legacy frequency into rules.

### Context Management

- `sk-copy-context` - Copy current session context to clipboard

## Agent Definitions

The following agents are available for task delegation:

### sk-acceptance-reviewer
Verify business requirements are met (QA acceptance). Creates VERIFICATION.md with final verdict.

### sk-architect
Design how to implement an approved change, prove boundary ownership and decision completeness, and create design.md, tasks.md, and required ADRs.

### sk-developer
Implement approved tasks with TDD while enforcing architecture boundaries, project-authoritative conventions, and pre-write structure and abstraction gates.

### sk-doc-reviewer
Review documentation for consistency, gaps, and alignment before testing. Verifies user's mental model matches the plan.

### sk-product-analyst
Transform ideas into detailed requirements (PM + BA). Creates proposal.md with vision, user stories, and acceptance criteria.

### sk-researcher
Research unknown domains, technologies, APIs, and best practices before planning. Creates RESEARCH.md with findings, options, and recommendations.

### sk-review-orchestrator
Review complete tracked and untracked changes through exactly three independent architecture-design, correctness-safety, and engineering-quality lenses with bounded remediation verification.

### sk-tester
Write tests BEFORE code (TDD red phase). Proposes categorized test plan for user approval, supports E2E testing. Creates failing tests based on approved plan.

## Multi-Agent Orchestration

- Give each child one bounded deliverable. New phases, redo, remediation, and
  independent review use clean contexts; on Codex use `fork_turns="none"` and omit
  model/reasoning overrides so children inherit the parent profile.
- Keep nesting at depth 2. Only a named orchestrator with an explicit child budget
  may spawn; review lenses are leaves. Codex and current Kimi support the canonical
  review-orchestrator → three leaf-reviewers shape.
- Agents return compact `FINAL` or `BLOCKED` messages to their immediate parent.
  Full reports, evidence, diffs, and logs live in shared artifacts; messages carry
  paths and fingerprints.
- Durable change artifacts live under `openspec/changes/<name>/`; heavy runtime
  state lives under `$(git rev-parse --git-path sk-workflow)/<name>/`. The global
  root owns the semantic `events.jsonl` journal and derived `state.json` projection;
  the bounded nested-review lease may record leaf attempts through the same helper.
  Stages own gates/tasks and tasks own attempt history.
- Planning separates required work, explicit non-goals, and individually approved
  Scope Delta IDs. Review keeps severity/disposition separate from remedy authority;
  remediation receives an approved finding-ID allowlist with per-ID routing, and
  only work proven within the approved design goes directly to the developer.
- Optional/rejected proposals stage in change-local `DEFERRED.md`. Promote only
  user-selected items to the repository tracker or `openspec/backlog/` fallback.
- Full review uses a deterministic lossless review map and exactly three independent
  lenses in one wave: architecture-design, correctness-safety, and engineering-quality.
  Root runs gates once per snapshot; validated scope-manifest union covers every path.
- Launch a full wave before waiting. Keep required children in a foreground join and
  use the longest event-driven mailbox wait permitted by the host and higher-priority
  policy. Record one semantic foreground attempt join; transport-only timeouts are
  not workflow retries, budget events, or runtime-state writes. Never
  list, nudge, or chatter between routine returns. Detach only on explicit user
  request, a forced host deadline, or unavailable/failing wait support; persist the
  reason. Notifications are observability, not workflow continuation. Drain ready
  completions before launching new work.

Canonical policies: `workflow/agents/shared/orchestration-policy.md`,
`workflow/agents/shared/handoff-protocol.md`, and
`workflow/agents/shared/scope-governance.md`. Runtime transitions and migration are
defined by `workflow/agents/shared/runtime-state-policy.md`.
The runtime helper requires Python 3.10+ and resolves `python3`, `python`, or `py -3`.

## Best Practices Profiles

Stack-specific coding and review rules live in `shared/best-practices/`, organized by
language, framework, and tooling, plus a framework-agnostic UI (anti-slop design)
profile that loads for any React/Vue/Svelte/Angular/Tailwind/HTML+CSS work. The review orchestrator and developer resolve the
project stack via `shared/best-practices/index.yaml` and load matching profiles
automatically (precedence: project > tooling > framework > language > default).
Downstream projects override or extend profiles via `.agents/best-practices/project/`.
Project `coder.md`/`reviewer.md` contain Enforced and Approved rules only;
`evidence.md` keeps Observed and Legacy/uncertain patterns non-normative.

Available profiles:

- **languages**: go, js, python, typescript
- **frameworks**: fastapi, gin, vue
- **tooling**: ansible, docker, github-actions, kubernetes, terraform
- **ui** (framework-agnostic): anti-slop UI/design rules (coder + reviewer)


## Usage

### Claude Code
```bash
./scripts/install-claude-code.sh
```

### OpenAI Codex
```bash
./scripts/install-codex.sh
```

### Cursor
```bash
CURSOR_SKILLS_DIR=/path/to/project/.cursor/skills ./scripts/install-cursor.sh
./scripts/generate-cursor-rules.sh
cp -R adapters/cursor/.cursor /path/to/project/
```

## Quick Start

Invocation syntax depends on the host:

- **Claude Code:** `/sk-team-feature Add user authentication`
- **OpenAI Codex:** `$sk-team-feature Add user authentication`
- **Kimi Code CLI:** `/skill:sk-team-feature Add user authentication`
- **Cursor and other agents:** mention `sk-team-feature` in chat

## License

MIT
