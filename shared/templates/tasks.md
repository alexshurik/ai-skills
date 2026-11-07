# Implementation Tasks: <Feature Name>

> Created by: Architect
> Date: YYYY-MM-DD
> Design: ./design.md
> Proposal: ./proposal.md

## Outcome Plan

Repeat the milestone below for each independently observable user/operator outcome.
A small fix may use one compact milestone. Split by responsibility, acceptance
boundary, risk, and dependency order; file counts and durations are estimates, not
split rules. Shared groundwork is a dependency of the first outcome that needs it,
not an invented user outcome.

Milestones organize the approved task graph within the existing workflow phases.
Testing keeps its risk-based Tester/Developer route. Code Review remains a phase;
one normal full review may cover several milestones by explicit scope. No extra
full-review wave or user gate is required per milestone. A milestone is accepted
only after its required tests and review dispositions are complete.

## M1 — <Observable user/operator outcome>

- **Acceptance:** <user criterion IDs and observable success/failure>
- **Scenarios and primary owner:** <scenario IDs, project-native owner>
- **Dependencies:** <prior outcomes or shared groundwork; none when independent>
- **Contracts and invariants:** <public dependency contracts and transaction/state rows in design>

Keep all four kinds of work inside each milestone. Every task cites an acceptance
criterion or explicitly approved Scope Delta ID; omit unapproved proposals.

- [ ] M1-D — **Design:** <contract/decision work or link to its completed decision>.
  Scope basis: <AC/SD IDs>. Owner: <owner>. Evidence: <approved design/ADR paths>.
- [ ] M1-I — **Development:** <verifiable implementation result>.
  Scope basis: <AC/SD IDs>. Owner: <boundary/component>. Files: <exact candidate paths>.
  Dependencies: <task IDs>. Evidence: <observable result>.
- [ ] M1-T — **Testing:** <lowest faithful layer and relevant failure cases>.
  Scope basis: <AC/SD IDs>. Owner: <Tester or Developer per risk route>.
  Dependencies: <task IDs>. Evidence: <exact commands/receipts and expected behavior>.
- [ ] M1-R — **Review:** <applicable owner and changed scope>.
  Scope basis: <AC/SD IDs>. Dependencies: <task IDs>.
  Evidence: <normal review coverage and resolved dispositions>.

## Dependencies and Progress

Record only useful task/milestone edges; do not recreate a horizontal
foundation/core/integration/testing ladder.

| Milestone | Design | Development | Testing evidence | Review evidence | Acceptance |
|---|---|---|---|---|---|
| M1 | <status/link> | <status/link> | <status/link> | <status/link> | <pending/verified> |

Task status: Pending | In Progress | Complete | Blocked.
Shared finish checks can close the change, but do not replace each milestone's
testing or review work.
