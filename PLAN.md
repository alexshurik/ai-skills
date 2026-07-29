# 📋 Plan: Strengthen the global `sk-*` workflows

## Summary

Strengthen the existing skills using the `webapp-auth-shell` retrospective as a
regression specification. Keep the git repository root
as the only source of truth; treat `~/.agents/skills`, `~/.codex/skills`,
`~/.claude`, and Kimi directories as generated installation targets.

The implementation will add explicit architecture and implementation stop-gates,
classify convention evidence by authority, split code review into independent
lenses, add a mandatory lightweight retrospective to the full feature workflow,
and forward-test the result against the historical bad auth implementation.

## Background (Phase 1)

- **Request:** Analyze the auth retrospective and produce a detailed plan for
  improving `sk-architect`, `sk-developer`, `sk-explore-codestyle`,
  `sk-review-orchestrator`/`sk-code-review`, and `sk-team-feature`.
- **Primary regression source:**
  `deli-check-backend/openspec/changes/webapp-auth-shell/RETROSPECTIVE.md`.
- **Historical bad implementation:** backend commits `ee6100b..5aa47ea`.
  The range contains the first auth implementation with `LoginNonceService`,
  custom IP rate limiting, API leakage, one-use abstractions, and raw JWT
  dictionaries. Targeted companion fixtures will cover the unverified local
  import and unauthorized Ansible secret-delivery cases that are not fully
  represented by that range.

### Confirmed current gaps

| Area | Current behavior | Gap to close |
|---|---|---|
| Source of truth | The repo is canonical in practice, but Codex has copies in both `~/.agents/skills` and `~/.codex/skills` | Current discovery exposes duplicates and stale agent skills; installation drift is not checked |
| Packaging | `install-codex.sh` copies only each catalog skill's `SKILL.md` | New `references/`, `scripts/`, and `agents/openai.yaml` would be silently omitted |
| Adapter generation | Kimi installer embeds a second hard-coded team workflow | Workflow changes can diverge even when source skills are correct |
| Architecture | `sk-architect` says “follow existing patterns” and has no boundary matrix, vocabulary gate, module-growth forecast, or infrastructure non-goals | A behaviorally correct but wrongly layered design can pass planning |
| Implementation | `sk-developer` treats the project profile and nearest files as authority and begins from failing tests | Frequent legacy patterns can override the approved design before any boundary check |
| Convention extraction | The shared guide explicitly converts sampled frequency into rules, for example `0/14 → rule` | `Observed` becomes normative even without human or tooling authority |
| Review scope | The orchestrator's diff command omits important working-tree and untracked states | Standalone review can miss the exact files it claims to review |
| Review lenses | Architecture, abstraction, structure, and imports are mixed into one pass | A green security/test result can hide independent shape failures |
| Baseline findings | Full-repo analyzer output is not formally separated from change-caused findings | Old debt may either block incorrectly or obscure new regressions |
| Instruction review | `instruction-quality` self-skips unless the repo defines executable agent prompts | Changes to ordinary `AGENTS.md`, `CLAUDE.md`, `.agents/`, OpenSpec, or skills may escape instruction review |
| Learning loop | `sk-team-feature` ends after acceptance and archive | Escaped review signals are not converted into a deliberate repo/skill/no-promotion decision |

### Source-of-truth decision

1. The git repository is the sole editable source.
2. Catalog skills and internal agent resources are separate products of one
   manifest-driven build.
3. `~/.agents/skills` is the default Codex catalog target.
4. A legacy `~/.codex/skills` installation must be detected and migrated out of
   the discovery path; it must not be maintained as a second live copy.
5. `.system` and unrelated third-party skills are never touched.
6. Installed files are verified against a rendered manifest, including intentional
   platform path substitutions.

### Prevention map from the auth regression

| Historical failure | Planning gate | Developer gate | Review gate |
|---|---|---|---|
| Custom limiter in API | Boundary matrix + reuse research | Transport-only ownership check | Architecture/layer pass |
| Redis keys/JSON/TTL in service | One named persistence owner | Boundary ownership check | Architecture/layer pass |
| `LoginNonceService` | Business-vocabulary table | Names checked against use case | Architecture/layer pass |
| One-use aliases/constants/micro-files | Abstraction forecast | Justification inventory | Abstraction/navigation pass |
| Raw JWT dictionary | Trust-boundary model inventory | Typed boundary check | Contract/security + architecture passes |
| Unverified local import | Import plan with reproducible cycle | Fresh-process reproduction + regression test | Dedicated import-evidence pass |
| God module | Module-growth forecast | Before/after responsibility inventory | Dedicated structure pass |
| Ansible secret-delivery scope creep | Infrastructure authority + non-goals | No undeclared deployment path | Architecture/non-goal pass |
| Frequent legacy pattern promoted to rule | Evidence authority classification | Approved sources outrank samples | Stack/profile review |

### Key files identified

- `workflow/agents/sk-architect.md` — planning workflow and design output.
- `workflow/agents/sk-developer.md` — implementation workflow.
- `utilities/sk-explore-codestyle/SKILL.md` — standalone convention extraction.
- `shared/best-practices/project-conventions-guide.md` — canonical extraction
  logic also used by onboarding and developer.
- `workflow/agents/sk-review-orchestrator.md` — review scope, dispatch,
  aggregation, and verdict.
- `workflow/agents/review-steps/*.md` — independent review lenses.
- `utilities/sk-code-review/SKILL.md` — top-level standalone review entry point.
- `workflow/skills/sk-team-feature/SKILL.md` — feature lifecycle.
- `scripts/install-*.sh`, `scripts/uninstall.sh` — platform packaging and drift.
- `README.md`, `workflow/skills/sk-team-help/SKILL.md`,
  `workflow/skills/sk-team-status/SKILL.md`, `AGENTS.md` — public workflow map.

### Constraints

- Do not create a new monolithic skill.
- Keep `SKILL.md` and agent entry files focused on workflow and stop-gates.
- Put detailed checklists in one-level `references/` resources.
- Put repeatable evidence collection in scripts and test those scripts.
- Preserve Claude Code, Codex, Cursor, and Kimi compatibility.
- Never edit installed home-directory copies by hand.
- Do not let a retrospective automatically mutate global skills.
- Forward-tests must use fresh context and raw artifacts, not leaked expected answers.

## Implementation Plan (Phase 2)

### Changes overview

| File or directory | Action | Description |
|---|---|---|
| `skills-manifest.yaml` | Create | Declare catalog skills, internal agents/resources, platform targets, and owned paths |
| `scripts/build-install-tree.sh` | Create | Render a complete platform installation into a staging directory |
| `scripts/doctor-installation.sh` | Create | Detect duplicate names, stale copies, missing resources, and hash drift |
| `scripts/verify-installation.sh` | Create | Compare a rendered expected tree with an installed tree |
| `scripts/validate-skills.sh` | Create | Validate metadata, references, uniqueness, size budgets, and generated docs |
| `scripts/install-codex.sh` | Edit | Install complete skill directories and manifest-owned internal resources |
| `scripts/install-claude-code.sh` | Edit | Consume the same manifest and link every required resource |
| `scripts/install-kimi.sh` | Edit | Remove the duplicated hard-coded workflow and render from canonical sources |
| `scripts/uninstall.sh` | Edit | Remove only manifest-owned entries; support recoverable legacy migration |
| `shared/review-evidence/collect-change-evidence.sh` | Create | Collect diff, untracked, file-size, changed-hunk, and local-import evidence |
| `shared/best-practices/convention-evidence-model.md` | Create | Define Enforced/Approved/Observed/Legacy authority semantics |
| `shared/best-practices/project-conventions-guide.md` | Edit | Generate only authoritative coder/reviewer rules and separate evidence |
| `onboarding/sk-explore-codebase.md` | Edit | Use the shared authority model when generating project profiles |
| `onboarding/sk-onboard.md` | Edit | Report the new evidence artifact and profile confirmation gate |
| `workflow/agents/references/architecture-gates.md` | Create | Boundary, vocabulary, reuse, growth, trust-boundary, and non-goal templates |
| `workflow/agents/sk-architect.md` | Edit | Require the architecture gate before task breakdown |
| `workflow/agents/references/developer-prewrite-gate.md` | Create | Pre-write ownership, typing, reuse, abstraction, growth, and import checks |
| `workflow/agents/sk-developer.md` | Edit | Refuse implementation when required architecture decisions are incomplete |
| `utilities/sk-explore-codestyle/SKILL.md` | Edit | Produce authority-classified project conventions |
| `workflow/agents/review-steps/security.md` | Edit | Add contract/trust-boundary comparison inputs while retaining security depth |
| `workflow/agents/review-steps/architecture.md` | Edit | Focus on design, layer ownership, business vocabulary, reuse, and non-goals |
| `workflow/agents/review-steps/abstraction.md` | Create | Review one-use declarations, wrappers, aliases, and navigation cost |
| `workflow/agents/review-steps/structure.md` | Create | Review file growth, responsibility count, fragmentation, and placement |
| `workflow/agents/review-steps/imports.md` | Create | Require reproducible cycle evidence for local/dynamic imports |
| `workflow/agents/review-steps/instruction-quality.md` | Edit | Trigger from changed instruction artifacts, not only agent repos |
| `workflow/agents/references/review-tooling.md` | Create | Move detailed tool discovery/run instructions out of the orchestrator |
| `workflow/agents/references/review-verdict-policy.md` | Create | Centralize applicability, baseline classification, severity, and verdict rules |
| `workflow/agents/sk-review-orchestrator.md` | Edit | Use complete scope evidence and run every applicable lens |
| `utilities/sk-code-review/SKILL.md` | Edit | Invoke the updated top-level review and canonical convention profile |
| `shared/templates/retrospective.md` | Create | Short symptom/root-cause/escape/prevention/lesson-disposition template |
| `workflow/skills/sk-team-feature/references/phase-prompts.md` | Create | Move verbose dispatch prompts out of the core skill |
| `workflow/skills/sk-team-feature/SKILL.md` | Edit | Add the mandatory retrospective phase and keep the core workflow compact |
| `workflow/skills/sk-team-status/SKILL.md` | Edit | Recognize review, acceptance, retrospective, and archive states |
| `workflow/skills/sk-team-help/SKILL.md` | Edit | Document new gates and lesson disposition |
| `agents/openai.yaml` under changed catalog skills | Create | Add current Codex-facing display metadata and default prompts |
| `tests/` | Create | Structural, packaging, evidence-script, and prompt-contract tests |
| `evals/webapp-auth-shell/` | Create | Historical and targeted behavioral forward-test specifications |
| `README.md`, `AGENTS.md`, adapter READMEs | Edit/regenerate | Document the canonical source, installation model, and upgraded workflow |

### Detailed steps

#### 1. Establish deterministic packaging before splitting files

1. Add `skills-manifest.yaml` with explicit groups:
   - user-invocable catalog skills;
   - onboarding commands rendered as catalog skills;
   - internal workflow agents;
   - review lenses;
   - shared prompt references;
   - best-practice profiles;
   - static-analysis and review-evidence scripts.
2. Make `build-install-tree.sh` render a target-specific tree in a temporary
   directory before touching a real installation.
3. Copy complete catalog directories, not only `SKILL.md`, so `references/`,
   `scripts/`, and `agents/openai.yaml` survive installation.
4. Replace ad hoc path rewriting with one documented render step. Validate every
   rendered local reference exists.
5. Remove the large hard-coded Kimi system prompt. Generate a thin platform
   wrapper that points to the same canonical workflow and agent resources.
6. Write an installation receipt containing the source commit and hashes of
   manifest-owned files. Do not claim ownership of unrelated files.
7. Add a read-only doctor that reports:
   - duplicate skill names across scanned roots;
   - different hashes for the same skill;
   - legacy agent roles incorrectly exposed as catalog skills;
   - missing references/scripts;
   - installed content that differs from the rendered source.
8. Make legacy migration explicit and recoverable: move only manifest-owned
   `sk-*` entries from `~/.codex/skills` to a backup outside the discovery root.
   Preserve `~/.codex/skills/.system` and all unrelated entries.
9. Test every installer with a temporary `HOME`. Do not update the real global
   installation until repository tests and forward-tests pass.

**Acceptance gate:** a temp Codex install contains one catalog entry per
user-invocable skill, no internal agent catalog entries, all referenced resources,
and zero hash drift. The doctor fails on the current duplicate installation.

#### 2. Add one deterministic change-evidence collector

Create `shared/review-evidence/collect-change-evidence.sh` with:

- optional explicit base ref and a robust merge-base fallback;
- committed, staged, unstaged, deleted, renamed, and untracked file inventories;
- changed line intervals per tracked file;
- current and base line counts, with `>300` and newly-crossed thresholds;
- new files small enough to be micro-file candidates;
- language-aware local/dynamic import candidates;
- a stable machine-readable section plus a human-readable Markdown summary;
- NUL-safe path handling internally.

The script must label outputs as **review leads**, not automatic findings. A human
lens still decides responsibility, abstraction value, and whether a real cycle
exists.

Add temporary-repository tests covering first commit, shallow/no-upstream fallback,
staged + unstaged changes, untracked files, deletion/rename, spaces in paths,
threshold crossing, and Python/JS local imports.

**Acceptance gate:** the fixture's untracked API file, >300-line module, and local
import all appear exactly once in the evidence output.

#### 3. Introduce one convention authority model

Define four classifications in
`shared/best-practices/convention-evidence-model.md`:

- **Enforced:** proven by formatter, linter, type checker, test, or CI config.
- **Approved:** stated in current repository guidance, accepted ADR, or approved
  OpenSpec design.
- **Observed:** sample frequency only; useful evidence, never automatically
  normative.
- **Legacy/uncertain:** inconsistent, contradicted, deprecated, or unsupported by
  an authority.

Update the shared project convention generator so each item has a stable ID,
classification, source path, evidence count, and confidence.

Generate three project artifacts:

1. `coder.md` — only Enforced and Approved instructions.
2. `reviewer.md` — checks derived from the same normative IDs.
3. `evidence.md` — Observed and Legacy/uncertain patterns plus questions needing
   human promotion or rejection.

Never promote dependency aliases, local imports, wrappers, helpers, constants, or
micro-files solely from sample frequency. Human approval moves an item from
Observed to Approved.

Make `.agents/best-practices/project/` the canonical cross-platform output of
`sk-explore-codestyle`. A Claude-specific `code-style.md`, when needed, becomes a
short pointer instead of a second rules database. Update onboarding, developer,
review, README, and help text to consume the same artifacts.

**Acceptance gate:** a `12/12 private constants` sample is emitted as Observed or
Legacy/uncertain and does not appear as a coder instruction without an approved or
enforced source.

#### 4. Add the architect decision-completeness gate

Keep the core workflow in `sk-architect.md`; move detailed tables and examples to
`workflow/agents/references/architecture-gates.md`.

Before task breakdown, require these design outputs:

1. **Authority inventory:** accepted specs/ADRs and repo guidance outrank tooling;
   tooling outranks raw code samples. A repeated implementation is evidence, not
   authority.
2. **Boundary matrix:** concern, input/trust boundary, owning layer/component,
   typed boundary model, persistence owner, and explicitly forbidden layers.
3. **Business-vocabulary check:** use-case/API/service names describe user or
   business capabilities; storage/algorithm nouns stay in repository or
   infrastructure names unless the domain itself uses them.
4. **Reuse research:** before custom cross-cutting infrastructure, inspect the
   project's existing integration, official library documentation, and supplied
   reference projects. Record why reuse is accepted or rejected.
5. **Module-growth forecast:** current line count, added responsibility, expected
   post-change shape, and split-or-keep decision for every materially touched file.
6. **Trust-boundary types:** external HTTP/JWT/Redis/settings/provider payloads
   become explicit validated types before business policy consumes them.
7. **Infrastructure authority and non-goals:** deployment, secret delivery,
   runtime ownership, and deliberately deferred scope are explicit.
8. **Abstraction budget:** list planned new wrappers/aliases/helpers/files with
   consumers and independently testable value.

If a persistence detail, framework integration, configuration validation rule, or
trust-boundary payload lacks exactly one owner, return `## NEEDS USER INPUT` or
request planning rework. Do not create tasks for an incomplete design.

Add the matrix, growth forecast, reuse decisions, and non-goals to `design.md` and
the handoff digest. Make implementation tasks reference their owning boundary.

**Acceptance gate:** the historical auth proposal cannot reach task breakdown with
rate limiting in the API, Redis serialization in the service, or unnamed
secret-delivery ownership.

#### 5. Add the developer pre-write architecture gate

Move the detailed checklist to
`workflow/agents/references/developer-prewrite-gate.md`; keep the stop condition in
`sk-developer.md`.

Before editing code:

1. Load the approved boundary matrix, non-goals, and normative convention IDs.
2. Run change evidence and record pre-change file sizes/responsibilities.
3. Map each planned edit to transport, use-case policy, persistence,
   framework/infrastructure, or configuration ownership.
4. Search for an existing project/library/reference integration before writing a
   custom cross-cutting wrapper.
5. Inventory every planned one-use alias/helper/constant/wrapper/file and retain it
   only when it isolates substantial independently testable behavior.
6. Ensure untrusted/serialized boundary data has a precise validated shape.
7. Reject local imports unless a clean-process import sequence reproduces the
   exact cycle; require a comment naming it and an import regression test.
8. Re-run file-size/responsibility evidence after implementation and report
   threshold crossings or second responsibilities.

Change the authority statement from “nearest files are your authority” to:

```text
approved spec/ADR and repository guidance
  > enforced tooling
  > approved project profile
  > observed neighboring code
```

When these conflict materially, stop and request clarification instead of copying
the common pattern. Constrain “minimum code to pass tests” by the approved design,
security, and boundary rules; tests are not permission to violate them.

Add the pre-write decisions, new-abstraction inventory, import evidence, and
before/after structure evidence to the developer handoff.

**Acceptance gate:** when given the historical weak auth design, the developer
stops or corrects the boundary before writing a custom limiter/service rather than
making the existing tests green around it.

#### 6. Decompose review into mandatory independent lenses

Refactor `sk-review-orchestrator.md` to contain only:

1. scope collection;
2. profile/resource resolution;
3. static analysis;
4. applicable-lens dispatch;
5. aggregation and verdict.

Move the tool catalog and verdict details into one-level references. Use seven
lenses:

1. **Contract/security** — public contract, trust boundaries, auth/security, typed
   external payloads.
2. **Architecture/layers** — owner matrix, design compliance, business vocabulary,
   reuse decisions, infrastructure non-goals.
3. **Abstraction/navigation** — one-use declarations, trivial wrappers, aliases,
   micro-files, utility dumping, indirection cost.
4. **Structure** — file growth, responsibility count, fragmentation, placement,
   and module/package cohesion.
5. **Imports** — all local/dynamic imports, clean-process reproduction, exact cycle,
   and regression coverage.
6. **Stack rules** — resolved normative reviewer profile and language/framework
   idioms.
7. **Instruction quality** — changed `AGENTS.md`, `CLAUDE.md`, `.agents/**`,
   `openspec/**`, `SKILL.md`, agent prompts, or workflow references.

Run lenses in parallel waves according to available concurrency; no applicable
lens may disappear because fan-out is unavailable. Nested execution uses disclosed
inline passes.

The instruction-quality lens is applicable from the changed-path inventory, even
in an ordinary application repository. If no instruction artifact changed, it may
return a documented N/A without blocking approval.

Classify findings:

- **Change-caused:** introduced, modified, or materially worsened by this diff;
  affects the feature verdict.
- **Touched structural regression:** a pre-existing issue made worse or relied on
  by the change; affects the verdict with explicit evidence.
- **Baseline/out-of-scope:** unchanged line/file and not worsened; reported in a
  separate section and does not determine the feature verdict.

For file-level metrics, compare base and current values. Crossing or worsening a
threshold is change-caused; an unchanged existing violation is baseline.

`APPROVED` requires:

- every applicable lens ran and returned a valid result;
- no change-caused BLOCKER or MAJOR remains;
- the static-analysis provenance table is complete;
- no required dimension is UNVERIFIED;
- untracked files were included;
- baseline findings are visible but do not mask the feature decision.

Update `sk-code-review` to use the canonical `.agents` project profile, the complete
scope collector, the seven-lens list, and the same verdict policy.

**Acceptance gate:** the bad auth diff receives `CHANGES REQUESTED` with independent
findings for API infrastructure leakage, Redis ownership, mechanism naming,
one-use navigation cost, raw JWT data, and any unverified local import.

#### 7. Add a mandatory short retrospective to `sk-team-feature`

After final review and acceptance, but before archive, add a required retrospective
phase using `shared/templates/retrospective.md`.

The artifact is `openspec/changes/<feature>/RETROSPECTIVE.md` with:

- outcome versus approved design;
- escaped or late review signals;
- symptom → root cause → why the earlier gate missed it → prevention;
- verification gaps and baseline debt;
- one explicit lesson disposition per durable lesson:
  - repository guide;
  - a named existing skill;
  - no promotion.

The retrospective records proposed skill changes but never edits global skills.
Promotion to a global skill requires cross-project value or a reproducible
regression case; project-specific rules stay in the repository guide.

Make this a normal approval gate before archive. Update status detection, help,
artifact lists, and README. Keep quick fixes lightweight; do not add the mandatory
phase to `sk-team-quick` unless a future retrospective shows repeated quick-fix
escapes.

Move verbose phase dispatch prompts from `sk-team-feature/SKILL.md` into
`references/phase-prompts.md`. Target a compact core skill containing lifecycle,
stop-gates, routing, and state transitions.

**Acceptance gate:** a completed feature cannot be archived without a retrospective
and a repo-guide/specific-skill/no-promotion decision.

#### 8. Add structural and packaging validation

Add tests that run without modifying real home directories:

- frontmatter/name uniqueness and catalog-vs-internal classification;
- every referenced file exists in source and every rendered platform tree;
- catalog skill resources are copied recursively;
- `bash -n` for every shell script and `shellcheck` when available;
- generated `AGENTS.md` matches the source inventory;
- no core `SKILL.md` exceeds 500 lines; oversized agent prompts have an explicit
  split plan and stay within the chosen budget;
- temp-HOME install/uninstall/reinstall idempotency for Codex, Claude, and Kimi;
- duplicate legacy installation is detected;
- `.system` and an unrelated dummy skill survive migration/uninstall;
- exact expected review lens inventory and retrospective state transition.

Generate or refresh `agents/openai.yaml` for changed catalog skills from their
actual descriptions and prompts, and validate it stays in sync.

#### 9. Build the auth forward-test suite

Create `evals/webapp-auth-shell/eval.yaml` with immutable source/base/head SHAs,
neutral user-like prompts, expected artifact types, and a scorer rubric. Do not put
the expected diagnoses in the prompts.

Use isolated temporary repositories:

1. Archive `ee6100b` as the base.
2. Initialize it as a clean local git repository.
3. Apply `ee6100b..5aa47ea` as an uncommitted working-tree diff so untracked-file
   review is exercised.
4. Never run the eval in the dirty live backend worktree.
5. Store agent outputs outside the fixture so later agents cannot discover prior
   answers.

Add targeted cases:

- `auth-bad-diff` — historical custom limiter, Redis service, mechanism naming,
  raw JWT dictionary, and one-use abstractions;
- `local-import-claim` — a local import justified by a comment but no real cycle;
- `deployment-scope-creep` — application auth work adding an Ansible/env secret
  delivery path without infrastructure authority;
- `codestyle-frequency-trap` — many files repeat a legacy pattern contradicted by
  approved guidance;
- `review-scope-baseline` — untracked changed issues plus unrelated analyzer debt.

Run fresh-context forward-tests for:

- `sk-architect` — design must contain complete owners and non-goals;
- `sk-developer` — pre-write gate must stop/correct the weak design;
- `sk-explore-codestyle` — frequency must remain Observed/Legacy;
- `sk-code-review` — all applicable lenses and baseline separation must work;
- `sk-team-feature` — retrospective and lesson disposition must be produced.

Record a before/after score. Required behavioral assertions:

1. Custom limiter in API detected.
2. Redis serialization/TTL/transactions in service detected.
3. `LoginNonceService` rejected as mechanism vocabulary.
4. One-use aliases/constants/wrappers/micro-files inventoried.
5. Raw JWT dictionary rejected at a trust boundary.
6. Circular import claim rejected without fresh-process reproduction.
7. Unauthorized Ansible secret-delivery path rejected as scope expansion.
8. Untracked files included.
9. Baseline findings separated.
10. No verdict is `APPROVED` while a required assertion is missing.

Retain existing security, stack-rule, test, and static-analysis coverage as
non-regression requirements. A longer prompt that merely repeats the rubric is not
a pass; the fresh agent must find the issues from raw artifacts.

#### 10. Roll out in controlled stages

1. Run repository validation and temp-HOME installation tests.
2. Run the behavioral eval baseline with current skills.
3. Implement and iterate on the skills.
4. Run the same eval suite in fresh sessions until all required assertions pass.
5. Render and verify Codex, Claude, and Kimi target trees.
6. Review the final repo diff with the upgraded review pipeline.
7. Only then install to the real configured target.
8. Run the doctor and explicitly migrate stale manifest-owned
   `~/.codex/skills/sk-*` entries to a recoverable backup.
9. Restart the client and verify actual discovery:
   - no duplicate `sk-*` names;
   - internal roles are not catalog skills;
   - changed catalog skills load their references and scripts;
   - installation receipt hashes match the source commit.

## Verification matrix

| Layer | Command or check | Expected result |
|---|---|---|
| Shell syntax | `bash -n scripts/*.sh shared/**/*.sh` | No syntax errors |
| Skill schema | `scripts/validate-skills.sh` | Unique names, valid metadata, all references present |
| Generated docs | generate `AGENTS.md`, then `git diff --exit-code -- AGENTS.md` | No stale generated content |
| Packaging | temp-HOME install for each adapter | Full resources present; unrelated files preserved |
| Installation drift | `scripts/doctor-installation.sh` | Fails before legacy migration; clean afterward |
| Evidence collector | `tests/test-collect-change-evidence.sh` | Diff/untracked/size/import fixtures all pass |
| Prompt contracts | `tests/test-workflow-contracts.sh` | Required stop-gates and lens inventory present |
| Historical eval | fresh auth suite | All ten behavioral assertions pass |
| Review regression | run upgraded `sk-code-review` on its own diff | No required lens missing; zero UNVERIFIED gates |
| Repository hygiene | `git diff --check` and `git status --short` | No whitespace errors; only intended files changed |

## Risk Assessment (Phase 3)

| Risk | Level | Mitigation |
|---|---|---|
| Prompt bloat from more rules | High | Keep entry files to workflow/stop-gates; load one-level references conditionally; enforce line budgets |
| Seven review lenses increase latency | Medium | Dispatch in concurrency-aware waves and use deterministic evidence once for all lenses |
| New gates over-block ordinary small work | Medium | Apply reuse research only to custom cross-cutting infrastructure; use explicit N/A rules; keep `sk-team-quick` lightweight |
| Heuristic script creates false findings | Medium | Script emits evidence/leads only; human lenses assign ownership and severity |
| Existing project code is mislabeled Legacy | Medium | Require source path, evidence count, confidence, and human promotion to Approved |
| Platform adapters diverge | High | One manifest, one rendered install tree, temp-HOME tests, installation receipts |
| Legacy cleanup removes user data | High | Operate only on manifest-owned `sk-*`; preserve `.system` and unrelated entries; move to recoverable backup |
| Historical eval leaks the retrospective | High | Use historical commits/targeted raw fixtures, neutral prompts, fresh sessions, and isolated output directories |
| Dirty deli-check worktree contaminates eval | High | Build temp repos from immutable commit archives; never reuse the live worktree |
| Baseline findings hide regressions | Medium | Compare base/current locations and metrics; render separate change-caused and baseline sections |
| Refactoring review prompts loses existing security depth | High | Keep the current security/stack/static checks as explicit non-regression assertions |
| Real discovery behavior differs from adapter assumptions | Medium | Verify discovery after restart; doctor reports actual duplicate names rather than trusting README claims |

## Definition of done

- The repository is the documented and mechanically verified source of truth.
- No live duplicate `sk-*` installation remains in discovered Codex roots.
- Modified catalog skills retain all references/scripts after installation.
- Architect and developer stop before wrong layer ownership is implemented.
- Generated conventions distinguish authority from frequency.
- Review includes complete worktree/untracked scope and independent architecture,
  abstraction, structure, and import findings.
- Baseline debt is visible but does not distort the feature verdict.
- Full feature workflow produces a retrospective and lesson disposition.
- The historical auth regression suite catches every required failure without
  receiving the expected answer in its prompt.
- Existing security, test, stack, and static-analysis behavior does not regress.

## Implementation record (2026-07-24)

- The planned single `build-install-tree.sh` was implemented as cohesive Python
  modules: `skills_render.py` (staging render), `skills_installation.py`
  (receipt-owned apply/verify/uninstall), `skills_validation.py`, and the thin
  `skills_tool.py` CLI.
- A fresh self-review initially rejected the implementation for broad directory
  deletion, incomplete receipts, missing rename coverage, and a 696-line
  packaging monolith. Rollout was paused and those findings were corrected before
  any home-directory mutation.
- Recorded fresh-context behavioral evaluation improved from `2/10` to `10/10`;
  the result and evidence are in
  `evals/webapp-auth-shell/results/2026-07-24.json`.
- Repository validation, generated-doc checks, evidence tests, prompt contracts,
  eval scoring, and temp Codex/Claude/Kimi install/reinstall/uninstall tests pass.
- On 2026-07-27 the manifest-owned trees were installed for Codex, Claude Code,
  and Kimi. The previous Codex catalog was moved, without deletion, to
  `~/.codex/backups/sk-skills-legacy-20260727`.
- Post-install receipt verification and the duplicate-installation doctor pass.
  `~/.codex/skills` now contains only the platform-owned `.system`
  directory.

## Post-audit remediation (2026-07-28)

- Platform docs and generated inventories now describe current Codex, Claude
  Code, Cursor, and Kimi invocation/discovery contracts. Cursor has a native
  manifest-owned skill installer plus a generated `.cursor/rules/` catalog;
  `.cursorrules` remains explicitly legacy.
- Manifest validation now rejects malformed shapes and path escapes, checks that
  every installable prompt is declared, renders all four platform trees, and
  verifies local Markdown reference closure.
- Installation preflights reject unowned leaf collisions, replacement uses
  atomic sibling files with rollback, multi-target uninstall preflights every
  typed/versioned receipt with its explicitly paired platform before mutation.
  Legacy migration uses an exclusively created same-filesystem backup root,
  descriptor-relative renames, and rollback while refusing source and backup
  parent-symlink escapes. Descriptor-relative candidate typing accepts only
  regular/symlink resource leaves and real skill directories with a regular
  `SKILL.md`.
- Receipt parsing now requires a regular non-symlink file, stable suite identity,
  exact platform/manifest compatibility, canonical safe ownership keys, and
  valid hash/symlink values before any ownership decision; reads are capped at
  4 MiB.
- Render staging rejects top-level and nested source symlinks before creating
  output, and Kimi prompt assembly uses the same bounded no-follow reader.
  Review change evidence traverses held no-follow directory descriptors, caps
  current/base reads at 4 MiB, gates base blobs with `git cat-file -s`, skips
  per-file diffing when either side is oversized, and enforces a 20 MiB streamed
  diff-output cap. JSON and Markdown both expose incomplete read/interval status.
  It records symlink metadata without reading a leaf or ancestor symlink target.
- Shared manifest-rendered prompts use host-neutral skill names and are rendered
  under Codex, Cursor, Claude Code, and Kimi contract tests. `sk-copy-context`
  copies a tool-written file through `pbcopy`, `wl-copy`, `xclip`, or PowerShell;
  arbitrary context is never shell source and success requires backend exit 0.
- `manifest_inventory.py` is the single catalog/description formatter used by
  `AGENTS.md`, legacy Cursor rules, and current Cursor Project Rules. Intentional
  copies of the runtime handoff protocol are narrowly excluded from duplication
  analysis; other generator/template duplication was removed.
- The context handoff template now ships inside `sk-copy-context/references/`, so
  the skill and its required reference install together on every platform.
- Repository tests, strict complexity checks, diff whitespace checks, and the
  full static-analysis battery pass. This remediation did not mutate user-level
  installations; rerun the relevant installer before treating the 2026-07-27
  live copies as current.

## Checklist

- [x] Phase 1: Understanding complete
- [x] Phase 2: Design complete
- [x] Phase 3: Review complete
- [x] Phase 4: Final plan written
- [x] Ready for approval
- [x] Implementation and behavioral forward-tests complete
- [x] Real Codex/Claude/Kimi rollout verified
- [x] Post-audit source remediation verified
- [ ] Reinstall live targets from the remediated source

## Status: 🟡 SOURCE VERIFIED — LIVE REINSTALL PENDING
