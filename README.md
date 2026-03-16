# SK-* Skills

A collection of AI coding agent skills for multi-agent development workflows.

**Compatible with:** Claude Code, OpenAI Codex, Cursor, Kimi/MiniMax

## Quick Start

### Claude Code

```bash
./scripts/install-claude-code.sh
```

```
/sk-team-help       # Show documentation
/sk-team-feature    # Start full feature workflow
/sk-team-quick      # Quick fix workflow
/sk-onboard         # Project onboarding
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

## Multi-Agent Workflow

```
/sk-team-feature "Add user authentication"
```

```
Discovery → [Research] → Planning → [Doc Review] → Testing → Implementation → Code Review → Acceptance
```

| Phase | Agent | Output | User interaction |
|-------|-------|--------|------------------|
| Discovery | Product Analyst | `proposal.md` | Asks 5-7 clarifying questions |
| Research | Researcher | `RESEARCH.md` | Optional, for unknown domains |
| Planning | Architect | `design.md`, `tasks.md` | Asks about approach and trade-offs |
| Doc Review | Doc Reviewer | `DOC_REVIEW.md` | Optional, verifies alignment |
| Testing | Tester | Test files (failing) | Proposes test plan for approval |
| Implementation | Developer | Code (tests pass) | — |
| Code Review | Code Reviewer | Verdict | Researches best practices, runs analysis tools, may loop back to Developer |
| Acceptance | Acceptance Reviewer | `VERIFICATION.md` | Final quality gate |

Every phase requires **explicit user approval** before proceeding to the next one.

## Quick Fix Workflow

```
/sk-team-quick "Fix null pointer in login handler"
```

Two phases only: Developer (fix + tests) → Code Review.

## All Commands

| Command | Description |
|---------|-------------|
| `/sk-team-feature` | Full feature workflow with multi-agent team |
| `/sk-team-quick` | Quick workflow for bugfixes and small changes |
| `/sk-team-status` | Show status of active workflows |
| `/sk-team-help` | Team workflow documentation |
| `/sk-onboard` | Full project onboarding |
| `/sk-discover-project` | Discover project structure and tech stack |
| `/sk-explore-codebase` | Generate navigation rules for AI |
| `/sk-plan-mode` | Structured planning with file-based plan storage |
| `/sk-code-review` | Deep code review with best practices research and analysis tools |
| `/sk-explore-codestyle` | Generate code style guidelines |
| `/sk-copy-context` | Copy session context to clipboard |

### Agents

| Agent | Role |
|-------|------|
| `sk-product-analyst` | Requirements gathering (PM + BA) |
| `sk-researcher` | Research unknown domains and best practices |
| `sk-architect` | System design and task breakdown |
| `sk-doc-reviewer` | Documentation consistency and alignment review |
| `sk-tester` | TDD red phase — test plan approval, E2E support |
| `sk-developer` | TDD green phase — implementation |
| `sk-code-reviewer` | Deep review with best practices research, analysis tools, SOLID, security |
| `sk-acceptance-reviewer` | Business validation and QA |

## Artifacts

All feature artifacts are stored in `openspec/changes/<feature-name>/`:

| Artifact | Created by | Purpose |
|----------|-----------|---------|
| `proposal.md` | Product Analyst | Requirements and acceptance criteria |
| `RESEARCH.md` | Researcher | Technology findings (optional) |
| `design.md` | Architect | Technical design |
| `tasks.md` | Architect | Implementation task breakdown |
| `DOC_REVIEW.md` | Doc Reviewer | Alignment verification (optional) |
| `VERIFICATION.md` | Acceptance Reviewer | QA verification report |
| `SUMMARY.md` | Acceptance Reviewer | Executive summary |
| `API_CHANGELOG.md` | Acceptance Reviewer | API changes for frontend |
| `OPERATIONAL_TASKS.md` | Acceptance Reviewer | Deployment checklist |

Structure inspired by [OpenSpec](https://openspec.dev/). No additional tools needed — directories are created automatically.

## Directory Structure

```
skills/
├── workflow/
│   ├── skills/          # Orchestrator commands
│   ├── flows/           # Flow definitions (Kimi)
│   └── agents/          # Agent definitions (8 agents)
├── onboarding/          # Project onboarding commands
├── planning/            # Planning workflows
├── utilities/           # Standalone tools
├── context/             # Context management
├── shared/templates/    # Artifact templates
├── scripts/             # Installation scripts
├── adapters/            # Platform-specific adapters
├── AGENTS.md            # Cross-platform agent docs
└── README.md
```

## Customization

**Add a skill:** create `workflow/skills/sk-my-skill/SKILL.md`, run install script.

**Add an agent:** create `workflow/agents/sk-my-agent.md`, run install script.

## Uninstallation

```bash
./scripts/uninstall.sh
```

## License

MIT
