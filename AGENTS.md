# AGENTS.md

> Auto-generated. Provides context for AI coding agents.
> Compatible with: OpenAI Codex, Cursor, Aider, RooCode, Zed, Kimi/MiniMax

## Available Commands

### Workflow (Multi-Agent Team)

- `/sk-team-feature` - Full workflow for new feature development with multi-agent team. User approval required between each phase. Worktree-based isolation.
- `/sk-team-help` - Show help and documentation for multi-agent team workflow
- `/sk-team-quick` - Quick workflow for bugfixes, typos, and small changes
- `/sk-team-status` - Show status of current team workflow

### Onboarding

- `/sk-discover-project` - Discover project structure, stack, domains, and API surface for quick onboarding
- `/sk-explore-codebase` - Explore codebase and generate check-before-create navigation rules
- `/sk-onboard` - Full project onboarding - discover structure + generate navigation rules

### Utilities

- `/sk-code-review` - Standalone code review for uncommitted changes. Delegates to sk-review-orchestrator for the full review pipeline.
- `/sk-explore-codestyle` - Analyze project code and generate universal code style guidelines. Detects stack, extracts linter rules, identifies patterns linters don't catch.

### Planning

- `/sk-plan-mode` - Structured planning workflow with file-based plan storage. Separates research from execution through 4 phases. Wait for explicit user approval before making changes.

### Context Management

- `/sk-copy-context` - Copy current session context to clipboard

## Agent Definitions

The following agents are available for task delegation:

### sk-acceptance-reviewer
Verify business requirements are met (QA acceptance). Creates VERIFICATION.md with final verdict.

### sk-architect
Design HOW to implement - system design and task breakdown. Creates design.md and tasks.md.

### sk-developer
Implement code that passes tests (TDD green phase). Writes clean, maintainable code following project patterns.

### sk-doc-reviewer
Review documentation for consistency, gaps, and alignment before testing. Verifies user's mental model matches the plan.

### sk-product-analyst
Transform ideas into detailed requirements (PM + BA). Creates proposal.md with vision, user stories, and acceptance criteria.

### sk-researcher
Research unknown domains, technologies, APIs, and best practices before planning. Creates RESEARCH.md with findings, options, and recommendations.

### sk-review-orchestrator
Coordinate code review through specialized subagents. Resolve stack-specific profiles, run static analysis, dispatch parallel review passes, aggregate findings, render verdict.

### sk-tester
Write tests BEFORE code (TDD red phase). Proposes categorized test plan for user approval, supports E2E testing. Creates failing tests based on approved plan.

## Best Practices Profiles

Stack-specific coding and review rules live in `shared/best-practices/`, organized by
language, framework, and tooling. The review orchestrator and developer resolve the
project stack via `shared/best-practices/index.yaml` and load matching profiles
automatically (precedence: project > tooling > framework > language > default).
Downstream projects override or extend profiles via `.agents/best-practices/project/`.

Available profiles:

- **languages**: go, js, python, typescript
- **frameworks**: fastapi, gin, vue
- **tooling**: ansible, docker, github-actions, kubernetes, terraform


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
./scripts/generate-cursorrules.sh
cp adapters/cursor/.cursorrules /path/to/project/
```

## Quick Start

1. **Start a feature**: `/sk-team-feature Add user authentication`
2. **Quick fix**: `/sk-team-quick Fix null pointer in login`
3. **Check status**: `/sk-team-status`
4. **Get help**: `/sk-team-help`

## License

MIT
