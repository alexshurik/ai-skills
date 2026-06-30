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
| Code Review | Review Orchestrator | Verdict | Resolves stack profiles, runs the static-analysis battery, dispatches parallel review passes, may loop back to Developer |
| Acceptance | Acceptance Reviewer | `VERIFICATION.md` | Final quality gate |

Every phase requires **explicit user approval** before proceeding to the next one.

## Quick Fix Workflow

```
/sk-team-quick "Fix null pointer in login handler"
```

Four phases: Architect (design note) → Developer (fix + tests) → Review Orchestrator → Acceptance Reviewer.

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
| `/sk-code-review` | Deep code review with stack-specific profiles and parallel review passes |
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
| `sk-review-orchestrator` | Orchestrates parallel review passes with stack-specific profiles |
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

## Best-Practice Profiles & Project Conventions

`sk-developer` and `sk-review-orchestrator` load stack-specific **coder** and **reviewer**
profiles so generated code and review checks match the target stack. Profiles live in
`shared/best-practices/` and are resolved by precedence (later overrides earlier):

```
default  →  language  →  framework  →  tooling  →  project
```

- **Universal layers** (`default/`, `languages/`, `frameworks/`, `tooling/`) ship with the
  repo and stay generic. Stack is auto-detected via `index.yaml`; see `resolver.md`.
- **Project layer** (`.agents/best-practices/project/coder.md` + `reviewer.md`) is the
  **highest-precedence** layer and is written **into the target repo**, capturing *that*
  repo's actual conventions (naming, docstring policy, imports, typing, test style, and the
  exact format/lint/type/test commands). It is generated from evidence — tooling config
  (`pyproject.toml`, `eslint.config`, `.editorconfig`, …) plus 8–15 sampled files — by
  `sk-explore-codebase`/`sk-onboard` at onboarding, or by `sk-developer` on first run if
  missing. Greenfield repos (no code to observe) are asked instead of guessed. The full
  extraction spec is `shared/best-practices/project-conventions-guide.md`.

This is why agents produce code in the project's own style instead of generic defaults.
`sk-developer` also runs the project's pinned formatter + linter on its own output (through
the resolved `$RUN` prefix — `uv`/`poetry`/`pdm`/`pnpm`/`yarn`/`npx`, honoring pre-commit/CI)
and conforms before returning. The review orchestrator runs static-analysis tools through
the same `$RUN` prefix and treats a tool that fails to execute as **UNVERIFIED** rather than
a silent pass, reporting command + version + exit-code provenance.

## Agent Clarification (Handoff Protocol)

Subagents have **no channel to the user** — `AskUserQuestion` does not reach them and their
final message goes to the orchestrator, not the user. When an agent hits a genuine blocker it
**returns a `## NEEDS USER INPUT` block** instead of guessing; the orchestrator surfaces the
questions verbatim, collects answers, and re-dispatches. Agents also return a handoff block at
the end of each phase, which the orchestrator surfaces verbatim rather than paraphrasing. The
canonical spec is `workflow/agents/shared/handoff-protocol.md`, installed alongside the agents.

## Directory Structure

```
skills/
├── workflow/
│   ├── skills/                  # Orchestrator commands (sk-team-*)
│   └── agents/                  # 8 workflow agents
│       ├── review-steps/        # Review sub-passes (security, architecture, stack-rules, instruction-quality)
│       └── shared/              # Cross-agent docs (handoff-protocol.md)
├── onboarding/                  # Project onboarding commands
├── planning/                    # Planning workflows (sk-plan-mode)
├── utilities/                   # Standalone tools (sk-code-review, sk-explore-codestyle)
├── context/                     # Context management (sk-copy-context)
├── shared/
│   ├── templates/               # Artifact templates
│   ├── context-handoff.md       # Phase-to-phase context passing
│   ├── static-analysis/         # Deep-analysis battery (run-static-analysis.sh) for review step 5
│   └── best-practices/          # Coder + reviewer profiles
│       ├── default/             # Universal fallback profiles
│       ├── languages/           # python, js, typescript, go
│       ├── frameworks/          # fastapi, gin, vue
│       ├── tooling/             # ansible, docker, github-actions
│       ├── index.yaml           # Stack detection signals
│       ├── resolver.md          # Profile resolution logic
│       └── project-conventions-guide.md  # How agents derive a repo's own profile
├── scripts/                     # Installation scripts
├── adapters/                    # Platform-specific adapters
├── AGENTS.md                    # Cross-platform agent docs (auto-generated)
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
