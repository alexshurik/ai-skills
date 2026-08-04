# Agent Handoff & Clarification Protocol

Canonical interaction contract shared by `sk-*` agents and orchestrators. Keep the
short `<interaction_protocol>` blocks in role prompts aligned with this source.

A subagent normally has no direct channel to the human. The caller owns user
interaction; the child owns one bounded deliverable and its durable artifact.

## 1. Clarification through the caller

1. Read available authority and perform safe read-only investigation first.
2. If a material decision only the user can make remains, do not guess and do not
   write the final artifact.
3. Persist a small checkpoint under the workflow runtime path when useful. It records
   facts already established, artifact inputs, the unresolved decision, and the next
   step; it does not contain raw logs.
4. Return `## NEEDS USER INPUT` as a compact `BLOCKED` result with at most four
   grouped questions, impact, options, and a recommendation.
5. The caller surfaces the questions. It may use **one short follow-up** in the same
   thread when this remains the same bounded deliverable. Otherwise it starts a clean
   successor with the checkpoint path and answers.

Never fabricate the user's answer or answer an agent question on the user's behalf.

```markdown
## NEEDS USER INPUT
- Agent/stage: ...
- Checkpoint: `path` or none
- Q1: ...
  - Why it matters: ...
  - Options: ...
  - Recommendation: ...
- Next after answer: ...
```

## 2. Artifact-first handoff

Every completed agent persists complete details in a **durable artifact** or a named
Git-local runtime artifact. Raw logs, tables, full findings, and evidence remain
there.

The model-visible handoff is a **compact return**, normally at most **50 lines** or
about 2,500 tokens. It contains only status/verdict, required actions, critical
evidence, blockers, and artifact paths with fingerprints.

```markdown
## FINAL
- Deliverable: ...
- Status/verdict: ...
- Required actions: ...
- Critical evidence: ...
- Artifacts: `path` (`fingerprint`)
- Blockers: none
```

Do not paste a full artifact or tool log into the caller message by default. The user
can request `Show <artifact>` at an approval gate.

## 3. Caller responsibilities

The caller:

1. validates that the referenced artifact exists and matches the returned status;
2. surfaces the compact decision, required actions, blockers, and artifact paths;
3. surfaces `## NEEDS USER INPUT` immediately and never answers it on the user's
   behalf;
4. records explicit approval and artifact fingerprints in workflow state;
5. never auto-proceeds through an approval gate;
6. starts a clean child for a new phase, redo, remediation, or review cycle.
7. passes remediation an allowlist of approved finding IDs, never a generic
   instruction to fix every reviewer suggestion.
