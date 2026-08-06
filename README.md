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

The quick workflow uses two bounded threads:

1. A developer diagnoses the issue, writes a short design for approval, then
   implements and tests the approved fix.
2. A fresh reviewer checks all seven review dimensions and verifies acceptance.

It keeps the design approval and independent-review gates without running the full
feature workflow.

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

Artifacts are split by lifetime and audience. OpenSpec stores durable human decisions;
Git-local workflow state stores resumable counters and heavy evidence. Agent mailbox
messages contain only compact receipts with paths and fingerprints.

### Durable OpenSpec artifacts

Active feature artifacts are version-controlled under
`openspec/changes/<feature-name>/`. After approved retrospective and archive, the
complete directory moves to `openspec/completed/<feature-name>/`.

| Artifact | Created by | Purpose |
|----------|-----------|---------|
| `proposal.md` | Product Analyst | Request, acceptance criteria, required scope, and non-goals |
| `RESEARCH.md` | Researcher | Technology findings (optional) |
| `design.md` | Architect | Approved design and Scope Delta decisions |
| `tasks.md` | Architect | Only required or explicitly approved implementation work |
| `adr/` | Architect | Significant approved architecture decisions (optional) |
| `DOC_REVIEW.md` | Doc Reviewer | Alignment verification (optional) |
| `VERIFICATION.md` | Acceptance Reviewer | QA verification report |
| `CODE_REVIEW.md` | Review Orchestrator | Compact full-workflow verdict, triage, fingerprint, and evidence links |
| `REVIEW.md` | Quick reviewer | Compact quick-workflow review and triage |
| `DEFERRED.md` | Orchestrator | Change-local staging register for optional/rejected/promoted proposals |
| `RETROSPECTIVE.md` | Orchestrator | Root causes, prevention, and lesson disposition |
| `SUMMARY.md` | Acceptance Reviewer | Executive summary when actually required |
| `API_CHANGELOG.md` | Acceptance Reviewer | API changes when applicable |
| `OPERATIONAL_TASKS.md` | Acceptance Reviewer | Operational actions when applicable |

`DEFERRED.md` is not automatically the project backlog. It records
`candidate | deferred | rejected | promoted` decisions. At archive, only
user-selected items are promoted to the repository's existing tracker; when no
tracker exists, `openspec/backlog/<slug>.md` is the portable fallback. Rejected and
deferred decisions remain with the archived change to prevent reviewers from
reopening them repeatedly.

### Git-local runtime and review evidence

The workflow resolves `git rev-parse --git-path sk-workflow` and stores non-versioned
runtime data under `<runtime-root>/<feature-name>/`:

```text
<runtime-root>/<feature-name>/
├── state.json                    # phase, execution/join state, approvals, cycles, next action
├── checkpoints/                  # compact resumable phase state
├── logs/                         # large test/tool output
└── review/<snapshot>/
    ├── change-evidence.json      # complete Git scope and fingerprint
    ├── review-map.json           # lossless path inventory
    ├── coverage-ledger.json      # neutral full-scope reading record
    ├── lens-scopes/              # per-lens reading depth and reasons
    ├── lenses/                   # seven complete lens reports
    ├── static-analysis/          # full analyzer logs/provenance
    └── CODE_REVIEW.md            # full technical review report
```

`state.json` contains counters for review, remediation, and acceptance attempts plus
spawned/running/completed agents, `execution_status` (`foreground_join` or
`background_detached` while children run), the foreground join set, any detach
reason, and the next action—not a duplicate transcript. Exact host tool calls already
live in Codex/Claude/Kimi session logs. Do not create parallel `SCOPE.md`, `TRIAGE.md`,
`AGENT_CALLS.md`, or `review-summary.md`: scope belongs in proposal/design, triage in
the durable review, and orchestration state in runtime state.

Structure is inspired by [OpenSpec](https://openspec.dev/). No additional tools are
required; directories are created automatically.

## Scope Governance

The canonical contract is `workflow/agents/shared/scope-governance.md`.

Before planning writes normative design/tasks, it shows a Scope Delta Gate with:

- work required by the request/acceptance criteria;
- separately identified `SD-*` additions with cost and blast radius;
- explicit non-goals.

Queues/outboxes, workers, new storage, telemetry/SQL rollout gates, expanded threat
models, additional finality/reorg systems, public contracts, and broad neighboring
refactors require an explicit item decision. A general approval or autonomous-mode
request does not silently approve them.

Review remains strict across all seven lenses. Every finding has both severity and
scope disposition:

| Disposition | Meaning | Automatic remediation |
|---|---|---|
| `required_fix` | Approved behavior/design/gate or realistic change-caused defect | Yes, after the review gate |
| `user_decision` | Material scope/threat/infrastructure expansion | Only when its ID is approved |
| `backlog` | Useful non-critical hardening/cleanup | No |
| `baseline` | Pre-existing and not materially worsened | No |

Review triage separates mandatory fixes, scope decisions, deferred work, and
pre-existing debt. Remediation receives an approved finding-ID allowlist rather
than a broad “fix everything” instruction. `CHANGES REQUESTED` means required work
or verification is missing; `TRIAGE REQUIRED` means a scope decision is pending;
`APPROVED` means the approved scope passes.

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

Before editing, `sk-developer` checks boundaries, types, reuse, abstractions,
structure, and imports, then runs the project's formatter and linter. The review
orchestrator builds one change-evidence inventory, runs seven independent review
lenses, separates baseline debt, and marks checks that did not execute as
`UNVERIFIED`. Detailed evidence and safety rules live under
`workflow/agents/references/` and `shared/review-evidence/`.

## Source of Truth and Installation Verification

This git repository is the only editable source. Home-directory installations are
generated targets described by `skills-manifest.yaml`.

- `scripts/validate-skills.sh` validates metadata, prompt budgets, manifest path
  confinement, declared inventory, rendered reference closure, and scripts.
- `scripts/doctor-installation.sh` finds duplicate/conflicting discovered skills.
- `scripts/verify-installation.sh` compares an install with the manifest-rendered tree.
- Installers stage a complete platform tree, reject unowned collisions, preserve
  unrelated files, and record manifest-owned paths in a versioned receipt.
- Installed skills include their `references/`, `scripts/`, and
  `agents/openai.yaml` resources.
- `scripts/migrate-legacy-codex.sh` moves legacy manifest-owned entries to a
  recoverable backup without touching `.system` or unrelated siblings.
- `scripts/uninstall.sh` preflights all standard platform targets before removing
  receipt-owned files and skips platforms that are not installed.

## Orchestration and Handoff

Subagents have no direct user channel. They send compact `FINAL`/`BLOCKED` results
through the host mailbox to their immediate parent; complete reports, evidence,
diffs, and logs go through the shared filesystem as artifact paths plus content
fingerprints. A parent validates those artifacts and surfaces only the decision,
required actions, and blockers unless the user asks for the full report. One short
same-thread clarification is allowed; a new phase, redo, or remediation gets a
clean child. The canonical specs are
`workflow/agents/shared/{orchestration-policy,handoff-protocol,scope-governance}.md`.

Full reviews use one lossless review map. The structure lens covers every changed
human-authored text file; the other six lenses use the map to inspect relevant raw
source without repeating the same full-tree read. Required results stay in an
event-driven foreground join. Detached background state is resumable but is used
only when requested or forced by host/wait limitations.

## Directory Structure

```
skills/
├── workflow/
│   ├── skills/                  # Orchestrator commands (sk-team-*)
│   └── agents/                  # 8 workflow agents
│       ├── review-steps/        # Seven lenses: security, architecture, abstraction, structure, imports, stack, instructions
│       ├── references/          # Conditional workflow gates and verdict/tooling policy
│       └── shared/              # Context, waiting, handoff, and scope-governance policies
├── onboarding/                  # Project onboarding commands
├── planning/                    # Planning workflows (sk-plan-mode)
├── utilities/                   # Standalone tools (sk-code-review, sk-explore-codestyle)
├── context/                     # Context management skill and its handoff template
├── shared/
│   ├── templates/               # Artifact templates
│   ├── static-analysis/         # Deep-analysis battery used by review step 4
│   ├── review-evidence/         # Evidence collector plus lossless review-map/coverage validator
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
