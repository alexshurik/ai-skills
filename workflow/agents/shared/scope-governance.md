# Scope Governance and Artifact Policy

Canonical scope/remediation contract for `sk-team-feature`, `sk-team-quick`,
planning, implementation, review, and acceptance. Detection remains strict;
review findings do not create implementation authority by themselves.

## 1. Scope authority

Treat these as implementation authority, in order:

1. the user's explicit request and approved acceptance criteria;
2. explicitly approved Scope Delta IDs;
3. approved design/ADRs that trace to items 1–2;
4. repository-enforced gates and realistic defects caused or materially worsened by
   the change.

Existing code, reviewer preference, optional hardening, and an attractive design
idea are evidence or proposals, not authority. A general `Approved`, `autonomous`, or
`finish it` instruction does not silently approve an unlisted material scope delta.

Real defects cannot be hidden by calling them out of scope. A proven auth bypass,
BOLA/IDOR, secret exposure, arbitrary transaction substitution, uncontrolled repeat
spend, data corruption, broken approved public contract, remediation regression, or
required CI/type/build failure remains mandatory. The choices are to fix it or stop/
cancel the change; do not issue a false approval.

## 2. Scope Delta Gate

Before final design/tasks, show one compact gate:

```markdown
## Scope Delta

### Required by the request
- <requirement/AC IDs>

### Proposed additions
| ID | Addition | Why | Cost/blast radius | Recommendation |
|---|---|---|---|---|
| SD-001 | ... | ... | ... | include / defer |

### Explicit non-goals
- ...
```

Write `None` when there are no proposed additions. Require an explicit decision for
each material addition before making it normative. Material additions include:

- a queue/outbox, worker, background reconciliation, new storage, or migration not
  required by acceptance criteria;
- a telemetry pipeline, SQL rollout gate, mandatory observation window, or new
  deployment/operations system;
- a new public API/data contract or a materially different compatibility promise;
- an expanded threat model, such as changing a trusted upstream into a fully
  compromised adversary;
- finality/reorg behavior for additional networks or other rare-state machinery;
- broad refactoring of neighboring/baseline code;
- a meaningful increase in effort, affected subsystems, or file count.

Only required work and explicitly approved Scope Delta IDs enter `design.md` and
`tasks.md`. Put unselected useful proposals in `DEFERRED.md`; record rejected ideas
there only when preserving the decision prevents repeat proposals.

## 3. Finding schema

Keep risk severity separate from remediation authority. Every non-N/A review finding
uses:

```yaml
id: SEC-001
file: path/to/file
line: 10
finding: concise defect or proposal
required_outcome: observable behavior or invariant the remediation must restore
severity: BLOCKER | MAJOR | MINOR | NITPICK
change_class: change-caused | touched-regression | baseline
disposition: required_fix | user_decision | backlog | baseline
scope_basis: acceptance_criterion | approved_design | enforced_gate |
  realistic_security_defect | remediation_regression | threat_model_expansion |
  infrastructure_expansion | optional_hardening | baseline_debt
remedy_authority: within_approved_design | architecture_decision_required |
  scope_decision_required | investigation_required
risk_if_deferred: concise concrete consequence
blocks_release: true | false
recommendation: smallest sufficient action
```

Disposition rules:

- `required_fix`: violates approved behavior/design/contract, an enforced gate, or
  is a realistic defect/regression caused or materially worsened by the change.
  `blocks_release` is true. Only this disposition enters remediation automatically
  after the workflow's review approval gate.
- `user_decision`: a credible recommendation that changes architecture, threat
  model, infrastructure, persistence, public contract, neighboring subsystems, or
  material effort. It cannot enter remediation without an approved ID.
- `backlog`: useful non-critical hardening, observability, cleanup, formalization,
  or rare-case support whose deferral does not invalidate approved behavior.
- `baseline`: pre-existing and not materially worsened. It is visible but cannot
  block the current change.

Severity describes impact if the finding is real; it does not grant scope. A severe
hypothetical that depends on an unapproved threat-model expansion may still be
`user_decision`. Conversely, a small but enforced build failure is `required_fix`.
Insufficient evidence is `UNVERIFIED`/`NEEDS_INVESTIGATION`, not an automatic
security BLOCKER and not automatic implementation work.

`remedy_authority` is independent of severity and disposition. A mandatory defect
may still need an architecture or scope decision before source edits:

- `within_approved_design`: at least one sufficient remedy is proven to fit the
  approved owners, models, contracts, dependencies, mechanisms, and non-goals;
- `architecture_decision_required`: the required outcome is known, but the approved
  design is missing, contradicted, or must change before implementation;
- `scope_decision_required`: the remedy would change approved scope, a public
  contract, a non-goal, or material cost/blast radius and needs explicit approval;
- `investigation_required`: available evidence cannot yet establish a safe remedy
  route; investigate before implementation authority is granted.

A review recommendation is evidence, not authority to choose a new architecture.
Do not label a remedy `within_approved_design` merely because the finding itself is
mandatory or its proposed patch looks small.

## 4. Review Triage Gate and frozen remediation scope

Round 1 reviewers must each return their complete finding set; do not drip one issue
per remediation round. After the initial full review and before remediation, render:

```markdown
## Review Triage

### Mandatory in-scope fixes
| ID | Severity | Defect | Required outcome | Remedy authority | Route |

### Scope additions requiring a decision
| ID | Proposal | Required outcome | Risk if deferred | Cost/blast radius | Route |

### Deferred/backlog candidates
| ID | Proposal | Why non-blocking |
```

Resolve every `user_decision`, then freeze the exact remediation allowlist containing
only:

1. `required_fix` IDs; and
2. `user_decision` IDs explicitly approved for this change.

The allowlist authorizes the required outcome and selected scope, not a new remedy
design. Freeze a route beside every allowlisted ID:

- `within_approved_design` → Developer;
- `architecture_decision_required` → clean Architect replan, explicit design
  approval, then Developer against the new design fingerprint;
- `scope_decision_required` → Scope Triage and explicit approval before any replan
  or implementation;
- `investigation_required` → bounded read-only investigation and re-triage.

Do not dispatch a finding to Developer until its route is
`within_approved_design`. A later design amendment may reclassify the route without
changing the finding's disposition, but the new authority and fingerprint must be
recorded. Also pass acceptance criteria, approved Scope Delta IDs, and explicit
non-goals.
Resolve every `user_decision` as include, defer, or reject before dispatching
remediation; do not carry an undecided addition through a code cycle. Do not send
“fix all findings”. If a proposed fix itself crosses a material scope boundary,
return to triage rather than implementing it.

After triage, freeze non-critical scope. A targeted verification round still blocks:

- an unresolved approved `required_fix`;
- a regression introduced by remediation;
- a newly proven critical security/correctness defect;
- a violated acceptance criterion or mandatory gate.

New non-critical hardening, refactoring, observability, or threat-model expansion
goes to `DEFERRED.md`; it does not start another remediation loop. If triage changes
only dispositions/deferred decisions and no source or normative artifact, do not
repeat review. Any implementation requires a fresh snapshot, root readiness gates
once, a provable remediation delta, and every finding-owning/impact-routed lens.
Old evidence never proves changed content.

Round 2 is targeted when the parent full review, immutable pre/post fingerprints,
complete delta, unchanged hashes, no scope expansion, and routing are all proven.
A material scope expansion, changed authority/base, dependency/trust/infrastructure
expansion, unexplained path, invalid parent artifact, or unprovable delta forces all
three lenses but consumes the same round budget. Round 3 is exceptional and only
for unresolved allowlisted defects, remediation regressions, or newly proven
critical correctness/security defects. There is no automatic Round 4; return
`NEEDS USER DECISION`. Transport-only waits do not consume or reset rounds.

A normative design or ADR amendment invalidates targeted mode: the next review is
full against the new authority fingerprint and uses the remaining round budget. If
the budget is exhausted, only explicit user approval may start a new review cycle;
never disguise it as an automatic Round 4.

## 5. Artifact ownership

### Durable, version-controlled decisions

Store under `openspec/changes/<name>/` and archive the directory to
`openspec/completed/<name>/`:

- `proposal.md`: request, acceptance criteria, required scope, non-goals;
- optional `RESEARCH.md`;
- `design.md`, `tasks.md`, and required `adr/` entries: approved work only;
- optional `DOC_REVIEW.md`;
- `CODE_REVIEW.md` for a full workflow or `REVIEW.md` for quick mode: compact current
  verdict, triage, approved finding IDs, snapshot fingerprint, and evidence paths;
- `VERIFICATION.md` and only genuinely required acceptance supplements;
- `RETROSPECTIVE.md`;
- `DEFERRED.md` only when a candidate/deferred/rejected/promoted item exists.

Do not create separate `SCOPE.md`, `TRIAGE.md`, `AGENT_CALLS.md`, or duplicate
`review-summary.md`. Keep scope in proposal/design, triage in the durable review
artifact, and orchestration counters in runtime state.

### Git-local runtime state and heavy evidence

Resolve the root using `git rev-parse --git-path sk-workflow` and store under
`<runtime-root>/<name>/`:

- `events.jsonl`: authoritative semantic workflow transitions written only through
  the shared runtime-state helper;
- `state.json`: derived schema-v2 projection whose stages own gates/checks/tasks and
  whose tasks preserve agent attempts; `control` records current wait/block/terminal
  state;
- checkpoints and large test/static-analysis logs;
- `review/<snapshot>/change-evidence.json`, `review-map.json`, the three lens scope
  manifests, full lens reports, readiness/static-analysis provenance, remediation
  delta evidence, and the full technical `CODE_REVIEW.md`.

Runtime state contains only semantic transitions and resumable decisions, not raw
conversation or tool transcripts. Host session logs already record exact calls and
are not workflow artifacts. Mailbox messages carry compact status, paths, and
fingerprints only. Apply `runtime-state-policy.md` for the event/projection contract.

## 6. Deferred lifecycle

Use the repository's existing issue tracker/backlog when one is authoritative.
Otherwise `openspec/backlog/<slug>.md` is the portable fallback.

`DEFERRED.md` is a change-local staging register, not an automatic backlog. Each item
records ID, source lens, proposal, risk if deferred, why it is outside current scope,
status (`candidate | deferred | rejected | promoted`), user decision/date, and a
follow-up target or acceptance criteria when useful.

Use `~/.claude/agents/templates/deferred.md` or `shared/templates/deferred.md` from
the skills repository as the format source.

Before archive, resolve every `candidate`. Promote only user-selected useful items;
leave rejected/deferred decisions in the archived change so another reviewer does
not repeatedly reopen them. Never implement or create external issues automatically
without the workflow/user authority to do so.
