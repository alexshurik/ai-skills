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

You are a skill running at the **TOP level** (in the main loop), so you can spawn
subagents. **Do NOT spawn `sk-review-orchestrator` as a subagent.** A subagent
cannot spawn its own subagents, so a nested orchestrator could never run its
parallel lens passes (its step 6) — it would silently collapse to one shallow
single-pass review and still render a verdict. Instead, **execute the
orchestrator flow yourself, here, in this top-level context**, so the fan-out is
legal.

Read the flow definition (single source of truth — do not reinvent it):

```
Read("~/.claude/agents/sk-review-orchestrator.md")
  or Read("workflow/agents/sk-review-orchestrator.md")   # from the skills repo
```

Then run its `<execution_flow>` step by step in THIS context:

1. **Steps 1–5** (scope, profile resolution, tool discovery, static analysis) —
   run inline with your Read/Bash/Glob/Grep tools. Step 5 is NOT optional and NOT
   hand-run: invoke the deep-analysis battery script
   (`~/.claude/agents/static-analysis/run-static-analysis.sh`) and paste its
   provenance table into the verdict. A green pre-commit/CI is not a substitute.
2. **Step 6 (dispatch)** — spawn ALL FOUR lens agents **IN PARALLEL** via Task,
   in a single message (multiple tool uses), each with full file content plus the
   data step 6 specifies: `sk-review-security`, `sk-review-architecture`,
   `sk-review-stack-rules`, `sk-review-instruction-quality`. This is the whole
   reason the flow runs top-level — the fan-out is legal here.
3. **Steps 7–8** (aggregate, verdict) — run inline. Honor the verdict-downgrade
   and the ✓ parallel / ⊟ inline / ⊘ skipped disclosure rules in the flow.

Pass into the flow:
- Design doc: [path if the user selected one in Step 2, or "none"]
- Code style: [path if exists, or "none"]

**If the Task tool is genuinely unavailable** (e.g., Codex, Cursor — no subagents
at all), run the four lens passes as **sequential inline sections** instead of
parallel Task calls, driven by `workflow/agents/review-steps/*.md`, and **say so
in the report** (mark each pass ⊟ inline). Do NOT improvise a different process —
always drive from the orchestrator definition.

---

## Guardrails

- **Read-only for source code** — NEVER make any changes to source code files
- **No commits** — Do not create, amend, or modify any commits
- **No git operations** — Only read git state, never modify it
- **Objective review** — Focus on the code, not on validating prior decisions
