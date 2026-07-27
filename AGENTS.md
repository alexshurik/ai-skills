# AGENTS.md

> Auto-generated. Provides context for AI coding agents.
> Compatible with: OpenAI Codex, Cursor, Aider, RooCode, Zed, Kimi/MiniMax

## Available Commands

### Workflow (Multi-Agent Team)

- `/sk-team-feature` - Run a worktree-isolated multi-agent feature workflow with explicit approval gates from discovery through retrospective and acceptance archive.
- `/sk-team-help` - Show help and documentation for multi-agent team workflow
- `/sk-team-quick` - Quick workflow for bugfixes, typos, and small changes
- `/sk-team-status` - Show status of current team workflow

### Onboarding

- `/sk-discover-project` - Discover project structure, stack, domains, and API surface for quick onboarding
- `/sk-explore-codebase` - Explore codebase and generate check-before-create navigation rules
- `/sk-onboard` - Full project onboarding - discover structure + generate navigation rules

### Utilities

- `/sk-code-review` - Review committed, staged, unstaged, and untracked changes through the full baseline-aware multi-lens pipeline without modifying source code.
- `/sk-explore-codestyle` - Derive project-specific coder, reviewer, and evidence profiles from enforced tooling, approved repository guidance, and representative source samples without promoting legacy frequency into rules.

### Planning

- `/sk-plan-mode` - Structured planning workflow with file-based plan storage. Separates research from execution through 4 phases. Wait for explicit user approval before making changes.

### Context Management

- `/sk-copy-context` - Copy current session context to clipboard

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
Review complete tracked and untracked changes through independent contract/security, architecture, abstraction, structure, import, stack, and instruction-quality lenses with baseline-aware verdicts.

### sk-tester
Write tests BEFORE code (TDD red phase). Proposes categorized test plan for user approval, supports E2E testing. Creates failing tests based on approved plan.

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
