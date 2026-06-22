# Agent Handoff & Clarification Protocol

Canonical interaction contract shared by every `sk-*` agent and the team
orchestrators. The rules below are **inlined** into each agent (an `<interaction_protocol>`
block) because a spawned subagent only reliably follows instructions in its own
prompt — it cannot be assumed to Read this file at runtime. This document is the
single source of truth; keep the inlined blocks in sync with it.

It exists because of a structural fact about how these agents run:

> An `sk-*` agent is almost always spawned as a **subagent** (via the Agent/Task
> tool) by a team orchestrator or by the main assistant. A subagent has **no direct
> channel to the human** — its `AskUserQuestion` does not reach the user, and its
> final message is returned to the *caller*, not shown to the user. Only the caller
> (the orchestrator or the main assistant) has the user's screen.

Two failure modes follow if agents ignore this, and the protocol fixes both:

- The agent produces a rich result, but the caller summarizes it to "done" and the
  user never sees the structure. → **Handoff contract** (below).
- The agent needs a decision from the user, calls `AskUserQuestion`, gets no answer
  (or guesses), and proceeds on a fabricated assumption. → **Clarification-via-return**
  (below).

---

## 1. Clarification-via-return (how a subagent asks the user)

**A subagent MUST NOT assume it can reach the user.** Do not rely on
`AskUserQuestion` to surface a question — when you run as a subagent it does not
reach the human. Instead:

1. Do your read-only work first (read inputs, explore the codebase) so your
   questions are specific and informed.
2. If genuine ambiguity remains — a decision only the user can make (approach
   trade-off, scope boundary, integration choice, missing requirement) — **STOP**.
   Do **not** write final artifacts. Do **not** guess or pick a default to keep
   moving.
3. Return a `## NEEDS USER INPUT` block as your entire result (template below) and
   end your turn. The caller will surface the questions, collect answers, and
   re-invoke you with those answers appended to your prompt.
4. When re-invoked with answers, proceed. If new ambiguity appears, you may return
   `## NEEDS USER INPUT` again — it is a loop, not a one-shot.

Never fabricate the user's answer. "No answer available" means *ask via return*, not
*decide for them*. This is the same rule the orchestrators state as "NEVER answer
agent questions on behalf of the user."

### `## NEEDS USER INPUT` template

```markdown
## NEEDS USER INPUT

**Agent:** <agent name>  ·  **Stage:** <what you were doing>  ·  **Status:** BLOCKED — no artifacts written

I explored <what you read/looked at>. Before I write <artifact>, I need decisions on:

### Q1: <question>
- **Why it matters:** <impact of the choice>
- **Options:**
  - **A)** <option> — <trade-off>
  - **B)** <option> — <trade-off>
- **My recommendation:** <A/B + one-line reason> (still your call)

### Q2: <question>
- ... (max 4 questions per round; group related ones)

**What happens next:** answer these and I'll <write the artifact / continue>.
```

A subagent may still *list* `AskUserQuestion`-shaped options in this block (label +
description) so the caller can render them directly — but the **deciding** happens
at the caller, never inside the subagent.

---

## 2. Handoff contract (how a subagent returns a result)

Every agent ends its turn with a **self-contained handoff block** — the structured
result the user needs to act, not a "done" line. The block must:

- Be complete on its own: a caller pasting it verbatim gives the user everything to
  decide the next step (decision/verdict, artifact paths, the structural digest —
  e.g. file map, model changes, API changes, findings).
- Persist its key digest to an **artifact file on disk** (the agent already writes
  `design.md` / `VERIFICATION.md` / etc.), so the information survives even if a
  caller fails to relay it.
- End with an explicit relay directive so any caller honors it:

  > **Caller: surface this block to the user verbatim — do not summarize, truncate,
  > or replace it with "done". If you are an orchestrator, also persist it per your
  > phase rules.**

## 3. Caller responsibilities (orchestrator or main assistant)

Whoever spawns an `sk-*` agent owns the user's screen and MUST:

1. **Relay handoffs verbatim.** Show the agent's handoff block (and the specific
   artifact sections it names) without paraphrasing. Never compress a returned
   structure to a status line.
2. **Surface `## NEEDS USER INPUT` immediately.** When an agent returns this block,
   present the questions to the user (via `AskUserQuestion` or inline), wait for
   answers, then **re-invoke the same agent** with the answers appended to its
   prompt. Never answer on the user's behalf; never skip to the next phase.
3. **Never auto-proceed** past a handoff or an input request without explicit user
   approval.
