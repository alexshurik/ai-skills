# SK-* Skills

A collection of AI coding agent skills for multi-agent development workflows.

**Compatible with:** Claude Code, OpenAI Codex, Cursor, Kimi Code CLI

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

Use `$sk-team-help`, `$sk-team-feature`, `$sk-team-quick`, or `$sk-onboard`.

### Cursor

```bash
CURSOR_SKILLS_DIR=/path/to/project/.cursor/skills ./scripts/install-cursor.sh
./scripts/generate-cursor-rules.sh
cp -R adapters/cursor/.cursor /path/to/project/
```

### Kimi Code CLI

```bash
./scripts/install-kimi.sh
kimi --agent-file ~/.config/agents/agents/sk-team.yaml
```

## Multi-Agent Workflow

```
sk-team-feature "Add user authentication"
```

```
Discovery → [Research] → Planning → [Doc Review] → Testing → Implementation → Code Review → Acceptance → Retrospective → Archive
```

| Phase | Agent | Output | User interaction |
|-------|-------|--------|------------------|
| Discovery | Product Analyst | `proposal.md` | Resolves material ambiguity and confirms scope |
| Research | Researcher | `RESEARCH.md` | Optional, for unknown domains |
| Planning | Architect | `design.md`, `tasks.md` | Asks about approach and trade-offs |
| Doc Review | Doc Reviewer | `DOC_REVIEW.md` | Optional, verifies alignment |
| Testing | Tester | Test files (failing) | Proposes test plan for approval |
| Implementation | Developer | Code (tests pass) | — |
| Code Review | Review Orchestrator | `CODE_REVIEW.md` | Reviews complete tracked/untracked scope through independent contract/security, architecture, abstraction, structure, import, stack, and instruction lenses |
| Acceptance | Acceptance Reviewer | `VERIFICATION.md` | Final quality gate |
| Retrospective | Orchestrator | `RETROSPECTIVE.md` | Records escaped signals and routes lessons to repo guidance, a named skill proposal, or no promotion |
| Archive | Orchestrator | `openspec/completed/<feature-name>/` | Moves the approved artifact set after final user approval |

Every phase requires **explicit user approval** before proceeding to the next one.

## Quick Fix Workflow

```
sk-team-quick "Fix null pointer in login handler"
```

Four phases: Architect (design note) → Developer (fix + tests) → Review Orchestrator → Acceptance Reviewer.

## All Commands

| Skill | Description |
|---------|-------------|
| `sk-team-feature` | Full feature workflow with multi-agent team |
| `sk-team-quick` | Quick workflow for bugfixes and small changes |
| `sk-team-status` | Show status of active workflows |
| `sk-team-help` | Team workflow documentation |
| `sk-onboard` | Full project onboarding |
| `sk-discover-project` | Discover project structure and tech stack |
| `sk-explore-codebase` | Generate navigation rules and project convention profiles |
| `sk-plan-mode` | Structured planning with file-based plan storage |
| `sk-code-review` | Deep review of committed, staged, unstaged, and untracked changes |
| `sk-explore-codestyle` | Generate code style guidelines |
| `sk-copy-context` | Copy session context to clipboard |

Invocation syntax is host-specific: Claude uses `/skill-name`, Codex uses
`$skill-name` or `/skills`, Kimi uses `/skill:skill-name`, and Cursor exposes
installed skills in its slash-command menu.

`sk-copy-context` detects `pbcopy` (macOS), `wl-copy`/`xclip` (Linux), or
PowerShell clipboard support and fails with an actionable message when none is
available. It copies from a tool-written temporary file; context text is never
embedded in shell source.

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

Active feature artifacts are stored in `openspec/changes/<feature-name>/`. After
approved retrospective and archive, they move to `openspec/completed/<feature-name>/`.

| Artifact | Created by | Purpose |
|----------|-----------|---------|
| `proposal.md` | Product Analyst | Requirements and acceptance criteria |
| `RESEARCH.md` | Researcher | Technology findings (optional) |
| `design.md` | Architect | Technical design |
| `tasks.md` | Architect | Implementation task breakdown |
| `DOC_REVIEW.md` | Doc Reviewer | Alignment verification (optional) |
| `VERIFICATION.md` | Acceptance Reviewer | QA verification report |
| `CODE_REVIEW.md` | Review Orchestrator | Full latest verdict, baseline section, and tool provenance |
| `RETROSPECTIVE.md` | Orchestrator | Root causes, prevention, and lesson disposition |
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

- **Universal layers** (`default/`, `languages/`, `frameworks/`, `ui/`, `tooling/`) ship with the
  repo and stay generic. Stack is auto-detected via `index.yaml`; see `resolver.md`.
- **Project layer** is the highest-precedence target-repo layer:
  `coder.md` and `reviewer.md` contain only **Enforced** tooling rules and
  **Approved** repository/ADR/spec decisions. `evidence.md` keeps **Observed** and
  **Legacy/uncertain** source patterns non-normative. Sample frequency never becomes
  a rule by itself. The extraction contract is
  `shared/best-practices/project-conventions-guide.md`.

This is why agents produce code in the project's own style instead of generic defaults.
Before editing, `sk-developer` runs a boundary/typing/reuse/abstraction/structure/import
gate. It also runs the project's pinned formatter + linter on its own output (through
the resolved `$RUN` prefix — `uv`/`poetry`/`pdm`/`pnpm`/`yarn`/`npx`, honoring pre-commit/CI)
and conforms before returning. The review orchestrator consumes one deterministic
change-evidence inventory, runs independent review lenses, separates unchanged
baseline debt, and treats a tool that fails to execute as **UNVERIFIED**.
The collector traverses changed paths through held no-follow directory
descriptors and never follows a leaf or ancestor symlink. Current files and base
blobs are each capped at 4 MiB; base size is checked with `git cat-file -s`
before the bounded `git show`. Per-file interval diffing is skipped when either
side exceeds that limit, and otherwise uses a 20 MiB streaming output cap.
Machine-readable and Markdown output both expose incomplete read/interval status.

## Source of Truth and Installation Verification

This git repository is the only editable source. Home-directory installations are
generated targets described by `skills-manifest.yaml`.

- `scripts/validate-skills.sh` validates metadata, prompt budgets, manifest path
  confinement, declared inventory, rendered reference closure, and scripts.
- `scripts/doctor-installation.sh` finds duplicate/conflicting discovered skills.
- `scripts/verify-installation.sh` compares an install with the manifest-rendered tree.
- installers first render a complete platform tree in staging, reject unowned
  leaf collisions, and atomically replace each prepared manifest-owned leaf;
- the versioned installation receipt records a stable suite identity, exact
  platform/manifest version, owned paths, hashes, and symlink targets. A
  symlinked, malformed, foreign, or incompatible receipt is never treated as
  ownership authority, and receipt input is capped at 4 MiB; unrelated files
  inside shared target directories are preserved;
- installers include complete skill resources such as `references/`, `scripts/`,
  and `agents/openai.yaml`.
- `scripts/migrate-legacy-codex.sh` moves named manifest-owned legacy skills and
  exact rendered resource leaves to a recoverable backup without touching
  `.system` or unrelated siblings. The backup root must not already exist and
  must be on the legacy tree's filesystem; migration uses no-follow directory
  descriptors, refuses source/backup symlinks, and rolls earlier moves back on
  failure instead of using a cross-filesystem copy fallback. Exact resource
  leaves must be regular files or symlinks; named legacy skills must be real
  directories containing a real regular `SKILL.md`.
- `scripts/uninstall.sh` preflights all standard platform targets before removing
  any receipt-owned file and safely skips platforms that are not installed.
  Every target is paired with an explicit expected platform; platform is never
  inferred from a filesystem path.

Receipts created before the stable suite/schema fields existed are intentionally
not auto-upgraded: inspect that installation and remove it with its matching
older checkout before installing this version. This prevents an untyped file
from becoming deletion authority merely because it has the receipt filename.

## Agent Clarification (Handoff Protocol)

Subagents have no direct user channel. They send compact `FINAL`/`BLOCKED` results
through the host mailbox to their immediate parent; complete reports, evidence,
diffs, and logs go through the shared filesystem as artifact paths plus content
fingerprints. A parent validates those artifacts and surfaces only the decision,
required actions, and blockers unless the user asks for the full report. One short
same-thread clarification is allowed; a new phase, redo, or remediation gets a
clean child. The canonical specs are
`workflow/agents/shared/{orchestration-policy,handoff-protocol}.md`.

## Directory Structure

```
skills/
├── workflow/
│   ├── skills/                  # Orchestrator commands (sk-team-*)
│   └── agents/                  # 8 workflow agents
│       ├── review-steps/        # Seven lenses: security, architecture, abstraction, structure, imports, stack, instructions
│       ├── references/          # Conditional workflow gates and verdict/tooling policy
│       └── shared/              # Context, nesting, waiting, and handoff policy
├── onboarding/                  # Project onboarding commands
├── planning/                    # Planning workflows (sk-plan-mode)
├── utilities/                   # Standalone tools (sk-code-review, sk-explore-codestyle)
├── context/                     # Context management skill and its handoff template
├── shared/
│   ├── templates/               # Artifact templates
│   ├── static-analysis/         # Deep-analysis battery used by review step 4
│   ├── review-evidence/         # Complete diff/untracked/size/import evidence collector
│   └── best-practices/          # Coder + reviewer profiles
│       ├── default/             # Universal fallback profiles
│       ├── languages/           # python, js, typescript, go
│       ├── frameworks/          # fastapi, gin, vue
│       ├── ui/                  # Framework-agnostic anti-slop UI/design profile (coder + reviewer + catalog)
│       ├── tooling/             # ansible, docker, github-actions, kubernetes, terraform
│       ├── index.yaml           # Stack detection signals
│       ├── resolver.md          # Profile resolution logic
│       └── project-conventions-guide.md  # How agents derive a repo's own profile
├── scripts/                     # Installation scripts
├── tests/                       # Structural, packaging, and workflow contract tests
├── evals/                       # Non-installed behavioral regression fixtures
├── skills-manifest.yaml         # Canonical catalog/internal resource inventory
├── adapters/                    # Platform-specific adapters
├── AGENTS.md                    # Cross-platform agent docs (auto-generated)
└── README.md
```

## Customization

**Add a skill:** create its `SKILL.md`, register the source under `catalog` or
`onboarding` in `skills-manifest.yaml`, run `scripts/validate-skills.sh`, regenerate
the public docs, then run the relevant installer.

**Add an agent:** create `workflow/agents/sk-my-agent.md`, register it under
`agents` in `skills-manifest.yaml`, validate, regenerate docs, and reinstall.

## Uninstallation

```bash
./scripts/uninstall.sh
```

Cursor project installs are explicit because their locations vary:

```bash
python3 scripts/skills_tool.py uninstall \
  --target cursor /path/to/project/.cursor/skills
```

## License

MIT
