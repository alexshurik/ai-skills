# Language-Specific Agent Instructions Refactor

> Created by: Product Analyst
> Date: 2026-04-14
> Status: Ready for Planning

## Vision

### Problem Statement
The current `skills` repository provides a useful multi-agent SDD workflow, but key instructions are too generic and too large. In practice, this leads to weaker language/framework guidance, missed tool invocations during code review, and too much low-signal instruction content ("slop") across skills. The project needs a more modular and extensible system that can apply the right best practices for a project, framework, and language without overloading a single agent.

### Target Users
- Primary: the repository author, using the workflow across personal projects.
- Secondary: other developers or teams who want to extend the workflow with their own language-, framework-, or project-specific best-practice profiles.

### Success Metrics
- Reviewer orchestration explicitly runs specialized review steps, including analysis/tooling steps, with fewer missed checks.
- The system supports a clear precedence chain: project best practices -> framework -> language -> default.
- Curated best-practice profiles exist for `python`, `fastapi`, `js`, `vue.js`, `ansible`, `terraform`, `go`, and `gin`.
- Existing skills are reviewed and simplified to reduce redundant or low-value instruction text.
- The architecture is extensible enough that new profiles can be added without rewriting the core workflow.

## Requirements

### User Stories

#### US-1: Context-aware instruction selection
**As a** workflow user  
**I want** the agent to load the most relevant best-practice instructions for the current project  
**So that** coding and review behavior matches the actual stack instead of falling back to generic advice too early

**Acceptance Criteria:**
```gherkin
Scenario: Project-specific best practices exist
  Given a target repository contains project-specific best-practice instructions
  When the workflow analyzes the repository
  Then it loads the project-specific instructions before framework, language, or default profiles

Scenario: Only framework-level best practices exist
  Given no project-specific best-practice instructions are found
  And a supported framework is detected
  When the workflow selects guidance
  Then it loads the framework-specific profile
  And it documents that project-specific guidance was not found

Scenario: No specific profiles are found
  Given no project-specific, framework-specific, or language-specific profile is available
  When the workflow selects guidance
  Then it falls back to the default profile
  And it explicitly reports that fallback in its output
```

#### US-2: Modular reviewer orchestration
**As a** workflow author  
**I want** code review to be orchestrated through smaller specialized steps and subagents  
**So that** analysis tools and stack-specific checks are run more reliably with less context overload

**Acceptance Criteria:**
```gherkin
Scenario: Review includes parallelizable checks
  Given a review task with independent analysis steps
  When the reviewer orchestrator runs
  Then it dispatches parallelizable review subtasks in parallel
  And it aggregates their findings into one review result

Scenario: Review requires tool-backed analysis
  Given the target project has relevant analysis tools or static checks available
  When the review workflow executes
  Then the dedicated analysis step is responsible for invoking those tools
  And the final review output reflects those results
```

#### US-3: Curated stack profiles
**As a** workflow maintainer  
**I want** curated profiles for common languages and frameworks  
**So that** users get strong default guidance without having to write everything themselves

**Acceptance Criteria:**
```gherkin
Scenario: Supported stack profile is requested
  Given the repository uses one of the supported stacks
  When the workflow selects best practices
  Then it can use a curated profile for that stack

Scenario: Curated profiles are seeded from references
  Given reference implementations are available for selected stacks
  When curated profiles are authored
  Then the profile content reflects patterns observed in those reference projects
  And unsupported reference gaps can be filled using explicit best-practice research
```

#### US-4: Skill cleanup and simplification
**As a** maintainer of the repository  
**I want** the existing skills and agents to be reviewed for redundant or low-value instruction text  
**So that** the repository becomes easier to maintain and agents receive denser, more reliable instructions

**Acceptance Criteria:**
```gherkin
Scenario: Existing skills contain low-signal instructions
  Given the repository contains verbose or repetitive skill instructions
  When the refactor is planned and implemented
  Then the affected skills are identified
  And concrete simplification recommendations are documented

Scenario: Skill cleanup changes are applied
  Given a skill is simplified
  When the updated skill is reviewed
  Then it preserves the intended behavior
  And removes redundant or low-value content
```

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Define and implement a best-practice selection hierarchy: project -> framework -> language -> default. | Must |
| FR-2 | Define where project-specific best practices live in a target repository and how the agent discovers them. | Must |
| FR-3 | Add curated profiles for `python`, `fastapi`, `js`, `vue.js`, `ansible`, `terraform`, `go`, and `gin`. | Must |
| FR-4 | Use `~/Project/delicheck` as a reference source for `python`, `fastapi`, `js`, and `vue.js` profiles where applicable. | Must |
| FR-5 | Create `go` and `gin` profiles from explicit best-practice guidance when no internal reference project exists. | Must |
| FR-6 | Refactor the current reviewer into an orchestrator with smaller specialized review steps or subagents. | Must |
| FR-7 | Run independent review steps in parallel where that reduces latency without reducing review quality. | Should |
| FR-8 | Ensure analysis/tool execution responsibility is explicit and attached to dedicated review steps. | Must |
| FR-9 | Review all existing skills and agent instructions and identify low-value, repetitive, or AI-generated slop for cleanup. | Must |
| FR-10 | Propose and implement concrete simplifications to the current skills structure and instruction content. | Must |
| FR-11 | Make it straightforward for future users to add project-, framework-, or language-specific profiles. | Must |
| FR-12 | Emit an explicit message or artifact note whenever fallback to a less-specific profile occurs. | Must |

### Non-Functional Requirements

| ID | Requirement | Metric |
|----|-------------|--------|
| NFR-1 | Extensibility | Adding a new profile should not require redesigning the orchestrator or duplicating large instructions. |
| NFR-2 | Review reliability | Tool-backed analysis steps should be structurally hard to skip because responsibility is isolated to dedicated steps. |
| NFR-3 | Maintainability | Refactored skills should be shorter, more focused, and easier to reason about than the current baseline. |
| NFR-4 | Transparency | Profile selection and fallback decisions must be visible in workflow output or artifacts. |
| NFR-5 | Compatibility | The repository should continue to support its target agent platforms unless a deliberate improvement requires coordinated adapter updates. |

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Target repository is a monorepo with backend, frontend, and infra stacks | The design defines whether best practices are selected per subproject/path or via another deterministic strategy, rather than assuming one profile for the whole repo. |
| Framework is detected but curated profile is missing | The workflow falls back to language or default and explicitly reports the missing specialized profile. |
| Project-specific best practices exist but are incomplete | The workflow uses available project guidance, supplements it from lower-precedence profiles, and reports the composition clearly. |
| Multiple review subtasks find overlapping issues | The orchestrator deduplicates or consolidates findings in the final review output. |
| A target project has no usable analysis tools installed | The analysis step records what was attempted, what was unavailable, and continues with static review instead of silently skipping checks. |
| Existing skill cleanup removes too much detail | Review and acceptance phases verify that essential workflow behavior and guardrails are preserved. |

## Data Models

### New Entities
- Best-practice profile definitions for language-, framework-, and possibly project-level instruction packs.
- Reviewer orchestration structure describing specialized review steps, their responsibilities, and whether they can run in parallel.
- Optional manifest or convention for declaring project-specific best-practice files in downstream repositories.

### Modified Entities
- Existing coder/reviewer instruction files and potentially other skill files that currently contain overly broad or repetitive guidance.
- Installation or adapter logic if profile packaging/discovery needs to change across Codex, Claude Code, Cursor, or Kimi/MiniMax.
- Workflow skills that invoke the code-review process.

### Relationships
- A workflow run resolves best-practice guidance through a precedence chain.
- The reviewer orchestrator delegates to specialized review steps/subagents.
- Curated profiles can be referenced by workflow skills and potentially overridden by project-level profiles.

## Out of Scope
- Adding business features to downstream application repositories.
- Building exhaustive curated profiles for every language or framework beyond the explicitly requested initial set.
- Silent fallback behavior that hides missing profile coverage.
- Perfect preservation of the current repository structure where a better design requires change.

## Open Questions
- [ ] What exact on-disk convention should downstream repositories use for project-specific best-practice files?
- [ ] Should coder instructions and reviewer instructions share the same profile taxonomy and file layout, or be separated?
- [ ] What review-step granularity is optimal before orchestration overhead outweighs reliability gains?
- [ ] Which existing skills should be treated as the highest-priority cleanup targets after `sk-code-reviewer`?

## References
- `~/Project/delicheck` backend/frontend/infra repositories for Python, FastAPI, JavaScript, and Vue.js reference patterns.
- Current `skills` repository workflow and agent definitions, especially `workflow/agents/sk-code-reviewer.md`.
