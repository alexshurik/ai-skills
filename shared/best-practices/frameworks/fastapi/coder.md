# FastAPI Coder Profile

FastAPI-specific coding rules. Applied on top of the Python language profile.

## Endpoint Definitions

### Prefer async def

Prefer `async def` for endpoints performing async I/O. Sync `def` endpoints are safe (FastAPI runs them in a threadpool) but consume a thread per request, limiting concurrency under high load. Use `async def` with async libraries (httpx, asyncpg, aiofiles) for best throughput.

```python
# Good — async with async libraries
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> UserResponse:
    ...

# Acceptable — sync with sync-only libraries (runs in threadpool)
@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)) -> ReportResponse:
    ...
```

Blocking calls inside an `async def` are the real defect — see Async Discipline below for the canonical rule.

### Response Model on Every Endpoint

Declare `response_model` or a return type annotation on every endpoint. This enables automatic validation, serialization, and OpenAPI schema generation.

```python
# Good — return annotation serves as response model
@router.get("/users/{user_id}")
async def get_user(user_id: int) -> UserResponse:
    ...

# Good — explicit response_model
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(body: CreateUserRequest) -> UserResponse:
    ...
```

Use semantically correct status codes: `201` for creation, `204` for deletion (no body), `202` for accepted async jobs.

### `response_model` Is a Security Boundary, Not Just a Schema

Returning an ORM object or an internal model directly serializes **every** attribute — including `password_hash`, `is_admin`, internal tokens. The response model is the response-side mirror of mass-assignment: declare a response schema that lists only the fields the client may see; never return the ORM row.

```python
# Bad — leaks every column, including password_hash
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: DbSession) -> User:  # ORM model
    return await db.get(User, user_id)

# Good — response schema exposes only safe fields
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: DbSession) -> UserResponse:
    ...
```

Tune serialization with `response_model_exclude_none=True` (drop nulls) and `response_model_exclude_unset=True` (drop fields the server never set) — but these are output shaping, not a substitute for a field-limited schema.

## Request and Response Schemas

Use Pydantic models for all request bodies and response shapes. Never accept or return raw dicts.

```python
# Good
class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

# Bad — unvalidated dict
@router.post("/users")
async def create_user(body: dict) -> dict:
    ...
```

### Pydantic v2 Idioms

FastAPI in 2026 uses Pydantic v2. Use the v2 APIs, not their deprecated v1 equivalents:

- Validators: `@field_validator` and `@model_validator`, not `@validator` / `@root_validator`.
- Serialization: `model_dump()` / `model_dump_json()`, not `.dict()` / `.json()`.
- Construction from objects: `model_validate()`, not `.from_orm()`. Set `model_config = ConfigDict(from_attributes=True)` to read ORM attributes.
- Constraints: prefer `Annotated[int, Field(gt=0)]` over bare `Field` defaults, so the constraint travels with the type and is reusable.

```python
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class CreateUserRequest(BaseModel):
    name: str
    age: Annotated[int, Field(gt=0, le=150)]
    password: str
    password_confirm: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "CreateUserRequest":
        if self.password != self.password_confirm:
            raise ValueError("passwords do not match")
        return self

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

payload = user_response.model_dump()  # not .dict()
```

## Dependency Injection

### Dependencies with `yield` (Per-Request Resource Lifecycle)

The canonical way to provide a per-request resource (DB session, transaction, file handle) is a dependency that `yield`s it. Code before `yield` runs on the way in; code after runs on the way out — including when the endpoint raised — so teardown is guaranteed. This is what `Depends(get_db)` resolves to.

```python
async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:  # async with handles close()
        yield session                              # injected into the endpoint
        # after yield: runs on success AND on exception (the CM's __aexit__)

DbSession = Annotated[AsyncSession, Depends(get_db)]
```

Semantics to respect:

- Teardown after `yield` always runs, but you **cannot** raise `HTTPException` (or other response-shaping exceptions) from it — the response has already started. Raise from the endpoint instead, and let teardown only clean up.
- An exception from the endpoint propagates *through* the `yield` point, so a surrounding `async with` (or `try/finally`) sees it and can roll back. Commit on success, roll back on exception:

```python
async def get_db_tx() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Use Depends() for All Dependencies

Inject services, database sessions, auth, and config through `Depends()`. Never instantiate dependencies manually inside endpoints.

```python
# Good
@router.get("/items")
async def list_items(
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user),
) -> list[ItemResponse]:
    return await service.list_for_user(current_user.id)

# Bad — manual instantiation
@router.get("/items")
async def list_items() -> list[ItemResponse]:
    service = ItemService(get_db_session())
    ...
```

### Prefer Annotated Dependencies

Declare dependencies with `Annotated[T, Depends(...)]` rather than the `= Depends(...)` default-value form. The `Annotated` form is reusable (define a type alias once, share it across endpoints), keeps the parameter free of a runtime default (avoiding the footgun where the function is callable outside FastAPI with a `Depends` object as its argument), and is the form the FastAPI docs now recommend. The same applies to `Query`, `Path`, `Body`, `Header`, and `Form` metadata.

```python
from typing import Annotated
from fastapi import Depends, Query, Path

# Good — reusable type alias
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/items/{item_id}")
async def get_item(
    item_id: Annotated[int, Path(gt=0)],
    db: DbSession,
    current_user: CurrentUser,
    limit: Annotated[int, Query(le=100)] = 20,
) -> ItemResponse:
    ...

# Avoid — default-value form
@router.get("/items/{item_id}")
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)) -> ItemResponse:
    ...
```

### Service Layer Pattern

Thin handlers / business logic in a service layer is a generic rule — see the Python profile. The FastAPI-specific part: wire services as dependencies (constructor-inject their own deps) so handlers receive them via `Depends()` and tests can override them.

```python
async def get_order_service(db: DbSession, payment: PaymentClientDep) -> OrderService:
    return OrderService(db, payment)
```

## Authorization

Authentication answers *who you are*; authorization answers *what you may do*. Authenticating a request is not enough — every endpoint must enforce what the authenticated principal is allowed to access.

### Default-Deny and Object-Ownership Checks

Default to deny. Any resource fetched by a user-supplied ID must be checked against the caller's ownership or permissions on the server — never trust that the client only requests its own IDs. Missing this check is Broken Object-Level Authorization (BOLA / IDOR), the top API security risk: an attacker simply increments an ID and reads or mutates another tenant's data.

```python
# Bad — authenticated, but no ownership check: any logged-in user can read any order
@router.get("/orders/{order_id}")
async def get_order(order_id: int, db: DbSession, user: CurrentUser) -> OrderResponse:
    return await db.get(Order, order_id)  # BOLA: returns other users' orders

# Good — server-side ownership enforcement
@router.get("/orders/{order_id}")
async def get_order(order_id: int, db: DbSession, user: CurrentUser) -> OrderResponse:
    order = await db.get(Order, order_id)
    if order is None or order.owner_id != user.id:
        raise NotFoundException()  # 404, not 403 — don't reveal existence to non-owners
    return order
```

Do the ownership check for reads *and* writes (GET, PATCH, PUT, DELETE). Prefer scoping the query itself (`WHERE owner_id = :user_id`) so the row is never loaded for the wrong user.

### Field-Level Write Authorization

Never blind-bind a request body to an ORM model. A user-controlled payload must not be able to set privileged or ownership fields like `role`, `is_admin`, `owner_id`, or `tenant_id` (mass-assignment / privilege escalation). Use a request schema that contains only client-writable fields, and set server-controlled fields explicitly.

```python
# Bad — mass assignment: client can send {"is_admin": true} and escalate
@router.post("/users")
async def create_user(body: dict, db: DbSession) -> UserResponse:
    user = User(**body)  # binds is_admin, role, owner_id straight from the request
    ...

# Good — schema excludes privileged fields; server sets them
class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    # no role / is_admin / owner_id

@router.post("/users")
async def create_user(body: CreateUserRequest, db: DbSession, actor: CurrentUser) -> UserResponse:
    user = User(name=body.name, email=body.email, role="member", owner_id=actor.id)
    ...
```

### Reusable Scope / Role Dependencies

Express coarse-grained permissions as a reusable dependency that runs before the handler. Default-deny inside it. (This complements — does not replace — the per-object ownership check above.)

```python
from typing import Annotated
from fastapi import Depends

def require_scopes(*required: str):
    async def checker(user: CurrentUser) -> User:
        if not set(required).issubset(user.scopes):
            raise ForbiddenException()  # 403
        return user
    return checker

def require_role(role: str):
    async def checker(user: CurrentUser) -> User:
        if user.role != role:
            raise ForbiddenException()
        return user
    return checker

# Usage — dependency enforces the scope/role
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    _admin: Annotated[User, Depends(require_role("admin"))],
    db: DbSession,
) -> None:
    ...

@router.post("/reports")
async def create_report(
    body: ReportRequest,
    _user: Annotated[User, Depends(require_scopes("reports:write"))],
) -> ReportResponse:
    ...
```

## Exception Hierarchy

Define a base application exception that maps to HTTP responses. Domain exceptions inherit from it.

```python
# Base exceptions
class BaseAppException(Exception):
    status_code: int = 500
    detail: str = "Internal server error"

class BadRequestException(BaseAppException):
    status_code: int = 400

class NotFoundException(BaseAppException):
    status_code: int = 404

class UnprocessableEntityException(BaseAppException):
    status_code: int = 422

# Domain exceptions
class OrderNotFoundError(NotFoundException):
    detail = "Order not found"

class InsufficientInventoryError(UnprocessableEntityException):
    detail = "Not enough items in stock"
```

Register a global exception handler:

```python
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
```

## Settings Organization

Use Pydantic `BaseSettings` grouped by concern. Access settings through a single root object.

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    url: str
    pool_size: int = 5
    model_config = SettingsConfigDict(env_prefix="DB_")

class AuthSettings(BaseSettings):
    secret_key: str
    token_ttl_seconds: int = 3600
    model_config = SettingsConfigDict(env_prefix="AUTH_")

class Settings(BaseSettings):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)

settings = Settings()
```

Use `default_factory` for nested settings groups rather than instantiating at class-definition time (`database: DatabaseSettings = DatabaseSettings()`). A bare `DatabaseSettings()` runs at import, reading the environment once when the class is defined — it cannot be re-read per-instance and makes test overrides and lazy env loading harder. `default_factory` defers construction to instantiation. Build the root `Settings()` once and inject it via a cached dependency (`@lru_cache`) so tests can override it.

## Application Lifespan

Manage resources whose lifetime spans the whole application — the DB connection pool, a shared `httpx.AsyncClient`, ML models, caches — with a `lifespan` async context manager passed to `FastAPI(lifespan=...)`. Do **not** use `@app.on_event("startup")` / `@app.on_event("shutdown")`; those are deprecated. Code before `yield` runs at startup; code after runs at shutdown, even on error. Stash long-lived objects on `app.state` and expose them through dependencies.

```python
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.db_pool = await create_pool(settings.database.url)
    app.state.http = httpx.AsyncClient(timeout=10.0)
    app.state.model = load_model()
    yield
    # shutdown — runs on exit, including on error
    await app.state.http.aclose()
    await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)

# Bad — deprecated event hooks
@app.on_event("startup")
async def startup() -> None:
    ...
```

## Router Organization

One `APIRouter` per domain with a `prefix` and `tags`, mounted in the main app via `app.include_router(...)`. Keep each router file focused on a single domain.

## Class-Based Views (optional, external)

Group related endpoints into a class when they share dependencies or operate on the same resource. Note: `@cbv` is **not** part of core FastAPI — it comes from the third-party `fastapi-utils` (or `fastapi-restful`) package. It is optional; idiomatic FastAPI groups endpoints with an `APIRouter` plus shared `Depends()`. Only reach for `@cbv` if you have a real need to share instance state across handlers, and accept the extra dependency.

```python
from fastapi_utils.cbv import cbv  # external package, not core FastAPI

@cbv(router)
class UserViewSet:
    service: UserService = Depends(get_user_service)

    @router.get("/{user_id}")
    async def get_user(self, user_id: int) -> UserResponse:
        return await self.service.get(user_id)

    @router.post("/", status_code=status.HTTP_201_CREATED)
    async def create_user(self, body: CreateUserRequest) -> UserResponse:
        return await self.service.create(body)
```

## Async Discipline

Never call blocking operations inside async endpoints or services:

```python
# Bad — blocks event loop
import time
import requests

async def slow_endpoint():
    time.sleep(5)                          # use asyncio.sleep
    response = requests.get("https://...")  # use httpx.AsyncClient
    data = open("large.csv").read()         # use aiofiles

# Good
import asyncio
import httpx
import aiofiles

async def fast_endpoint():
    await asyncio.sleep(5)
    async with httpx.AsyncClient() as client:
        response = await client.get("https://...")
    async with aiofiles.open("large.csv") as f:
        data = await f.read()
```

## Database Access Patterns

### Avoid N+1 Queries — Eager Load

When you load a collection and then touch a relationship per row, you trigger one query per row (N+1). With SQLAlchemy, eager-load the relationship in the initial query (`selectinload` for collections, `joinedload` for many-to-one). With async SQLAlchemy this is also a correctness issue: lazy loading raises outside an awaited context.

```python
# Bad — N+1: one query per order to load items
orders = (await db.scalars(select(Order))).all()
for order in orders:
    total = sum(item.price for item in order.items)  # lazy load per order

# Good — eager load in one round trip
from sqlalchemy.orm import selectinload
orders = (await db.scalars(select(Order).options(selectinload(Order.items)))).all()
```

### Don't await in a loop when calls are independent

Serial `await` over independent I/O is a generic async issue — see the Python profile (`asyncio.gather`, semaphore-bounded fan-out). It matters here because list/detail endpoints commonly loop over IDs and fetch each sequentially.

## Pagination

List endpoints must be bounded. Returning an entire table is both a performance problem and a DoS vector. Use limit/offset or cursor pagination, enforce a maximum page size, and return total/next-cursor metadata.

```python
from typing import Annotated
from fastapi import Query

@router.get("/items")
async def list_items(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedItems:
    rows = (await db.scalars(select(Item).limit(limit).offset(offset))).all()
    total = await db.scalar(select(func.count()).select_from(Item))
    return PaginatedItems(items=rows, total=total, limit=limit, offset=offset)

# Bad — unbounded
@router.get("/items")
async def list_items(db: DbSession) -> list[ItemResponse]:
    return (await db.scalars(select(Item))).all()  # whole table
```

## Testing

FastAPI's killer testing feature is `app.dependency_overrides`: swap any dependency (DB session, auth, external clients) for a fake without monkeypatching. Test through `TestClient` (sync) or `httpx.AsyncClient` with `ASGITransport` (async).

```python
from fastapi.testclient import TestClient

def fake_current_user() -> User:
    return User(id=1, role="admin", scopes={"reports:write"})

app.dependency_overrides[get_current_user] = fake_current_user

def test_create_report() -> None:
    with TestClient(app) as client:  # `with` runs the lifespan
        resp = client.post("/reports", json={"title": "Q2"})
    assert resp.status_code == 201
    app.dependency_overrides.clear()

# Async client for async-native tests
import httpx
from httpx import ASGITransport

async def test_list_items() -> None:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/items?limit=10")
    assert resp.status_code == 200
```

Override the DB dependency to point at a transactional test database/session, and clear overrides between tests (a fixture is cleanest).

## Rate Limiting and Request Size Limits

Protect endpoints from abuse and resource exhaustion:

- Apply rate limiting (e.g. `slowapi`, or an API-gateway/reverse-proxy limit) on public and auth endpoints.
- Cap request body size so a client can't exhaust memory with a huge upload. Enforce it at the proxy (e.g. nginx `client_max_body_size`) and/or in middleware that checks `Content-Length` and rejects oversized bodies with `413`.
- Set timeouts on all outbound clients (`httpx.AsyncClient(timeout=...)`) so a slow upstream can't pin a worker.

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest) -> TokenResponse:
    ...
```

## Observability

- Use structured (JSON) logging, not `print` or bare string logs.
- Attach a per-request correlation/request ID (generate one if absent, propagate inbound `X-Request-ID`) via middleware and include it in every log line.
- Expose a `/health` liveness endpoint and a `/ready` readiness endpoint that checks critical dependencies (DB, cache) so orchestrators don't route traffic before the app can serve it. Keep liveness cheap; do dependency checks in readiness.

```python
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/ready")
async def ready(db: DbSession) -> dict[str, str]:
    await db.execute(text("SELECT 1"))  # fail if DB unreachable -> 503
    return {"status": "ready"}
```

## Background Tasks

Use the `BackgroundTasks` parameter for fire-and-forget work that should not block the response.

```python
@router.post("/reports", status_code=status.HTTP_202_ACCEPTED)
async def request_report(
    body: ReportRequest,
    background_tasks: BackgroundTasks,
    service: ReportService = Depends(get_report_service),
) -> ReportAccepted:
    report_id = await service.create_pending(body)
    background_tasks.add_task(service.generate, report_id)
    return ReportAccepted(report_id=report_id)
```

`BackgroundTasks` runs **in-process, after the response, in the same worker** — tasks die if the worker restarts or crashes, and they share its event loop. Use it only for short, best-effort work (send an email, bump a counter). For anything durable, retryable, or long-running, use a real task queue (Celery, ARQ, Dramatiq); `BackgroundTasks` is not a substitute.

## Streaming Responses (SSE)

For incrementally-produced output (LLM token streams, large exports, progress events) return a `StreamingResponse` driven by an async generator instead of buffering the whole body. For Server-Sent Events set `media_type="text/event-stream"` and emit `data: ...\n\n` frames. Disable any per-request timeout / `WriteTimeout` on these routes — they will truncate the stream.

```python
from fastapi.responses import StreamingResponse

@router.get("/events")
async def events() -> StreamingResponse:
    async def gen() -> AsyncIterator[str]:
        async for chunk in produce():
            yield f"data: {chunk}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
```

## WebSockets

Use `@app.websocket` for bidirectional connections. Authenticate **on the handshake** (query param / cookie / subprotocol — there is no `Authorization` header flow before accept), `accept()`, then run a receive/send loop. Handle `WebSocketDisconnect` to clean up shared state (e.g. a connection registry); the `HTTPException` hierarchy does not apply once the socket is open.

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def ws(websocket: WebSocket, token: str) -> None:
    user = await authenticate(token)
    if user is None:
        await websocket.close(code=1008)  # policy violation — reject before accept loop
        return
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(handle(user, msg))
    except WebSocketDisconnect:
        registry.remove(websocket)  # client gone — release resources
```

## CORS

Configure CORS explicitly with `CORSMiddleware`. List exact origins in production — never `allow_origins=["*"]` for a credentialed API. The spec forbids wildcard origin with credentials: Starlette **silently** refuses to send `Access-Control-Allow-Credentials` when `allow_origins=["*"]` and `allow_credentials=True`, so auth cookies break with no error.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # explicit; not ["*"] with credentials
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Validation Errors (422)

Pydantic request-validation failures raise `RequestValidationError`, which FastAPI returns as `422` through its **own** handler — they do **not** flow through your `BaseAppException` hierarchy. If you need a consistent error envelope across the API, register a handler for `RequestValidationError` too.

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "VALIDATION_ERROR", "errors": exc.errors()})
```

## Middleware Ordering

Register middleware in the correct order. Middleware executes top-to-bottom on request, bottom-to-top on response. Auth must run before business-logic middleware; CORS is registered too (see CORS above).
