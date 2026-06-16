---
name: sk-code-review
description: Standalone code review for uncommitted changes. Delegates to sk-review-orchestrator for the full review pipeline.
license: MIT
allowed-tools: Task, Read, Bash, Glob, Grep, AskUserQuestion
---

# Code Review for Uncommitted Changes

**IMPORTANT: Context Reset.** Treat this as a fresh review session. Ignore any prior conversation context. Your only focus is analyzing the uncommitted changes objectively.

---

## Step 1: Check for Changes

```bash
git status --porcelain
```

**If no changes:** Output "No uncommitted changes to review." and stop.

---

## Step 2: Gather Context

### Check for design documents
```bash
find . -maxdepth 3 -name "design.md" -o -name "*.spec.md" -o -name "PROPOSAL.md" 2>/dev/null | head -10
```

If design documents exist, ask the user via AskUserQuestion if they want to review changes in context of a specific document.

### Check for code style rules
```bash
ls -la .claude/rules/code-style.md .claude/CLAUDE.md .cursorrules .cursor/rules/*.mdc AGENTS.md .clinerules .github/copilot-instructions.md 2>/dev/null
```

If no code-style.md exists, ask the user if they want to generate one first (`/sk-explore-codestyle`).

---

## Step 3: Run Review

Spawn the **sk-review-orchestrator** agent:

```
Task tool:
  subagent_type: "sk-review-orchestrator"
  prompt: |
    Review uncommitted changes in the current repository.

    Context:
    - Design doc: [path if user selected one, or "none"]
    - Code style: [path if exists, or "none"]
```

**If the Task / subagent tool is not available** (e.g., Codex, Cursor),
the orchestrator's flow runs as a single role inside the current
session: read `~/.claude/agents/sk-review-orchestrator.md` (or
`workflow/agents/sk-review-orchestrator.md` from the skills repo) and
execute its `<execution_flow>` step-by-step. Subagents become sequential
sections of the review rather than parallel calls. Do NOT improvise a
different review process — always drive from the orchestrator definition.

---

## Guardrails

- **Read-only for source code** — NEVER make any changes to source code files
- **No commits** — Do not create, amend, or modify any commits
- **No git operations** — Only read git state, never modify it
- **Objective review** — Focus on the code, not on validating prior decisions
