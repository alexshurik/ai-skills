# Tasks: scenario workflow and durable decision evidence

Status: source implementation, engineering checks and six independent behavioral cases complete; independent code review and acceptance pending.
Evidence: [implementation.md](implementation.md), [EVALUATION.md](EVALUATION.md).
Design: [design.md](./design.md).
Scope: [proposal.md](./proposal.md), R-1–R-5. Approved additions: None.

These are outcome milestones. The existing Testing, Implementation, Code Review,
and Acceptance phases remain in force. A single normal full review may cover all
four milestone review items. Checking a development item does not accept its
milestone before the associated testing and review evidence exists.

## M1 — A user receives a complete, project-native scenario plan

Acceptance: AC-1 and AC-2. Each outcome has criteria, design/development/testing/
review work, ownership, dependencies, and evidence. Plans preserve atomic boundaries
and the project's architecture. A coherent task is not split merely at five files.
Dependencies: approved design only.

- [x] M1-D — Confirm the shared scenario and milestone contracts against the design.
  Owner: Architect/planning. Files: `workflow/agents/references/architecture-gates.md`,
  `shared/templates/tasks.md`, `shared/templates/design.md`.
  Result: one scenario schema and one milestone output shape; existing boundary and
  state tables retain their separate responsibilities. AC-1/AC-2.
- [x] M1-I — Implement the contracts and narrow caller changes.
  Owner: workflow/discovery instructions. Files: the three above;
  `workflow/agents/sk-architect.md`; `onboarding/sk-discover-project.md`;
  `onboarding/sk-explore-codebase.md`; `workflow/skills/sk-team-feature/SKILL.md`;
  `workflow/agents/sk-doc-reviewer.md`.
  Result: discovery supplies evidence, Architect makes approved decisions, the task
  template groups complete outcomes, and phase/risk routing stays intact. Replace
  the 3–5-file/mandatory-duration heuristic; do not add a new workflow runtime.
  Keep discovery under its existing prompt budget. Depends on M1-D. AC-1/AC-2.
- [x] M1-T — Prepare and run scenario-planning forward cases plus packaging checks.
  Owner: evaluator/testing. Files: `evals/scenario-workflow/cases.json`,
  `evals/scenario-workflow/goldens.json`, `evals/scenario-workflow/README.md`,
  `tests/test-scenario-workflow-eval.py`, `tests/run.sh`.
  Result: shared corpus support plus layered/atomic and small-fix cases. Test corpus
  integrity separately from actual fresh-context generated design/tasks. Withhold
  goldens and judge outcome completion, dependency/transaction preservation, and
  absence of universal VSA or new full-review loops. Depends on M1-I. AC-1/AC-2.
- [ ] M1-R — Review actual plans and instruction flow.
  Owner: architecture-design and correctness-safety review.
  Evidence: evaluator artifacts and platform-render/reference checks. Verify each
  milestone's AC→design→development→test→review trace and unchanged workflow phases.
  Required result: no contradictory owner or missing criterion. Depends on M1-T.

## M2 — Architectural decisions stay discoverable after archive

Acceptance: AC-3. Use the existing permanent ADR directory/index. Keep old records
and their bodies. Preserve navigation after archiving a change.
Dependencies: none on M1 implementation; coordinate the shared Architect/design
template edits in one source checkout.

- [x] M2-D — Confirm the ADR destination and link lifecycle.
  Owner: artifact policy. File: `workflow/agents/shared/scope-governance.md` §6.
  Result: one policy for project-native resolution, fallback only when needed,
  legacy references, index navigation, supersession, and archive checks. AC-3.
- [x] M2-I — Apply the lifecycle through existing callers and documentation.
  Owner: planning/onboarding/archive. Files: scope-governance above;
  `workflow/agents/sk-architect.md`; `onboarding/sk-onboard.md`;
  `shared/templates/design.md`; `workflow/skills/sk-team-feature/SKILL.md`;
  `workflow/skills/sk-team-quick/SKILL.md`; `workflow/skills/sk-team-help/SKILL.md`;
  `README.md`.
  Result: stop defaulting new ADRs to a moving change folder. Record resolved owner
  once and link it. Full/Quick archive steps repair and verify only affected
  navigation. Public artifact lists distinguish permanent ADRs from legacy entries.
  Depends on M2-D. AC-3.
- [x] M2-T — Exercise permanent, legacy, and missing-owner cases.
  Owner: evaluator/testing. Files: the shared `evals/scenario-workflow/` corpus.
  Result: evaluator creates/archives sample artifacts in a temporary repository;
  compare legacy body hashes and IDs, resolve affected Markdown links after move,
  count one body per decision, and repeat resolution without duplicate navigation.
  Test existing `docs/decisions` as a non-default owner and fallback `docs/adr` when
  a significant new decision actually needs it. Depends on M2-I. AC-3.
- [ ] M2-R — Review ownership, archive compatibility, and preserved records.
  Owner: architecture-design and engineering-quality review.
  Evidence: actual before/after tree, links, hashes, and source caller audit. Verify
  accepted ADR text was not rewritten or copied and unrelated docs were untouched.
  Depends on M2-T. AC-3.

## M3 — A user can tell which rules are approved and which checks actually block

Acceptance: AC-4. Authority, checker availability, execution, CI invocation, merge
blocking, manual gaps, and freshness remain separately evidenced.
Dependencies: none; coordinate architecture-gates edit with M1.

- [x] M3-D — Confirm the two-part rule record and compatibility boundary.
  Owner: convention evidence. File:
  `shared/best-practices/convention-evidence-model.md`.
  Result: existing IDs/classes remain; mechanical authority does not imply a merge
  gate. Authority and enforcement each retain their own sources. AC-4.
- [x] M3-I — Implement evidence fields and tighten collection instructions.
  Owner: profile generation. Files: evidence model above;
  `shared/best-practices/project-conventions-guide.md`;
  `utilities/sk-explore-codestyle/SKILL.md`;
  `workflow/agents/references/architecture-gates.md` authority inventory.
  Result: output templates collect exact command/scope/invocation, verified blocking
  behavior or unknown, freshness, and manual gaps. They link to one field contract.
  No target-project checks are installed. Depends on M3-D. AC-4.
- [x] M3-T — Evaluate positive and negative enforcement evidence.
  Owner: evaluator/testing. Files: shared `evals/scenario-workflow/` corpus.
  Result: actual profiles distinguish Approved/manual, available-but-unused,
  optional CI, verified blocking, unknown remote required-check policy, and stale
  receipts. Ensure coder/reviewer stable IDs match and Observed evidence remains
  non-normative. Depends on M3-I. AC-4.
- [ ] M3-R — Review evidence claims against raw configuration and receipts.
  Owner: engineering-quality with architecture-design for authority conflicts.
  Evidence: generated profiles and cited inputs. Reject invented blocking status,
  freshness, commands, or authority promotion. Depends on M3-T. AC-4.

## M4 — Static analysis reports real findings without false failures or suppression

Acceptance: AC-5a and AC-5b. Clean Lizard reports pass; actual warnings survive;
failed or unrecognized evidence remains UNVERIFIED. Bandit review depends on source
context while raw findings and required fixes remain visible.
Dependencies: none on the instruction milestones.

- [x] M4-D — Confirm Lizard semantic states and Bandit disposition boundaries.
  Owner: analyzer interpretation and Python security guidance. Files:
  `shared/static-analysis/run-static-analysis.sh`;
  `shared/best-practices/languages/python/reviewer.md`.
  Result: design decision table, preserved runner/status interface, no broad
  suppression or approval-gate schema change. AC-5a/AC-5b.
- [x] M4-T1 — Add failing regressions before the parser change.
  Owner: regression testing. Files: `tests/test-static-analysis-artifacts.sh`;
  `tests/fixtures/static-analysis/lizard-clean.txt`, `lizard-findings.txt`,
  `lizard-failure.txt`; `tests/test-review-approval-gate.py`.
  Result: normalized real Lizard 1.21.2 output proves the current clean false finding.
  Test exit 0 clean, exit 1 findings, findings with forced exit 0, exit 2 failure,
  timeout/error precedence, and inconsistent/unrecognized output. Compare logged
  and in-memory classifications; preserve complete logs and non-Lizard controls.
  Verify unchanged consumer behavior: OK needs no disposition; FINDINGS requires
  one; UNVERIFIED cannot approve. Depends on M4-D. AC-5a.
- [x] M4-I — Implement the narrow parser and contextual Bandit guidance.
  Owner: runner and Python profile. Files: the two M4-D owners plus
  `workflow/agents/references/review-tooling.md` semantic-output clarification.
  Result: semantic Lizard helper with failure precedence and no threshold-text
  false positive. Replace direct Bandit severity mapping with contextual assessment
  tied to existing correctness-safety/scope policy. Preserve raw issues and all
  existing approval obligations. Depends on M4-T1. AC-5a/AC-5b.
- [x] M4-T2 — Pass regressions and run security-context forward cases.
  Owner: regression testing and fresh evaluator. Files: M4-T1 tests plus shared
  `evals/scenario-workflow/` corpus.
  Result: scanner tests green; evaluator differentiates non-secret randomness from
  secret generation and trusted fixed subprocess arguments from untrusted shell
  input. Missing context remains investigation. No blanket exclusions or `nosec`.
  Depends on M4-I. AC-5a/AC-5b.
- [ ] M4-R — Review failure semantics and contextual security judgments.
  Owner: engineering-quality and correctness-safety review.
  Evidence: raw fixture outputs, statuses, actual evaluator reasoning, unchanged
  provenance consumer interface. Do not treat test/fixture presence as acceptance.
  Depends on M4-T2. AC-5a/AC-5b.

## Shared finish checks

These close all four outcomes; they do not replace milestone testing or review.

- [x] F-1 — Run affected tests during development, then `bash tests/run.sh` once
  against the final implementation. It includes existing generated-file checks,
  pinned Python tooling, renderer/reference closure, workflow contracts, and
  isolated installer tests. Refresh only stale/affected evidence after changes.
- [x] F-2 — Inspect source diff and rendered-platform outputs. Regenerate managed
  files only through their existing scripts if maintained generator inputs changed.
  Verify C-1–C-3, prompt budgets, no global installation, and no runtime-schema delta.
- [ ] F-3 — Complete the normal independent review and acceptance against the
  current source fingerprint. Record each AC's evidence and any unavailable check.
  Parent owns runtime receipts, the `skills-design.md` pointer, archive, and selected
  MR finish. No merge or deployment is authorized.

Task dependency summary: M1, M2, M3, and M4 can progress by owner, but shared-file
edits are coordinated rather than concurrent writes. All milestone T/R items and
F-1/F-2 precede F-3. Root controls any future delegation; this planning task has none.
