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

- `/sk-code-review` - Review uncommitted changes with fresh context. Skips automated checks, focuses on patterns linters miss.
- `/sk-explore-codestyle` - Analyze project code and generate universal code style guidelines. Detects stack, extracts linter rules, identifies patterns linters don't catch.

### Context Management

- `/sk-copy-context` - Copy current session context to clipboard
- `/sk-pass-to-claude` - Save context and switch to aclaude in a new tab
- `/sk-pass-to-minimax` - Save context and switch to mclaude in a new tab

## Agent Definitions

The following agents are available for task delegation:

### sk-acceptance-reviewer
Verify business requirements are met (QA acceptance). Creates VERIFICATION.md with final verdict.

### sk-architect
Design HOW to implement - system design and task breakdown. Creates design.md and tasks.md.

### sk-code-reviewer
Review code quality, patterns, and security. Provides actionable feedback or approves changes.

### sk-developer
Implement code that passes tests (TDD green phase). Writes clean, maintainable code following project patterns.

### sk-product-analyst
Transform ideas into detailed requirements (PM + BA). Creates proposal.md with vision, user stories, and acceptance criteria.

### sk-tester
Write tests BEFORE code (TDD red phase). Creates failing tests based on requirements.


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
