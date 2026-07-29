---
name: sk-copy-context
version: 1.1.0
description: Copy current session context to clipboard
license: MIT

# Claude Code
disable-model-invocation: true
allowed-tools: Bash, Write

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

Read the canonical [context handoff template](references/context-handoff.md).
Replace every placeholder with the current session's concrete state; keep all
sections so the next agent can continue without reconstructing context.

### 2. Copy to clipboard

1. Run `mktemp` to allocate a new temporary file.
2. Use the host's file-writing tool to write the completed context byte-for-byte
   to that file. Never place context text in shell source, a command argument,
   an environment variable, `printf`, or a shell redirection construct.
3. Resolve `scripts/copy-context.sh` relative to this `SKILL.md` and invoke it
   with the temporary file path as its only argument.
4. Remove the temporary file after the helper returns.

The helper selects `pbcopy`, `wl-copy`, `xclip`, or PowerShell without changing
the context. If it reports that no supported command exists, relay that error
and do not claim the copy succeeded. Only report success when the helper exits
with status 0.

### 3. Tell the user

Say: "Context copied to clipboard."
