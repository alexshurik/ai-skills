# Context Handoff Template

Use this template when passing context between AI agents or sessions.

## Template

```markdown
# Session Context Handoff

## Working Directory
[full pwd path]

## Current Task
[Main goal - what the user asked for originally]
[Sub-tasks if any]

## Durable State
- Ledger: [git-local state.json path or none]
- Phase/status: [current bounded phase and status]
- Approved artifact fingerprints: [paths + fingerprints]

## Changed and Authority Files
- [Durable artifacts] - [brief purpose + fingerprint]
- [Dirty source paths only] - [brief state]
- [Authoritative guidance/design paths]

## Current State
[Where we stopped - what's the current situation]
[Any pending operations]

## Next Steps
1. [Immediate next action]
2. [Following actions]

## Verification
- [Exact important command] → [status/log artifact]
- [Skipped or UNVERIFIED gates]

## Decisions & Constraints
- [Design decisions made and why]
- [Constraints to keep in mind]
- [User preferences expressed]

## Open Questions / Blockers
- [Any unresolved issues]
- [Things that need clarification]
```

## Guidance

1. Include exact paths, line numbers, values, and commands where they matter.
2. Record why decisions were made, not only what changed.
3. List unresolved blockers and user preferences explicitly.
4. Prefer a validated workflow ledger over reconstructing a long narrative.
5. Do not include conversation history, full artifacts/diffs/logs, routine tool
   output, or files that were only read.
6. Keep the handoff below 100 lines / about 4,000 tokens; use artifact paths and
   fingerprints for larger data.
