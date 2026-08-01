---
name: sk-code-review
description: Review committed, staged, unstaged, and untracked changes through the full baseline-aware multi-lens pipeline without modifying source code.
---

# Review Repository Changes

Treat this as a fresh, read-only review. Ignore prior conclusions and derive scope,
authority, evidence, findings, and verdict from the repository.

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

Use seven independent clean lens threads. Pass artifact paths for complete
tracked/untracked scope, evidence, design authority, runner, profiles, and
static-analysis provenance as specified by the orchestrator; do not paste full
files, base diffs, or raw tool output into prompts. For Codex, use
`fork_turns="none"` and omit model/reasoning overrides so reviewers inherit the
parent's selected profile. No lens may spawn another agent.

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

## Guardrails

- Read-only for source and feature artifacts.
- Do not create commits, branches, or tags.
- Do not auto-install tools.
- Do not expose secret values.
- Do not promote Observed/Legacy project evidence into review rules.
- Return a compact decision and report paths. Keep full findings, baseline section,
  commands, exit codes, and logs in review artifacts; show them on request.
