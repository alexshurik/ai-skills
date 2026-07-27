# Feature Workflow Phase Prompts

Read only the section for the phase being dispatched. Agents ask the user through
the caller by returning `## NEEDS USER INPUT`; they do not use a hidden direct
question channel.

## Discovery — `sk-product-analyst`

```text
Feature request: <verbatim request>
Worktree: <path>
Output: openspec/changes/<name>/proposal.md

Read the repository and existing specifications first. Ask only unresolved,
material product questions through a NEEDS USER INPUT return. Then present scope
and understanding for confirmation. Write proposal.md only after confirmation.
Include observable acceptance criteria, edge cases, constraints, and explicit
non-goals. End with the standard handoff block.
```

## Research — `sk-researcher` (optional)

```text
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
Feature: <name>
Worktree: <path>
Proposal: openspec/changes/<name>/proposal.md
Research: <path or none>

Read requirements, authority, code, project profiles, and the complete architecture
gate reference. Resolve high-cost ambiguity through NEEDS USER INPUT. Present the
approach for confirmation. Only then create design.md, tasks.md, and required ADRs.
The design must include boundary ownership, business vocabulary, reuse decisions,
trust-boundary models, abstraction budget, module-growth forecast, infrastructure
authority, and non-goals. End with the standard handoff block.
```

## Documentation Review — `sk-doc-reviewer` (optional)

```text
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
Feature: <name>
Worktree: <path>
Artifacts: proposal.md, design.md, tasks.md, ADRs

Run the complete developer pre-write gate before editing. Implement approved tasks
with Red→Green→Refactor. Respect boundary owners, trust-boundary models,
non-goals, authority-classified project conventions, abstraction budget, structure
forecast, and local-import evidence. Return exact verification and structural
handoff evidence.
```

## Code Review — top-level orchestrator flow

```text
Feature: <name>
Worktree: <path>
Design: openspec/changes/<name>/design.md
Base: <feature merge-base>

Execute the canonical sk-review-orchestrator flow. Include committed, staged,
unstaged, untracked, deleted, and renamed scope. Run contract/security,
architecture, abstraction, structure, imports, stack rules, and applicable
instruction quality. Separate change-caused findings from baseline. Persist the
final full verdict to openspec/changes/<name>/CODE_REVIEW.md.
```

If review returns CHANGES REQUESTED, return to Implementation with the full
required-findings block. Re-run review after fixes; never reuse the old approval.

## Acceptance — `sk-acceptance-reviewer`

```text
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
CODE_REVIEW.md, VERIFICATION.md, git diff/history, phase handoffs, and user redo
feedback. Use the canonical retrospective template.

Write only durable evidence:

- intended versus delivered result;
- escaped/late signals;
- symptom → root cause → why gate missed → prevention;
- verification gaps/baseline debt;
- lesson disposition: repository guide, named existing skill, or no promotion.

Project-specific lessons remain project guidance. A skill proposal requires
portable cross-project value plus a reproducible case or repeated evidence.
Never edit global/installed skills from the retrospective.
