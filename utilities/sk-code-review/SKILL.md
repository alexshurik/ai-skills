---
name: sk-code-review
description: Review committed, staged, unstaged, and untracked changes through the full baseline-aware multi-lens pipeline without modifying source code.
---

# Review Repository Changes

Treat this as a fresh, read-only review. Ignore prior conclusions and derive scope,
authority, evidence, findings, and verdict from the repository.

Read `~/.claude/agents/shared/scope-governance.md` or
`workflow/agents/shared/scope-governance.md` from the skills repository.
Report concerns strictly, but keep severity separate from remediation authority.
This skill never modifies source or feature artifacts.

## 1. Confirm scope exists

Resolve a git-local review runtime directory and run the installed change-evidence
collector with an artifact output path:

```text
git rev-parse --git-path sk-workflow
shared/review-evidence/collect-change-evidence.sh --format json \
  --output <runtime-review-dir>/change-evidence.json
```

If committed, staged, unstaged, untracked, deleted, and renamed scopes are all
empty, report `No changes to review` and stop.

## 2. Find authority

Find applicable proposal/design/tasks/ADRs and repository guidance. If multiple
active designs could define the contract, ask the user to select one.

Check for the canonical project profile:

```text
.agents/best-practices/project/coder.md
.agents/best-practices/project/reviewer.md
.agents/best-practices/project/evidence.md
```

If normative coder/reviewer profiles are absent, offer
`sk-explore-codestyle`. Do not require a Claude-specific `code-style.md`.

## 3. Execute the orchestrator flow at top level

Do not spawn `sk-review-orchestrator` as one nested subagent. Read its canonical
flow:

```text
~/.claude/agents/sk-review-orchestrator.md
or workflow/agents/sk-review-orchestrator.md
```

Execute that workflow in this top-level context so independent lenses may run in
parallel waves.

Required lenses:

1. contract/security;
2. architecture/layers;
3. abstraction/navigation;
4. structure;
5. imports;
6. stack rules;
7. instruction quality when instruction artifacts changed.

Every finding includes `change_class`, `disposition`, `scope_basis`,
`risk_if_deferred`, and `blocks_release`. Preserve strict stack/security detection;
unapproved infrastructure or threat-model expansion is `user_decision`, and
unchanged debt is `baseline`, not an automatic required fix.

Use seven clean lens threads with independent verdicts. Build `review-map.json`
deterministically. Run structure/coverage first: it reads every human-authored text
path in full, writes a neutral `coverage-ledger.json`, and reviews placement. Validate
that ledger against the review map before launching the other six targeted lenses.
They may use the ledger only for navigation and must verify assigned raw current/base
content independently. Specialists query only their assigned full/targeted rows and
do not load the complete review map plus ledger into every context.

Pass artifact paths for complete tracked/untracked scope, evidence, design authority,
runner, profiles, and static-analysis provenance as specified by the orchestrator; do
not paste full files, base diffs, or raw tool output into prompts. For Codex, use
`fork_turns="none"` and omit model/reasoning overrides so reviewers inherit the
parent's selected profile. Give every reviewer a complete lens scope manifest with
full/targeted/metadata depth and reasons. No lens may spawn another agent.

Apply the shared foreground-join policy to every required reviewer. Prefer the
longest host-permitted event-driven wait, re-enter it after transport-only timeouts,
and do not turn empty wake-ups into workflow counters. Never list, nudge, or emit
progress chatter between returns. Detach only for a shared-policy reason and persist
the join set plus `detach_reason`; notifications do not resume aggregation.

If subagent dispatch is genuinely unavailable, execute every applicable lens as a
separate inline section from the installed `review-steps/` resources and disclose
`inline` mode. Never collapse to a single general review.

## 4. Enforce verdict semantics

Use the orchestrator's verdict policy:

- change-caused and touched structural regressions affect the verdict;
- unchanged baseline debt is shown separately;
- APPROVED requires every applicable lens, complete untracked scope, complete
  provenance, and zero required UNVERIFIED dimensions;
- tests and security scans alone cannot approve architectural shape.
- only `required_fix` findings block the change; unresolved `user_decision` items
  produce `TRIAGE REQUIRED`, while backlog/baseline remain visible and non-blocking.

## Guardrails

- Read-only for source and feature artifacts.
- Do not create commits, branches, or tags.
- Do not auto-install tools.
- Do not expose secret values.
- Do not promote Observed/Legacy project evidence into review rules.
- Return a compact decision and report paths. Keep full findings, baseline section,
  commands, exit codes, and logs in review artifacts; show them on request.
- Keep the full report in the Git-local review snapshot. Because this standalone
  skill is read-only, do not create `DEFERRED.md`, update OpenSpec, or promote items
  to an external backlog.
