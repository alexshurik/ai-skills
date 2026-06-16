# Gin Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Gin-specific review checklist. Applied on top of the Go reviewer profile.

## Gin Review Checklist

### Router Setup (Security-Critical)
- [ ] `SetTrustedProxies` pins the proxy set to real infra (or `nil` when there is no proxy) — Gin trusts ALL proxies by default, making `c.ClientIP()` (and any rate-limit/allowlist/audit keyed on it) spoofable via `X-Forwarded-For`
- [ ] `gin.SetMode(gin.ReleaseMode)` (or `GIN_MODE=release`) in production
- [ ] Security headers middleware sets `X-Content-Type-Options: nosniff`, `X-Frame-Options`, `Strict-Transport-Security`, and a scoped `Content-Security-Policy`
- [ ] CORS via `gin-contrib/cors` lists explicit origins; `AllowAllOrigins`/origin-echo is **not** combined with `AllowCredentials: true`

### Middleware Ordering
- [ ] `gin.Recovery()` is registered first (before all other middleware)
- [ ] Logging middleware runs before auth (so failed auth attempts are logged)
- [ ] Auth middleware runs before any business-specific middleware
- [ ] CORS middleware runs before auth (preflight requests must not require auth)
- [ ] Route groups have appropriate middleware -- public routes do not carry auth middleware

### Authorization
- [ ] Authentication (identity) and authorization (permission) are distinct -- `Auth` alone does not gate privileged routes
- [ ] Privileged/admin route groups carry a role or scope check (`RequireRole`), not just `Auth`
- [ ] Handlers that read/mutate a resource by ID verify the caller owns (or is privileged for) that resource
- [ ] Ownership/role checks happen server-side -- the request is never trusted to scope itself
- [ ] Authorization failures return 403 (not 401, not 404-masking unless intentional)

### Rate Limiting and Body Size
- [ ] Request bodies are capped with `http.MaxBytesReader` (and/or `MaxMultipartMemory` for uploads)
- [ ] Public and authentication endpoints are rate limited per IP or per API key
- [ ] Rate limiter evicts/bounds idle keys so it cannot grow without limit
- [ ] Rate-limit key built on `c.ClientIP()` relies on a correct `SetTrustedProxies` (see Router Setup) — otherwise the key is spoofable

### Per-Request Timeout and Streaming
- [ ] Handlers derive a deadline from `c.Request.Context()` (or use `http.TimeoutHandler`), not just server `WriteTimeout`
- [ ] Cancellation propagates into service and database calls (context passed down)
- [ ] Streaming/SSE/long-download routes are excluded from `WriteTimeout` / `http.TimeoutHandler` (which would truncate them)
- [ ] Streaming uses `c.Stream` / `c.SSEvent` and stops on client disconnect (`c.Request.Context().Done()` / `c.Stream` returning `false`) so disconnected clients don't leak goroutines

### Structured Logging
- [ ] Logging is structured (`log/slog` or equivalent), not unstructured text or `fmt.Printf`
- [ ] Every request log line includes the request ID for cross-service correlation
- [ ] `Recovery` logs the panic stack with the request ID before returning a clean 500

### Binding and Validation
- [ ] Every `ShouldBind*` / `ShouldBindJSON` call checks the returned error
- [ ] `ShouldBind*` used instead of `Bind*` (avoids auto-abort with 400)
- [ ] Request structs use `binding:"required"` for mandatory fields
- [ ] Validation errors return structured details (not raw validator output)
- [ ] Slice/map fields needing per-element rules use `dive` (a bare tag validates only the container; elements pass unchecked without it)
- [ ] Custom validators registered for domain-specific rules that struct tags cannot express
- [ ] No raw `map[string]interface{}` for request or response bodies -- typed structs required

### Context Safety
- [ ] `*gin.Context` is never stored in a struct or passed to a goroutine
- [ ] Background work extracts needed values from context before spawning goroutines
- [ ] Background goroutines use `context.Background()` or `context.WithTimeout()`, not the request context
- [ ] `c.Set` / `c.Get` usage is wrapped in typed helpers (no raw string keys in handlers)

### Error Responses
- [ ] All error paths return the same `ErrorResponse` JSON structure (code, message, details)
- [ ] No error path returns a plain string or unstructured body
- [ ] Status codes match HTTP semantics (401 for auth, 403 for authz, 404 for missing, 409 for conflict)
- [ ] 500 responses never expose stack traces, SQL queries, or internal error messages
- [ ] `c.AbortWithStatusJSON` used in middleware (not `c.JSON` followed by `return`)

### Handler Structure
- [ ] Handlers are thin: parse input, call service, format output
- [ ] No business logic (calculations, conditional workflows, data transformations) in handlers
- [ ] Service methods receive `context.Context` (from `c.Request.Context()`), not `*gin.Context`
- [ ] Response mapping uses dedicated functions or methods (`toResponse`, `fromDomain`)

### Route Organization
- [ ] Routes grouped by API version and domain (`v1.Group("/users")`)
- [ ] No route definitions scattered across unrelated files
- [ ] Path parameters use nouns (`:id`, `:slug`), not verbs

### Graceful Shutdown
- [ ] Production code uses `http.Server` with explicit `Shutdown()`, not `router.Run()`
- [ ] `signal.NotifyContext` or `signal.Notify` handles SIGINT/SIGTERM
- [ ] Shutdown timeout is set (server does not wait forever for connections to drain)
- [ ] `ReadTimeout`, `WriteTimeout`, `IdleTimeout` are configured on the server

### File Uploads
- [ ] File size validated before processing (reject oversized uploads early)
- [ ] File handle closed with `defer` after `FormFile`
- [ ] Content type validated by sniffing bytes (`http.DetectContentType`), not by trusting the header or extension
- [ ] Reader is rewound (`Seek(0, io.SeekStart)`) after sniffing, before storage

### Testing
- [ ] Handlers have tests using `httptest.NewRecorder` + `router.ServeHTTP` (full chain) or `gin.CreateTestContext` (isolated)
- [ ] Tests assert status code and the structured response body
- [ ] `gin.SetMode(gin.TestMode)` is set in tests

## Tooling

Run these in CI and locally before review. Findings from these tools are not optional -- they map to the severities below.

```bash
# Static analysis + style + common bugs (govet, staticcheck, errcheck, ineffassign, etc.)
golangci-lint run ./...

# Security scanner -- backs the auth, injection, and info-disclosure checks above
gosec ./...

# CI-friendly machine output
gosec -fmt=sarif -out=gosec.sarif ./...
```

Enable `gosec` inside `golangci-lint` via `.golangci.yml` so a single `golangci-lint run` covers both:

```yaml
linters:
  enable:
    - gosec
    - errcheck
    - staticcheck
    - govet
    - bodyclose   # flags unclosed http.Response.Body / file handles
```

### Tool-Finding Severity Mapping

| Tool Finding | Severity | Notes |
|---|---|---|
| `gosec` G104 (unhandled error) on a `ShouldBind*`/DB call | **BLOCKER** | Maps to ignored-binding-error and silent failure rules |
| `gosec` G107/G201/G202 (SSRF, SQL string-format) | **BLOCKER** | Injection / request forgery reaching backend |
| `gosec` G401/G402/G404 (weak crypto, TLS verify off, weak rand for tokens) | **BLOCKER** | Auth/transport security broken |
| `gosec` G101 (hardcoded credential) | **BLOCKER** | Secret in source |
| `gosec` G304 (file path from user input) | **MAJOR** | Path traversal on uploads/downloads -- validate and sanitize |
| `errcheck` unchecked error on a write/IO path | **MAJOR** | Silent failure, often a dropped response or commit |
| `bodyclose` unclosed body/file handle | **MAJOR** | Resource leak (mirrors `defer file.Close()` rule) |
| `staticcheck` / `govet` correctness finding | **MAJOR** | Real bug (nil deref, format string, lost cancel) |
| `golangci-lint` style-only finding (gofmt, naming) | **MINOR** | Consistency, no runtime impact |

## Anti-Patterns with Severity

| Anti-Pattern | Severity | Why |
|---|---|---|
| `ShouldBind*` error ignored | **BLOCKER** | Unvalidated input reaches business logic |
| `*gin.Context` passed to goroutine | **BLOCKER** | Context invalid after handler returns -- race condition or panic |
| Business logic in handler | **MAJOR** | Untestable without HTTP, violates separation of concerns |
| `router.Run()` in production | **MAJOR** | No graceful shutdown -- in-flight requests dropped |
| Plain string error response | **MAJOR** | Breaks API contract, clients cannot parse errors reliably |
| `Bind*` instead of `ShouldBind*` | **MAJOR** | Auto-aborts with 400 and content-type-dependent response format |
| No `ReadTimeout` / `WriteTimeout` on server | **MAJOR** | Slow clients can exhaust server resources |
| Missing auth middleware on protected route group | **BLOCKER** | Unauthenticated access to protected resources |
| `c.ClientIP()` used for rate-limit/allowlist/audit without `SetTrustedProxies` configured | **MAJOR** | Default trusts all proxies — client IP spoofable via `X-Forwarded-For`, defeating the control |
| `AllowAllOrigins`/origin-echo combined with `AllowCredentials: true` | **MAJOR** | Invalid per CORS spec; exposes credentialed endpoints to any site |
| No security headers middleware (nosniff / frame-options / HSTS / CSP) | **MINOR** | Missing baseline hardening against MIME-sniffing, clickjacking, downgrade |
| Per-element slice/map validation missing `dive` | **MAJOR** | Element constraints silently ignored — invalid items reach business logic |
| Debug mode (`gin.SetMode` not Release) in production | **MINOR** | Verbose route logging, not production-tuned |
| Streaming/SSE handler that ignores client disconnect | **MAJOR** | Leaks a goroutine per dropped client |
| `c.JSON` without `return` in middleware | **MAJOR** | Handler continues executing after error response |
| Raw string keys for `c.Set` / `c.Get` | **MINOR** | Typo-prone, no type safety |
| `map[string]interface{}` as response body | **MINOR** | No compile-time safety, inconsistent API shape |
| File upload without size limit | **MAJOR** | Denial of service via oversized uploads |
| 500 response leaking internal details | **BLOCKER** | Information disclosure -- exposes internals to attackers |
| Mutating a resource by ID without an ownership check | **BLOCKER** | IDOR/BOLA -- any authenticated user can act on others' resources |
| Privileged route gated by `Auth` only, no role/scope check | **BLOCKER** | Authenticated but unauthorized access (privilege escalation) |
| Upload content type taken from header/extension, not sniffed | **MAJOR** | Spoofed type smuggles disallowed/malicious files past validation |
| No `http.MaxBytesReader` / body size cap | **MAJOR** | Memory-exhaustion DoS via large request bodies |
| No per-IP / per-key rate limiting on public or auth endpoints | **MAJOR** | Brute-force and request-flood DoS |
| No per-request timeout (relying on `WriteTimeout` alone) | **MAJOR** | Slow upstream calls pile up; no cancellation into service/DB |
| Streaming/SSE behind `http.TimeoutHandler` or short `WriteTimeout` | **MAJOR** | Long responses silently truncated mid-stream |
| Unstructured request logging / no request ID in logs | **MINOR** | Requests cannot be correlated across services during incidents |
| Handlers with no `httptest` coverage | **MAJOR** | Behavior and error paths unverified, regressions ship silently |
