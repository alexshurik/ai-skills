---
name: sk-code-review
description: Review committed, staged, unstaged, untracked, deleted, and renamed changes through exactly three independent baseline-aware lenses without modifying source code.
---

# Review Repository Changes

Run a fresh read-only review. Derive scope, authority, evidence, findings, and verdict
from the repository. Read `scope-governance.md`, the canonical
`sk-review-orchestrator.md`, and `review-verdict-policy.md` completely. This skill
never modifies source or feature artifacts.

## 1. Capture scope and authority

Resolve the Git-local review runtime directory, run the installed change-evidence
collector with an explicit output, and build `review-map.json`. Stop with `No changes
to review` only when committed, staged, unstaged, untracked, deleted, and renamed
scope is empty.

Find applicable proposal/design/tasks/ADRs and repository guidance. If competing
active designs could define the contract, ask the user to select one. Resolve the
reviewer profile chain; treat project `evidence.md` as non-normative.

## 2. Execute the orchestrator at top level

Do not spawn one nested orchestrator from this skill. Execute its canonical flow at
top level so Codex can dispatch exactly three independent lenses in one Codex wave
(`root + 3`):

1. architecture-design;
2. correctness-safety;
3. engineering-quality.

Build one JSON scope manifest per lens. Their deterministically validated union
accounts for every review-map path. Lenses read only raw full/targeted current/base
content assigned to them; unchanged content is reusable only by verified hash. Do
not require every lens to read every file and do not create a separate structure
agent or LLM-authored coverage ledger.

The root runs formatter/lint/type/build/tests/diff gates and applicable static
analysis once per snapshot before dispatch. A red required gate means review does
not start. Store full output in Git-local logs and pass only compact provenance plus
paths. Engineering-quality must not rerun the full suite/tool battery.

Every lens returns its complete finding set in Round 1. Launch all three before one
long event-driven foreground wait. Apply shared no-poll semantics: transport-only
timeouts are not rounds/retries/events; never list, nudge, or chatter between
routine returns. Full reports stay Git-local; compact receipts return to the model.

If dispatch is unavailable, run three separately labelled inline passes and disclose
`inline`. Never collapse to a single general review.

## 3. Verdict and round cap

Classify every finding with severity, `change_class`, `disposition`, `scope_basis`,
`risk_if_deferred`, and `blocks_release`. Freeze the exact remediation allowlist
after triage; this standalone read-only skill reports it but does not remediate.

Use the orchestrator's lifecycle if the caller later authorizes remediation:

- Round 1: full three-lens review and exhaustive findings;
- targeted Round 2: fresh snapshot, root gates once, valid parent full review,
  immutable pre/post fingerprints, complete delta, verified unchanged hashes, no
  expansion, and every finding-owning/impact-routed lens;
- exceptional Round 3: only unresolved allowlisted defects, remediation regression,
  or newly proven critical correctness/security defects;
- no automatic Round 4: return `NEEDS USER DECISION` with exact blockers/options.

Approval requires complete scope/provenance, valid required lenses, no required
finding, and zero required UNVERIFIED dimensions. A targeted approval additionally
requires valid parent/routing/delta evidence. Disclose mode, round, and parent.

## Guardrails

- Read-only for source and feature artifacts; no commits, branches, tags, installs,
  secret exposure, or backlog promotion.
- Do not infer a pass from old evidence, tests, scans, or one lens alone.
- Keep full findings/baseline/logs in the Git-local snapshot and return a compact
  decision with artifact paths/fingerprints.
