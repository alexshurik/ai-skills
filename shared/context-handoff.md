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

## Usage

### Copy to Clipboard
Use `/sk-copy-context` to generate and copy this to clipboard.

### Switch to Another Agent
Use `/sk-pass-to-claude` or `/sk-pass-to-minimax` to switch to another AI agent with context.

## Tips for Good Handoffs

1. **Be Specific** - Include file paths, line numbers, exact values
2. **Include Why** - Not just what was done, but why decisions were made
3. **List Blockers** - Anything that stopped progress
4. **Note Preferences** - User preferences that affect future work
5. **Keep Updated** - Update context as work progresses
