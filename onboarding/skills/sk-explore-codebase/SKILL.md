---
name: sk-explore-codebase
version: 1.0.0
description: Explore codebase and generate check-before-create navigation rules
license: MIT
platforms:
  codex: true
  cursor: true
  kimi: true
---

# /sk-explore-codebase - Codebase Navigation Rules

<sk-explore-codebase>

Analyze the codebase to generate navigation rules that help AI agents understand where to find existing code before creating new files. Creates `.claude/rules/codebase-navigation.md`.

## Purpose

Create rules that answer:
- "Where do I put new components?"
- "What naming convention should I use?"
- "Where are similar features implemented?"
- "What patterns should I follow?"

## What to Analyze

### 1. Directory Conventions
- Where components live
- Where tests live
- Where utilities/helpers live
- Where types/interfaces live

### 2. Naming Patterns
- File naming (kebab-case, PascalCase, etc.)
- Function naming conventions
- Variable naming patterns
- Test file naming

### 3. Module Organization
- How features are grouped
- How shared code is organized
- Import/export patterns
- Barrel files usage

### 4. Check-Before-Create Rules
For each file type, document:
- Where to look for existing implementations
- Common locations to check
- Similar patterns to follow

## Output

Create `.claude/rules/codebase-navigation.md`:

```markdown
# Codebase Navigation Rules

## Quick Reference
| If you need to... | Check these locations first |
|-------------------|----------------------------|
| Add a component   | `src/components/`, `src/features/*/components/` |
| Add a utility     | `src/utils/`, `src/shared/` |
| Add a test        | Mirror the source structure in `tests/` |

## Naming Conventions

### Files
- Components: `PascalCase.tsx`
- Utilities: `kebab-case.ts`
- Tests: `*.test.ts` or `*.spec.ts`

### Code
- Functions: camelCase
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE

## Directory Structure
```
[observed structure with notes]
```

## Common Patterns

### Pattern 1: Feature-Based Organization
Description of how features are organized...

### Pattern 2: Shared Resources
Description of shared code organization...

## Check-Before-Create

### Before creating a new component:
1. Search in `src/components/`
2. Check `src/features/*/components/`
3. Look for similar patterns

### Before creating a new utility:
1. Search in `src/utils/`
2. Check `src/shared/`
3. Verify not already in lodash/ramda
```

## Execution Steps

1. **Analyze root structure** - Understand top-level organization
2. **Explore src/ or main code dir** - Find patterns
3. **Check existing files** - Identify naming conventions
4. **Look for configs** - eslint, prettier, etc. for style rules
5. **Document patterns** - Write to codebase-navigation.md

</sk-explore-codebase>
