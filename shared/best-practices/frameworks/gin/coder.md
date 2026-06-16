# Gin Coder Profile

Gin-specific coding rules. Applied on top of the Go language profile.

## Router Setup: Trusted Proxies and Release Mode

### Set Trusted Proxies (security-critical)

By default Gin trusts **all** proxies, so `c.ClientIP()` blindly believes the `X-Forwarded-For` / `X-Real-IP` headers — an attacker sets them to any value. Every IP-based control built on `c.ClientIP()` (rate limiter, audit logs, allowlists) is then trivially spoofable. Always pin the trusted proxy set to your actual infrastructure (or disable proxy trust entirely if there is no proxy).

```go
r := gin.New()

// Trust only the known reverse-proxy / load-balancer CIDRs; ClientIP() now
// resolves the real client through XFF only from these hops.
if err := r.SetTrustedProxies([]string{"10.0.0.0/8"}); err != nil {
    log.Fatalf("trusted proxies: %v", err)
}

// No proxy in front? Don't trust any forwarding headers at all.
r.SetTrustedProxies(nil)
```

### Release Mode in Production

Run `gin.SetMode(gin.ReleaseMode)` (or set `GIN_MODE=release`) outside dev/test. Debug mode logs every route and a startup warning, and is not tuned for production.

```go
gin.SetMode(gin.ReleaseMode)
```

## Middleware Registration Order

Register middleware in this order -- recovery must be first so panics in later middleware are caught.

```go
router := gin.New()

router.Use(gin.Recovery())          // 1. panic recovery -- always first
router.Use(middleware.RequestID())   // 2. request ID for tracing
router.Use(middleware.Logger())      // 3. logging (uses request ID)
router.Use(middleware.SecurityHeaders()) // 4. security response headers
router.Use(middleware.CORS())            // 5. CORS (must precede auth — preflight is unauthenticated)
router.Use(middleware.Auth())            // 6. authentication
// Business-specific middleware goes last
```

## Security Headers

Set hardening response headers on every response via middleware. At minimum: `X-Content-Type-Options: nosniff` (stop MIME sniffing), `X-Frame-Options: DENY` (clickjacking), `Strict-Transport-Security` (force HTTPS), and a `Content-Security-Policy` scoped to what the app actually loads.

```go
func SecurityHeaders() gin.HandlerFunc {
    return func(c *gin.Context) {
        h := c.Writer.Header()
        h.Set("X-Content-Type-Options", "nosniff")
        h.Set("X-Frame-Options", "DENY")
        h.Set("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
        h.Set("Content-Security-Policy", "default-src 'self'")
        c.Next()
    }
}
```

## CORS

Use `gin-contrib/cors` and enumerate the exact allowed origins. `AllowAllOrigins: true` (or echoing the request origin) combined with `AllowCredentials: true` is invalid per the CORS spec and exposes credentialed endpoints to any site — never pair them.

```go
import "github.com/gin-contrib/cors"

r.Use(cors.New(cors.Config{
    AllowOrigins:     []string{"https://app.example.com"}, // explicit, not "*"
    AllowMethods:     []string{"GET", "POST", "PUT", "DELETE"},
    AllowHeaders:     []string{"Authorization", "Content-Type"},
    AllowCredentials: true, // requires explicit origins — not AllowAllOrigins
    MaxAge:           12 * time.Hour,
}))
```

## Route Grouping

Group routes by API version and domain. Each group gets its own middleware chain.

```go
v1 := router.Group("/api/v1")
{
    users := v1.Group("/users")
    users.Use(middleware.Auth())
    {
        users.GET("", handler.ListUsers)
        users.POST("", handler.CreateUser)
        users.GET("/:id", handler.GetUser)
    }

    public := v1.Group("/health")
    {
        public.GET("", handler.HealthCheck)
    }
}
```

## Request and Response Structs

Define typed structs for every endpoint. Never use `map[string]interface{}` for request or response bodies.

```go
type CreateUserRequest struct {
    Name  string `json:"name"  binding:"required,min=1,max=100"`
    Email string `json:"email" binding:"required,email"`
    Role  string `json:"role"  binding:"required,oneof=admin user guest"`
}

type UserResponse struct {
    ID    string `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}
```

## Binding and Validation

Always use `ShouldBind*` (not `Bind*`) -- the `Should` variants do not auto-abort, giving you control over the error response.

```go
func CreateUser(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, ErrorResponse{
            Code:    "VALIDATION_ERROR",
            Message: "Invalid request body",
            Details: formatValidationErrors(err),
        })
        return
    }
    // proceed with validated req
}
```

### Validating Slice and Map Elements (`dive`)

A `binding` tag on a slice/map validates the *container*, not its elements. Add `dive` to descend into each element and apply the rules after it — without `dive`, per-element constraints are silently ignored and invalid items pass through.

```go
type BulkCreateRequest struct {
    // required,min=1 applies to the slice; dive applies email/required to each item
    Emails []string          `json:"emails" binding:"required,min=1,dive,required,email"`
    Tags   map[string]string `json:"tags"   binding:"dive,keys,required,endkeys,max=50"`
}
```

### Custom Validators

Register custom validators at startup for complex rules that struct tags cannot express.

```go
if v, ok := binding.Validator.Engine().(*validator.Validate); ok {
    v.RegisterValidation("iso_currency", validateISOCurrency)
}

type PaymentRequest struct {
    Amount   int64  `json:"amount"   binding:"required,gt=0"`
    Currency string `json:"currency" binding:"required,iso_currency"`
}
```

## Consistent Error Responses

Use a single error response struct across the entire API. Return it from every error path.

```go
type ErrorResponse struct {
    Code    string      `json:"code"`
    Message string      `json:"message"`
    Details interface{} `json:"details,omitempty"`
}

func notFound(c *gin.Context, resource string, id string) {
    c.JSON(http.StatusNotFound, ErrorResponse{
        Code:    "NOT_FOUND",
        Message: fmt.Sprintf("%s %s not found", resource, id),
    })
}
```

Use semantically correct status codes (`201` create, `204` delete, `401` vs `403`, `409` conflict, `422` unprocessable, `500` never leaking internals) — generic HTTP semantics, not Gin-specific.

## Context Usage

### Passing Data Through Middleware

Use `c.Set` / `c.Get` for values that middleware needs to pass to handlers. Use typed helper functions to avoid stringly-typed access.

```go
const userContextKey = "authenticated_user"

func SetCurrentUser(c *gin.Context, user *User) {
    c.Set(userContextKey, user)
}

func GetCurrentUser(c *gin.Context) (*User, bool) {
    val, exists := c.Get(userContextKey)
    if !exists {
        return nil, false
    }
    user, ok := val.(*User)
    return user, ok
}
```

### Context Lifetime

Never store `*gin.Context` or pass it beyond the request lifecycle. If you need to spawn background work, extract values first.

```go
// Good -- extract what you need, use a fresh context
func CreateOrder(c *gin.Context) {
    userID := GetCurrentUserID(c)
    orderData := extractOrderData(c)

    go func() {
        ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()
        sendConfirmationEmail(ctx, userID, orderData)
    }()

    c.JSON(http.StatusCreated, orderData)
}

// Bad -- passing gin.Context to a goroutine
func CreateOrder(c *gin.Context) {
    go sendConfirmationEmail(c) // c is invalid after handler returns
}
```

## Handler Structure

Thin handlers (parse, delegate to a service, format) is a generic rule — see the Go profile. The Gin-specific part: pass `c.Request.Context()` (not `*gin.Context`) into the service so cancellation/deadline propagate, and map the domain result/error to an HTTP response in the handler.

```go
func (h *OrderHandler) Create(c *gin.Context) {
    var req CreateOrderRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, newValidationError(err))
        return
    }
    user, _ := GetCurrentUser(c)

    order, err := h.orderService.Create(c.Request.Context(), user.ID, req) // request ctx, not c
    if err != nil {
        handleServiceError(c, err)
        return
    }
    c.JSON(http.StatusCreated, toOrderResponse(order))
}
```

## Middleware Patterns

### Authentication Middleware

```go
func Auth(tokenService TokenService) gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, ErrorResponse{
                Code:    "UNAUTHORIZED",
                Message: "Missing authorization header",
            })
            return
        }

        user, err := tokenService.Validate(c.Request.Context(), token)
        if err != nil {
            c.AbortWithStatusJSON(http.StatusUnauthorized, ErrorResponse{
                Code:    "UNAUTHORIZED",
                Message: "Invalid token",
            })
            return
        }

        SetCurrentUser(c, user)
        c.Next()
    }
}
```

### Request ID Middleware

```go
func RequestID() gin.HandlerFunc {
    return func(c *gin.Context) {
        requestID := c.GetHeader("X-Request-ID")
        if requestID == "" {
            requestID = uuid.NewString()
        }
        c.Set("request_id", requestID)
        c.Header("X-Request-ID", requestID)
        c.Next()
    }
}
```

### Authorization Middleware

Authentication answers *who* the caller is; authorization answers *what* they may do. `Auth` only proves identity -- every mutating or sensitive route still needs a role/scope check, and any route that operates on a resource by ID needs an ownership check. Do not rely on the client to scope its own requests.

```go
// RequireRole gates a route group on one of the allowed roles.
func RequireRole(roles ...string) gin.HandlerFunc {
    allowed := make(map[string]struct{}, len(roles))
    for _, r := range roles {
        allowed[r] = struct{}{}
    }
    return func(c *gin.Context) {
        user, ok := GetCurrentUser(c)
        if !ok {
            c.AbortWithStatusJSON(http.StatusUnauthorized, ErrorResponse{
                Code: "UNAUTHORIZED", Message: "Authentication required",
            })
            return
        }
        if _, permitted := allowed[user.Role]; !permitted {
            c.AbortWithStatusJSON(http.StatusForbidden, ErrorResponse{
                Code: "FORBIDDEN", Message: "Insufficient privileges",
            })
            return
        }
        c.Next()
    }
}
```

Apply it per group, and enforce resource ownership inside the handler (or a resource-loading middleware) -- never trust that a matching ID belongs to the caller.

```go
admin := v1.Group("/admin")
admin.Use(middleware.Auth(tokenService), middleware.RequireRole("admin"))

// Ownership check: the authenticated user may only mutate their own order.
func (h *OrderHandler) Update(c *gin.Context) {
    user, _ := GetCurrentUser(c)

    order, err := h.orderService.Get(c.Request.Context(), c.Param("id"))
    if err != nil {
        handleServiceError(c, err)
        return
    }

    // Anti-IDOR/BOLA: reject access to a resource the caller does not own.
    if order.OwnerID != user.ID && user.Role != "admin" {
        c.AbortWithStatusJSON(http.StatusForbidden, ErrorResponse{
            Code: "FORBIDDEN", Message: "Not the owner of this resource",
        })
        return
    }
    // proceed with the mutation
}
```

### Request Body Size Limits and Rate Limiting

Cap request bodies globally and reject oversized payloads before they are buffered into memory. `MaxMultipartMemory` bounds in-memory multipart parsing; `http.MaxBytesReader` hard-caps the whole body (and makes `ShouldBind*` return an error past the limit).

```go
router.MaxMultipartMemory = 8 << 20 // 8 MiB held in memory; rest spills to temp files

func BodyLimit(maxBytes int64) gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Request.Body = http.MaxBytesReader(c.Writer, c.Request.Body, maxBytes)
        c.Next()
    }
}

router.Use(middleware.BodyLimit(1 << 20)) // 1 MiB default for JSON endpoints
```

Apply per-IP (or per-API-key) rate limiting on public and auth endpoints to blunt brute-force and DoS. Use `golang.org/x/time/rate` with a token bucket per key; evict idle keys to bound memory.

```go
func RateLimit(r rate.Limit, burst int) gin.HandlerFunc {
    var mu sync.Mutex
    buckets := make(map[string]*rate.Limiter)

    keyFor := func(c *gin.Context) string {
        if k := c.GetHeader("X-API-Key"); k != "" {
            return k
        }
        return c.ClientIP() // requires SetTrustedProxies to be configured correctly
    }

    return func(c *gin.Context) {
        key := keyFor(c)
        mu.Lock()
        lim, ok := buckets[key]
        if !ok {
            lim = rate.NewLimiter(r, burst)
            buckets[key] = lim
        }
        mu.Unlock()

        if !lim.Allow() {
            c.AbortWithStatusJSON(http.StatusTooManyRequests, ErrorResponse{
                Code: "RATE_LIMITED", Message: "Too many requests",
            })
            return
        }
        c.Next()
    }
}
```

### Per-Request Timeout

The server's `WriteTimeout` is a blunt connection-level cap, not a per-handler deadline -- and it will truncate legitimate long responses (streaming, SSE, large downloads). Derive a per-request deadline from `c.Request.Context()` so cancellation propagates into the service and database layers; for streaming endpoints, run them on a router without `WriteTimeout` (or use `http.ResponseController` to extend it) rather than fighting the global cap.

Two correct approaches — **do NOT hand-roll one that writes to `c` from a second goroutine**: `gin.Context` and its `ResponseWriter` are not safe for concurrent use, so running `c.Next()` in a goroutine while the parent writes a 504 is a data race / double-write panic.

```go
// 1. Propagate a deadline so cancellation reaches the service/DB layer (always safe)
func Deadline(d time.Duration) gin.HandlerFunc {
    return func(c *gin.Context) {
        ctx, cancel := context.WithTimeout(c.Request.Context(), d)
        defer cancel()
        c.Request = c.Request.WithContext(ctx)
        c.Next() // handlers select on ctx.Done() and stop work themselves
    }
}

// 2. To actually abort the response on timeout, use a writer-guarded middleware,
//    not a hand-rolled goroutine. gin-contrib/timeout buffers the response writer:
import "github.com/gin-contrib/timeout"
r.Use(timeout.New(
    timeout.WithTimeout(15*time.Second),
    timeout.WithResponse(func(c *gin.Context) {
        c.JSON(http.StatusGatewayTimeout, ErrorResponse{Code: "TIMEOUT", Message: "Request timed out"})
    }),
))
```

Equivalently, wrap the router with `http.TimeoutHandler(router, 15*time.Second, "request timed out")` (it buffers the writer too). Either way, **exclude streaming/SSE routes** — both will cut long responses short.

### Streaming and Server-Sent Events

For incremental output use `c.Stream` (it flushes after each write and returns when the client disconnects via `c.Request.Context().Done()`); use `c.SSEvent` to emit `text/event-stream` frames. Stop producing when `c.Stream` returns `false` so a disconnected client doesn't leak a goroutine. These routes must be on a router/server **without** `WriteTimeout` or `http.TimeoutHandler`.

```go
func (h *Handler) Stream(c *gin.Context) {
    events := h.svc.Subscribe(c.Request.Context())
    c.Stream(func(w io.Writer) bool {
        select {
        case ev, ok := <-events:
            if !ok {
                return false // source closed — end the stream
            }
            c.SSEvent("message", ev) // writes "event: message\ndata: ...\n\n" and flushes
            return true
        case <-c.Request.Context().Done():
            return false // client disconnected — stop
        }
    })
}
```

### Structured Logging with Request-ID Correlation

Use `log/slog` for machine-parseable logs and stamp every line with the request ID set by `RequestID()`, so a request can be traced across services. Replace the default `gin.Logger()` (which emits unstructured text) with a slog-backed middleware, and make `Recovery` log the panic stack with the same request ID instead of dropping it to stderr.

```go
func Logger(base *slog.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        c.Next()

        requestID, _ := c.Get("request_id")
        base.LogAttrs(c.Request.Context(), slog.LevelInfo, "http_request",
            slog.Any("request_id", requestID),
            slog.String("method", c.Request.Method),
            slog.String("path", c.Request.URL.Path),
            slog.Int("status", c.Writer.Status()),
            slog.Duration("latency", time.Since(start)),
            slog.String("client_ip", c.ClientIP()),
        )
    }
}

// Recovery logs the stack with the request ID, then returns a clean 500.
func Recovery(base *slog.Logger) gin.HandlerFunc {
    return gin.CustomRecoveryWithWriter(nil, func(c *gin.Context, err any) {
        requestID, _ := c.Get("request_id")
        base.LogAttrs(c.Request.Context(), slog.LevelError, "panic_recovered",
            slog.Any("request_id", requestID),
            slog.Any("error", err),
            slog.String("stack", string(debug.Stack())),
        )
        c.AbortWithStatusJSON(http.StatusInternalServerError, ErrorResponse{
            Code: "INTERNAL_ERROR", Message: "Internal server error",
        })
    })
}
```

## File Upload Handling

Validate both size *and* content type. A client-supplied `Content-Type` header or file extension is trivially spoofed -- sniff the real type from the leading bytes with `http.DetectContentType` (which reads the first 512 bytes), then rewind the reader before storing.

```go
func (h *FileHandler) Upload(c *gin.Context) {
    file, header, err := c.Request.FormFile("document")
    if err != nil {
        c.JSON(http.StatusBadRequest, newError("INVALID_FILE", "No file provided"))
        return
    }
    defer file.Close()

    if header.Size > maxUploadSize {
        c.JSON(http.StatusRequestEntityTooLarge, newError("FILE_TOO_LARGE",
            fmt.Sprintf("File exceeds %d bytes limit", maxUploadSize)))
        return
    }

    // Sniff the real content type from the first 512 bytes -- do not trust the
    // header's Content-Type or the filename extension.
    sniff := make([]byte, 512)
    n, _ := io.ReadFull(file, sniff)
    detected := http.DetectContentType(sniff[:n])
    if !allowedContentTypes[detected] {
        c.JSON(http.StatusUnsupportedMediaType, newError("UNSUPPORTED_TYPE",
            fmt.Sprintf("Content type %s is not allowed", detected)))
        return
    }
    if _, err := file.Seek(0, io.SeekStart); err != nil { // rewind for storage
        handleServiceError(c, err)
        return
    }

    result, err := h.fileService.Store(c.Request.Context(), file, header.Filename)
    if err != nil {
        handleServiceError(c, err)
        return
    }

    c.JSON(http.StatusCreated, result)
}
```

## Testing Handlers

Test handlers without a live server using `httptest.NewRecorder` and the router's `ServeHTTP`. This exercises the full middleware chain. For unit-testing a single handler in isolation, `gin.CreateTestContext` gives you a `*gin.Context` backed by a recorder. Always set `gin.SetMode(gin.TestMode)` in tests to silence debug output.

```go
func TestCreateUser(t *testing.T) {
    gin.SetMode(gin.TestMode)
    router := setupRouter(testDeps())

    body := `{"name":"Ada","email":"ada@example.com","role":"user"}`
    req := httptest.NewRequest(http.MethodPost, "/api/v1/users", strings.NewReader(body))
    req.Header.Set("Content-Type", "application/json")

    w := httptest.NewRecorder()
    router.ServeHTTP(w, req)

    require.Equal(t, http.StatusCreated, w.Code)

    var resp UserResponse
    require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))
    require.Equal(t, "Ada", resp.Name)
}

// Isolated handler test with a synthetic context.
func TestGetUser_NotFound(t *testing.T) {
    gin.SetMode(gin.TestMode)
    w := httptest.NewRecorder()
    c, _ := gin.CreateTestContext(w)
    c.Request = httptest.NewRequest(http.MethodGet, "/api/v1/users/missing", nil)
    c.Params = gin.Params{{Key: "id", Value: "missing"}}

    handler := NewUserHandler(stubService{err: ErrNotFound})
    handler.Get(c)

    require.Equal(t, http.StatusNotFound, w.Code)
}
```

## Graceful Shutdown

Graceful shutdown with `http.Server` + `signal.NotifyContext` + `Shutdown(ctx)` and the `ReadTimeout`/`WriteTimeout`/`IdleTimeout` settings is generic `net/http` — see the Go profile. The Gin-specific rule: **never use `router.Run()` in production** — it owns the listener and gives you no handle to call `Shutdown()`, so in-flight requests are dropped. Mount the Gin router as the `http.Server.Handler` instead:

```go
srv := &http.Server{Addr: ":8080", Handler: router, /* timeouts */ }
// ... ListenAndServe in a goroutine; srv.Shutdown(ctx) on SIGINT/SIGTERM
```
