# Feature Workflow Phase Prompts

Read only the section for the phase being dispatched. Agents ask the user through
the caller by returning `## NEEDS USER INPUT`; they do not use a hidden direct
question channel.

## Standard task envelope

Every phase dispatch uses one bounded prompt and, on Codex, `fork_turns="none"`
without model or reasoning overrides:

```text
Deliverable: <one bounded phase result>
Worktree: <absolute path>
Authority: <approved artifact/guidance paths>
Scope: <paths and explicit non-goals>
Scope governance: <scope-governance.md path>; approved Scope Delta IDs: <IDs/none>
Constraints: <C-* statement, user/normative authority, and source artifact/gate>
Preferences: <non-binding caller suggestions or none>
Acceptance: <observable completion criteria>
Output: <artifact path>
Return: FINAL or BLOCKED; status, required actions, critical evidence, artifact
        paths and fingerprints; no raw logs; max 50 lines
Delegation budget: none | depth-2 <named helpers and maximum count>
```

Only put a material restriction under `Constraints` when it is traceable to a user
decision, approved artifact, or repository policy. Persist a new user choice before
dispatch or cite its stage gate. Put caller assumptions and implementation
preferences under `Preferences`; they are advisory and cannot silently remove a
solution family. Route a preference that changes architecture/scope through the
applicable decision gate.

Do not append the caller's conversation, full files, logs, prior handoffs, or static
output when paths are available. A new phase, redo, or remediation is a clean child.

## Discovery — `sk-product-analyst`

```text
Deliverable: approved product proposal for <name>
Worktree: <path>
User request digest: <complete material requirements, concise>
Authority: <repository guidance/specification paths>
Output: openspec/changes/<name>/proposal.md

Read the repository and existing specifications first. Ask only unresolved,
material product questions through a NEEDS USER INPUT return. Then present scope
and understanding for confirmation. Write proposal.md only after confirmation.
Include observable acceptance criteria, edge cases, constraints, and explicit
non-goals. Separate user-required behavior from suggestions that need later Scope
Delta approval. End with the standard handoff block.
```

## Research — `sk-researcher` (optional)

```text
Deliverable: bounded research decision for <approved topics>
Feature: <name>
Worktree: <path>
Proposal: openspec/changes/<name>/proposal.md
Research topics: <approved topics>
Output: openspec/changes/<name>/RESEARCH.md

Research only unknown/high-cost domains, current APIs, or alternatives identified
by Discovery/user. Prefer primary sources. Record options, evidence, trade-offs,
recommendation, and open decisions. End with the standard handoff block.
```

## Planning — `sk-architect`

```text
Deliverable: approved design, tasks, and required ADRs
Feature: <name>
Worktree: <path>
Proposal: openspec/changes/<name>/proposal.md
Research: <path or none>

Read requirements, authority, code, project profiles, and the complete architecture
gate and scope-governance references. Resolve high-cost ambiguity through NEEDS USER
INPUT. Present the Scope Delta Gate: required items, stable `SD-*` proposed
additions with cost/blast radius (or `None`), and non-goals. Require an explicit
decision for every proposed addition. Only then create design.md, tasks.md, and
required ADRs from required plus approved work.
The design must include boundary ownership, business vocabulary, reuse decisions,
trust-boundary models, abstraction budget, a conditional mechanism budget,
state/coordination invariant alignment when applicable, module-growth forecast,
infrastructure authority, and non-goals. End with the standard handoff block.
```

## Architecture replan after review — `sk-architect`

```text
Deliverable: approved bounded design amendment for allowlisted findings
Feature: <name>
Worktree: <path>
Authority: current proposal/design/tasks/ADRs and review artifact/fingerprint
Findings: <only IDs routed architecture_decision_required>

Preserve each required outcome, approved scope, and non-goals. Do not implement or
revisit unrelated design. Identify the missing/invalidated decision, compare the
smallest sufficient options, and apply the mechanism/invariant gates when relevant.
Return the normal approach-confirmation gate before editing normative artifacts.
After explicit approval, amend design/tasks and an ADR when required; return their
new fingerprints and per-finding evidence that the route can become
within_approved_design or remains blocked. The caller records the route transition.
```

## Documentation Review — `sk-doc-reviewer` (optional)

```text
Deliverable: documentation traceability verdict
Feature: <name>
Worktree: <path>
Artifacts: proposal.md, optional RESEARCH.md, design.md, tasks.md, ADRs
Output: openspec/changes/<name>/DOC_REVIEW.md

Build requirement→design→task traceability. Check authority, contradictions,
decision completeness, scope, and the user's mental model. Return material
questions through NEEDS USER INPUT before finalizing the verdict.
```

## Testing — `sk-tester`

```text
Deliverable: approved categorized tests demonstrating Red
Feature: <name>
Worktree: <path>
Artifacts: proposal.md, design.md, tasks.md, ADRs

Read project test/safety guidance. Return a categorized test plan through
NEEDS USER INPUT and stop. Include unit, integration/service, contract, import/
architecture regression, and user-journey tests as applicable. Separate safe
default tests from live/paid/credential-backed tests. Write tests only after the
user approves or modifies the plan. Confirm Red for the intended reason.
```

## Implementation — `sk-developer`

```text
Deliverable: approved implementation with Green verification
Feature: <name>
Worktree: <path>
Artifacts: proposal.md, design.md, tasks.md, ADRs

Run the complete developer pre-write gate before editing. Implement approved tasks
with Red→Green→Refactor. Respect boundary owners, trust-boundary models,
non-goals, authority-classified project conventions, abstraction budget, structure
forecast, and local-import evidence. Return exact verification and structural
handoff evidence.

For remediation, also receive an explicit finding-ID allowlist. Implement only
`required_fix` plus user-approved addition IDs that are routed
`within_approved_design`; never treat the complete review report or a reviewer
recommendation as implementation-design authority. Run the remediation design-delta
gate before editing and return `BLOCKED — REPLAN_REQUIRED` to Architecture or Scope
Triage when the approved design cannot contain the intended fix.
```

## Code Review — top-level orchestrator flow

```text
Deliverable: complete baseline-aware code-review verdict
Feature: <name>
Worktree: <path>
Design: openspec/changes/<name>/design.md
Base: <feature merge-base>

Execute the canonical sk-review-orchestrator flow from a shared review snapshot.
Include committed, staged, unstaged, untracked, deleted, and renamed scope. Build a
deterministic lossless review map. Root runs readiness gates/static analysis once;
red formatter/lint/type/build/tests/diff prevents review from starting. Build three
complete lens scope manifests whose validated union accounts for every path. Launch
architecture-design, correctness-safety, and engineering-quality together in one
wave. Each reads only assigned raw full/targeted current/base content and returns its
complete finding set. Engineering-quality consumes compact root provenance and does
not rerun the full battery. Separate change-caused findings from baseline and
classify every finding through scope governance. Persist the full technical report
in the Git-local snapshot and the compact verdict/Review Triage in
openspec/changes/<name>/CODE_REVIEW.md.
```

Before remediation, show mandatory fixes, scope additions requiring a decision, and
deferred/backlog candidates. Resolve every decision and freeze the exact remediation
allowlist plus each ID's remedy authority/route. Send Developer only IDs routed
`within_approved_design`. Route the others through a clean Architect replan, Scope
Triage, or bounded investigation first. Return to a clean remediation agent with
findings artifact/fingerprint, acceptance criteria, non-goals, approved Scope Delta
IDs, and only developer-routed allowlisted IDs. Treat the allowlist as authority for
the required outcome, not for an unapproved remedy design.

Targeted Round 2 uses a fresh snapshot, root gates once, immutable pre/post
fingerprints, complete delta, verified unchanged hashes, no expansion, and every
finding-owning/impact-routed lens. Old evidence never proves changed content.
An approved normative design/ADR amendment invalidates targeted mode: the next
review is full against the new authority fingerprint and remaining round budget.
Exceptional Round 3 is only for unresolved allowlisted defects, a remediation
regression, or newly proven critical correctness/security defect. No automatic
Round 4: return NEEDS USER DECISION. New non-critical proposals after frozen triage
go to `DEFERRED.md` and cannot start another cycle.

## Acceptance — `sk-acceptance-reviewer`

```text
Deliverable: acceptance verdict with criterion evidence
Feature: <name>
Worktree: <path>
Proposal: openspec/changes/<name>/proposal.md
Design/tasks: corresponding approved artifacts
Code review: openspec/changes/<name>/CODE_REVIEW.md

Verify every acceptance criterion with evidence. Confirm applicable safe gates,
tasks, contract behavior, and approved review status. Create VERIFICATION.md and
other genuinely applicable acceptance artifacts. Do not accept an incomplete or
CHANGES REQUESTED code review.
```

## Retrospective — orchestrator

Do not dispatch a new implementation agent. Read proposal, design/tasks/ADRs,
CODE_REVIEW.md, VERIFICATION.md, DEFERRED.md when present, git diff/history, phase handoffs, and user redo
feedback. Use the canonical retrospective template.

Write only durable evidence:

- intended versus delivered result;
- escaped/late signals;
- symptom → root cause → why gate missed → prevention;
- verification gaps/baseline debt;
- scope deltas, deferred/rejected proposals, and accidental scope expansion;
- lesson disposition: repository guide, named existing skill, or no promotion.

Project-specific lessons remain project guidance. A skill proposal requires
portable cross-project value plus a reproducible case or repeated evidence.
Never edit global/installed skills from the retrospective.
