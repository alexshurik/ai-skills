---
name: sk-pass-to-claude
version: 1.0.0
description: Save context and switch to aclaude in a new tab
license: MIT

# Claude Code
disable-model-invocation: true
allowed-tools: Bash, Read, Write

# Cross-platform hints
platforms:
  codex: false
  cursor: false
  kimi: false
---

# Switch to aclaude

Open aclaude in a new tab with detailed context passed as argument.

## Steps:

### 1. Generate Detailed Context Summary

Create a comprehensive handoff (will be passed as CLI argument):

```
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

### 2. Open new tab and launch aclaude with context as argument

IMPORTANT: Escape single quotes in context with '\''

```bash
osascript <<EOF
tell application "System Events"
    keystroke "t" using command down
    delay 0.2
    keystroke "cd $(pwd) && aclaude '[ESCAPED_CONTEXT]'"
    keystroke return
end tell
EOF
```

If keystroke fails with "not allowed" error, copy command to clipboard:
```bash
echo "cd $(pwd) && aclaude '[ESCAPED_CONTEXT]'" | pbcopy
```

### 3. Tell the user

If worked: "Done! aclaude opening with context."

If failed: "Command in clipboard. Cmd+T -> Cmd+V -> Enter"
