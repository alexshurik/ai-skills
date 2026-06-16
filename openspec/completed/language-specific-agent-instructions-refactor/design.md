# Technical Design: Language-Specific Agent Instructions Refactor

## Overview

This refactor replaces the monolithic reviewer (1266 lines), bloated developer (672 lines), and embedded best-practice logic with a three-layer architecture: **policy** (reusable profile files), **resolver** (prompt-based instructions for profile discovery), and **execution** (thin orchestrator + focused subagents).

The core insight: large generic prompts cause context overload, missed tool invocations, and unmaintainable agent files. Splitting policy from orchestration fixes all three.

## Architecture

### Three-Layer Model

```
                    POLICY LAYER
    shared/best-practices/
    +-----------+  +------------+  +-----------+
    | default/  |  | languages/ |  | frameworks|
    | coder.md  |  | python/    |  | fastapi/  |
    | reviewer  |  | js/  go/   |  | vue/ gin/ |
    +-----------+  +------------+  +-----------+
          |              |               |
          v              v               v
                   RESOLVER LAYER
    index.yaml (detection patterns + profile list)
    Prompt instructions in agents: "how to find and load profiles"
    Precedence: project -> framework -> language -> default
          |
          v
                  EXECUTION LAYER
    +---------------------+     +------------------+
    | sk-review-           |     | sk-developer.md  |
    | orchestrator.md      |     | (loads coder.md  |
    | (~150 lines)         |     |  profiles)       |
    +---------------------+     +------------------+
      |   |   |   |
      v   v   v   v
    review-steps/
    security.md  architecture.md  stack-rules.md  instruction-quality.md
```

### Downstream Project Convention

Target repositories can provide project-level overrides:

```
.agents/
  best-practices/
    project/
      coder.md          # project-specific coding rules
      reviewer.md       # project-specific review rules
    projects/           # monorepo support
      backend/
        coder.md
        reviewer.md
      frontend/
        coder.md
        reviewer.md
```

Adapters also read `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/` for compatibility, but the canonical `.agents/best-practices/` directory takes precedence when present.

## File/Directory Layout

### shared/best-practices/

```
shared/best-practices/
  index.yaml
  default/
    coder.md              # extracted from sk-developer.md <coding_guidelines>
    reviewer.md           # extracted from sk-code-reviewer.md checklist sections
  languages/
    python/
      coder.md            # PEP compliance, type hints, pathlib, f-strings
      reviewer.md         # ruff rules, bandit, radon, vulture, Python anti-patterns
    js/
      coder.md            # no-any, strict null, async/await, const/let
      reviewer.md         # eslint, madge, depcheck, TS-specific checks
    go/
      coder.md            # gofmt, error handling, context propagation, defer
      reviewer.md         # go vet, gosec, gocognit, golangci-lint
  frameworks/
    fastapi/
      coder.md            # CBV, Pydantic models, async endpoints, DI
      reviewer.md         # FAST ruff rules, async def checks, dependency injection
    vue/
      coder.md            # Vue 3 composition API, Vue Query, component structure
      reviewer.md         # Vue-specific linting, reactivity pitfalls
    gin/
      coder.md            # middleware, binding/validation, error responses
      reviewer.md         # gin-specific security, middleware ordering
  tooling/
    ansible/
      coder.md            # role-based layout, FQCN, idempotency
      reviewer.md         # ansible-lint profiles, variable precedence
    terraform/
      coder.md            # standard module structure, naming, validate
      reviewer.md         # tflint, module depth, state management
```

### Profile Format Specification

**coder.md** contains rules the developer agent follows when writing code:
- Language idioms and conventions
- Import organization rules
- Error handling patterns
- File structure expectations
- Anti-patterns to avoid
- Code examples (good vs bad)

**reviewer.md** contains rules the reviewer agent checks during review:
- Checklist items specific to the stack
- Tool commands to run (linters, analyzers)
- Severity mappings for findings
- Anti-patterns to flag with explanations

Both files are dense, concrete, actionable. No filler, no vague advice. Each rule must be universal (applies to any project using that stack), never project-specific.

### index.yaml Schema

```yaml
# shared/best-practices/index.yaml
#
# Maps file-system detection signals to profile paths.
# Agents read this file to determine which profiles to load.

precedence:
  - project      # .agents/best-practices/project/ in target repo
  - framework
  - language
  - default

detection:
  languages:
    python:
      signals:
        - file: pyproject.toml
        - file: setup.py
        - file: requirements.txt
      profiles:
        coder: languages/python/coder.md
        reviewer: languages/python/reviewer.md

    js:
      signals:
        - file: package.json
      profiles:
        coder: languages/js/coder.md
        reviewer: languages/js/reviewer.md

    go:
      signals:
        - file: go.mod
      profiles:
        coder: languages/go/coder.md
        reviewer: languages/go/reviewer.md

  frameworks:
    fastapi:
      parent: python
      signals:
        - grep: "fastapi"
          in: [pyproject.toml, requirements.txt, setup.py]
      profiles:
        coder: frameworks/fastapi/coder.md
        reviewer: frameworks/fastapi/reviewer.md

    vue:
      parent: js
      signals:
        - grep: '"vue"'
          in: [package.json]
      profiles:
        coder: frameworks/vue/coder.md
        reviewer: frameworks/vue/reviewer.md

    gin:
      parent: go
      signals:
        - grep: "gin-gonic"
          in: [go.mod]
      profiles:
        coder: frameworks/gin/coder.md
        reviewer: frameworks/gin/reviewer.md

  tooling:
    ansible:
      signals:
        - file: ansible.cfg
        - file: playbook.yml
        - directory: roles/
      profiles:
        coder: tooling/ansible/coder.md
        reviewer: tooling/ansible/reviewer.md

    terraform:
      signals:
        - file: "*.tf"
        - file: terraform.tfvars
      profiles:
        coder: tooling/terraform/coder.md
        reviewer: tooling/terraform/reviewer.md
```

## Resolver Instructions

The resolver is NOT executable code. It is a block of prompt text embedded in agent files that tells the agent how to discover and load the right profiles. The same resolver text (with minor role variations) goes into both the developer and the review orchestrator.

### Resolver Prompt Block (embedded in agents)

```xml
<resolve_best_practice_profiles>
## Profile Resolution

Load best-practice profiles for the detected stack. Profiles contain rules
you MUST follow during [coding | review].

### Step 1: Read the index

Read `shared/best-practices/index.yaml` (relative to the skills repo root).
This file lists detection signals and profile paths.

### Step 2: Detect stack

Check the TARGET repository for detection signals, in this order:
1. **Frameworks** — grep manifest files for framework identifiers
2. **Languages** — check for manifest file existence
3. **Tooling** — check for config files or directories

Record all detected stacks.

### Step 3: Check for project overrides

In the TARGET repository, check for `.agents/best-practices/project/[coder|reviewer].md`.
For monorepos, also check `.agents/best-practices/projects/<component>/[coder|reviewer].md`
if working in a subdirectory.

Also check for platform-native guidance:
- `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/` — read if present

### Step 4: Assemble profile chain

Build the profile chain by precedence (highest first):
1. **Project** — `.agents/best-practices/project/` from target repo
2. **Framework** — `shared/best-practices/frameworks/<name>/` from skills repo
3. **Language** — `shared/best-practices/languages/<name>/` from skills repo
4. **Default** — `shared/best-practices/default/` from skills repo

Load the [coder.md | reviewer.md] from each level that exists.
Rules from higher-precedence profiles override lower ones on conflict.

### Step 5: Report resolution

State which profiles were loaded and any fallbacks:
- "Loaded: project (from .agents/best-practices/project/coder.md),
   fastapi (frameworks/fastapi/coder.md), python (languages/python/coder.md),
   default (default/coder.md)"
- "Fallback: no project-level profile found, using framework as highest precedence"

If NO profiles were found at all, report that and use default only.
</resolve_best_practice_profiles>
```

## Reviewer Pipeline Architecture

### Component: sk-review-orchestrator.md (~150 lines)

Replaces `sk-code-reviewer.md`. Thin coordination layer.

**Responsibilities:**
1. Resolve review scope (git diff, changed files)
2. Detect stack (language, framework, tooling)
3. Collect changed files with full content
4. Resolve best-practice profiles (using resolver instructions)
5. Discover and install analysis tools (existing `check_and_install_tools` logic)
6. Run static analysis — dedicated step BEFORE parallel passes
7. Dispatch 4 parallel review subagents
8. Aggregate findings, deduplicate, assign severity
9. Render verdict (APPROVED / CHANGES REQUESTED)

**Does NOT contain:** checklist items, language-specific rules, SOLID/KISS/DRY details, security checklists. Those live in subagents and profiles.

### Component: review-steps/ (4 subagent files)

Each file is a focused review pass loaded via Task tool as a subagent.

#### review-steps/security.md
- Input validation, auth checks, data protection
- SQL injection, XSS, path traversal, command injection
- Hardcoded credentials (BLOCKER)
- Dependency vulnerability findings from static analysis
- Severity: security findings are BLOCKER by default

#### review-steps/architecture.md
- SOLID principles check
- KISS/DRY/YAGNI check
- Layer boundaries, dependency direction
- Design pattern appropriateness
- Module structure, file size
- Check against design.md if present
- Performance considerations (N+1, blocking async, memory leaks)

#### review-steps/stack-rules.md
- Loads the resolved `reviewer.md` profile for the detected stack
- Applies language-specific checklist (Python PEP, TS strict null, Go error handling)
- Runs through framework-specific anti-patterns
- Import organization check
- Error handling patterns (narrow try-catch, specific exceptions)
- Declarative vs imperative style
- Test coverage check

#### review-steps/instruction-quality.md
- Only runs for agent instruction repositories (detect by presence of `workflow/agents/` or `AGENTS.md` in repo root)
- AI slop detection: blank lines at file top, excessive comments, trivial wrappers, copy-paste
- Python packaging anti-patterns (sys.path hacks, from src. imports)
- Module organization (utilities portable, no parallel configs)
- File/method size limits
- If not an agent instruction repo: skip entirely, report "not applicable"

### Pipeline Flow

```
Orchestrator
  |
  |--> resolve scope, detect stack, collect files
  |--> resolve profiles (resolver instructions)
  |--> discover + install tools
  |--> run_static_analysis (sequential, before parallel)
  |
  |--> PARALLEL:
  |      security.md
  |      architecture.md
  |      stack-rules.md (with resolved reviewer.md profile)
  |      instruction-quality.md (conditional)
  |
  |--> aggregate: merge findings, deduplicate, set severity
  |--> render verdict
```

### Severity Mapping (stays in orchestrator)

The orchestrator owns the severity mapping table. Subagents report raw findings with suggested severity. The orchestrator normalizes using the existing mapping table (moved from current reviewer).

## Integration Points

### sk-developer.md Changes
- Remove `<coding_guidelines>` section (lines 211-602, ~390 lines)
- Add resolver instructions block
- Add step: "resolve and load coder.md profiles before implementation"
- Remaining content: role, philosophy, TDD discipline, execution flow, guardrails (~280 lines)

### sk-tester.md Changes
- Extract repeated test scaffolding patterns into shared reference (light cleanup)
- No profile loading needed — tester works from requirements, not stack rules
- Reduce verbosity in existing sections

### sk-team-feature/SKILL.md Changes
- Update agent table: `sk-code-reviewer` -> `sk-review-orchestrator`
- Update Task tool invocation for code review phase
- No other changes needed

### sk-team-quick/SKILL.md Changes
- Same agent reference update as sk-team-feature

### utilities/sk-code-review/SKILL.md Changes
- Update to spawn `sk-review-orchestrator` instead of `sk-code-reviewer`
- Simplify the prompt (orchestrator handles its own step ordering)

### Adapter Updates
- `adapters/codex/` — update skill-template.md if it references reviewer
- `adapters/cursor/` — update .cursorrules.template if it references reviewer
- `adapters/claude-code/` — update README if it references reviewer
- `adapters/kimi/` — update README if it references reviewer
- AGENTS.md — update agent descriptions

## Migration Path

1. Create `shared/best-practices/` with all profiles (no existing files affected)
2. Create `workflow/agents/review-steps/` subagent files (no existing files affected)
3. Create `workflow/agents/sk-review-orchestrator.md` (new file)
4. Update `sk-developer.md` — extract coding guidelines, add resolver
5. Update skill files to reference new orchestrator
6. Delete `workflow/agents/sk-code-reviewer.md` (replaced by orchestrator + steps)
7. Update adapters and AGENTS.md

Steps 1-3 are additive-only. Steps 4-6 are the breaking changes. Step 7 is documentation cleanup.

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Subagent dispatch overhead slows review | Keep to 4 parallel passes; orchestrator handles lightweight setup only |
| Profile content drifts from actual best practices | Add source links in each profile; plan periodic refresh |
| Resolver instructions too complex for agents to follow reliably | Keep resolver to 5 concrete steps; test with real repos |
| Go and Gin profiles weaker without local reference project | Base on official docs; mark as v1 for future refinement |
| Removing coding guidelines from developer breaks behavior | Extract verbatim first, then clean up; verify developer still loads profiles |
| Existing adapter users see broken references | Update all adapters in same phase as agent rename |

## Testing Strategy

This is an agent instruction repo — there is no executable test suite. Verification is manual:

1. **Profile completeness**: each profile covers the checklist items currently in the monolithic reviewer for that language
2. **Resolver correctness**: test against deli-check-backend (should resolve: project + fastapi + python + default)
3. **Orchestrator flow**: run `/sk-code-review` against a real project, verify all 4 subagents are dispatched
4. **No regression**: verify existing review quality is preserved by comparing review output before/after on a sample diff
5. **Slop check**: verify all refactored files are shorter, denser, and contain no filler

## Security Considerations

No new security surfaces. Profile files are static markdown read at agent invocation time. No secrets, no network calls, no code execution beyond existing tool invocations.

## Performance Considerations

- Parallel subagent dispatch should reduce wall-clock review time vs sequential monolith
- Profile loading adds minor overhead (reading 2-4 small markdown files) but reduces total prompt size
- Static analysis step runs once before parallel passes, not duplicated per subagent
