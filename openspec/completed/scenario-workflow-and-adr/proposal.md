# Scenario planning, durable decisions, and truthful quality evidence

Status: approved intent and approach; concrete implementation plan prepared.
Date: 2026-11-06.
Base: `8a096e0ca6f3c9a386d0058391f60478f8ae6f01` (`main`).

## Authority

The user's approved request is recorded in the parent workflow's
`organize-vsa-and-workflow/request.md`. Its “Five approved source sk skill
improvements” authorize the five requirements below. This change affects the
skills source worktree only. The Deli Check migration is a separate change.

Repository policy: [AGENTS.md](../../../AGENTS.md) and
[source-of-truth policy](../../../README.md#source-of-truth-and-installation-verification).
There is no root `CLAUDE.md` at the selected base. The `skill-creator` skill was
read for minimal shared ownership, progressive disclosure, and behavioral testing.

## Problem and desired outcome

Plans currently default to foundation/core/integration/testing buckets. They also
suggest splitting at roughly 3–5 files. That can hide whether a user scenario is
complete and can fragment cohesive changes. Discovery locates domains and service
files but does not consistently connect an operation to its owner, public
dependencies, state boundary, and acceptance evidence.

New ADRs currently default to a change-local directory that moves on archive.
Convention evidence distinguishes authority classes, but its records do not
consistently describe actual invocation, blocking behavior, or freshness. The
Lizard runner matches a threshold expression in clean output. The Python review
profile maps Bandit severity directly to review severity without requiring context.

## Required scope and acceptance criteria

| ID | Required outcome | User acceptance criteria |
|---|---|---|
| R-1 | Outcome-oriented milestones | AC-1: Each meaningful milestone identifies an independently observable user/operator outcome and its criterion IDs. It contains its design, development, testing, and review work, dependencies, and evidence. Existing Testing and Code Review workflow phases remain. Small fixes can use one compact milestone. |
| R-2 | Scenario-aware discovery and design | AC-2: In the requested scope, planning traces entry, input, responsible owner, public dependency contracts, result/failure, state and transaction boundaries, and acceptance evidence. Unknowns are explicit. Responsibilities, risk, and dependencies determine splits; a file count does not. Approved architectures remain valid without adopting VSA. |
| R-3 | Durable ADR ownership | AC-3: Existing permanent decision owners take precedence over change-local storage. New significant decisions use one permanent owner and navigation. Legacy records are not copied or bulk-moved. New and legacy decision links resolve after archive; accepted decision text remains intact. |
| R-4 | Accurate enforcement claims | AC-4: Each normative rule's authority is distinguishable from enforcement evidence: command, checked scope, invocation/CI behavior, known blocking status, manual gaps, and freshness. Configuration existence or a green local check never proves a required merge gate. Missing evidence remains unknown. |
| R-5 | Reliable static-analysis interpretation | AC-5a: Lizard clean output containing `No thresholds exceeded (cyclomatic_complexity > ...)` is OK. Actual warning output remains FINDINGS, including exit zero. Missing, failed, inconsistent, or unrecognized execution evidence is UNVERIFIED. AC-5b: Bandit reports retain their raw findings and receive contextual assessment without blanket exclusions, blanket suppression, or automatic severity escalation. |

## Constraints

| ID | Constraint | Authority |
|---|---|---|
| C-1 | Edit only this source worktree. Preserve unrelated canonical edits and all other worktrees. Do not install globally. | Approved request and task envelope; repository source-of-truth policy |
| C-2 | Identify any proposed scope addition before implementation. None is proposed by this plan. | Approved request; shared scope-governance policy |
| C-3 | Edit maintained sources. Regenerate managed files only through existing generators when their inputs change. | Repository `AGENTS.md`, `README.md`, and generated-file tooling |
| C-4 | Root owns runtime state and the requested `skills-design.md` runtime pointer. | Parent task envelope |

## Scope Delta

Required work: R-1–R-5 and their regression/behavioral evidence.

Proposed additions: **None**.

## Explicit non-goals

- No universal VSA, new required layer structure, or migration of target projects.
- No workflow phase removal, runtime/event-schema change, new agent topology, or
  mandatory additional review wave per milestone.
- No public skill rename, metadata expansion, new dependency, global installation,
  production application edit, deployment, or merge.
- No broad analyzer rewrite, repository-wide suppression, new CI architecture,
  generic ADR migration tool, or automatic promotion of legacy rules.
- No UI or rendered artifact change.

## Delivery and verification

The implementation uses existing canonical policy owners and narrow caller links.
[design.md](./design.md) identifies each owner and compatibility constraint.
[tasks.md](./tasks.md) groups work by four observable outcomes, with testing and
review inside each. Final verification combines deterministic scanner regressions,
fresh-context artifact-producing evaluations, and the repository's existing checks.

This document records an approved scope, not completed implementation or evidence
that the revised skills already pass acceptance.
