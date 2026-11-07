# Design: scenario workflow and durable decision evidence

Status: ready for implementation within the already approved approach.
Date: 2026-11-06.
Base: `8a096e0ca6f3c9a386d0058391f60478f8ae6f01`.
Scope: [R-1–R-5, AC-1–AC-5, and C-1–C-4](./proposal.md).
Scope Delta: **None**.

## Design decisions

Extend existing owners. Keep substantial policy in one place and replace conflicting
caller instructions with short links. Templates describe output shape; callers do
not repeat the full policy. No new shared instruction document is necessary.

```text
discovery + Architect -> architecture-gates -> scenario facts and boundaries
Architect -> tasks template -> outcome milestones and criterion-linked work
Architect + onboarding + archive -> scope-governance -> permanent ADR lifecycle
codestyle/profile generation -> convention-evidence-model -> authority + enforcement
static runner -> unchanged provenance table -> quality/security review -> review gate
```

## Source findings and ownership

All paths below are repository-relative. They identify maintained sources, not
installed copies. Consumers already receiving these references need no new policy
copy.

| Concern | Canonical source and confirmed gap | Necessary callers/output surfaces |
|---|---|---|
| Scenario contract | `workflow/agents/references/architecture-gates.md`: boundary and state tables exist, but no end-to-end scenario record | `workflow/agents/sk-architect.md`; `onboarding/sk-discover-project.md`; `onboarding/sk-explore-codebase.md`; `shared/templates/design.md` |
| Outcome task shape | `shared/templates/tasks.md`: horizontal Foundation/Core/Integration/Testing phases; `sk-architect.md` §7 prescribes 15–60 minutes and roughly 3–5 files | `workflow/skills/sk-team-feature/SKILL.md` Planning/Testing/Implementation; a short criterion-traceability check in `workflow/agents/sk-doc-reviewer.md` |
| ADR lifecycle | `workflow/agents/shared/scope-governance.md` §6: required `adr/` entries travel with the change; Architect §6 hardcodes change-local ADRs | Architect; `onboarding/sk-onboard.md` destination planning; Full and Quick archive callers; `shared/templates/design.md`; existing README/help artifact listings |
| Authority vs enforcement | `shared/best-practices/convention-evidence-model.md`: current four authority classes; `project-conventions-guide.md` repeats a smaller rule record | `shared/best-practices/project-conventions-guide.md`; `utilities/sk-explore-codestyle/SKILL.md`; the architecture gate's authority inventory |
| Lizard interpretation | `shared/static-analysis/run-static-analysis.sh`: `_tool_reports_findings` matches any `cyclomatic_complexity >`; `run_tool` treats most nonzero exits as findings | Existing `review-tooling.md` semantic-output paragraph; unchanged `shared/review-evidence/review_gate.py` consumer |
| Bandit classification | `shared/best-practices/languages/python/reviewer.md`: severity table maps high/medium/low directly to BLOCKER/MAJOR/MINOR | Existing correctness-safety context rules and engineering-quality provenance handling; no duplicated generic security policy |

`skills-manifest.yaml` already renders the complete reference, shared-policy,
template, best-practice, and static-analysis directories. No inventory addition is
needed for edits in those owners. New non-installed test fixtures stay under
`tests/` or `evals/`.

## 1. Plans describe complete outcomes

The tasks template becomes a repeatable milestone shape, not a fixed number or a
mandatory phase ladder. Each milestone contains:

- outcome and user acceptance criterion IDs;
- applicable scenario IDs and primary responsible owner;
- dependencies and public-contract/transaction constraints;
- design/contract work or a link to its completed decision;
- development work with exact candidate files and a verifiable result;
- testing work at the lowest faithful layer and expected evidence;
- review work with the applicable owner, scope, and completion evidence.

Tasks remain independently trackable and cite AC or approved SD IDs. Testing and
review are not relegated to a final “polish” milestone. Shared groundwork is an
explicit dependency of the first outcome that needs it; do not invent a user outcome
for an isolated mechanical prerequisite.

Split when responsibilities, acceptance boundaries, risk, or dependency order make
work independently verifiable. File counts and duration estimates are planning
signals only. A cohesive operation may span more than five files. A small change
may have one milestone and no table beyond what makes its boundary clear.

The workflow's Discovery, Planning, Testing, Implementation, Code Review,
Acceptance, Retrospective, and Archive phases remain intact. Milestones organize
the approved task graph within those phases; they are not new runtime stages.
Testing still chooses independent Tester versus Developer Red→Green by existing
risk rules. The normal full Code Review can satisfy the review work of multiple
milestones by explicit coverage. Do not require a new full review or user gate for
each milestone. An implemented milestone is not accepted until its required tests
and review dispositions are complete.

## 2. Discovery connects scenarios to owners and invariants

Add the canonical scenario record beside the existing boundary/state gates. Its
fields are:

| Field | Required meaning |
|---|---|
| Scenario ID / operation / actor | Meaningful action in the requested scope, not a directory name |
| Entry and input | UI/HTTP/event/job/CLI entry; input contract and validation/trust owner |
| Primary owner | Existing or approved responsibility owner; evidence or explicit unknown |
| Public dependencies | Provider owner, allowed contract, dependency direction; identify incidental internal coupling |
| State and transaction | State/source of truth, atomic operation or coordination scope, lifecycle/retry owner where applicable |
| Result and acceptance | Observable success/failure result, criterion IDs, faithful verification route |
| Evidence | Source paths; distinguish discovered facts, approved decisions, inferences, and gaps |

Discovery records the current system. Design chooses changes only within approved
scope. Existing source can reveal a dependency without authorizing that dependency.
Read the scenario/boundary subsection from discovery; do not load all architecture
gates merely to make a quick map. Reuse the resolved project map/navigation owner
and known facts rather than create a second scenario document.

For durable or concurrent behavior, reuse the existing invariant table rather than
repeat its details in each scenario. Link scenarios to that row. Do not replace an
atomic operation with asynchronous messaging merely to remove an import. Shared
contracts and composition wiring are valid when approved. Pure local operations
can record state/transaction as N/A with a short reason. A layered, functional,
framework-native, or VSA project uses its own owners and vocabulary.

The design template gets compact scenario and dependency slots that point to this
contract. Existing boundary, trust-model, mechanism, and state tables remain their
owners. Architect §2/§3 and full output checks reference the record. Discovery's
current domain/route/service coverage is tightened rather than appended wholesale.
`sk-discover-project.md` is already 491 lines against a 500-line catalog limit;
replace redundant example material and link the shared contract.

## 3. ADRs retain one permanent owner and usable archive navigation

The canonical lifecycle belongs in scope-governance §6 because that section already
owns durable artifacts and archival. Resolve an explicit user destination first,
then the project's existing permanent ADR/decision directory and index. Common
examples are `docs/adr` and `docs/decisions`; names are not mandates. A per-change
OpenSpec directory is historical context, not the default permanent owner. If no
permanent owner exists and a significant decision actually requires an ADR, use
`docs/adr/` with one concise index. Do not create empty ADR scaffolding otherwise.

Record the resolved directory/index in the design's structural digest. Architect
writes new ADRs there, following the project's numbering/status convention. Keep
Context, Decision, alternatives, consequences, and supersession semantics. Existing
accepted decisions are superseded, never silently replaced. This source change
needs no additional skills-repository ADR: it refines existing policy owners and
adds no dependency, runtime state model, or application public contract.

The change design links to each permanent ADR. For the conventional layout, a link
such as `../../../docs/adr/0001-example.md` resolves from both
`openspec/changes/<name>/` and `openspec/completed/<name>/`. Discover the actual
relative path; do not assume that layout in an arbitrary project.

The permanent index links to both the ADR and its related active/archived change.
Keep mutable related-change navigation in that index rather than embedding a
soon-to-move path in new accepted decision text. Archive moves only the change
directory, updates its affected navigation targets to the completed location, and
checks incoming/outgoing links for those records. Links between files inside the
change remain relative. Reuse existing project permalinks or stable navigation
owners where present; no new redirect service or registry is needed.

Legacy ADRs stay in their established location. Add index links to them, never a
copy of their text or a bulk relocation. A legacy ADR inside the active change
moves only as part of the already-defined whole-change archive; update its index
target. Already archived legacy records stay put. Preserve decision bodies and IDs;
repair only affected navigation metadata. Do not sweep unrelated documentation.

Architect, onboarding destination planning, and Full/Quick archive callers point
to this lifecycle. README/help list project-native ADRs separately from change-local
artifacts, with legacy records still supported. No runtime-schema change is needed.

## 4. Authority and enforcement are separate evidence

Keep stable `ENF-*`, `APP-*`, `OBS-*`, and `LEG-*` IDs and their normative boundaries.
Extend the existing evidence model rather than introduce a second taxonomy or a
new profile file. Enforced mechanical authority does not, by itself, mean a required
merge check. An Approved rule can be checked by tooling, manual review, or neither.

Each rule record has two independently sourced parts:

- **Authority:** classification, source/section, selected rule, scope, exceptions.
- **Enforcement evidence:** exact command/runner and config; actual checked scope
  and exclusions; invocation source; whether local/CI enforcement and merge
  blocking are proven, optional, absent, or unknown; last checked time and relevant
  revision/input evidence; remaining manual or uncovered requirements.

A configured checker is available evidence. A recorded execution proves that run
on its covered inputs. CI configuration may prove invocation and job failure
behavior; branch protection/required-check evidence is separate. If remote policy
was not inspected, merge blocking remains unknown. Do not infer it from a job name,
a local success, or a config file. Mark stale evidence and unexecuted commands
honestly. Preserve Approved authority even when enforcement is manual or incomplete.

`project-conventions-guide.md` owns the output presentation and links to the model
for field semantics. `sk-explore-codestyle` directs collection instead of restating
the schema. Architecture's authority inventory links to the same evidence when it
claims a gate. Discovery and review consumers already resolve these profiles.
This work documents enforcement; it does not install gates in target projects.

## 5. Analyzer results preserve semantics and review context

### Confirmed local Lizard behavior

Read-only experiments with available Lizard **1.21.2** on two temporary Python
files produced:

- simple function: exit 0, `No thresholds exceeded (cyclomatic_complexity > 15 or
  length > 1000 or nloc > 1000000 or parameter_count > 100)`, warning count 0;
- function with 17 branches: exit 1, `!!!! Warnings (...) !!!!`, warning count 1;
- unknown option: exit 2, usage plus `error: unrecognized arguments`.

The current broad regex matches the first result. The clean/finding/error capture
shapes, with temporary paths normalized, supply regression fixtures.

### Lizard parser decision

Keep interpretation in `shared/static-analysis/run-static-analysis.sh`. Add a
small Lizard-specific semantic classification helper over the captured result
body. It recognizes the explicit clean report and warning section/count, not the
threshold predicate alone. Failure/timeout precedence remains ahead of findings.
Preserve both logged and in-memory output paths.

| Observed result | Status |
|---|---|
| Exit 0 and explicit clean report, with no contradictory warning evidence | OK |
| Actual warnings section/positive warning evidence and normal report completion, exit 0 or 1 | FINDINGS |
| Timeout, missing tool, usage/error/traceback, unsupported nonzero exit | UNVERIFIED |
| Inconsistent clean/warning output, truncated/unrecognized report, exit 1 without warning evidence | UNVERIFIED with reason |

Do not let a clean marker hide a later failure or contradictory output. Preserve
exit-zero findings and the provenance columns/status vocabulary consumed by
`shared/review-evidence/review_gate.py`. The runner still reports outcomes in its
table and returns its existing top-level status contract. Other analyzers retain
their current classification; no general parser framework or new dependency.

### Bandit contextual review

Update only the Python review profile's Bandit guidance and conflicting severity
rows. Tool severity/confidence are evidence, not the review verdict. Assess the
reported location, test ID, data source, reachability, trust model, purpose,
controls, and changed/baseline status. In particular, non-cryptographic randomness
for non-security behavior differs from randomness used for secrets; a fixed trusted
subprocess invocation differs from untrusted shell interpolation.

Retain raw FINDINGS and issue-by-issue rationale. Do not add global excludes,
blanket `nosec`, or lower thresholds to make a battery green. Use the existing
scope-governance disposition and remedy routing, and existing correctness-safety
severity rules. Missing context is investigation/UNVERIFIED, not assumed safety or
an invented blocker. Existing approval-gate enums and fingerprint binding remain;
any `baseline` or `approved_exception` row needs its existing required authority
and rationale, covering all underlying issues rather than waiving the whole tool.

## Validation and acceptance

Deterministic regression owners are `tests/test-static-analysis-artifacts.sh` and
`tests/test-review-approval-gate.py`. Add normalized real Lizard report fixtures at
`tests/fixtures/static-analysis/`. Exercise clean, genuine findings, zero-exit
findings, execution failure, and inconsistent/unrecognized report; both output
modes must agree. Preserve existing non-Lizard, raw-log, and summary-only checks.

Add a small non-installed behavioral corpus under `evals/scenario-workflow/`:
`cases.json` contains realistic requests/raw fixture files, `goldens.json` holds
the withheld outcome rubric, and `README.md` describes bounded fresh-context use.
`tests/test-scenario-workflow-eval.py`, wired into `tests/run.sh`, checks corpus
integrity only. It must not be reported as proof that an agent followed the policy.
No new generic live-evaluation framework is needed.

The root's fresh evaluator receives current source prompts plus one raw case, no
intended diagnosis or answer key. Work happens in a temporary directory. Cases:

1. Existing layered application with two outcomes and an atomic shared operation:
   produce scenario-aware design and milestones without imposing VSA or asynchronous
   consistency. One cohesive task legitimately spans more than five files.
2. Existing permanent ADR owner plus a legacy archived ADR: prepare a significant
   decision and archive the sample change; all related links resolve, IDs/body
   hashes survive, and no duplicate ADR body exists. Repeat with no permanent owner.
3. Approved rule, configured-but-unused check, optional CI job, and unavailable
   required-check policy: produce profiles without inventing merge gating. Include
   a verified blocking-gate positive control and stale evidence.
4. Bandit reports with safe non-security randomness and unsafe secret generation,
   plus fixed trusted execution and untrusted shell input: preserve reports and
   classify from concrete context; no blanket suppression.
5. A bounded local bug fix: one compact outcome, existing architecture retained,
   no artificial domain migration, added mechanism, or mandatory full-review loop.

The evaluator checks actual generated artifacts, archive paths, source hashes, and
decisions. Record observed failures and unavailable runs. A rubric or validator
passing alone is not behavioral acceptance. Parent controls delegation and runtime
evidence; this design agent launches no evaluators.

Run affected deterministic tests first, then `bash tests/run.sh` once when ready.
That existing suite includes pinned Python checks, manifest/reference closure,
platform renders, generated-document checks, workflow contracts, and installer
tests in temporary destinations. Do not run a real home-directory installer.
Regenerate `AGENTS.md`/Cursor artifacts with existing generators only if their
maintained inputs change. Preserve prompt budgets and existing phase/risk behavior.

## Growth, risks, and compatibility

- Keep the scenario contract in architecture-gates and ADR lifecycle in
  scope-governance. Their growth is cohesive; do not fork policy into each caller.
- Tighten discovery in place to stay below its 500-line ceiling. No metadata rename
  is needed, so generated inventories should normally remain unchanged.
- The shell runner is 277 lines before this change. A small semantic helper may
  cross 300; keep it with its sole execution/classification owner. Split only if
  the implementation develops a separately testable responsibility worth a module.
- Contextual security classification must not weaken required fixes. Positive and
  negative cases must both pass. Raw scanner rows and existing gate obligations stay.
- Output templates change; runtime schemas, skill names, runner CLI/provenance,
  profile ID compatibility, and review-phase topology remain stable.
- Infrastructure, persistence migrations, UI composition, and application APIs are
  not touched. No deployment or external-service authority is required.

Required next action: implement [tasks.md](./tasks.md), then provide engineering
and behavioral acceptance evidence. No material unresolved design choice remains.
