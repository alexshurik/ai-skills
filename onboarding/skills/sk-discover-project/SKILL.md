---
name: sk-discover-project
version: 1.0.0
description: Discover project structure, stack, domains, and API surface for quick onboarding
license: MIT
platforms:
  codex: true
  cursor: true
  kimi: true
---

# /sk-discover-project - Project Discovery

<sk-discover-project>

Discover and document the project structure, technology stack, domains, and API surface. Creates `.claude/docs/project-map.md` for quick onboarding.

## What to Discover

### 1. Project Overview
- Project name and purpose
- Repository structure
- Key directories and their purposes

### 2. Technology Stack
- Programming languages
- Frameworks and libraries
- Build tools and package managers
- Database and infrastructure

### 3. Domains/Modules
- Business domains
- Feature modules
- Service boundaries

### 4. API Surface
- REST endpoints
- GraphQL schemas
- gRPC services
- WebSocket handlers

### 5. Key Files
- Configuration files
- Entry points
- Important documentation

## Output

Create `.claude/docs/project-map.md`:

```markdown
# Project Map: [Name]

## Overview
Brief description of what this project does.

## Tech Stack
- **Language:** 
- **Framework:** 
- **Database:** 
- **Key Libraries:** 

## Structure
```
[tree-like structure]
```

## Domains
| Domain | Description | Key Files |
|--------|-------------|-----------|

## API Surface
| Endpoint | Method | Description |
|----------|--------|-------------|

## Key Files
| File | Purpose |
|------|---------|
```

## Execution Steps

1. **Scan root directory** - Identify project type
2. **Read key config files** - package.json, pyproject.toml, etc.
3. **Explore src/ or equivalent** - Understand code organization
4. **Find API definitions** - routes, controllers, schemas
5. **Document findings** - Write to project-map.md

</sk-discover-project>
