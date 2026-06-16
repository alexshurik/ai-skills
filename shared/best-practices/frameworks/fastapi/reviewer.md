# FastAPI Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
FastAPI-specific review checklist and tooling. Applied on top of the Python language reviewer profile.

## FastAPI Review Checklist

### Endpoint Definitions
- [ ] Endpoints doing async I/O use `async def`; sync `def` is acceptable for sync-only libraries (FastAPI runs it in a threadpool). The real defect is a *blocking* call inside an `async def` — not the use of sync `def` itself
- [ ] Every endpoint has a response model (return annotation or `response_model=`)
- [ ] Correct HTTP status codes (`201` for creation, `204` for deletion, `202` for async jobs)
- [ ] Request bodies use Pydantic models (no raw `dict` inputs)
- [ ] Path/query parameters have type annotations

### Schemas (Pydantic v2)
- [ ] Validators use `@field_validator` / `@model_validator` — not deprecated `@validator` / `@root_validator`
- [ ] Serialization uses `model_dump()` / `model_dump_json()` — not `.dict()` / `.json()`
- [ ] ORM reads use `model_validate()` + `ConfigDict(from_attributes=True)` — not `.from_orm()`
- [ ] Field constraints use `Annotated[T, Field(...)]` (e.g. `Annotated[int, Field(gt=0)]`)
- [ ] Endpoints return a field-limited response schema, not an ORM/internal model (a returned ORM row leaks every column — `password_hash`, `is_admin`); `response_model_exclude_none/unset` is shaping, not a substitute

### Dependency Injection
- [ ] Per-request resources (DB session/transaction) provided by a `yield` dependency (`async with ...: yield s`) with guaranteed teardown; commit-on-success / rollback-on-exception when wrapping a transaction
- [ ] No `HTTPException` raised from the post-`yield` teardown (response already started — raise from the endpoint instead)
- [ ] Services injected via `Depends()` (not instantiated inside endpoints)
- [ ] DB sessions injected via `Depends()` (not created manually)
- [ ] Auth/current-user injected via `Depends()` (not extracted manually from headers)
- [ ] No global mutable service instances without proper lifecycle management
- [ ] Dependencies declared with `Annotated[T, Depends(...)]`, not the `= Depends(...)` default-value form; same for `Query`/`Path`/`Body`/`Header` metadata

### Authorization
- [ ] Default-deny: endpoints require explicit authorization, not just authentication
- [ ] Every resource accessed by a user-supplied ID has a server-side ownership/permission check (reads *and* writes) — guards against BOLA/IDOR. Prefer scoping the query (`WHERE owner_id = :user_id`) over loading then checking
- [ ] Non-owner access returns `404` (not `403`) where existence should not be revealed
- [ ] No blind binding of request body to ORM model (`Model(**body)`); request schemas exclude privileged/ownership fields (`role`, `is_admin`, `owner_id`, `tenant_id`) — guards against mass-assignment / privilege escalation
- [ ] Coarse-grained permissions enforced via a reusable `require_scopes` / `require_role` dependency (in addition to per-object checks)

### Architecture
- [ ] Business logic in service classes, not in endpoint functions
- [ ] Service classes use constructor DI for their own dependencies
- [ ] One router per domain, mounted in the main app
- [ ] Exception hierarchy: base app exception with status code mapping, domain exceptions inherit from it
- [ ] Global exception handler registered for base app exception

### Async Discipline
- [ ] No `time.sleep()` — use `asyncio.sleep()`
- [ ] No `requests` library — use `httpx.AsyncClient`
- [ ] No sync file I/O (`open().read()`) — use `aiofiles` or run in executor
- [ ] No sync database drivers in async context — use async drivers (asyncpg, motor, etc.)
- [ ] No CPU-bound work in async endpoints without `run_in_executor`

### Database Access
- [ ] No N+1 queries: relationships touched per row are eager-loaded (`selectinload` for collections, `joinedload` for many-to-one)
- [ ] No `await` in a loop over independent I/O where `asyncio.gather` applies (large fan-out bounded by a semaphore)
- [ ] No lazy-loaded relationships in async SQLAlchemy (raises outside an awaited context)

### Pagination
- [ ] List endpoints are bounded (limit/offset or cursor) with an enforced **max** page size — no unbounded "return the whole table" endpoints

### Application Lifespan
- [ ] App-scoped resources (DB pool, shared `httpx.AsyncClient`, ML models) managed via `lifespan=` async context manager
- [ ] No deprecated `@app.on_event("startup")` / `@app.on_event("shutdown")`
- [ ] Resources cleaned up after `yield` (pool closed, client `aclose()`d)

### Testing
- [ ] Tests use `TestClient` / `httpx.AsyncClient` (`ASGITransport`), not ad-hoc request mocking
- [ ] Dependencies (DB, auth, external clients) swapped via `app.dependency_overrides`, not monkeypatching internals
- [ ] Overrides cleared between tests; lifespan exercised (`with TestClient(app)`)

### Resilience and Limits
- [ ] Rate limiting applied to public/auth endpoints (e.g. `slowapi` or gateway-level)
- [ ] Request body size capped (proxy and/or middleware) — oversized bodies rejected with `413`
- [ ] Outbound clients have timeouts (`httpx.AsyncClient(timeout=...)`)

### Observability
- [ ] Structured (JSON) logging, not `print` / bare string logs
- [ ] Per-request correlation/request ID generated or propagated and attached to logs
- [ ] `/health` (liveness) and `/ready` (readiness, checks critical deps) endpoints present; liveness stays cheap

### Settings and Configuration
- [ ] Settings use Pydantic `BaseSettings` (not raw `os.environ` reads scattered in code)
- [ ] Settings grouped by concern (database, auth, external services)
- [ ] Nested settings groups use `Field(default_factory=...)`, not instantiation at class-definition time (`x: Sub = Sub()`)
- [ ] Secrets come from environment variables (not hardcoded)
- [ ] `@cbv` class-based views flagged as external (`fastapi-utils`), not core FastAPI; an `APIRouter` + shared `Depends()` is the default

### Middleware and CORS
- [ ] Auth middleware registered before business-logic middleware
- [ ] CORS configured explicitly via `CORSMiddleware` (not `allow_origins=["*"]` in production)
- [ ] `allow_origins=["*"]` **not** combined with `allow_credentials=True` — Starlette silently drops the credentials header and auth cookies break

### Streaming, WebSockets, Validation, Background Work
- [ ] Incrementally-produced output uses `StreamingResponse` + async generator (SSE: `media_type="text/event-stream"`, `data: ...\n\n` frames); streaming routes excluded from any request timeout
- [ ] WebSocket endpoints authenticate on the handshake (no `Authorization` header flow), `accept()` then loop, and handle `WebSocketDisconnect` to release shared state
- [ ] `RequestValidationError` (422) handled if a consistent error envelope is required — Pydantic validation errors bypass the `BaseAppException` hierarchy
- [ ] `BackgroundTasks` used only for short best-effort in-process work; durable/retryable/long work uses a task queue (Celery/ARQ/Dramatiq), not `BackgroundTasks`

## ruff FAST Rule Set

Enable the `FAST` rule set in ruff for FastAPI-specific lint checks:

```toml
[lint]
select = [
    # ... other rule sets ...
    "FAST",  # FastAPI best practices
]
```

The `FAST` rule set catches common FastAPI mistakes including redundant response model annotations and other framework-specific anti-patterns.

## Anti-Patterns and Severity

| Finding | Severity |
|---------|----------|
| Blocking call inside `async def` endpoint | **BLOCKER** |
| `time.sleep()` in async code | **BLOCKER** |
| Sync `requests` call in async code | **BLOCKER** |
| Sync file I/O in async endpoint | **BLOCKER** |
| Sync DB driver in async context | **BLOCKER** |
| Endpoint mutating/returning a resource by user-supplied ID without an ownership check (BOLA/IDOR) | **BLOCKER** |
| Request body blind-bound to ORM model exposing privileged fields (`role`/`is_admin`/`owner_id`) (mass assignment) | **BLOCKER** |
| Returning an ORM/internal model instead of a field-limited response schema (leaks `password_hash` etc.) | **BLOCKER** |
| WebSocket endpoint that accepts without authenticating on the handshake | **BLOCKER** |
| `allow_origins=["*"]` with `allow_credentials=True` (credentials silently dropped) | **MAJOR** |
| `HTTPException` raised from post-`yield` dependency teardown (no effect on response) | **MAJOR** |
| Per-request transaction without rollback-on-exception in a `yield` dependency | **MAJOR** |
| `BackgroundTasks` used for durable/long work that needs a task queue | **MAJOR** |
| `RequestValidationError`/422 not handled where a consistent error envelope is required | **MINOR** |
| Raw `dict` as request/response (no Pydantic model) | **MAJOR** |
| Missing `response_model` / return annotation | **MAJOR** |
| Manual service instantiation instead of `Depends()` | **MAJOR** |
| Business logic in endpoint (not in service layer) | **MAJOR** |
| Missing exception hierarchy (bare `HTTPException` raises everywhere) | **MAJOR** |
| `allow_origins=["*"]` in production CORS | **MAJOR** |
| No global exception handler for app exceptions | **MAJOR** |
| Missing coarse-grained authz (no `require_scopes`/`require_role` on privileged endpoint) | **MAJOR** |
| Unbounded list endpoint (no pagination / max page size) — perf + DoS | **MAJOR** |
| N+1 queries (no eager loading) | **MAJOR** |
| `await` in a loop over independent I/O where `asyncio.gather` applies | **MAJOR** |
| App resources managed via deprecated `@app.on_event` instead of `lifespan=` | **MAJOR** |
| No rate limiting on public/auth endpoints | **MAJOR** |
| No request body size limit | **MAJOR** |
| Outbound client without a timeout | **MAJOR** |
| Pydantic v1 API in v2 codebase (`@validator`/`@root_validator`/`.dict()`/`.from_orm()`) | **MAJOR** |
| `= Depends(...)` default-value form instead of `Annotated[T, Depends(...)]` | **MINOR** |
| Nested `BaseSettings` instantiated at class-definition time instead of `default_factory` | **MINOR** |
| `@cbv` presented as core FastAPI (external `fastapi-utils` package) | **MINOR** |
| Missing `/health` or `/ready` endpoint | **MINOR** |
| Unstructured logging / no request-ID correlation | **MINOR** |
| Wrong HTTP status code (200 for creation, 200 for deletion) | **MINOR** |
| Missing tags on router | **MINOR** |
| Settings read via `os.environ` instead of `BaseSettings` | **MINOR** |
