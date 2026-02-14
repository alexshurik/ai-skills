---
name: sk-copy-context
version: 1.0.0
description: Copy current session context to clipboard
license: MIT

# Claude Code
disable-model-invocation: true
allowed-tools: Bash

# Cross-platform hints
platforms:
  codex: true
  cursor: true
  kimi: true
---

# Copy Context to Clipboard

Copy a detailed summary of the current session context to clipboard.

## Steps:

### 1. Generate Detailed Context Summary

Create a comprehensive handoff text:

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

### 2. Copy to clipboard

```bash
cat << 'CONTEXT' | pbcopy
[the detailed context text here]
CONTEXT
```

### 3. Tell the user

Say: "Context copied to clipboard."
