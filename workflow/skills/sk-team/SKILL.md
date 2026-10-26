---
name: sk-team
description: Interactively choose and run a Micro, Quick, or Full development workflow with configurable checkpoints, workspace isolation, assurance, and finish.
license: MIT
---

# sk-team — Adaptive Development Workflow

Use this as the primary entry point for a coding objective. It resolves one
workflow charter, persists it, and then runs the smallest route that provides the
requested confidence.

## Required policy

Read completely before acting:

```text
workflow/agents/shared/workflow-charter-policy.md
workflow/agents/shared/orchestration-policy.md
workflow/agents/shared/handoff-protocol.md
workflow/agents/shared/scope-governance.md
workflow/agents/shared/runtime-state-policy.md
```

Installed adapters expose the same files under their shared agent references.

## Start

Before task setup, apply `sk-onboard check` once for the target repository, using
its read-only first-use contract. Reuse an existing check result for this session;
offer missing steering without blocking the task or starting onboarding without
acceptance. Pass the result to Quick/Full so they do not ask again.

1. Inspect the request and only enough repository state to make a recommendation.
   Do not delegate merely to classify the route.
2. Resolve the five user-facing choices from the request: Path, Control, Workspace,
   Finish, and Checks. Use the exact labels from `workflow-charter-policy.md`.
3. If any choice is missing, show one compact recommended charter and ask once.
   Offer advanced settings only on request or when a real ambiguity needs them.
4. If all choices are explicit, echo the resolved charter and begin without a
   confirmation round.
5. Create a new run for this objective. Never inherit YOLO from another run.
6. Resolve `auto` workspace once, preserve unrelated changes, and initialize the
   schema-v3 runtime ledger with `--workflow sk-team` plus the complete charter.
   Apply the shared `workspace-lifecycle.md` policy to record resource ownership
   and include post-merge cleanup in the start receipt when Merge is selected.

Recommend from the requested product risk, not from ceremony created by the
workflow. The number of bullets, generated acceptance criteria, touched test files,
screenshots, or downstream evidence artifacts must not promote a task to Full. A
clear UI refinement spanning several related screens is normally Quick even when it
needs responsive renders. Full requires a material product, boundary, contract,
migration, deployment, or ownership decision.

Visual quality is not a fifth user choice. When Git scope can affect rendered UI,
the visual quality gate is mandatory and route-appropriate; do not ask whether the
user wants a merely functional versus polished result.

The receipt uses this compact shape:

```markdown
## Маршрут задачи
- Путь: <Суперкороткий | Короткий | Полный>
- Контроль: <Каждый этап | Только важное | YOLO>
- Рабочая копия: <Текущая | Отдельная> — <reason when auto-resolved>
- Финиш: <Только разобраться | Оставить правки | Коммит | PR | Merge | Deploy>
- Проверки: <Обычные | Усиленные>
```

## Run the selected path

### Super-short / Micro

Keep ownership in the root context. Establish the intended behavior, inspect the
smallest relevant scope, make the smallest in-scope edit, run focused authoritative
checks, inspect the final diff, and record the delivery receipt. Do not spawn an
agent by default. Escalate when route criteria cease to hold.

For `Только разобраться`, remain read-only and return a diagnosis with evidence.
For a source change, preserve Red→Green when fixing behavior; for a typo or equally
mechanical change, proportionate verification is enough. `elevated` assurance adds
the relevant full repository gate and a fresh independent review when risk warrants
it; if that work no longer fits Micro, escalate to Quick.

For rendered UI, open the exact-source result at one representative compact or
desktop viewport appropriate to the change, cover the effective scroll extent, and
self-review hierarchy, grouping, density, alignment, rhythm, and product fit. The
root personally opens the final render; a passing test or source inspection is not
a visual pass. Escalate to Quick when the result needs independent judgment or
cross-viewport behavior.

### Short / Quick

Apply `sk-team-quick` as the execution contract, but do not ask the workflow choices
again.
Use one implementation thread and one fresh combined review/acceptance thread. Its
design and final gates follow the selected authorization mode, not legacy mandatory
approval behavior.

Use Quick for a coherent UI-polish batch with clear intended outcomes, including
several related screens. Do not reinterpret responsive states, regression tests, or
visual evidence as separate feature workstreams.

### Full

Apply `sk-team-feature` as the execution contract, but do not ask the workflow
choices again.
Use clean phase agents, independent core review lenses, acceptance, and the selected
optional phases. Phase-complete ceremony follows the authorization mode.

For Quick and Full rendered UI work, the root personally opens the final compact and
desktop evidence before finish and confirms that the current source has both
engineering and visual approval. This final look is aggregation, not a new user
approval gate.

## Continue without approval churn

- `manual`: surface each phase gate.
- `checkpoints`: surface Scope Lock and Execution plus genuine typed stops.
- `yolo`: continue across ceremony, implementation, verification, and authorized
  remediation until delivery or a typed stop.

Never ask for permission already granted by the charter. Never treat YOLO as scope
expansion or as authority for a different destination. On a typed stop, persist the
reason code and ask one concrete decision; after the answer, resume without replaying
the charter.

If the user adds another item mid-run, classify the added product behavior itself.
Continue in the current route when it shares the approved owners and risk envelope;
escalate only for a material boundary/contract/product decision, not because the
checklist became longer.

## Finish

Perform the selected terminal action after required checks. The charter itself is
authority for local changes, commit, PR, merge, or deploy to its recorded target.
Record the matching terminal receipt, then apply the shared
`workspace-lifecycle.md` policy before completing the workflow. Preserve evidence
outside any worktree being removed; report the outcome, verification, surviving
artifacts, deferred items, and removed/retained resources with reasons. Complete
only after delivery succeeds and cleanup is reconciled. Do not add a redundant
“final approval” gate.
