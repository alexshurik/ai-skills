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

Copy a compact, artifact-first resume handoff to the clipboard. This is a fallback
for sessions without a usable workflow ledger, not a transcript export.

## Steps:

### 1. Resolve durable state first

Read the canonical [context handoff template](references/context-handoff.md).
Resolve `git rev-parse --git-path sk-workflow` and locate the active change's runtime
directory. `events.jsonl` is the authoritative ledger and `state.json` is only its
projection. Resolve Python 3.10+ and run the installed/source runtime helper `status`;
when `snapshot_status` is `valid`, also run `validate` before using the projection.
Use `~/.claude/agents/shared/runtime-state-policy.md` or the source
`workflow/agents/shared/runtime-state-policy.md`, and its colocated installed/source
`runtime-state/sk_state.py` helper. Report the complete status vocabulary:
valid | stale | diverged | missing | orphaned | legacy_v1 | unsupported_schema.
Validate valid; repair stale/diverged/missing only with a valid non-empty journal;
migrate legacy_v1 without history (repair it when valid history exists); fail closed
with `recover-journal-or-reinitialize` for orphaned or missing/diverged without
history; and fail closed with `require-compatible-helper` for unsupported_schema.
Do not mutate state during copy.

Include only the current goal, approvals/constraints, current phase/status, runtime
directory, journal/projection paths, schema/revision/snapshot health, exact artifact
fingerprints, dirty paths, blockers, and next action.

Never paste conversation history, full artifacts/diffs, raw tool output, or a list
of every file merely read. Keep the handoff under 100 lines / about 4,000 tokens.
If a needed detail is too large, persist it to a named artifact and copy its path
and fingerprint.

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
