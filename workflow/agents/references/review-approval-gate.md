# Executable Review Approval Gate

Use this gate after review aggregation and again from Acceptance. It validates
artifacts and current identity only; it never reruns tests, analyzers, or agents.

## Build the current map

Reuse the reviewed snapshot's exact base and `review-policy.json`:

```bash
collect-change-evidence.sh \
  --repo <repo> --base <base> --format json \
  --output <snapshot>/current-evidence.json

review-map.sh build \
  --evidence <snapshot>/current-evidence.json \
  --policy <snapshot>/review-policy.json \
  --output <snapshot>/current-review-map.json
```

Changing the base or policy is not a current-source check; it creates a new review
identity and requires appropriately routed review.

## Dispositions artifact

Write `dispositions.json` beside the review artifacts:

```json
{
  "review_map_fingerprint": "<approved review-map fingerprint>",
  "structural": [
    {
      "path": "src/example.py",
      "lead": "over_300",
      "decision": "keep_approved | not_applicable",
      "rationale": "Concrete current-source reason.",
      "authority": "Design/ADR/profile/finding reference."
    }
  ],
  "static_analysis": [
    {
      "dimension": "duplication",
      "tool": "jscpd",
      "decision": "baseline | approved_exception",
      "rationale": "Concrete classification.",
      "authority": "Finding or approved exception reference."
    }
  ],
  "incomplete_tasks": [
    {
      "task": "Exact text after the unchecked checkbox",
      "decision": "deferred | not_applicable",
      "rationale": "Why finish remains honest.",
      "authority": "Recorded user/scope/operational decision."
    }
  ],
  "scale": {
    "decision": "approved_exception",
    "rationale": "Why this large change remains one reviewable unit.",
    "authority": "Approved scope/design reference."
  }
}
```

Omit arrays with no entries and omit `scale` when `large_change` is false. A
change-caused static finding normally gets fixed and rerun to OK; use
`approved_exception` only with actual authority. “Unrelated” cannot classify a new
file or responsibility created by the reviewed change as baseline.

Every collected `over_300`, `crossed_300`, `micro_file_candidate`, and route-owner
observation needs exactly one structural disposition. Collector observations are
framework evidence, not universal architectural rules. Classify route ownership
against repository guidance, project profiles, approved design, and representative
analogues. Human-declared second-responsibility leads belong in the same artifact
and architecture inventory even when no generic collector can infer them safely.

Carry those human leads into `review-policy.json` so they become fingerprinted and
machine-required:

```json
{
  "additional_structure_leads": [
    {
      "path": "src/example.py",
      "kind": "second_responsibility",
      "reason": "The change adds persistence ownership to a transport module.",
      "authority": "Developer pre-write handoff or architecture finding ID"
    }
  ]
}
```

A persisted `competing_route_owners` observation does not establish that one owner
must win. Use `not_applicable` when authoritative project evidence permits the
observed ownership model, or `keep_approved` when an approved design deliberately
retains it. If project authority says the owners conflict, a lens must remain
`FINDINGS` until the conflict is fixed; a structural disposition cannot turn that
finding into PASS. Capture the post-fix map where the observation is absent.

The map marks a change large at 50 reviewable paths or 5,000 changed-line span. This
does not reject the change or force a route by itself; it requires one explicit
scope/design acknowledgement before finish.

## Lens binding

Each supplied report begins with:

```text
Review map: <approved review-map fingerprint>
Source fingerprint: <approved source fingerprint>
Status: PASS
```

Full mode requires architecture-design, correctness-safety, engineering-quality,
and conditional UI/UX reports plus their validated scope manifests. Quick mode
requires `combined=<REVIEW.md>` and no full-review manifests.

When `ui_ux_required` is true, the Full `ui-ux` report or Quick `combined`
report must also contain:

```text
CONTRACT: PASS
VISUAL: PASS
```

Each required verdict field occurs exactly once in its report. Plain text and bold
Markdown fields are accepted. Missing, repeated, conflicting, empty, or non-PASS
values block approval; a general `Status: PASS` cannot override either UI verdict.
Non-UI reports do not need UI verdicts. The gate validates declared verdicts and
identity; the reviewer remains responsible for actually inspecting the evidence
under `~/.claude/agents/best-practices/ui/rendered-evidence.md` or source fallback
`shared/best-practices/ui/rendered-evidence.md`.

For targeted review, an unrouted lens may use a small current-source reuse receipt
only when it also records the parent report path/hash, parent snapshot, verified
unchanged assigned paths/hashes, and why impact routing excludes that lens. This is
not permission to relabel an old report without proof.

## Commands

Full:

```bash
review-gate.sh --mode full \
  --approved-map <review-map.json> \
  --current-map <current-review-map.json> \
  --manifest <architecture-design.json> \
  --manifest <correctness-safety.json> \
  --manifest <engineering-quality.json> \
  [--manifest <ui-ux.json>] \
  --lens-report architecture-design=<report.md> \
  --lens-report correctness-safety=<report.md> \
  --lens-report engineering-quality=<report.md> \
  [--lens-report ui-ux=<report.md>] \
  --dispositions <dispositions.json> \
  [--static-summary <provenance.md>] \
  [--tasks <tasks.md>]
```

Quick:

```bash
review-gate.sh --mode quick \
  --approved-map <review-map.json> \
  --current-map <current-review-map.json> \
  --lens-report combined=<REVIEW.md> \
  --dispositions <dispositions.json> \
  [--static-summary <provenance.md>]
```

Only exit zero with `"approval_gate": "PASS"` authorizes an approval/acceptance
handoff. Any failure is review incomplete or stale, not a reason to rerun unchanged
broad verification.
