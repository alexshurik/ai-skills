# Workflow Charter Policy

This policy is the entry contract for `sk-team`. Read it before choosing a route,
creating a worktree, asking for approval, or dispatching an agent. The charter is
fixed for one objective and persisted in runtime state; it is not inferred again at
every phase.

## One compact start decision

When the request does not already answer the choices, show one compact charter with
a recommendation and ask once. Do not ask the fields serially.

```markdown
## Как ведём задачу

Рекомендую: **<path> · <control> · <workspace> · <finish>**

1. **Путь:** Подбери сам | Суперкороткий | Короткий | Полный
2. **Контроль:** Каждый этап | Только важное | YOLO
3. **Рабочая копия:** Текущая | Отдельная | Выбрать безопасно
4. **Финиш:** Только разобраться | Оставить правки | Коммит | PR | Merge | Deploy
5. **Проверки:** Обычные | Усиленные

Ответьте `Запускай` для рекомендации или перечислите изменения одной строкой.
```

If the user already said, for example, “коротко, в текущей копии, YOLO, до PR”,
do not ask again. Echo the resolved charter as a receipt and start. A blanket phrase
such as “доведи до конца без меня” selects YOLO for the current objective, but does
not broaden scope or silently select merge/deploy.

Advanced settings are offered only on request or when they resolve a real ambiguity:

- **Этапы:** recommended set, or explicit include/skip choices
- **Если задача выросла:** Повысить путь автоматически | Спросить
- **Статусы:** Только решения | Короткие вехи

`Обычные` (`standard`) is the default. `Усиленные` (`elevated`) adds genuinely
independent or broader evidence for high-risk work; it does not authorize repeating
the same unchanged test matrix at every phase. Explicit stage customization is
stored with the scope/constraints digest. It may remove optional ceremony or
advisory phases, never a safety boundary, required visual gate, or selected terminal
verification.

Visual quality is not an optional assurance mode. Any route that changes rendered
UI automatically enables the route-appropriate visual quality gate; do not ask the
user to choose between “functional” and “polished” UI.

## Internal charter

Persist these orthogonal fields in schema-v3 runtime state:

| User-facing choice | Runtime value | Meaning |
|---|---|---|
| Подбери сам | resolved to `micro`, `quick`, or `full` | Root classifies once from evidence. |
| Суперкороткий | `micro` | Root-owned inspection, edit, focused checks, and self-review. No agents by default. |
| Короткий | `quick` | One implementation thread and one fresh combined review/acceptance thread. |
| Полный | `full` | Discovery/design/execution plus independent review and acceptance roles. |
| Каждый этап | `manual` | Ceremony and authority gates wait for the user. |
| Только важное | `checkpoints` | Wait only at Scope Lock, Execution, and genuine authority/safety stops. |
| YOLO | `yolo` | Policy decides ceremony gates and continues within approved scope and destination. |
| Текущая | `current` | Work in the current checkout after preserving unrelated changes. |
| Отдельная | `worktree` | Create one named sibling worktree. |
| Выбрать безопасно | `auto` | Resolve once using the rules below and record the result. |
| Оставить правки | `local` | Finish with verified working-tree changes. |
| Коммит | `commit` | Create a local commit after green checks. |
| PR | `pr` | Push and open/update the selected pull request. |
| Merge | `merge` | Merge into the selected target after its required checks. |
| Deploy | `deploy` | Perform the explicitly selected deployment target and verify it. |
| Обычные | `standard` | Risk-proportionate focused evidence plus one final applicable broad receipt. |
| Усиленные | `elevated` | Additional independent/broader evidence justified by material risk. |

`Только разобраться` is a read-only objective: produce a diagnosis/report and no
source mutation. Its terminal delivery is recorded as `local` with report evidence.
Changing from diagnosis to implementation is a scope change and must be recorded.

The root initializes runtime state with `--workflow sk-team` and the selected
`--route`, `--assurance`, `--authorization`, `--workspace`, and `--destination`.
The scope digest covers the objective, constraints, non-goals, and selected finish.
Use the helper's `change-authorization`, `change-scope`, `resolve-workspace`,
`change-destination`, `escalate-route`, and `record-terminal` transitions; never
hand-edit the journal or projection.

## Route selection

Choose the cheapest route that preserves the required confidence:

- **Micro** — localized, well-understood, normally one owner and a small diff;
  no unresolved product or architecture decision; focused verification is enough.
- **Quick** — a bounded bugfix or small feature needing implementation plus a fresh
  independent review, but no multi-role discovery/design program.
- **Full** — new or changed public contract/data model/trust boundary/deployment
  path; multiple components with non-obvious ownership; material product choices;
  high-risk migration, payment, destructive data, concurrency, or broad feature.

Classify the user's requested behavior before expanding it into specifications or
tests. Do not use these as Full-route signals by themselves:

- number of request bullets or acceptance criteria;
- several related screens sharing established owners and design language;
- generated test files, screenshots, goldens, or OpenSpec artifacts;
- safeguards and edge cases proposed by the agent after the user request;
- a large diff caused mainly by test/evidence updates.

A clear multi-screen UI polish pass, even with responsive behavior and one shared
query/view-model adjustment, is normally Quick. Promote it to Full only when the
requested outcome introduces a material product decision, new public/data/trust
boundary, non-obvious cross-owner architecture, migration, or deployment risk.

Escalate only upward: `micro → quick → full`. The root may escalate automatically
when the charter selected “Повысить путь автоматически”; otherwise stop once with
the evidence and recommendation. Never silently reduce assurance.

Default budgets are visible policy, not hidden retry loops:

| Route | Agent attempts | Review rounds | Remediations |
|---|---:|---:|---:|
| Micro | 1 | 1 | 1 |
| Quick | 6 | 3 | 2 |
| Full | 20 | 3 | 2 |

These are ceilings, not targets. They cover the ordinary pass, one remediation, and
the one bounded recovery already authorized by policy; Full also has room for its
independent leaves. Route escalation raises every ceiling to at least the target
route default and never reduces an existing explicit ceiling. Transport-only wait
timeouts do not consume budgets. Exhaustion uses the typed stop `budget.exhausted`
and returns the exact remaining decision.

## Verification economy

Treat verification as a content-addressed workflow resource:

1. During implementation, repeat only focused Red/Green checks and narrowly filtered
   renders needed for the current edit.
2. After the implementation input closure is stable, run the applicable broad suite
   once and record its command, toolchain/config/lockfile/environment identity, path
   hashes, result, and logs.
3. Review validates and consumes that receipt. It runs only missing, stale, or
   untrusted rows; it does not create a second root-owned copy of an already trusted
   broad receipt.
4. Remediation runs focused gates for the changed delta. Unchanged receipt rows are
   reused by verified hash.
5. Acceptance consumes review and gate receipts and runs only missing
   criterion-specific interactions. It is not another regression-suite phase.

A full rerun is justified only when its covered input closure changed, the original
receipt is invalid/untrusted, or repository/release policy explicitly requires an
independent run. High-risk or Elevated work adds orthogonal evidence instead of
invalidating an unchanged exact-input receipt. Record the reason.

## Authorization semantics

Gate kinds are distinct:

- `ceremony`: phase/artifact ready acknowledgements;
- `authority_decision`: material product, scope, architecture, or public-contract
  choice not already covered by the charter and approved artifacts;
- `sensitive_action`: external access, secrets, live cost/value, or destructive /
  irreversible action;
- `terminal_action`: a finish beyond the selected destination or target.

`manual` waits at every ceremony and authority gate. `checkpoints` auto-decides
ordinary ceremony but waits at Scope Lock, Execution, and every authority/sensitive/
terminal gate. `yolo` auto-decides all ceremony gates and performs reversible,
in-scope implementation, tests, review, and remediation without asking again.

YOLO may automatically remediate only findings with both:

```text
disposition = required_fix
remedy_authority = within_approved_design
```

YOLO never authorizes a material scope/product decision, missing credentials or
external access, destructive/irreversible operations, live spend/value transfer,
unverifiable evidence, or a terminal action beyond the chosen finish. These stops
remain user-owned. Optional reviewer ideas are deferred rather than implemented.

When an allowlisted required fix remains after targeted verification, YOLO may
start one narrow successor recovery automatically if the outcome still fits the
approved design, scope, safety envelope, and destination. That recovery changes
only affected inputs, runs focused gates, and repeats the owning targeted
verification; it does not restart a full review or open a fresh feature cycle. If
the same blocker remains after that bounded recovery, use `budget.exhausted` with
the exact unresolved IDs rather than asking for a ceremonial approval.

The authorization lifetime is exactly one run/objective. A new independent request
starts a new charter; it never inherits YOLO from an earlier run. The user may
change authorization mid-run; record the source and reason once.

Only the user may increase autonomy or change the selected destination. Repository
or safety policy may reduce autonomy or stop the run, but may not promote itself to
YOLO, approve an authority gate, or extend Local/Commit into PR/Merge/Deploy.

## Workspace resolution

Ask once when the user explicitly wants to choose. For `auto`, select and record:

- current checkout for Micro/Quick when it is safe, there is no overlapping dirty
  work, and parallel isolation is unnecessary;
- a worktree for Full, overlapping/unattributed dirty changes, parallel execution,
  or repository policy requiring isolation.

Do not create a worktree merely because a legacy workflow used one. Before either
choice, inspect Git state and preserve unrelated user changes. Read
`workspace-lifecycle.md` at setup and finish. Record ownership of worktrees and
temporary resources; the selected Merge finish includes its verified, run-owned
cleanup. Pre-existing/shared workspaces and destructive overrides require separate
authority.

## Typed stops

Use one of these stable reason codes and ask one decision-focused question:

```text
decision.material_product
decision.material_scope
boundary.external_access
boundary.destructive_or_irreversible
boundary.live_cost_or_value
boundary.terminal_not_authorized
evidence.unverifiable
budget.exhausted
control.user_reset
```

A stop is not a new approval ceremony. Explain the concrete boundary, options,
recommendation, and what resumes afterward. Do not repeat a question already
answered by the charter or an approved artifact.

## Finish and receipt

The selected destination is authority to perform that terminal action when its
normal checks pass; it does not need a second generic “final approval”. Record a
terminal receipt matching the destination before completing the run. A failed or
blocked PR/merge/deploy remains visible with evidence and does not become a false
success.

After delivery, reconcile resources using `workspace-lifecycle.md` before marking
the run complete. Local/Commit/open-PR worktrees remain available; a verified merge
removes eligible task worktrees after preserving artifacts and Git-local runtime
state. Report removed and retained resources with reasons and surviving evidence
paths. Do not turn normal authorized cleanup into another approval ceremony.
