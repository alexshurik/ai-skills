---
name: sk-code-review
version: 3.1.0
description: Standalone code review for uncommitted changes. Delegates to sk-code-reviewer agent for the full review process.
license: MIT

# Claude Code
allowed-tools: Task, Read, Bash, Glob, Grep, AskUserQuestion

# Cross-platform hints
platforms:
  codex: true
  cursor: true
  kimi: true
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

Spawn the **sk-code-reviewer** agent to perform the full review:

```
Task tool:
  subagent_type: "sk-code-reviewer"
  prompt: |
    Review the codebase in the current repository.

    Context:
    - Design doc: [path if user selected one, or "none"]
    - Code style: [path if exists, or "none"]

    CRITICAL — follow steps IN ORDER, do NOT skip any:

    1. Detect project stack
    2. Research best practices (if framework/domain detected)
    3. Run linters
    4. **MANDATORY: check_and_install_tools step** — check which analysis
       tools are missing, then use AskUserQuestion to ask the user which
       ones to install. WAIT for user response. Install approved tools.
       DO NOT skip this step. DO NOT just list tools in the report.
    5. Run deep analysis with ALL available tools (including just-installed)
    6. Review each changed file against all checklists
    7. Provide structured verdict: APPROVED or CHANGES REQUESTED
```

**If Task tool is not available** (e.g., Codex, Cursor):
Apply the review process from the `sk-code-reviewer` agent definition directly. The agent file contains the complete review checklists, tool commands, and severity mappings.

---

## Guardrails

- **Read-only for source code** — NEVER make any changes to source code files
- **No commits** — Do not create, amend, or modify any commits
- **No git operations** — Only read git state, never modify it
- **Objective review** — Focus on the code, not on validating prior decisions
