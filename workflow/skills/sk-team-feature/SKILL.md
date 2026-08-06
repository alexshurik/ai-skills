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
  `## NEEDS USER INPUT`. Surface the compact questions, collect answers, and follow
  the clarification policy below.
- Never answer agent questions for the user.
- Never auto-proceed between phases.
- Surface compact decisions and artifact paths; show full artifacts only on request.
- Never create a worktree before the user confirms the feature name/path.
- Never archive without approved code review, acceptance, and retrospective.
- Never let a feature retrospective edit installed/global skills automatically.
- Read and apply the shared orchestration policy before any delegation. On Codex,
  every independent phase, redo, remediation, and review child uses
  `fork_turns="none"`; omit model/reasoning overrides so it inherits the parent.
- Children return only FINAL or BLOCKED and do not send routine progress chatter.

## Required resources

Read the relevant phase section before dispatch:

- [phase prompts](references/phase-prompts.md)

Read the shared orchestration and handoff contracts completely:

```text
~/.claude/agents/shared/orchestration-policy.md
~/.claude/agents/shared/handoff-protocol.md
or workflow/agents/shared/ from the skills repo
```

From that shared directory also read `scope-governance.md` before Discovery,
Planning, Code Review, remediation, or Archive. It defines Scope Delta approval,
finding dispositions, artifact ownership, and deferred-item lifecycle.

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
6. Resolve `git rev-parse --git-path sk-workflow`, create its `<name>/` runtime
   directory, and record worktree, branch, base commit, current phase, artifact
   fingerprints, approval state, review/remediation/acceptance counters, spawned/
   running/completed IDs, `execution_status`, the foreground join set, any
   `detach_reason`, blockers, and next action in `state.json`.

Do not infer permission for a different branch/path or destructive cleanup.

## Clarification loop

When an agent returns `## NEEDS USER INPUT`:

1. show the compact block without adding raw child logs;
2. stop for the user's answers;
3. use **one short follow-up** in the same child only when this is still the same
   bounded deliverable and the child has not accumulated large tool output;
4. otherwise start a clean successor with `fork_turns="none"`, the checkpoint path,
   answers, authority paths, and remaining acceptance criteria;
5. continue only when the agent returns a valid artifact and compact FINAL result.

## Phase execution

### 1. Discovery

Dispatch `sk-product-analyst` using the Discovery prompt. Require scope
confirmation before `proposal.md`. Show user stories, acceptance criteria,
required scope, non-goals, deferred proposals, and open questions; request approval.

### 1.5 Research — optional

Offer Research only when Discovery identifies a real unknown/high-cost area or the
user requests it. Ask for topic approval, dispatch `sk-researcher`, show findings/
recommendation/open decisions, and request approval.

### 2. Planning

Dispatch `sk-architect` using the full decision-completeness prompt. Require user
approach confirmation before artifacts. Require the Scope Delta Gate with required
items, separately identified `SD-*` additions (or `None`), cost/blast radius, and
non-goals. General approach approval does not approve an unlisted addition. Show
boundary/architecture summary, file map, model/interface changes, growth forecast,
risks, and non-goals; request approval.

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

Execute the canonical review-orchestrator flow with a depth-2 lens budget when the
host permits nested delegation. Codex uses a clean review-orchestrator child whose
seven clean lens children are leaves. Stable Kimi children cannot nest, so its
generated root-team override performs setup/aggregation and dispatches all lens
leaves directly. If the active host has neither mechanism, run each lens as a
separately labelled inline section and disclose that limitation.

Persist the compact durable verdict/triage as:

```text
openspec/changes/<name>/CODE_REVIEW.md
```

Persist the full technical report and seven lens artifacts in the Git-local review
snapshot. Do not create a second `review-summary.md`.

Run an **initial full review** through every applicable independent lens. Before any
remediation, show the Review Triage Gate: mandatory `required_fix` IDs, scope
additions requiring a decision, and deferred/backlog candidates. Record decisions
in `CODE_REVIEW.md` and `DEFERRED.md` when needed; resolve every `user_decision`
before dispatching remediation. Send the Developer only the
allowlisted required IDs plus explicitly approved addition IDs, acceptance criteria,
approved Scope Delta IDs, and non-goals; never send “fix all findings”. Start a clean
remediation child. Then run a **final full review** through **all applicable lenses**
against a fresh snapshot. Targeted lenses may give diagnostic feedback during
remediation but cannot approve. Each reviewer receives a complete lens scope
manifest with explicit reading depth and exclusions; unexplained omitted paths
invalidate the review.

After initial triage, newly discovered non-critical hardening, refactoring,
observability, or threat-model expansion is deferred and cannot open another
remediation cycle. Remediation regressions, unresolved allowlisted fixes, newly
proven critical defects, acceptance violations, and mandatory gate failures still
block. Disposition-only triage changes do not require another full review; source or
normative-artifact changes do.

The structure/coverage reviewer runs first, reads every human-authored changed text
path in full, and writes a neutral coverage ledger validated against the deterministic
review map. The other six lenses remain independent, use that ledger only for
navigation, query only assigned rows, and verify targeted raw source themselves.

Apply the shared foreground-join policy to every required child. Prefer the longest
host-permitted event-driven wait, re-enter it after transport-only timeouts, and do
not turn empty wake-ups into workflow counters. Do not list, nudge, or emit progress
chatter between returns. Detach only for a shared-policy reason and persist the join
set plus `detach_reason`; notifications never substitute for mailbox aggregation.

The automatic budget is **two review/remediation cycles** total. After it is
exhausted, surface remaining findings and ask the user whether to authorize one more
bounded cycle. Do not proceed on a stale approval. When approved, surface the compact
scope/provenance/baseline/verdict and request approval for Acceptance.

### 6. Acceptance

Dispatch `sk-acceptance-reviewer`. Require an approved compact `CODE_REVIEW.md` for
the current snapshot. Show
criterion evidence and verdict. Route NEEDS WORK to the owning prior phase with a
budget of **one acceptance repair**. A second repair requires an explicit user
decision. Request approval before Retrospective.

### 7. Retrospective

Use the canonical template and the Retrospective prompt. Create:

```text
openspec/changes/<name>/RETROSPECTIVE.md
```

For each durable lesson choose exactly one disposition:

- repository guide;
- named existing skill proposal;
- no promotion.

Also reconcile `DEFERRED.md`: resolve every `candidate`, promote only user-selected
items to the repository's tracker or `openspec/backlog/<slug>.md` fallback, and keep
deferred/rejected decisions in the archived change. Do not implement them.

Keep project-specific architecture, deployment, runtime, vocabulary, and safe
commands in repository guidance. Require portable value plus reproducible/repeated
evidence for a skill proposal. Do not edit global skills. Show the retrospective
and request final archive approval.

## Approval gate

After every phase show:

```markdown
## Phase Complete: <name>

### Decision
<compact status/verdict, required actions, critical evidence, blockers>

### Artifacts
- `<path>` — purpose

## APPROVAL REQUIRED

- `Approved` / `Continue` / `Next` — proceed
- `Show <artifact>` — display it
- `Modify: <changes>` / `Redo` — re-run this phase
- `Cancel` — stop
```

Treat vague acknowledgement as non-approval.

At Review Triage, also accept explicit choices:

- `Fix mandatory only`;
- `Also include: <finding IDs>`;
- `Defer: <finding IDs>`;
- `Reject: <finding IDs> — <reason>`.

Only the first two groups may enter the remediation allowlist.

After explicit approval, update `state.json` with the phase, exact artifact
fingerprints, approval record, retry counters, and next action before dispatching the
next clean child.

## Redo

Start a new clean phase agent with:

- current artifact and checkpoint paths;
- a compact feedback digest preserving every required point;
- requirement to address every point;
- permission to ask through NEEDS USER INPUT;
- remaining acceptance criteria and required output path.

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

Read Git-local workflow `state.json` first and validate recorded artifact fingerprints.
File presence alone does not prove user approval. If Git-local state is missing or a
fingerprint differs, recover safe facts from artifacts and ask the user to reconfirm
only the approval that cannot be proven.

## Archive

After final retrospective approval:

1. verify that `DEFERRED.md` has no unresolved `candidate`, then move
   `openspec/changes/<name>` to `openspec/completed/<name>`;
2. report worktree, branch, base, final verification, and all artifact paths;
3. show user-owned next steps for push/PR/integration;
4. do not push, merge, or delete the worktree unless explicitly requested.
