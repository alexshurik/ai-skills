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

## Progress & Completed Work
- [What was done step by step]
- [Key decisions made]
- [Problems solved]

## Key Files
- [Files created] - [brief description]
- [Files modified] - [what changed]
- [Files read/analyzed] - [why important]

## Current State
[Where we stopped - what's the current situation]
[Any pending operations]

## Next Steps
1. [Immediate next action]
2. [Following actions]

## Technical Context
- [Important technical details]
- [Dependencies, versions, configs]
- [Commands that were run]

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
4. Keep the handoff current as the work progresses.
