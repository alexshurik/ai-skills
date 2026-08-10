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
Read `runtime-state-policy.md` before Setup or resume. It defines the only permitted
writer, schema-v2 state model, semantic events, attempts, gates, and migration.

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
   directory, and run the shared runtime-state helper `init` with workflow name,
   pinned skill/policy revision, and repository worktree/branch/base identities.
   Enter Setup as the first stage. Never hand-edit `state.json` or `events.jsonl`.

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
host permits nested delegation. Codex and current Kimi use a clean
review-orchestrator child whose exactly three clean lens children are leaves:
architecture-design, correctness-safety, and engineering-quality. If the active
host cannot nest, run three separately labelled inline sections and disclose that
limitation.

Use the canonical parked orchestrator bootstrap for nested review. Dispatch the
orchestrator first with an instruction to remain parked and perform no work. Once
dispatch returns its real host ID, record its task and `start-attempt`, record the
`wait-agents --join foreground`, and run `grant-review-lease` with the holder attempt
and actor IDs. Then deliver the runtime directory, stage, revision, lease ID, and
actor ID as the lease envelope that activates the child.

The child records successful leaf dispatches/results with CAS and its exact leased
actor identity, then runs `release-review-lease` before returning. The existing join
expands and drains automatically. The root performs no state mutation during the
lease, then reloads and validates before recording the orchestrator result. For a
forced detach, follow the release → root detach → foreground resume → new lease
sequence in `runtime-state-policy.md`; never carry a lease across turns.

Persist the compact durable verdict/triage as:

```text
openspec/changes/<name>/CODE_REVIEW.md
```

Persist the full technical report and three lens artifacts in the Git-local review
snapshot. Do not create a second `review-summary.md`.

Before Round 1, the root captures an immutable snapshot and runs readiness gates
once. Red formatter/lint/type/build/tests/diff or another mandatory gate returns to
Implementation; review does not start. Root stores full logs and passes compact
provenance only. Engineering-quality must not rerun the full suite/tool battery.

Round 1 is one full review. Launch exactly three independent lenses together in one
Codex wave. Root builds a deterministic lossless review map and creates complete
per-lens scope manifests whose validated union
accounts for every changed/untracked/deleted/renamed path. Lenses read only assigned
raw full/targeted current/base content; unchanged content is reusable only by
verified hash. Do not create a separate structure reviewer or neutral coverage
ledger. Every lens returns its complete finding set, not one issue per round.

Before remediation, show the Review Triage Gate and resolve every `user_decision`.
Freeze the exact remediation allowlist to mandatory `required_fix` plus explicitly
approved addition IDs. Record decisions in `CODE_REVIEW.md`/`DEFERRED.md` and send a
clean remediation developer only that allowlist, acceptance criteria, approved
Scope Delta IDs, and non-goals; never send “fix all findings”. New noncritical
suggestions after triage are deferred and cannot create cycles.

Targeted Round 2 uses a fresh post-remediation snapshot. Run root gates once and
only finding-owning/impact-routed lenses. Require a valid parent full review,
immutable pre/post fingerprints, a complete remediation delta, unchanged hashes,
no expansion, and old evidence never proving changed content. Route architecture
for boundary/API/schema/model/import/loader/structure/abstraction/packaging changes;
correctness for behavior/trust/validation/recovery/migration/concurrency/idempotency/
instruction semantics; quality for maintained source/test/tooling changes. Multiple
lenses may apply, including a narrow contract/schema fix.

A material scope expansion, changed authority/base, dependency/trust/infrastructure
expansion, unexplained path, invalid parent artifact, or unprovable delta forces all
three lenses but consumes Round 2. Exceptional Round 3 is allowed only for an
unresolved allowlisted defect, remediation regression, or newly proven critical
correctness/security defect; use a fresh snapshot, root gates once, and only owning/
impact-routed lenses unless escalation requires all three.

Apply the shared foreground-join policy to every required child. Prefer the longest
host-permitted event-driven wait, re-enter it after transport-only timeouts, and do
not turn empty wake-ups into workflow counters. Do not list, nudge, or emit progress
chatter between returns. Represent each child as a task attempt and record one
foreground attempt join before waiting. Detach only for a shared-policy reason and
record a detached attempt join plus `detach_reason`; notifications never substitute
for mailbox aggregation.

There is no automatic Round 4. After Round 3 return `NEEDS USER DECISION` with exact
blockers/options. Transport-only timeouts do not consume review rounds, and the
counter does not reset within the workflow without explicit user approval of a new
scope/workflow. Targeted approval requires valid parent/routing/delta evidence,
resolved allowlist, green gates, no blocking regression/critical defect, and zero
required UNVERIFIED dimensions. Every verdict discloses mode, round, and parent.

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

Before asking, record a stage-owned pending gate. After explicit approval, use the
runtime-state helper to decide that gate, record exact artifact fingerprints/checks,
complete the stage, and enter the next stage before dispatching its clean child.
Every mutation uses the current `expected_revision` and a stable semantic
`command_id`; never overwrite an earlier task attempt.

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

Run the shared helper `status`, follow its `recommended_action`, and apply the
journal-conditioned status matrix in `runtime-state-policy.md` exactly, including
its `unsupported_schema` fail-closed route and validation step. Then validate recorded
artifact fingerprints. `events.jsonl` is
authoritative and `state.json` is its projection. File presence alone does not prove
user approval. If durable state is missing or a fingerprint differs, recover safe
facts from artifacts and ask the user to reconfirm only the approval that cannot be
proven.

## Archive

After final retrospective approval:

1. verify that `DEFERRED.md` has no unresolved `candidate`, then move
   `openspec/changes/<name>` to `openspec/completed/<name>`;
2. report worktree, branch, base, final verification, and all artifact paths;
3. show user-owned next steps for push/PR/integration;
4. do not push, merge, or delete the worktree unless explicitly requested.
