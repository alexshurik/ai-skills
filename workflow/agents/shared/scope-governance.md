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
severity: BLOCKER | MAJOR | MINOR | NITPICK
change_class: change-caused | touched-regression | baseline
disposition: required_fix | user_decision | backlog | baseline
scope_basis: acceptance_criterion | approved_design | enforced_gate |
  realistic_security_defect | remediation_regression | threat_model_expansion |
  infrastructure_expansion | optional_hardening | baseline_debt
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

## 4. Review Triage Gate

After the initial full review and before remediation, render:

```markdown
## Review Triage

### Mandatory in-scope fixes
| ID | Severity | Defect | Smallest fix |

### Scope additions requiring a decision
| ID | Proposal | Risk if deferred | Cost/blast radius | Recommendation |

### Deferred/backlog candidates
| ID | Proposal | Why non-blocking |
```

Pass the remediation developer an allowlist containing only:

1. `required_fix` IDs; and
2. `user_decision` IDs explicitly approved for this change.

Also pass acceptance criteria, approved Scope Delta IDs, and explicit non-goals.
Resolve every `user_decision` as include, defer, or reject before dispatching
remediation; do not carry an undecided addition through a code cycle. Do not send
“fix all findings”. If a proposed fix itself crosses a material scope boundary,
return to triage rather than implementing it.

After the initial review, freeze non-critical scope. A final review still blocks:

- an unresolved approved `required_fix`;
- a regression introduced by remediation;
- a newly proven critical security/correctness defect;
- a violated acceptance criterion or mandatory gate.

New non-critical hardening, refactoring, observability, or threat-model expansion
goes to `DEFERRED.md`; it does not start another remediation loop. If triage changes
only dispositions/deferred decisions and no source or normative artifact, do not
repeat the full review. Any implemented change requires a fresh snapshot and all
applicable final lenses.

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
- `review/<snapshot>/change-evidence.json`, `review-map.json`,
  `coverage-ledger.json`, scope manifests, full lens reports, provenance, and the
  full technical `CODE_REVIEW.md`.

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
