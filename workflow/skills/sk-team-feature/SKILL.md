---
name: sk-team-feature
description: Run the Full multi-agent feature workflow under a selected charter, with independent discovery, design, review, acceptance, and retrospective.
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

Research and Documentation Review are optional. Phase transitions follow the
selected workflow charter: Manual asks at every phase, Checkpoints asks only at
important authority gates, and YOLO continues through ceremony automatically.

## Hard constraints

- Agents are subagents and ask the user only by returning
  `## NEEDS USER INPUT`. Surface the compact questions, collect answers, and follow
  the clarification policy below.
- Never fabricate an answer to an agent's material product, scope, or safety
  question. Policy may decide ceremony gates covered by the charter.
- Apply the charter's authorization mode at every phase; do not invent additional
  approval gates.
- Surface compact decisions and artifact paths; show full artifacts only on request.
- Resolve the workspace choice once before creating a worktree.
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
~/.claude/agents/shared/workflow-charter-policy.md
~/.claude/agents/shared/orchestration-policy.md
~/.claude/agents/shared/handoff-protocol.md
or workflow/agents/shared/ from the skills repo
```

From that shared directory also read `scope-governance.md` before Discovery,
Planning, Code Review, remediation, or Archive. It defines Scope Delta approval,
finding dispositions, artifact ownership, and deferred-item lifecycle.
Read `workflow-charter-policy.md` and `runtime-state-policy.md` before Setup or
resume. They define authorization/workspace/destination semantics, the only
permitted writer, schema-v3 state model, semantic events, attempts, gates, and
migration.
Read `workspace-lifecycle.md` from the same shared directory at Setup and Archive
for resource ownership, merge verification, preservation, and cleanup.
Before Code Review, Acceptance, or finish, read
`~/.claude/agents/references/review-approval-gate.md` or the source fallback
`workflow/agents/references/review-approval-gate.md` completely.

For Retrospective read:

```text
~/.claude/agents/templates/retrospective.md
or shared/templates/retrospective.md from the skills repo
```

## Setup

Reuse the parent's `sk-onboard check` result. On direct invocation, apply that
read-only first-use check once before task setup. Offer missing steering without
blocking the task; setup requires acceptance and is not implied by the charter.

1. Derive a short kebab-case feature name.
2. When no parent `sk-team` charter exists, resolve one compact charter first with
   route fixed to Full; recommend Checkpoints, Auto workspace, Local finish, and
   Standard assurance unless the request implies otherwise.
3. Inspect current git status and preserve unrelated work.
4. Resolve the workspace once. For a worktree, show/record branch
   `feature/<name>` and sibling path `../<name>-worktree`; for the current checkout,
   record its existing branch/path. Ask only when the user selected an explicit
   workspace choice that is still ambiguous.
5. Create `openspec/changes/<name>/` in the resolved workspace.
6. Resolve `git rev-parse --git-path sk-workflow`, create its `<name>/` runtime
   directory, and run the shared runtime-state helper `init --workflow sk-team`
   with the full charter, pinned skill/policy revision, and repository worktree/
   branch/base identities. Enter Setup as the first stage. Never hand-edit
   `state.json` or `events.jsonl`.

Record run-owned worktrees and temporary resources under `workspace-lifecycle.md`.
The Merge receipt includes normal post-merge cleanup. Do not infer permission for
a different branch/path or destructive overrides.

## Gate behavior

- **Manual:** request a ceremony decision after every completed phase.
- **Checkpoints:** request user decisions only for Scope Lock, the Execution
  checkpoint, and typed authority/safety stops. Other phase-complete gates are
  ceremony and are policy-approved.
- **YOLO:** policy-approve ceremony gates and continue through in-scope work,
  verification, and authorized remediation. Stop only for the typed reasons in
  `workflow-charter-policy.md`.

The user's selected destination is terminal authority; do not ask for a redundant
final approval before performing it. Material Scope Delta or product decisions stay
user-owned in every mode.

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
required scope, non-goals, deferred proposals, and open questions; apply Gate
behavior. In Checkpoints this is the Scope Lock.

If the request bundles independently acceptable high-risk backend work and a broad
UI/PWA/platform change, prefer sequenced changes with their own acceptance receipts
instead of one monolithic criteria set. Keep them together only when neither can be
accepted safely without the other.

### 1.5 Research — optional

Offer Research only when Discovery identifies a real unknown/high-cost area or the
user requests it. Treat selection of a new research topic as an authority decision;
otherwise dispatch `sk-researcher`, show findings/recommendation/open decisions,
and apply Gate behavior.

### 2. Planning

Dispatch `sk-architect` using the full decision-completeness prompt. Require user
approach confirmation before artifacts. Require the Scope Delta Gate with required
items, separately identified `SD-*` additions (or `None`), cost/blast radius, and
non-goals. General approach approval does not approve an unlisted addition. Show
boundary/architecture summary, file map, model/interface changes, growth forecast,
conditional mechanism budget, state/coordination invariant alignment when
applicable, risks, and non-goals; apply Gate behavior. In Checkpoints this is the
Execution checkpoint.

### 2.5 Documentation Review — optional

Recommend for complex, multi-component, public-contract, external-integration, or
high-risk changes. Dispatch `sk-doc-reviewer`, surface traceability/verdict, route
NEEDS_CLARIFICATION to Discovery or Planning, and apply Gate behavior.

### 3. Testing strategy and risk route

Classify testing before dispatch. Use a separate clean `sk-tester` only for any of:

- auth/authz or another trust-boundary change;
- payments or destructive/data-loss behavior;
- migrations or public API/schema compatibility;
- concurrency/idempotency;
- a complex external integration or material side effects;
- a new reusable test harness;
- the user's explicit request for a separate Tester.

Surface its categorized plan and apply Gate behavior, then require Red for the
intended reason.
For ordinary UI, local behavior, and standard application changes, do not launch a
separate Tester: approve the test strategy in Planning and have Developer implement
tests and code together Red→Green. This route is risk-based, not UI-only. Keep
live/paid/credential-backed/destructive suites explicitly approved in either route.
Every real bug gets a lowest-faithful-layer regression test; unit tests cover only
non-trivial logic; component/browser tests cover UI states/interactions; integration/
contract tests cover boundaries; use only a few critical E2E journeys and a small
stable visual-regression set. Do not require one test per acceptance criterion or
duplicate the same assertion at multiple layers without unique confidence.

### 4. Implementation

Dispatch `sk-developer`. Require the pre-write architecture gate and full handoff
evidence. Show files, boundary/abstraction/structure decisions, and exact
verification; apply Gate behavior.
For meaningful user-visible UI work, require the early rendered visual loop and
exact-source desktop/compact evidence covering the complete effective scroll extent
from Developer before review.

Before broad readiness gates or the multi-lens code review, run a visual macro gate:
the root personally opens the first coherent exact-source compact and desktop
renders and checks hierarchy, entity grouping, density, alignment, rhythm,
responsive priority, and product fit. If the macro composition is weak, return to
Implementation immediately with a concrete visual outcome; do not spend a full test
battery or three engineering lenses validating a screen that is visibly not ready.
For browser chrome, safe-area, fixed navigation, dynamic viewport, or
`visualViewport` changes, require an actual target browser/device when available or
the closest project-appropriate WebKit approximation with the remaining gap stated.

### 5. Code Review

Execute the canonical review-orchestrator flow with a depth-2 lens budget when the
host permits nested delegation. Codex and current Kimi use a clean review-
orchestrator child whose three core lens children are leaves: architecture-design,
correctness-safety, and engineering-quality. When the review map confirms user-
visible frontend impact, also run the clean `ui-ux` leaf. On a four-slot host it runs
as a short second wave after the core three; that is still Round 1 and does not rerun
gates. If the active host cannot nest, run separately labelled inline sections and
disclose that limitation.

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

Persist the full technical report, three core artifacts, and conditional UI/UX
artifact in the Git-local review
snapshot. Do not create a second `review-summary.md`.

Before Round 1, the root captures an immutable snapshot and ensures the workflow has
one green full applicable readiness receipt. Validate and reuse exact trusted
Developer rows and run only missing, stale, or untrusted gates; do not rerun a
trusted battery merely to make it root-owned. Red formatter/lint/type/build/tests/diff or another mandatory gate returns to
Implementation; review does not start. Root stores full logs and passes compact
provenance only. Engineering-quality must not rerun the full suite/tool battery.

There is one full review round. Launch three independent core lenses together and
conditional UI/UX without repeating root gates. Root builds a deterministic
lossless review map that accounts for every changed/untracked/deleted/renamed path,
classifies reviewable/preserved-baseline/workflow-output/derived-acceptance-output,
and creates complete core scope manifests whose validated union covers every
reviewable path. Lenses read only assigned
raw full/targeted current/base content; unchanged content is reusable only by
verified hash. Do not create a separate structure reviewer or neutral coverage
ledger. Every lens returns its complete finding set, not one issue per round.

Before remediation, show the Review Triage Gate and resolve every `user_decision`.
Freeze the exact remediation allowlist to mandatory `required_fix` plus explicitly
approved addition IDs, together with each ID's remedy authority and route. Record
decisions in `CODE_REVIEW.md`/`DEFERRED.md`. Send a clean remediation developer only
allowlisted IDs routed `within_approved_design`, plus acceptance criteria, approved
Scope Delta IDs, and non-goals. Route other IDs to a clean Architect replan, Scope
Triage, or bounded investigation first; never send “fix all findings”. The allowlist
authorizes required outcomes, not an unapproved remedy design. New noncritical
suggestions after triage are deferred and cannot create cycles.

One targeted remediation verification uses a fresh post-remediation snapshot. Run fresh targeted gates
for changed inputs, reuse only exact-input green receipt rows, and run only finding-
owning/impact-routed lenses. Require a valid parent full review,
immutable pre/post fingerprints, a complete remediation delta, unchanged hashes,
no expansion, and old evidence never proving changed content. Route architecture
for boundary/API/schema/model/import/loader/structure/abstraction/packaging changes;
correctness for behavior/trust/validation/recovery/migration/concurrency/idempotency/
instruction semantics; quality for maintained source/test/tooling changes. Multiple
lenses may apply, including a narrow contract/schema fix; UI/UX reruns only affected
rendered screens/states when remediation is user-visible.

A material scope expansion, changed authority/base, dependency/trust/infrastructure
expansion, unexplained path, invalid parent artifact, or unprovable delta forces all
three core lenses plus conditional UI/UX and consumes the targeted verification.

A normative design/ADR amendment invalidates targeted review. Exit this review cycle
and route through the owning Planning/Scope gate before a new full review against the
new authority fingerprint.

Apply the shared foreground-join policy to every required child. Prefer the longest
host-permitted event-driven wait, re-enter it after transport-only timeouts, and do
not turn empty wake-ups into workflow counters. Do not list, nudge, or emit progress
chatter between returns. Record successfully dispatched one-shot children as one
compact batched task; use a long-lived
task attempt only when its retry lineage matters. Validate the complete running set
with the read-only foreground wait before entering the host wait. Detach only for a
shared-policy reason and record a detached attempt join plus `detach_reason`;
notifications never substitute for mailbox aggregation.

After targeted verification, an unresolved allowlisted defect, remediation
regression, or newly proven critical correctness/security defect may use one bounded
recovery: focused remediation plus owning/impact-routed verification only. In YOLO
this continues automatically when it stays within approved design, scope, safety,
and destination; it does not restart a full review. If the blocker remains, return
`budget.exhausted` with exact IDs. Transport-only timeouts consume no review or
recovery budget. Targeted approval requires valid parent/routing/delta evidence,
resolved allowlist, green gates, no blocking regression/critical defect, and zero
required UNVERIFIED dimensions. Every verdict discloses mode, round, and parent.

Before Acceptance, recapture current evidence/map and require the executable Full
review approval gate to pass for the current source/review fingerprints, required
lens artifacts/reuse receipts, all collector/static/task/scale dispositions, and
applicable tasks. This is a hash/artifact check, not another review wave or test
battery. A stale source, absent lens report, unchecked undispositioned task,
UNVERIFIED analyzer, or undispositioned structural/scale lead blocks finish.

### 6. Acceptance

Dispatch `sk-acceptance-reviewer`. Require an approved compact `CODE_REVIEW.md` for
the current source and review-policy fingerprints. Acceptance reuses a trusted green full-suite receipt
only for an exact input closure; it reruns the full safe suite when no exact receipt
exists or repository/release policy explicitly requires independence. High-risk or
Elevated assurance adds orthogonal criterion-specific, boundary, failure-path, or
manual evidence instead of repeating an unchanged matching broad suite.
Show
criterion evidence and verdict. Route NEEDS WORK to the owning prior phase with a
budget of **one acceptance repair**. A second repair requires an explicit user
decision. Apply Gate behavior before Retrospective.

For user-visible UI, acceptance also requires current `CONTRACT: PASS` and
`VISUAL: PASS`. Before finish, the root personally opens the final exact-source
compact and desktop renders and records Engineering, Visual, and Acceptance status;
this aggregation reuses existing receipts and is not another approval ceremony.

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
and apply Gate behavior before Archive.

## Approval gate

When Gate behavior requires user input, show:

```markdown
## Phase Complete: <name>

### Decision
<compact status/verdict, required actions, critical evidence, blockers>

### Artifacts
- `<path>` — purpose

## DECISION REQUIRED

- `Approved` / `Continue` / `Next` — proceed
- `Show <artifact>` — display it
- `Modify: <changes>` / `Redo` — re-run this phase
- `Cancel` — stop
```

In Manual mode, treat vague acknowledgement as non-approval. In Checkpoints or
YOLO, do not turn an informational milestone into a pending user gate.

At Review Triage, also accept explicit choices:

- `Fix mandatory only`;
- `Also include: <finding IDs>`;
- `Defer: <finding IDs>`;
- `Reject: <finding IDs> — <reason>`.

Only the first two groups may enter the remediation allowlist.

Before asking, record a stage-owned pending gate with its kind and typed reason.
For a policy-decided ceremony gate, record `decision_source=policy` and continue
without user input. After a user decision, record `decision_source=user`, exact
artifact fingerprints/checks, complete the stage, and enter the next stage before
dispatching its clean child. Every mutation uses the current `expected_revision`
and a stable semantic `command_id`; never overwrite an earlier task attempt.

## Redo

Start a new clean phase agent with:

- current artifact and checkpoint paths;
- a compact feedback digest preserving every required point;
- requirement to address every point;
- permission to ask through NEEDS USER INPUT;
- remaining acceptance criteria and required output path.

Reapply Gate behavior. Never silently patch an artifact outside the approved scope.

## State detection

| Evidence | State |
|---|---|
| no proposal | Discovery |
| `proposal.md` | Discovery approved / Planning next |
| `design.md` + `tasks.md` | Planning approved / test-risk route next |
| separate Tester selected + approved tests in Red | Implementation next |
| integrated testing selected | Developer Red→Green next |
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

After Retrospective satisfies Gate behavior:

1. verify that `DEFERRED.md` has no unresolved `candidate`, then move
   `openspec/changes/<name>` to `openspec/completed/<name>`;
2. ensure durable reports are included in the reviewed delivery and record
   worktree, branch, base, and final verification;
3. perform the charter's selected Local/Commit/PR/Merge/Deploy finish and record its
   terminal receipt; the selected destination counts as explicit authority;
4. apply `workspace-lifecycle.md`: verify merge targets, preserve reports and
   Git-local runtime state outside the worktree, and remove eligible run-owned
   worktrees/temporary output;
5. record the cleanup receipt and report surviving artifact paths plus every
   removed/retained resource with its reason before completing runtime state.
   Never exceed the selected destination or force removal of a blocked workspace.
