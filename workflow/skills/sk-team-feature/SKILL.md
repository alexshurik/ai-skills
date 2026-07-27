---
name: sk-team-feature
description: Run a worktree-isolated multi-agent feature workflow with explicit approval gates from discovery through retrospective and acceptance archive.
---

# Full Feature Workflow

Coordinate a feature through:

```text
Setup
  → Discovery
  → [Research]
  → Planning
  → [Documentation Review]
  → Testing
  → Implementation
  ↔ Code Review
  → Acceptance
  → Retrospective
  → Archive
```

Research and Documentation Review are optional. Every completed phase requires
explicit user approval before the next phase.

## Hard constraints

- Agents are subagents and ask the user only by returning
  `## NEEDS USER INPUT`. Surface questions verbatim, collect answers, and re-invoke
  the same agent with an `## ANSWERS` block.
- Never answer agent questions for the user.
- Never auto-proceed between phases.
- Surface structured handoff blocks verbatim.
- Never create a worktree before the user confirms the feature name/path.
- Never archive without approved code review, acceptance, and retrospective.
- Never let a feature retrospective edit installed/global skills automatically.

## Required resources

Read the relevant phase section before dispatch:

- [phase prompts](references/phase-prompts.md)

For Retrospective read:

```text
~/.claude/agents/templates/retrospective.md
or shared/templates/retrospective.md from the skills repo
```

## Setup

1. Derive a short kebab-case feature name.
2. Show the proposed branch `feature/<name>` and sibling worktree
   `../<name>-worktree`.
3. Wait for explicit approval/change/cancel.
4. Inspect current git status and preserve unrelated work.
5. Create the worktree and `openspec/changes/<name>/`.
6. Record worktree, branch, base commit, and current phase.

Do not infer permission for a different branch/path or destructive cleanup.

## Clarification loop

When an agent returns `## NEEDS USER INPUT`:

1. show the block verbatim;
2. stop for the user's answers;
3. re-invoke the same agent with original prompt plus verbatim answers;
4. repeat if another material ambiguity appears;
5. continue only when the agent returns an artifact and handoff.

## Phase execution

### 1. Discovery

Dispatch `sk-product-analyst` using the Discovery prompt. Require scope
confirmation before `proposal.md`. Show user stories, acceptance criteria,
non-goals, and open questions; request approval.

### 1.5 Research — optional

Offer Research only when Discovery identifies a real unknown/high-cost area or the
user requests it. Ask for topic approval, dispatch `sk-researcher`, show findings/
recommendation/open decisions, and request approval.

### 2. Planning

Dispatch `sk-architect` using the full decision-completeness prompt. Require user
approach confirmation before artifacts. Show boundary/architecture summary, file
map, model/interface changes, growth forecast, risks, and non-goals; request
approval.

### 2.5 Documentation Review — optional

Recommend for complex, multi-component, public-contract, external-integration, or
high-risk changes. Dispatch `sk-doc-reviewer`, surface traceability/verdict, route
NEEDS_CLARIFICATION to Discovery or Planning, and request approval.

### 3. Testing

Dispatch `sk-tester`. Surface its proposed categorized test plan and wait for
approval before any test code. Keep live/paid/credential-backed suites explicit.
After Red is demonstrated, show test files/groups/skips and request approval.

### 4. Implementation

Dispatch `sk-developer`. Require the pre-write architecture gate and full handoff
evidence. Show files, boundary/abstraction/structure decisions, and exact
verification; request approval.

### 5. Code Review

Execute the canonical review-orchestrator flow at top level when possible so lenses
can run in parallel waves. If invoked nested, run every lens inline and disclose it.

Persist the full latest verdict as:

```text
openspec/changes/<name>/CODE_REVIEW.md
```

If CHANGES REQUESTED, send the complete required findings back to Developer, then
run a fresh review. Do not proceed on a stale approval. When approved, surface
scope/pass/provenance/baseline/verdict and request approval for Acceptance.

### 6. Acceptance

Dispatch `sk-acceptance-reviewer`. Require an approved `CODE_REVIEW.md`. Show
criterion evidence and verdict. Route NEEDS WORK to the owning prior phase. Request
approval before Retrospective.

### 7. Retrospective

Use the canonical template and the Retrospective prompt. Create:

```text
openspec/changes/<name>/RETROSPECTIVE.md
```

For each durable lesson choose exactly one disposition:

- repository guide;
- named existing skill proposal;
- no promotion.

Keep project-specific architecture, deployment, runtime, vocabulary, and safe
commands in repository guidance. Require portable value plus reproducible/repeated
evidence for a skill proposal. Do not edit global skills. Show the retrospective
and request final archive approval.

## Approval gate

After every phase show:

```markdown
## Phase Complete: <name>

### Handoff
<verbatim agent/orchestrator block>

### Artifacts
- `<path>` — purpose

## APPROVAL REQUIRED

- `Approved` / `Continue` / `Next` — proceed
- `Show <artifact>` — display it
- `Modify: <changes>` / `Redo` — re-run this phase
- `Cancel` — stop
```

Treat vague acknowledgement as non-approval.

## Redo

Re-invoke the same phase with:

- original prompt/artifacts;
- the user's feedback verbatim;
- requirement to address every point;
- permission to ask through NEEDS USER INPUT;
- summary of what changed.

Ask for approval again. Never silently patch an unapproved artifact and continue.

## State detection

| Evidence | State |
|---|---|
| no proposal | Discovery |
| `proposal.md` | Discovery approved / Planning next |
| `design.md` + `tasks.md` | Planning approved / Testing next |
| approved tests in Red | Implementation next |
| implementation + green evidence | Code Review next |
| `CODE_REVIEW.md` APPROVED | Acceptance next |
| `VERIFICATION.md` ACCEPTED | Retrospective next |
| `RETROSPECTIVE.md` approved | Archive ready |

File presence alone does not prove user approval; recover approval state from the
conversation/handoff when resuming.

## Archive

After final retrospective approval:

1. move `openspec/changes/<name>` to `openspec/completed/<name>`;
2. report worktree, branch, base, final verification, and all artifact paths;
3. show user-owned next steps for push/PR/integration;
4. do not push, merge, or delete the worktree unless explicitly requested.
