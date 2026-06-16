# Research: Language-Specific Agent Instructions Refactor

## Executive Summary

**Research Question:** How should this repository evolve from large generic prompts into a modular, extensible workflow with stack-aware best practices, project overrides, and a more reliable review process?

**Key Finding:** The strongest pattern is to separate orchestration from policy. Keep workflow skills and review agents thin, move best-practice guidance into reusable profile files, and resolve guidance through an explicit precedence chain instead of embedding everything into one reviewer prompt.

**Recommended Approach:** Introduce a vendor-neutral best-practice registry in this repository, support project-level overrides from a canonical project directory, and refactor `sk-code-reviewer` into an orchestrator plus small, tool-focused review steps that can run in parallel where independent.

## Findings

### Option 1: Keep best practices embedded in large agent prompts

**Overview:** Continue storing language/framework/domain review logic directly inside `sk-code-reviewer` and other agent files.

**Pros:**
- Minimal initial refactor.
- No new file discovery or profile resolution system required.

**Cons:**
- The current reviewer is already a 1266-line monolith, which is the main source of context overload and skipped tool behavior.
- Guidance cannot be reused cleanly between coder and reviewer.
- Adding a new language or framework means editing a large prompt instead of adding a profile pack.
- Project-specific overrides remain ad hoc and vendor-specific.

**Best For:** Tiny repos with one stack and no plan to extend or share practices.

**Evidence:**
- Current local baseline: [workflow/agents/sk-code-reviewer.md](/Users/alex/Project/language-specific-agent-instructions-refactor-worktree/workflow/agents/sk-code-reviewer.md:1)
- Current prompt size baseline from local analysis:
  - `sk-code-reviewer`: 1266 lines
  - `sk-tester`: 758 lines
  - `sk-developer`: 672 lines
  - `sk-team-feature`: 545 lines

### Option 2: Store overrides only in platform-specific locations

**Overview:** Put project-specific best practices only in places such as `AGENTS.md`, `CLAUDE.md`, `.claude/rules/`, `.claude/agents/`, or Cursor rules, and let each adapter depend on its own ecosystem.

**Pros:**
- Aligns with how some platforms already work.
- Can leverage auto-loaded files such as `AGENTS.md`.
- Requires less adapter logic up front.

**Cons:**
- Locks the design to vendor-specific paths.
- Harder to keep Codex, Claude, Cursor, and Kimi in sync.
- Project guidance becomes fragmented across formats rather than shared as one source of truth.

**Best For:** Single-platform usage where cross-platform consistency is not important.

**Evidence:**
- OpenAI Codex recommends using `AGENTS.md` for durable repo guidance and reusing `code_review.md` via `AGENTS.md`: https://developers.openai.com/codex/learn/best-practices
- Anthropic documents project-level subagents in `.claude/agents/` checked into version control: https://code.claude.com/docs/en/sub-agents
- Real local reference already has project guidance in `CLAUDE.md`: [CLAUDE.md](/Users/alex/Project/deli-check/deli-check-backend/CLAUDE.md:1)

### Option 3: Use a vendor-neutral canonical profile registry with adapter compatibility

**Overview:** Store curated best practices in this repo as reusable profile files, and let workflow logic resolve profiles by precedence. Downstream projects can optionally provide their own project profiles in one canonical directory, while adapters may also read `AGENTS.md` / `CLAUDE.md` / vendor files for compatibility.

**Pros:**
- Keeps policy data separate from orchestration logic.
- Makes it easy to add new languages/frameworks without rewriting agents.
- Supports both coder and reviewer with the same taxonomy.
- Preserves cross-platform support while still integrating with platform-native files.
- Makes fallback explicit and inspectable.

**Cons:**
- Requires a resolver design and some adapter changes.
- Needs a documented convention for downstream project overrides.

**Best For:** This repository’s actual goal: a reusable, extensible workflow supporting multiple agent platforms and multiple stacks.

**Evidence:**
- OpenAI recommends durable reusable repo guidance in `AGENTS.md`, reusable skills for repeated workflows, and keeping skills scoped to one job: https://developers.openai.com/codex/learn/best-practices
- OpenAI prompt caching guidance favors stable static prefixes and variable content later, which reinforces separating stable policy files from per-task context: https://developers.openai.com/api/docs/guides/prompt-caching
- Anthropic subagent guidance recommends focused subagents with separate context, specific tool access, and independent permissions: https://code.claude.com/docs/en/sub-agents

## Comparison Matrix

| Criteria | Embedded prompt logic | Platform-specific only | Vendor-neutral registry |
|----------|-----------------------|------------------------|-------------------------|
| Context size | Worst | Medium | Best |
| Cross-platform support | Weak | Weak to medium | Best |
| Extensibility | Weak | Medium | Best |
| Project override clarity | Weak | Medium | Best |
| Reviewer reliability | Weak | Medium | Best |
| Migration effort | Best | Medium | Medium |
| Long-term maintainability | Weak | Medium | Best |

## Detailed Findings

### 1. Best practices for this kind of agent workflow

**OpenAI guidance**
- Codex best-practices docs recommend giving the agent explicit `Goal`, `Context`, `Constraints`, and `Done when` structure, storing durable repo guidance in `AGENTS.md`, turning repeated workflows into skills, and keeping each skill scoped to one job: https://developers.openai.com/codex/learn/best-practices
- The same page also recommends referencing review-specific guidance from `AGENTS.md`, which supports splitting generic repo guidance from dedicated review policy files: https://developers.openai.com/codex/learn/best-practices
- OpenAI prompt guidance recommends keeping tone/role guidance in system-level durable instructions and task-specific details in user messages; this supports smaller static instruction files plus dynamic task context: https://developers.openai.com/api/docs/guides/prompting
- OpenAI prompt caching docs state that cache hits depend on exact prefix matches and recommend placing static instructions and examples first, variable content later. For this repo, that is an argument for reusable stable profile files rather than repeated large inline prompts: https://developers.openai.com/api/docs/guides/prompt-caching
- The GPT-5.2 prompting guide emphasizes explicit verbosity constraints and notes that disciplined structure materially improves production-agent reliability: https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide

**Anthropic guidance**
- Anthropic’s Claude Code docs recommend subagents when side work would flood the main conversation with search results, logs, or file contents, and explicitly highlight separate context windows, focused system prompts, and restricted tool access: https://code.claude.com/docs/en/sub-agents
- Anthropic also recommends project-level subagents in `.claude/agents/` under version control, which supports the general pattern of checking agent behavior into the repo rather than keeping it ephemeral: https://code.claude.com/docs/en/sub-agents
- Anthropic prompt-engineering docs recommend clear, direct, detailed instructions with explicit workflow context and sequential steps: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct
- Anthropic also recommends XML tags to separate context, instructions, and examples for better structure and easier maintenance: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags

**Implication for this repo**
- Large generic instructions are the wrong abstraction.
- Stable guidance should live in reusable files.
- Orchestrators should coordinate narrow workers rather than embed every policy inline.
- Repeated prompt scaffolding should be extracted or standardized.

### 2. Local evidence from the current `skills` repo

**Current problem areas**
- The main slop source is the current reviewer monolith: [workflow/agents/sk-code-reviewer.md](/Users/alex/Project/language-specific-agent-instructions-refactor-worktree/workflow/agents/sk-code-reviewer.md:1)
- Approval scaffolding and workflow boilerplate are repeated across multiple agent files instead of reused as shared patterns.
- The repo has `shared/templates/` for artifacts but no first-class `shared/best-practices/` area, so best-practice logic is embedded in prompts instead of stored as reusable content.
- `utilities/sk-code-review/SKILL.md` is a thin wrapper, but it still delegates into the same oversized reviewer, so modularity is currently superficial: [utilities/sk-code-review/SKILL.md](/Users/alex/Project/language-specific-agent-instructions-refactor-worktree/utilities/sk-code-review/SKILL.md:1)

**Implication**
- The right refactor is architectural, not cosmetic.
- Splitting the reviewer into steps matters more than editing wording in place.

### 3. What local project references suggest

**Python / FastAPI**
- `deli-check-backend` already has strong project-specific AI guidance in [CLAUDE.md](/Users/alex/Project/deli-check/deli-check-backend/CLAUDE.md:1), including architecture patterns, code style, service DI, exception hierarchy, and concrete commands.
- `pyproject.toml` and `ruff.toml` show an opinionated Python/FastAPI stack with strict linting, explicit typing, async testing, and FastAPI-specific lint rules: [pyproject.toml](/Users/alex/Project/deli-check/deli-check-backend/pyproject.toml:1), [ruff.toml](/Users/alex/Project/deli-check/deli-check-backend/ruff.toml:1)
- This makes `deli-check-backend` a good reference for `python` and `fastapi` curated profiles.

**JavaScript / Vue**
- `deli-check-frontend` uses Vue 3 + TypeScript + Vite + Vue Query + Vitest + Playwright and has clear separation between API client, queries, composables, and UI components: [package.json](/Users/alex/Project/deli-check/deli-check-frontend/package.json:1), [client.ts](/Users/alex/Project/deli-check/deli-check-frontend/src/api/client.ts:1), [useBill.ts](/Users/alex/Project/deli-check/deli-check-frontend/src/queries/bill/useBill.ts:1)
- This is a strong local reference for `js` and `vue.js` profiles, although the frontend currently lacks its own explicit project guidance file.

**Ansible**
- `deli-check-infrastructure` uses a role-based Ansible layout with inventory, group vars, playbooks, and roles under an explicit `roles_path`, which aligns with official Ansible guidance: [ansible.cfg](/Users/alex/Project/deli-check/deli-check-infrastructure/ansible.cfg:1), [security role main.yml](/Users/alex/Project/deli-check/deli-check-infrastructure/ansible/roles/security/tasks/main.yml:1)
- The deployment playbook is readable but shell-heavy, so it is useful as a real project example but should be supplemented with official Ansible best practices rather than copied blindly: [deploy.yml](/Users/alex/Project/deli-check/deli-check-infrastructure/ansible/playbooks/cicd/deploy.yml:1)

**Terraform**
- No Terraform code was found in the provided `deli-check` references. Terraform guidance will need to come from official HashiCorp sources rather than local project examples.

### 4. Best practices for Ansible and Terraform profiles

**Ansible**
- Official Ansible best-practices docs recommend role-based organization, top-level playbooks separated by role, group-based inventory variables, and keeping playbooks/inventory in version control: https://docs.ansible.com/ansible/2.9/user_guide/playbooks_best_practices.html
- Ansible community docs recommend using roles as complexity grows and choosing reuse patterns intentionally: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse.html
- `ansible-lint` documentation highlights `fqcn`, complexity thresholds, syntax-check, and production/shared profiles, which are useful inputs for a dedicated Ansible reviewer step: https://docs.ansible.com/projects/lint/profiles/ and https://docs.ansible.com/projects/lint/rules/fqcn/

**Terraform**
- HashiCorp’s style guide recommends standard file naming, frequent `terraform validate`, readable comments only where needed, and third-party linting such as TFLint: https://developer.hashicorp.com/terraform/language/syntax/style
- HashiCorp recommends keeping module trees relatively flat and avoiding thin wrapper modules that add no real abstraction: https://developer.hashicorp.com/terraform/language/modules/develop
- HashiCorp also documents a standard module structure, which is a good basis for a Terraform profile pack and a reviewer checklist: https://developer.hashicorp.com/terraform/language/modules/develop/structure

### 5. Best place for project-specific best practices

There are two valid but competing patterns:

**Pattern A: Use platform-native files**
- `AGENTS.md` for Codex
- `CLAUDE.md` / `.claude/*` for Claude Code
- `.cursor/*` for Cursor

**Pattern B: Use one canonical project-owned directory**
- Example: `.agents/best-practices/`

**Recommendation**
- Use a canonical, vendor-neutral project directory as the source of truth:

```text
.agents/
  best-practices/
    index.yaml
    default/
      coder.md
      reviewer.md
    project/
      coder.md
      reviewer.md
    projects/
      backend/
        coder.md
        reviewer.md
      frontend/
        coder.md
        reviewer.md
      infra/
        coder.md
        reviewer.md
```

- Then add compatibility readers for platform-native files:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `.claude/rules/*.md`
  - `.cursor/rules/*`

**Why this is the best fit**
- This repository itself is cross-platform.
- A canonical directory avoids tying best-practice content to one vendor.
- Adapter-specific files can still be generated or referenced where beneficial.
- Monorepos become easier to support via `projects/<component>/`.

**Inference from sources**
- OpenAI’s `AGENTS.md` recommendation suggests durable repo-local guidance should exist.
- Anthropic’s `.claude/agents/` pattern suggests project-checked-in agent behavior is valuable.
- For this cross-platform repo, the logical synthesis is one canonical project directory plus compatibility adapters.

### 6. Reviewer decomposition that fits the evidence

**Recommended review pipeline**
1. `resolve_review_scope`
2. `detect_stack`
3. `collect_changed_files`
4. `resolve_best_practice_profiles`
5. `discover_tools`
6. `run_static_analysis`
7. Parallel review passes:
   - `review_security_and_correctness`
   - `review_architecture_and_maintainability`
   - `review_language_framework_rules`
   - `review_instruction_slop_and_structure`
8. `aggregate_findings`
9. `render_verdict`

**What can run in parallel**
- `detect_stack`, `collect_changed_files`, `resolve_best_practice_profiles`, and `discover_tools`
- Multiple analyzers after tool discovery
- Concern-based review passes over the same diff

**Why this matches external guidance**
- Anthropic recommends narrow subagents with limited tools and isolated context.
- OpenAI recommends scoped reusable skills rather than giant multi-job prompts.
- The current reviewer’s missed tools problem is most likely caused by overload of responsibilities, not lack of rules.

## Recommendations

### Primary Recommendation

Adopt a three-layer design:

1. **Policy layer**
   - New reusable profiles under `shared/best-practices/`
   - Separate taxonomy for `default`, `languages`, `frameworks`, and infrastructure/tooling stacks such as `ansible` and `terraform`
   - Prefer paired files like `coder.md` and `reviewer.md` inside each profile

2. **Resolver layer**
   - Explicit precedence: `project -> framework -> language -> default`
   - Canonical downstream override directory: `.agents/best-practices/`
   - Explicit reporting of which profile(s) were selected and when fallback occurred

3. **Execution layer**
   - Thin workflow skills and reviewer orchestrator
   - Narrow subagents/steps with constrained tools and smaller prompts
   - Parallelization only for truly independent phases

### If Primary Fails

If the full canonical-directory design feels too large for the first pass, the fallback is:
- introduce `shared/best-practices/` first,
- keep downstream overrides temporarily in `AGENTS.md` / `CLAUDE.md`,
- add canonical project directories in phase 2.

This is weaker but still meaningfully better than leaving policy embedded in prompts.

### Implementation Notes

- Create `shared/best-practices/index.yaml` for aliases and precedence metadata.
- Start with profiles:
  - `default`
  - `languages/python`
  - `languages/js`
  - `languages/go`
  - `frameworks/fastapi`
  - `frameworks/vue`
  - `frameworks/gin`
  - `tooling/ansible`
  - `tooling/terraform`
- Use `deli-check-backend` and `deli-check-frontend` as input references for curated profile authoring.
- Use `deli-check-infrastructure` as one input to the Ansible profile, but normalize it against official Ansible docs rather than copying its shell-heavy habits directly.
- Treat Terraform as official-docs-first because no local Terraform reference is present.
- Reduce prompt repetition by moving shared approval templates, artifact rules, and reusable wording into either:
  - shared partial files/templates, or
  - shorter standardized sections in orchestrator skills.

## Risks Identified

- **Risk 1: Over-designing the profile system.**
  Mitigation: start with one resolver, one manifest, and the requested initial profile set only.

- **Risk 2: Creating too many review subagents and paying orchestration overhead.**
  Mitigation: keep subagents aligned with responsibility boundaries, not every checklist item.

- **Risk 3: Vendor-neutral storage may drift from platform-native behavior.**
  Mitigation: document compatibility readers and keep adapter behavior explicit.

- **Risk 4: Curated profiles may fossilize.**
  Mitigation: version them, add source links, and plan periodic refreshes.

- **Risk 5: Terraform profile quality may be lower initially because no local reference project exists.**
  Mitigation: base v1 on official HashiCorp guidance and refine later from real project usage.

## Open Questions

- Should `coder` and `reviewer` profiles share one combined file per stack, or two separate files per stack?
- Should monorepo project overrides be path-based (`projects/backend`) or pattern-based in the manifest?
- Which existing skills should be reduced first after the reviewer: `sk-tester`, `sk-developer`, or `sk-team-feature`?
- Do you want adapters to generate/update `AGENTS.md` references automatically from the canonical profile registry?

## Sources

### Local project references
- [workflow/agents/sk-code-reviewer.md](/Users/alex/Project/language-specific-agent-instructions-refactor-worktree/workflow/agents/sk-code-reviewer.md:1) - current reviewer baseline
- [utilities/sk-code-review/SKILL.md](/Users/alex/Project/language-specific-agent-instructions-refactor-worktree/utilities/sk-code-review/SKILL.md:1) - current review entrypoint
- [CLAUDE.md](/Users/alex/Project/deli-check/deli-check-backend/CLAUDE.md:1) - project-specific backend guidance
- [pyproject.toml](/Users/alex/Project/deli-check/deli-check-backend/pyproject.toml:1) - backend stack reference
- [ruff.toml](/Users/alex/Project/deli-check/deli-check-backend/ruff.toml:1) - backend linting/style reference
- [package.json](/Users/alex/Project/deli-check/deli-check-frontend/package.json:1) - frontend stack reference
- [client.ts](/Users/alex/Project/deli-check/deli-check-frontend/src/api/client.ts:1) - frontend API client pattern
- [useBill.ts](/Users/alex/Project/deli-check/deli-check-frontend/src/queries/bill/useBill.ts:1) - frontend query/composable pattern
- [ansible.cfg](/Users/alex/Project/deli-check/deli-check-infrastructure/ansible.cfg:1) - infrastructure Ansible layout reference
- [deploy.yml](/Users/alex/Project/deli-check/deli-check-infrastructure/ansible/playbooks/cicd/deploy.yml:1) - infra deployment playbook reference
- [main.yml](/Users/alex/Project/deli-check/deli-check-infrastructure/ansible/roles/security/tasks/main.yml:1) - role decomposition reference

### Official external sources
- OpenAI Codex best practices: https://developers.openai.com/codex/learn/best-practices
- OpenAI prompting guide: https://developers.openai.com/api/docs/guides/prompting
- OpenAI prompt caching: https://developers.openai.com/api/docs/guides/prompt-caching
- OpenAI GPT-5.2 prompting guide: https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide
- OpenAI instruction hierarchy research: https://openai.com/index/the-instruction-hierarchy/
- Anthropic Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Anthropic prompt engineering, clear/direct prompting: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct
- Anthropic prompt engineering, XML tags: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags
- Ansible best practices: https://docs.ansible.com/ansible/2.9/user_guide/playbooks_best_practices.html
- Ansible reuse guidance: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse.html
- Ansible lint profiles: https://docs.ansible.com/projects/lint/profiles/
- Ansible lint FQCN rule: https://docs.ansible.com/projects/lint/rules/fqcn/
- Terraform style guide: https://developer.hashicorp.com/terraform/language/syntax/style
- Terraform module development: https://developer.hashicorp.com/terraform/language/modules/develop
- Terraform standard module structure: https://developer.hashicorp.com/terraform/language/modules/develop/structure
