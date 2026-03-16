# AGENTS.md

> Auto-generated. Provides context for AI coding agents.
> Compatible with: OpenAI Codex, Cursor, Aider, RooCode, Zed, Kimi/MiniMax

## Available Commands

### Workflow (Multi-Agent Team)

- `/sk-team-feature` - Full workflow for new feature development with multi-agent team
- `/sk-team-help` - Show help and documentation for multi-agent team workflow
- `/sk-team-quick` - Quick workflow for bugfixes, typos, and small changes
- `/sk-team-status` - Show status of current team workflow

### Onboarding

- `/sk-discover-project` - Discover project structure, stack, domains, and API surface for quick onboarding
- `/sk-explore-codebase` - Explore codebase and generate check-before-create navigation rules
- `/sk-onboard` - Full project onboarding - discover structure + generate navigation rules

### Planning

- `/sk-plan-mode` - Structured planning workflow with file-based plan storage. Separates research from execution through 4 phases. Wait for explicit user approval before making changes.

### Utilities

- `/sk-code-review` - Deep code review with best practices research, advanced analysis tools (complexity, maintainability, code smells, security), and SOLID/KISS/DRY checks. Caches research in .claude/rules/best-practices/.
- `/sk-explore-codestyle` - Analyze project code and generate universal code style guidelines. Detects stack, extracts linter rules, identifies patterns linters don't catch.

### Context Management

- `/sk-copy-context` - Copy current session context to clipboard

## Agent Definitions

The following agents are available for task delegation:

### sk-acceptance-reviewer
Verify business requirements are met (QA acceptance). Creates VERIFICATION.md with final verdict.

### sk-architect
Design HOW to implement - system design and task breakdown. Creates design.md and tasks.md.

### sk-code-reviewer
Deep code review with best practices research and advanced analysis tools. Researches framework/domain best practices (cached in .claude/rules/best-practices/), runs deep analysis (semgrep, lizard, radon, jscpd, bandit, etc.), checks SOLID/KISS/DRY, security, complexity, maintainability. Provides actionable feedback or approves changes.

### sk-doc-reviewer
Review documentation for consistency, gaps, and alignment before testing. Builds traceability matrix, finds contradictions, verifies user's mental model. Creates DOC_REVIEW.md. Optional phase between Planning and Testing.

### sk-developer
Implement code that passes tests (TDD green phase). Writes clean, maintainable code following project patterns.

### sk-product-analyst
Transform ideas into detailed requirements (PM + BA). Creates proposal.md with vision, user stories, and acceptance criteria. Asks minimum 5 questions in 1-2 rounds.

### sk-researcher
Research unknown domains, technologies, and best practices. Creates RESEARCH.md with findings and recommendations. Optional phase between Discovery and Planning.

### sk-tester
Write tests BEFORE code (TDD red phase). Proposes categorized test plan (unit, integration, service, E2E) for user approval. Supports E2E testing with Playwright (web) and real API calls (backend). Creates failing tests based on approved plan.


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

### Kimi/MiniMax
```bash
./scripts/install-kimi.sh
kimi --agent-file ~/.config/agents/agents/sk-team.yaml
```

## Quick Start

1. **Start a feature**: `/sk-team-feature Add user authentication`
2. **Quick fix**: `/sk-team-quick Fix null pointer in login`
3. **Check status**: `/sk-team-status`
4. **Get help**: `/sk-team-help`

## License

MIT
