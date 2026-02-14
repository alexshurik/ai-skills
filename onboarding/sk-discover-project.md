---
name: sk-discover-project
version: 1.1.0
description: Discover project structure, stack, domains, and API surface for quick onboarding
argument-hint: "[optional: quick|full]"
license: MIT
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Write
  - Task
---

# Discover Project Structure

Generate `.claude/docs/project-map.md` with comprehensive project overview for quick onboarding.

## Output Modes

- **`quick`** - Simple overview: tech stack table, domain list, key files
- **`full`** (default) - Comprehensive GambleMate-style overview with user stories, domain deep dives

## Process

### 1. Pre-flight Check
- Verify project root exists
- Check for existing `.claude/docs/project-map.md`
- Create `.claude/docs/` directory if needed

### 2. Run Parallel Explorers

Launch these 7 explorers in parallel using Task tool with `subagent_type=Explore`:

---

**Explorer 1: Purpose & Mission**

Find and analyze:
- `README.md` - look for project description, taglines, mission statement
- `package.json` description field (Node.js)
- `pyproject.toml` description field (Python)
- Main docs folder for overview docs
- App name and domain context

Extract:
- One-sentence mission statement
- Target audience
- Key value proposition
- Problem being solved
- **Key Business Outcomes** (3 items):
  - What value the platform delivers
  - What problems it solves for operators/users
  - Competitive advantage or efficiency gain

---

**Explorer 2: User Roles & Stories**

Find authentication/authorization system:
- Look for: `auth/`, `permissions/`, `roles/`, `rbac/`
- Find role enums, user types, permission matrices
- Check middleware for role checks
- Look for admin vs user vs operator patterns

For each role discovered:
- Map role to available API endpoints (by auth requirements)
- Infer user stories from what actions they can perform
- Format as: "I, as a {role}: can {action}"

Common role patterns to detect:
- Anonymous/Guest - unauthenticated access
- User/Member - basic authenticated user
- Admin/Operator - elevated privileges
- System/Service - internal service accounts

---

**Explorer 3: Enhanced Tech Stack**

Gather comprehensive stack information:

**Frontend:**
- Framework: React, Vue, Angular, Next.js, Nuxt, Svelte
- UI Library: Tailwind, MUI, Chakra, shadcn/ui, Ant Design
- State Management: Redux, Zustand, Jotai, Pinia, Context
- Animations: Framer Motion, GSAP, CSS animations
- Realtime: WebSocket, Socket.io, Pusher, Ably
- Forms: React Hook Form, Formik, Zod
- Testing: Jest, Vitest, Playwright, Cypress

**Backend:**
- Framework: FastAPI, Django, Express, NestJS, Gin, Echo
- API Style: REST, GraphQL, tRPC, gRPC
- ORM/DB: Prisma, TypeORM, SQLAlchemy, Django ORM, GORM
- Database: PostgreSQL, MySQL, MongoDB, SQLite, Redis
- Queue/Jobs: Celery, Bull, BullMQ, Sidekiq, temporal
- Cache: Redis, Memcached, in-memory
- Auth Strategy: JWT, Session, OAuth2, API Keys

**DevOps:**
- Containerization: Docker, docker-compose
- CI/CD: GitHub Actions, GitLab CI, Jenkins
- Deployment: Vercel, Railway, AWS, GCP, Kubernetes

---

**Explorer 4: Domain Deep Dive**

For each domain folder discovered (e.g., `src/domains/`, `app/`, `modules/`):

1. **Identify Domain Purpose**
   - Read models/entities to understand data
   - Read services to understand operations
   - Summarize in one sentence

2. **Extract User Stories**
   - From API endpoints: what actions are available?
   - From permissions: who can do what?
   - Format as bullet points

3. **Map Frontend Routes**
   - Find pages/routes for this domain
   - Extract path, component name, layout

4. **Map API Endpoints**
   - Find all routes for this domain
   - Extract: method, path, auth requirement
   - Note key request/response schemas

5. **Find Realtime Endpoints**
   - Look for Socket.IO namespaces and handlers
   - WebSocket upgrade endpoints
   - Server-Sent Events (SSE) endpoints
   - Patterns: `socket.on()`, `io.of()`, `/socket`, `/ws`, `/events`

6. **List Service Files**
   - Core business logic files
   - External integrations
   - Background jobs

---

**Explorer 5: Directory Structure**

Generate annotated directory tree:
- Top 2-3 levels of project structure
- Purpose annotation for each major folder
- Identify entry points and configuration

Focus on folders that matter:
- `src/` or `app/` - main application code
- `lib/` or `utils/` - shared utilities
- `config/` or `settings/` - configuration
- `tests/` or `__tests__/` - test files
- `docs/` - documentation
- `scripts/` - build/deployment scripts

---

**Explorer 6: External Integrations**

Find external service integrations:
- API clients to third-party services
- Webhook handlers (`/api/integrations/*`, `/api/webhooks/*`)
- SDK usage (Stripe, Twilio, AWS, SendGrid, etc.)
- AI/ML integrations (OpenAI, Anthropic, Cohere, etc.)
- Blockchain/Web3 integrations (ethers.js, web3.js, viem)
- KYC/Identity providers
- Payment processors
- Email/SMS services
- Cloud storage (S3, GCS, Cloudinary)

For each integration:
- Provider name
- What it's used for
- Key files/endpoints

---

**Explorer 7: Operations & Monitoring**

Find operational infrastructure:
- Health check endpoints (`/api/health`, `/health`, `/healthz`, `/ready`)
- Background workers and queues (Bull, BullMQ, Celery workers)
- Cron jobs or scheduled tasks
- Operational scripts (`scripts/*`, `bin/*`)
- Runbooks and ops documentation (`docs/*runbook*`, `docs/*operations*`, `docs/*deploy*`)
- Monitoring setup (Sentry, DataDog, NewRelic, Prometheus)
- Logging configuration

---

### 3. Generate Project Map

For **quick** mode, use simplified format:

```markdown
# Project Map: {project-name}

> Auto-generated by `/sk-discover-project` on [DATE]

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | [detected] |
| Framework | [detected] |
| Database | [detected] |
| Testing | [detected] |

## Domains

- **{domain}/** - {one-line purpose}

## Key Files

| Path | Purpose |
|------|---------|
| [path] | Entry point |
| [path] | Configuration |
```

---

For **full** mode (default), use GambleMate format:

```markdown
# {Project Name} Platform Overview

> Auto-generated by `/sk-discover-project` on [DATE]
> Re-run after major structural changes.

## 1. Purpose

{Mission statement paragraph describing:
- What the platform does
- Who it serves (target audience)
- Key value proposition
- Core problem being solved}

**Key Business Outcomes:**
- {Outcome 1 - what value the platform delivers}
- {Outcome 2 - what problems it solves for operators/users}
- {Outcome 3 - competitive advantage or efficiency gain}

## 2. Solution Components

### 2.1 {Client Application}
- Built with {framework}
- Hosts {surfaces/pages}
- Communicates via {protocols}

### 2.2 {Admin Console} (if exists)
- Lives under {path}
- Used by {roles}
- Features: {key features}

### 2.3 {Backend Platform}
- {Framework} exposes {API styles}
- Data layer: {DB + ORM}
- Background: {queue/workers}

## 3. Primary Users and Stories

### {Role 1 Name}
I, as a {role}:
- can {action 1 - inferred from API/permissions}
- can {action 2}
- can {action 3}

### {Role 2 Name}
I, as a {role}:
- can {action 1}
- can {action 2}

### {Role 3 Name}
...

## 4. Technology Stack

### Frontend
- **Framework:** {e.g., Next.js 14 with App Router}
- **UI:** {e.g., Tailwind CSS + shadcn/ui components}
- **State:** {e.g., Zustand for global state, React Query for server state}
- **Realtime:** {e.g., Socket.io for live updates}
- **Auth:** {e.g., NextAuth.js with JWT strategy}
- **Testing:** {e.g., Vitest + Playwright}

### Backend
- **Framework:** {e.g., NestJS with REST API}
- **Database:** {e.g., PostgreSQL via Prisma ORM}
- **Queue:** {e.g., BullMQ for background jobs}
- **Cache:** {e.g., Redis for session and query caching}
- **Auth:** {e.g., Passport.js with JWT + refresh tokens}

### DevOps
- **Container:** {e.g., Docker + docker-compose for local dev}
- **CI/CD:** {e.g., GitHub Actions for testing and deployment}
- **Hosting:** {e.g., Vercel (frontend) + Railway (backend)}

## 5. External Integrations

| Integration | Purpose | Location |
|-------------|---------|----------|
| {Provider} | {What it does} | `{file/endpoint path}` |
| Blockchain RPC | On-chain deposits/withdrawals | `src/lib/onchain/` |
| KYC Provider | Identity verification | `/api/integrations/kyc/` |
| SMTP/Email | Transactional emails | `src/lib/notifications/email.ts` |
| AI/GenAI | Content generation | `src/ai/` |

## 6. Domain Deep Dive

### 6.1 {Domain Name}

**Purpose:** {One sentence describing this domain's responsibility}

**Stories:**
- {User role} can {action}
- {User role} can {action}

**Frontend:**
- `/path` - {description}
- `/path` - {description}

**API:**
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/path | {role} | Description |
| POST | /api/path | {role} | Description |

**Realtime:** (if applicable)
- `GET /api/{domain}/socket` - {namespace description}
- `socket.on('{event}')` - {what it does}

**Services:**
- `{service-file}` — {purpose}
- `{service-file}` — {purpose}

### 6.2 {Domain Name}

**Purpose:** ...

**Stories:** ...

**Frontend:** ...

**API:** ...

**Realtime:** ...

**Services:** ...

{Continue for each domain...}

## 7. Monitoring & Operations

### Health Checks
- `GET /api/health` - {what it checks}
- `GET /api/ready` - {readiness probe}

### Background Workers
- `{worker/service}` - {purpose}
- `{queue processor}` - {what jobs it handles}

### Operational Scripts
| Script | Purpose |
|--------|---------|
| `scripts/{name}` | {what it does} |
| `scripts/{name}` | {what it does} |

### Ops Documentation
- `docs/operations-runbook.md`
- `docs/{other-ops-docs}`

## 8. Directory Navigator

```
{project-name}/
├── src/                    # Main application source
│   ├── app/                # Next.js app router pages
│   ├── components/         # Shared React components
│   ├── lib/                # Utility functions and helpers
│   ├── domains/            # Feature domains
│   │   ├── auth/           # Authentication & authorization
│   │   ├── users/          # User management
│   │   └── {domain}/       # {Domain purpose}
│   └── services/           # External service integrations
├── prisma/                 # Database schema and migrations
├── tests/                  # Test files
├── scripts/                # Build and deployment scripts
└── docs/                   # Documentation
```

## 9. Quick Navigation Guide

| Task | Location | Notes |
|------|----------|-------|
| Add new page | `src/app/{route}/page.tsx` | Follow existing page patterns |
| Add API endpoint | `src/domains/{domain}/api/` | Add to domain's router |
| Add business logic | `src/domains/{domain}/services/` | Keep controllers thin |
| Add database model | `prisma/schema.prisma` | Run `prisma generate` after |
| Add shared component | `src/components/` | Check for existing similar components |
| Add integration | `src/services/` or `src/lib/integrations/` | Follow existing patterns |
| Run tests | `{test command}` | |
| Start dev server | `{dev command}` | |
```

---

### 4. Summary Output

After generating the file, display:
- Project name and detected type
- Tech stack summary (framework + database)
- Number of domains discovered
- Number of user roles identified
- Number of API endpoints mapped
- Number of external integrations found
- Path to generated file
- Suggestion to run `/sk-explore-codebase` for navigation rules

## Edge Cases

### Monorepo Detection
If multiple `package.json` or framework markers found:
- Identify monorepo structure (apps/, packages/)
- Generate overview for each app/package
- Note shared dependencies

### No Clear Domain Structure
If no domain folders found:
- Fall back to file-type organization
- Group by: routes, components, services, models
- Note flat structure in output

### Limited Permissions/Auth
If no auth system detected:
- Note "No authentication system detected"
- Skip user roles section or mark as "Single user type"
- Still infer capabilities from available endpoints

### No External Integrations
If no third-party integrations detected:
- Note "No external integrations detected"
- Or mark section as "Self-contained application"

### No Operations Infrastructure
If no ops tooling found:
- Note "No operational infrastructure detected"
- Suggest adding health checks and monitoring

## Comparison with explore-codebase

| Aspect | explore-codebase | discover-project |
|--------|------------------|------------------|
| **Goal** | Prevent duplication | Understand structure |
| **Style** | Prescriptive ("check X before Y") | Descriptive ("here's what exists") |
| **When** | While working on project | First time onboarding |
| **Output** | `.claude/rules/codebase-navigation.md` | `.claude/docs/project-map.md` |

Both complement each other - use `/sk-onboard` to run both.
