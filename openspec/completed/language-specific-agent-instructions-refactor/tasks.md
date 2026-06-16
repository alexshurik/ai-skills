# Implementation Tasks: Language-Specific Agent Instructions Refactor

## Phase 1: Create Best-Practices Directory Structure and Default Profiles

### Task 1.1: Create index.yaml and directory skeleton

- **Files**: `shared/best-practices/index.yaml`
- **Details**: Create the full directory tree under `shared/best-practices/` with empty placeholder directories. Write `index.yaml` with the detection signals schema as specified in design.md. Include all detection patterns: pyproject.toml/setup.py/requirements.txt for python, package.json for js, go.mod for go, framework greps, tooling file checks.
- **Verify**: `index.yaml` parses as valid YAML. All directories exist: `default/`, `languages/{python,js,go}/`, `frameworks/{fastapi,vue,gin}/`, `tooling/{ansible,terraform}/`.

### Task 1.2: Extract default/coder.md from sk-developer.md

- **Files**: `shared/best-practices/default/coder.md`
- **Source**: `workflow/agents/sk-developer.md` lines 211-602 (`<coding_guidelines>` section)
- **Details**: Extract the entire `<coding_guidelines>` content into `default/coder.md`. This includes: Keep It Simple, Follow Project Patterns, Write Readable Code, File Size and Module Structure, Keep Complexity Low, Declarative Over Imperative, No Hardcoded Values, Imports Always at Top, Handle Errors Consistently, Boolean Naming, Anti-Slop, Project Structure Awareness, Python Packaging Hygiene. Remove language-specific subsections (Python-Specific PEP Compliance, TypeScript-Specific) -- those go into language profiles in Phase 2. Keep only universal rules in default. Preserve code examples.
- **Verify**: `default/coder.md` contains all universal coding rules. No Python-only or TS-only sections remain in it. Content is dense and actionable.

### Task 1.3: Extract default/reviewer.md from sk-code-reviewer.md

- **Files**: `shared/best-practices/default/reviewer.md`
- **Source**: `workflow/agents/sk-code-reviewer.md` steps: `solid_principles_check`, `kiss_dry_check`, `code_quality_check`, `error_handling_check` (universal parts only), `performance_check`, `test_coverage_check`
- **Details**: Extract universal review checklist items into `default/reviewer.md`. Include: SOLID principles checklist, KISS/DRY/YAGNI checklist, code quality/readability checklist (function length, naming, complexity), error handling rules (narrow try-catch, specific exceptions -- universal rules only, not language-specific catch syntax), performance checklist, test coverage checklist. Remove language-specific items (those go to language profiles). Include the severity mapping table and the "Focus On" priority order from `<review_guidelines>`.
- **Verify**: `default/reviewer.md` covers all universal review concerns. No Python/TS/Go/Rust-specific rules remain. Severity mapping table present.

### Task 1.4: Create shared/best-practices/resolver.md

- **Files**: `shared/best-practices/resolver.md`
- **Details**: Write the resolver instructions as a reusable prompt block that agents can reference. Contains the 5-step resolution algorithm from design.md: read index, detect stack, check project overrides, assemble profile chain, report resolution. Two variants in one file: one for coder context, one for reviewer context (differ only in which .md file to load from each profile level). This file is referenced by agents, not loaded by end-user projects.
- **Verify**: Resolver instructions are concrete, step-by-step. Cover all precedence levels. Include fallback reporting requirement.
- **Depends on**: Task 1.1

## Phase 2: Extract and Create Curated Language/Framework/Tooling Profiles

### Task 2.1: Create languages/python/coder.md and languages/python/reviewer.md

- **Files**: `shared/best-practices/languages/python/coder.md`, `shared/best-practices/languages/python/reviewer.md`
- **Source for coder**: Python-Specific section from `sk-developer.md` (lines 497-601), Python-specific items from `<coding_guidelines>`
- **Source for reviewer**: `language_specific_check` Python section (lines 725-746), `error_handling_check` Python rules (lines 691-696), `anti_slop_check` Python packaging anti-patterns (lines 812-817), `import_and_module_check` Python-specific items
- **Reference**: `deli-check-backend/CLAUDE.md` for real-world patterns, `deli-check-backend/ruff.toml` for linter configuration reference, `deli-check-backend/pyproject.toml` for tooling reference
- **Details**: **coder.md** -- PEP 8/257/484 compliance, type hints, f-strings, pathlib, is None, with statements, enumerate/zip, dataclass, docstring format, import order (3 groups). **reviewer.md** -- ruff as primary linter (list recommended rule sets from ruff.toml reference: E, F, W, B, ANN, N, PL, S, I, UP, SIM, RUF, T20, PERF, ASYNC, C4, C90), bandit for security, radon for complexity/maintainability, vulture for dead code, pip-audit for dependencies, pylint selective checks. Include tool commands and severity mapping.
- **Verify**: Both files are self-contained. Coder covers all PEP rules from the original developer file. Reviewer includes tool commands and severity mapping for all Python analysis tools.
- **Depends on**: Task 1.2, Task 1.3

### Task 2.2: Create languages/js/coder.md and languages/js/reviewer.md

- **Files**: `shared/best-practices/languages/js/coder.md`, `shared/best-practices/languages/js/reviewer.md`
- **Source for coder**: TypeScript-Specific section from `sk-developer.md` (lines 566-572), TS/JS items from `language_specific_check` (lines 748-760)
- **Source for reviewer**: `run_linters_if_available` JS/TS section, `run_deep_analysis` JS/TS section, JS-specific error handling rules from `error_handling_check`
- **Reference**: `deli-check-frontend/package.json` for typical JS/TS/Vue tooling stack
- **Details**: **coder.md** -- no any (use unknown), strict null, ===, const/let, optional chaining, nullish coalescing, async/await, destructuring, explicit return types, discriminated unions, utility types. **reviewer.md** -- eslint as primary linter, npm audit for dependencies, madge for circular deps, depcheck for unused deps, sonarjs for cognitive complexity, TypeScript strict mode checks. Include tool commands.
- **Verify**: Both files cover all JS/TS items currently in the monolithic reviewer. Tool commands are concrete and runnable.
- **Depends on**: Task 1.2, Task 1.3

### Task 2.3: Create languages/go/coder.md and languages/go/reviewer.md

- **Files**: `shared/best-practices/languages/go/coder.md`, `shared/best-practices/languages/go/reviewer.md`
- **Source for coder**: Go-Specific section from `language_specific_check` (lines 762-770), Go error handling from `error_handling_check` (lines 703-708)
- **Source for reviewer**: `run_linters_if_available` Go section, `run_deep_analysis` Go section
- **Research**: Official Go best practices (Effective Go, Go Code Review Comments) -- use WebSearch to supplement since no local Go reference project exists
- **Details**: **coder.md** -- gofmt, explicit error handling (check err != nil immediately), error wrapping with context (fmt.Errorf %w), context propagation, interface segregation (small interfaces), struct tags, nil checks, defer for cleanup, channel patterns. **reviewer.md** -- go vet, gofmt check, gosec for security, gocognit for cognitive complexity, golangci-lint with gocritic/gocognit/gocyclo. Include tool install commands and severity mapping.
- **Verify**: Both files provide concrete Go guidance. No placeholder content. Reviewer includes all tool commands from the original reviewer.
- **Depends on**: Task 1.2, Task 1.3

### Task 2.4: Create frameworks/fastapi/coder.md and frameworks/fastapi/reviewer.md

- **Files**: `shared/best-practices/frameworks/fastapi/coder.md`, `shared/best-practices/frameworks/fastapi/reviewer.md`
- **Reference**: `deli-check-backend/CLAUDE.md` (architecture patterns, CBV, service DI, exception hierarchy, settings), `deli-check-backend/ruff.toml` (FAST rule set)
- **Research**: FastAPI official best practices -- use WebSearch for current recommendations
- **Details**: **coder.md** -- async def for endpoints (never sync def in async app), Pydantic models for request/response, dependency injection pattern, service classes with constructor DI, exception hierarchy (base -> domain), settings organization (grouped by concern), CBV pattern with GenericViewSet. **reviewer.md** -- ruff FAST rules, check for sync def endpoints (blocks event loop), verify DI usage, check Pydantic model validation, verify exception hierarchy, check for proper async patterns (no blocking calls in async context).
- **Verify**: Patterns match deli-check-backend reference. Rules are universal FastAPI guidance, not deli-check-specific.
- **Depends on**: Task 2.1

### Task 2.5: Create frameworks/vue/coder.md and frameworks/vue/reviewer.md

- **Files**: `shared/best-practices/frameworks/vue/coder.md`, `shared/best-practices/frameworks/vue/reviewer.md`
- **Reference**: `deli-check-frontend/package.json` for stack (Vue 3, TypeScript, Vite, Vue Query, Vitest, Playwright)
- **Research**: Vue 3 Composition API best practices, Vue Query patterns -- use WebSearch
- **Details**: **coder.md** -- Composition API with `<script setup>`, Vue Query for server state (useQuery/useMutation), composables for reusable logic, component structure (single-file components), props typing with defineProps, emit typing with defineEmits, reactive refs and computed, provide/inject for deep DI. **reviewer.md** -- check for Options API usage (prefer Composition), verify Vue Query usage for async data, check reactivity (no losing reactivity by destructuring), verify component size and SRP, check for proper TypeScript integration.
- **Verify**: Rules are universal Vue 3 + Composition API guidance. No deli-check-specific patterns.
- **Depends on**: Task 2.2

### Task 2.6: Create frameworks/gin/coder.md and frameworks/gin/reviewer.md

- **Files**: `shared/best-practices/frameworks/gin/coder.md`, `shared/best-practices/frameworks/gin/reviewer.md`
- **Research**: Gin official docs and best practices -- use WebSearch (no local reference project)
- **Details**: **coder.md** -- middleware registration order, context usage (c.JSON, c.Bind, c.Param), binding/validation with struct tags, error response patterns, route grouping, graceful shutdown. **reviewer.md** -- check middleware ordering (auth before business logic), verify binding error handling, check for context leaks, verify proper error responses (consistent JSON structure), check for missing validation on user input.
- **Verify**: Rules are concrete and actionable. No placeholder or filler content.
- **Depends on**: Task 2.3

### Task 2.7: Create tooling/ansible/coder.md and tooling/ansible/reviewer.md

- **Files**: `shared/best-practices/tooling/ansible/coder.md`, `shared/best-practices/tooling/ansible/reviewer.md`
- **Reference**: `deli-check-infrastructure/ansible.cfg`, role-based layout from deli-check-infrastructure
- **Research**: Ansible best practices docs, ansible-lint profiles
- **Details**: **coder.md** -- role-based organization, FQCN for all modules, idempotent tasks, no shell/command when a module exists, group_vars/host_vars for variables, vault for secrets, handlers for service restarts, tags for selective runs. **reviewer.md** -- ansible-lint with production profile, check FQCN usage, verify idempotency (no shell commands that aren't idempotent without creates/removes), check variable precedence, verify vault usage for secrets, check for hardcoded hosts/IPs.
- **Verify**: Rules normalized against official Ansible docs, not blindly copied from deli-check shell-heavy patterns.
- **Depends on**: Task 1.3

### Task 2.8: Create tooling/terraform/coder.md and tooling/terraform/reviewer.md

- **Files**: `shared/best-practices/tooling/terraform/coder.md`, `shared/best-practices/tooling/terraform/reviewer.md`
- **Research**: HashiCorp style guide, standard module structure, TFLint docs -- use WebSearch
- **Details**: **coder.md** -- standard file naming (main.tf, variables.tf, outputs.tf, providers.tf), flat module trees (no thin wrappers), terraform validate before commit, readable comments (not excessive), variable descriptions and types, output descriptions, locals for computed values, data sources over hardcoding. **reviewer.md** -- terraform validate, terraform fmt check, tflint, check for hardcoded values in resources (use variables), verify module structure, check state management (no local state in shared infra), verify provider version constraints.
- **Verify**: Rules based on official HashiCorp guidance. Mark as v1 -- to be refined with real project usage.
- **Depends on**: Task 1.3

## Phase 3: Decompose Reviewer into Orchestrator + Subagents

### Task 3.1: Create review-steps/security.md

- **Files**: `workflow/agents/review-steps/security.md`
- **Source**: `sk-code-reviewer.md` steps: `security_check` (lines 875-899), security severity mappings from `run_deep_analysis`
- **Details**: Create focused security review subagent. Include: input validation (SQL injection, XSS, path traversal, command injection), auth checks (permissions, hardcoded credentials, JWT validation), data protection (no data leaks in errors, encryption, PII masking), dependency vulnerabilities. Reference the static analysis results passed by orchestrator (semgrep, bandit, gosec findings). Output: list of findings with severity (BLOCKER for security issues). Keep file under 150 lines.
- **Verify**: All security checklist items from original reviewer are present. Output format is structured for aggregation.
- **Depends on**: Task 1.3

### Task 3.2: Create review-steps/architecture.md

- **Files**: `workflow/agents/review-steps/architecture.md`
- **Source**: `sk-code-reviewer.md` steps: `solid_principles_check`, `kiss_dry_check`, `architecture_check`, `check_against_design`, `performance_check`
- **Details**: Create focused architecture review subagent. Include: SOLID principles checklist, KISS/DRY/YAGNI checklist, layer boundaries, design pattern appropriateness, abstraction quality, design.md compliance check, performance considerations (N+1, blocking async, memory leaks). Output: list of findings with severity. Keep file under 200 lines.
- **Verify**: Covers SOLID, KISS, DRY, architecture, performance, and design compliance. No language-specific rules leaked in.
- **Depends on**: Task 1.3

### Task 3.3: Create review-steps/stack-rules.md

- **Files**: `workflow/agents/review-steps/stack-rules.md`
- **Source**: `sk-code-reviewer.md` steps: `language_specific_check`, `error_handling_check` (language-specific parts), `import_and_module_check`, `code_quality_check` (readability items), `review_each_file` (full-file review instruction)
- **Details**: Create the stack-specific review subagent. This subagent receives the resolved reviewer.md profile from the orchestrator and applies it. Include: instruction to load and apply the profile rules, import organization check, error handling patterns (language-specific catch syntax), declarative vs imperative style check, test coverage check, full-file review instruction (not just diff). Output: list of findings with severity.
- **Verify**: Subagent instructions clearly state it loads the resolved profile. Generic enough to work with any language profile. Under 150 lines (bulk of rules come from the loaded profile).
- **Depends on**: Task 1.3, Phase 2

### Task 3.4: Create review-steps/instruction-quality.md

- **Files**: `workflow/agents/review-steps/instruction-quality.md`
- **Source**: `sk-code-reviewer.md` step: `anti_slop_check` (lines 793-822), `import_and_module_check` Python packaging items
- **Details**: Create the instruction/slop quality subagent. Only runs for agent instruction repositories (detect by: `workflow/agents/` directory or `AGENTS.md` in repo root). Include: blank lines at file top, excessive comments, trivial wrappers, copy-paste code, utility module portability, parallel config systems, exception classes in own files, file/method size limits, Python packaging anti-patterns (sys.path, from src.). If not an agent repo, output "Not applicable -- skipped" immediately. Keep under 100 lines.
- **Verify**: Detection logic for agent repos is clear. All anti-slop items from original reviewer present. Skip behavior documented.
- **Depends on**: Task 1.3

### Task 3.5: Create sk-review-orchestrator.md

- **Files**: `workflow/agents/sk-review-orchestrator.md`
- **Source**: `sk-code-reviewer.md` steps: `detect_project_stack`, `get_changed_files`, `research_best_practices` (replaced by profile resolver), `run_linters_if_available`, `check_and_install_tools`, `run_deep_analysis`, `provide_feedback`, `return_result`. Severity mapping table. Review guidelines (Focus On, Don't Nitpick, Be Constructive, Be Specific).
- **Details**: Create the thin orchestrator (~150 lines). Structure:
  1. YAML frontmatter (name, description, tools, version)
  2. Role section (coordinator, not reviewer)
  3. Execution flow:
     - Resolve scope (git diff, changed files)
     - Detect stack (reuse detection logic from index.yaml)
     - Resolve profiles (embed resolver instructions from `shared/best-practices/resolver.md`, reviewer variant)
     - Discover and install tools (`check_and_install_tools` logic -- keep existing user interaction)
     - Run static analysis (linters + deep analysis -- consolidate `run_linters_if_available` and `run_deep_analysis` into one step, parameterized by detected stack)
     - Dispatch 4 parallel subagents via Task tool, passing: changed files, static analysis results, resolved profile (for stack-rules)
     - Aggregate findings from all subagents
     - Deduplicate (same file:line from multiple subagents)
     - Apply severity mapping table
     - Render verdict using existing APPROVED/CHANGES REQUESTED templates
  4. Severity mapping table (from current reviewer)
  5. Review guidelines: Focus On priority order, Don't Nitpick list, Be Constructive/Specific guidance
  6. Guardrails
  7. Quality checklist (condensed)
- **Verify**: File is under 200 lines. All orchestration steps present. Subagent dispatch uses Task tool with correct subagent_type references. Severity table and guidelines preserved. No checklist items in orchestrator (those are in subagents).
- **Depends on**: Tasks 3.1-3.4, Task 1.4

## Phase 4: Add Resolver Instructions to Agents

### Task 4.1: Refactor sk-developer.md -- extract coding guidelines, add resolver

- **Files**: `workflow/agents/sk-developer.md`
- **Details**:
  1. Remove the entire `<coding_guidelines>` section (lines 211-602, ~390 lines)
  2. Add a new step `resolve_coding_profiles` after `review_context` and before `study_project_patterns`: embed the resolver instructions (coder variant) from `shared/best-practices/resolver.md`
  3. Add instruction in `study_project_patterns`: "Apply rules from all loaded coder.md profiles during implementation"
  4. Keep everything else: role, philosophy, TDD discipline, execution flow, guardrails, quality checklist
  5. Update quality checklist to reference profile compliance instead of inline rules
- **Verify**: File drops from ~672 lines to ~280 lines. Resolver step present. No coding rules remain inline -- they come from profiles. TDD flow and guardrails preserved.
- **Depends on**: Task 1.2, Task 1.4

### Task 4.2: Light cleanup of sk-tester.md

- **Files**: `workflow/agents/sk-tester.md`
- **Details**: Review for redundancy and slop. Specific targets:
  1. The test plan presentation template is repeated twice (in `mandatory_interaction_gate` and in `propose_test_plan`) -- consolidate into one
  2. Reduce verbosity in step descriptions where instructions are restated
  3. Remove any language-specific test scaffolding that duplicates what project patterns already provide
  4. Keep all interaction gates and user approval flows intact
- **Verify**: File is noticeably shorter. Test plan template appears once. All interaction gates preserved. No behavioral changes.
- **Depends on**: None (independent)

## Phase 5: Slop Cleanup Across All Skills

### Task 5.1: Clean up sk-team-feature/SKILL.md

- **Files**: `workflow/skills/sk-team-feature/SKILL.md`
- **Details**:
  1. Update agent table: rename `sk-code-reviewer` to `sk-review-orchestrator` with updated description
  2. Update Phase 6 (Code Review) Task tool invocation: change `subagent_type` to `sk-review-orchestrator`, simplify the prompt (orchestrator handles its own step ordering, no need to list steps in the dispatch prompt)
  3. Replace vague "Show summary to user" after each phase with specific instructions on what to show verbatim from agent output. Examples: after Planning — show Architecture Summary, File Map, Task Summary, Risks; after Code Review — show full findings and verdict; after Discovery — show proposal summary and open questions. The orchestrator must not paraphrase away key structured artifacts.
  4. Add explicit anti-autopilot rules to the orchestrator:
     - NEVER answer agent questions on behalf of the user. If an agent returns open questions, show them to the user verbatim and wait for answers.
     - NEVER auto-proceed to the next phase. After showing results, STOP and wait for explicit user approval ("go", "next", "approved", etc.).
     - These two rules must be stated as hard constraints at the top of the orchestrator, not buried in phase instructions.
  5. Review for any other verbose or redundant instructions -- tighten
- **Verify**: Agent reference updated. Review dispatch simplified. Each "After agent completes" block specifies exactly which artifacts to show verbatim. Anti-autopilot rules present as top-level constraints.
- **Depends on**: Task 3.5

### Task 5.2: Clean up sk-team-quick/SKILL.md

- **Files**: `workflow/skills/sk-team-quick/SKILL.md`
- **Details**: Same as Task 5.1 -- update reviewer agent reference from `sk-code-reviewer` to `sk-review-orchestrator`. Update the Task tool prompt for review phase.
- **Verify**: Agent reference updated. Quick workflow still works.
- **Depends on**: Task 3.5

### Task 5.3: Clean up utilities/sk-code-review/SKILL.md

- **Files**: `utilities/sk-code-review/SKILL.md`
- **Details**:
  1. Update Step 3 to spawn `sk-review-orchestrator` instead of `sk-code-reviewer`
  2. Simplify the Task tool prompt -- remove the step-by-step instructions (lines 59-77). The orchestrator owns its own execution flow. Just pass: context (design doc path, code style path) and the instruction to review.
  3. Update the fallback instructions for platforms without Task tool
- **Verify**: Skill spawns correct orchestrator. Prompt is shorter. Fallback path updated.
- **Depends on**: Task 3.5

### Task 5.4: Review and clean remaining agent files

- **Files**: `workflow/agents/sk-product-analyst.md`, `workflow/agents/sk-researcher.md`, `workflow/agents/sk-doc-reviewer.md`, `workflow/agents/sk-acceptance-reviewer.md`, `workflow/agents/sk-architect.md`
- **Details**: Read each file. Identify and note:
  1. Redundant or repeated instructions
  2. Verbose sections that can be tightened
  3. Any hardcoded patterns that should be configurable
  4. Apply light cleanup where clear wins exist (reduce filler paragraphs, remove obvious restating)
  5. Do NOT change behavioral logic or interaction gates
- **Verify**: Each file is reviewed. Changes are conservative -- only clear improvements. No behavioral changes.
- **Depends on**: None (independent)

### Task 5.5: Delete sk-code-reviewer.md

- **Files**: `workflow/agents/sk-code-reviewer.md` (DELETE)
- **Details**: Remove the old monolithic reviewer file. All its content has been distributed to: `sk-review-orchestrator.md`, `review-steps/*.md`, `shared/best-practices/default/reviewer.md`, and language/framework profiles.
- **Verify**: File is deleted. No remaining references to `sk-code-reviewer` in any skill or agent file (grep to confirm).
- **Depends on**: Tasks 3.5, 5.1, 5.2, 5.3

## Phase 6: Update Adapters and Integration Points

### Task 6.1: Update adapters

- **Files**: `adapters/codex/skill-template.md`, `adapters/codex/README.md`, `adapters/cursor/.cursorrules.template`, `adapters/cursor/.cursorrules`, `adapters/cursor/README.md`, `adapters/claude-code/README.md`, `adapters/kimi/README.md`
- **Details**: In each adapter file, search for references to `sk-code-reviewer` and update to `sk-review-orchestrator`. Update any descriptions of the review process to reflect the new pipeline (orchestrator + parallel subagents). Mention that profiles are loaded from `shared/best-practices/`.
- **Verify**: No references to `sk-code-reviewer` remain in adapters. Descriptions accurate.
- **Depends on**: Task 5.5

## Phase 7: Update Documentation

### Task 7.1: Update AGENTS.md

- **Files**: `AGENTS.md`
- **Details**:
  1. Update `sk-code-reviewer` entry to `sk-review-orchestrator` with new description: "Orchestrate code review through specialized subagents. Resolves stack-specific profiles, runs static analysis, dispatches parallel review passes (security, architecture, stack rules, instruction quality), aggregates findings."
  2. Add brief mention of `shared/best-practices/` in a new "Best Practices" section
  3. Note the `.agents/best-practices/` convention for downstream projects
  4. Update any other stale references
- **Verify**: AGENTS.md is accurate. Agent list matches actual files. New architecture mentioned.
- **Depends on**: Task 6.1

### Task 7.2: Add README or header to shared/best-practices/

- **Files**: `shared/best-practices/index.yaml` (update header comments)
- **Details**: Add clear header comments to `index.yaml` explaining: what this directory is, how profiles are organized, how to add a new profile (create directory, add coder.md and/or reviewer.md, add detection entry to index.yaml), the precedence chain. Do NOT create a separate README.md -- keep documentation in the index.yaml header and in AGENTS.md.
- **Verify**: A new contributor can understand how to add a profile by reading the index.yaml header.
- **Depends on**: Phase 2 complete

## Dependencies

```
Phase 1 (foundation)
  Task 1.1 ─── Task 1.4 depends on 1.1
  Task 1.2 ─── standalone (extracts from sk-developer.md)
  Task 1.3 ─── standalone (extracts from sk-code-reviewer.md)
  Task 1.4 ─── depends on 1.1

Phase 2 (profiles) ─── all depend on Phase 1
  Task 2.1 ─── depends on 1.2, 1.3
  Task 2.2 ─── depends on 1.2, 1.3
  Task 2.3 ─── depends on 1.2, 1.3
  Task 2.4 ─── depends on 2.1 (builds on python profile)
  Task 2.5 ─── depends on 2.2 (builds on js profile)
  Task 2.6 ─── depends on 2.3 (builds on go profile)
  Task 2.7 ─── depends on 1.3
  Task 2.8 ─── depends on 1.3

Phase 3 (reviewer decomposition) ─── depends on Phase 1
  Tasks 3.1-3.4 ─── depend on 1.3 (default reviewer profile)
  Task 3.3 ─── also depends on Phase 2 (needs profiles to reference)
  Task 3.5 ─── depends on 3.1-3.4 and 1.4

Phase 4 (agent updates) ─── depends on Phases 1-2
  Task 4.1 ─── depends on 1.2, 1.4
  Task 4.2 ─── independent

Phase 5 (cleanup) ─── depends on Phase 3
  Tasks 5.1-5.3 ─── depend on 3.5
  Task 5.4 ─── independent
  Task 5.5 ─── depends on 5.1, 5.2, 5.3

Phase 6 ─── depends on 5.5
Phase 7 ─── depends on Phase 6
```

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1 | 4 tasks | Foundation: directory structure, default profiles, resolver |
| Phase 2 | 8 tasks | Curated language/framework/tooling profiles |
| Phase 3 | 5 tasks | Reviewer decomposition into orchestrator + subagents |
| Phase 4 | 2 tasks | Update developer and tester with resolver/cleanup |
| Phase 5 | 5 tasks | Slop cleanup across skills, delete old reviewer |
| Phase 6 | 1 task | Update adapters |
| Phase 7 | 2 tasks | Update documentation |
| **Total** | **27 tasks** | |
