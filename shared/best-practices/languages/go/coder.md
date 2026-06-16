# Go Coder Profile

Go-specific coding rules. Applied on top of the default coder profile.

## Formatting

Always run `gofmt` (or `goimports`) before committing. Non-negotiable -- Go has one canonical style.

```bash
goimports -w .
```

## Error Handling

Check `err != nil` immediately after every call that returns an error. Never defer error checking to later.

```go
// Good -- check immediately, wrap with context
data, err := os.ReadFile(path)
if err != nil {
    return fmt.Errorf("reading config %s: %w", path, err)
}

// Bad -- ignored error
data, _ := os.ReadFile(path)

// Bad -- no context in wrap
if err != nil {
    return err
}
```

### Error Wrapping

Wrap errors with `fmt.Errorf("doing X: %w", err)` to build a chain of context. Use `%w` (not `%v`) so callers can use `errors.Is` and `errors.As`.

### Error Inspection

Use `errors.Is()` and `errors.As()` instead of type assertions or string matching on error values.

```go
// Good
if errors.Is(err, os.ErrNotExist) {
    return defaultConfig, nil
}

var pathErr *os.PathError
if errors.As(err, &pathErr) {
    log.Printf("path: %s", pathErr.Path)
}

// Bad -- breaks with wrapped errors
if err == os.ErrNotExist { ... }
if pe, ok := err.(*os.PathError); ok { ... }
```

### Defining Errors

Give callers something to match against. Export a **sentinel** `var ErrX = errors.New(...)` for a fixed condition (`errors.Is`), and a **custom error type** when callers need detail off the error (`errors.As`). Don't make callers string-match.

```go
// Sentinel -- matched with errors.Is
var ErrNotFound = errors.New("not found")

// Custom type -- carries data, matched with errors.As
type ValidationError struct {
    Field string
    Msg   string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("%s: %s", e.Field, e.Msg)
}
```

### Aggregating Errors

Use `errors.Join` to combine multiple errors (e.g. accumulated in a loop) into one;
`errors.Is`/`errors.As` see through a joined error.

```go
var errs error
for _, item := range items {
    if err := process(item); err != nil {
        errs = errors.Join(errs, fmt.Errorf("item %s: %w", item.ID, err))
    }
}
return errs // nil if every item succeeded
```

## Structured Logging

Use the stdlib structured logger `log/slog` (Go 1.21+) — never `log.Printf` with
interpolated strings. Log key/value attributes; include the request/trace id for
correlation; never log secrets or PII.

```go
slog.InfoContext(ctx, "user created", "user_id", u.ID, "trace_id", traceID)
// Bad -- unstructured, no correlation
log.Printf("created user %s", u.ID)
```

## Context Propagation

`context.Context` is always the first parameter. Never store it in a struct.

```go
// Good
func FetchUser(ctx context.Context, id string) (*User, error) { ... }

// Bad -- context buried or stored
func FetchUser(id string, ctx context.Context) (*User, error) { ... }

type Service struct {
    ctx context.Context // never do this
}
```

Use `context.Background()` only at program boundaries (main, top-level handler, test setup). Pass the received context everywhere else.

## Interfaces

Define small interfaces (1-3 methods) at the **consumer**, not the implementor. Accept interfaces, return concrete types.

```go
// Good -- small, defined where used
type UserStore interface {
    GetUser(ctx context.Context, id string) (*User, error)
}

func NewHandler(store UserStore) *Handler { ... }

// Bad -- large interface defined at the implementation
type UserService interface {
    GetUser(ctx context.Context, id string) (*User, error)
    ListUsers(ctx context.Context) ([]*User, error)
    CreateUser(ctx context.Context, u *User) error
    DeleteUser(ctx context.Context, id string) error
    UpdateUser(ctx context.Context, u *User) error
    // ... grows forever
}
```

## Generics

Use type parameters (1.18+) when the *same* logic operates over many types — container/algorithm helpers (`Map`, `Filter`, `Keys`). Use an **interface** when you need runtime polymorphism or only call methods on the value; reach for generics only when an interface forces needless boxing or loses the concrete type. Constrain with the narrowest constraint: `comparable` for map keys/equality, `cmp.Ordered` for `<`/`>`.

```go
// Good -- one implementation, type-safe across element types
func Keys[K comparable, V any](m map[K]V) []K {
    out := make([]K, 0, len(m))
    for k := range m {
        out = append(out, k)
    }
    return out
}

// Don't -- generics add nothing here; an interface is simpler
func Print[T fmt.Stringer](v T) { fmt.Println(v.String()) }
// just: func Print(v fmt.Stringer)
```

## Slice and Map Aliasing

Slices share a backing array; this aliasing causes silent bugs.

- **`append` may mutate the original.** If a slice has spare capacity, `append` writes in place — a sub-slice and its parent can clobber each other. Copy or three-index slice (`s[a:b:b]`) when you need isolation.
- **`range` copies each element.** Mutating the loop variable does not change the slice; index in (`s[i].X = ...`) to mutate.
- **Sub-slices retain the whole backing array.** Slicing one field out of a huge slice keeps the entire array alive. Use `slices.Clip` (or copy into a fresh slice) to release the excess.

```go
// Bad -- append into a sub-slice can overwrite the parent's data
sub := full[:2]
sub = append(sub, x) // may stomp full[2]

// Good -- cap-limited slice forces append to allocate
sub := full[:2:2]
sub = append(sub, x) // new backing array, full untouched

// Good -- release a large backing array held by a small sub-slice
small = slices.Clip(small)
```

## Nil Safety

Check pointers for nil before dereferencing — especially pointers returned from maps, type assertions, and functions. A missing map key returns the *zero value*, which for a pointer map is a nil pointer; dereferencing it panics.

```go
// Good -- the comma-ok form distinguishes "missing" from "present"
u, ok := users[id]   // users is map[string]*User
if !ok || u == nil {
    return ErrNotFound
}
name := u.Name       // safe

// Bad -- a missing key yields a nil *User; the field access panics
u := users[id]       // *User == nil when id absent
name := u.Name       // panic: nil pointer dereference
```

### The nil-interface gotcha

A non-nil interface can hold a nil concrete pointer. Returning a typed-nil `*MyError` through an `error` return makes `err != nil` *true* even though "nothing went wrong" — because the interface carries a type (`*MyError`) plus a nil value, and only a fully nil interface compares equal to `nil`. Return the interface type directly, or explicitly return `nil`.

```go
// Bad -- caller sees a non-nil error even on success
func find() error {
    var e *MyError      // typed nil
    // ... e never assigned ...
    return e            // wraps (*MyError)(nil) -> err != nil is TRUE
}

// Good -- return nil explicitly, or keep the variable as the interface type
func find() error {
    var err error       // interface, stays truly nil
    if bad {
        err = &MyError{...}
    }
    return err
}
```

## Resource Cleanup with defer

Use `defer` immediately after acquiring a resource. Keep the defer close to the acquisition so the pairing is visible.

```go
// Good
f, err := os.Open(path)
if err != nil {
    return err
}
defer f.Close()

mu.Lock()
defer mu.Unlock()
```

### defer Pitfalls

- **Don't drop a deferred `Close()` error on a writer.** A buffered write can fail on flush during `Close`; swallow it and you lose data silently. Capture it into the named return.
- **`defer` runs at function return, not block end.** A `defer` inside a loop accumulates until the function exits — open in a helper (so each iteration's defer fires) or close explicitly in the loop.
- **`defer f(x)` evaluates arguments now**, runs the call later. Capture the *current* value if that matters; close over the variable if you want its final value.

```go
// Good -- surface the Close error on a writer via named return
func writeAll(path string, data []byte) (err error) {
    f, err := os.Create(path)
    if err != nil {
        return err
    }
    defer func() {
        if cerr := f.Close(); cerr != nil && err == nil {
            err = cerr
        }
    }()
    _, err = f.Write(data)
    return err
}

// Bad -- defer in a loop holds every file open until the function returns
for _, p := range paths {
    f, _ := os.Open(p)
    defer f.Close() // fires only at function exit, not per iteration
}
```

## Goroutine Safety

Never launch a goroutine without a plan for its lifetime. Every goroutine must have:
- A way to stop (context cancellation, done channel, or WaitGroup)
- Error propagation (errgroup, channel, or logging)

```go
// Good -- errgroup manages lifetime and errors
g, ctx := errgroup.WithContext(ctx)
g.Go(func() error {
    return processItems(ctx, items)
})
if err := g.Wait(); err != nil {
    return err
}

// Bad -- fire and forget, no error handling, no shutdown
go processItems(ctx, items)
```

## Channel Patterns

Use directional channel types in function signatures to communicate intent.

```go
// Good -- direction is explicit
func produce(ctx context.Context, out chan<- Item) { ... }
func consume(ctx context.Context, in <-chan Item) { ... }

// Bad -- bidirectional when only one direction is used
func produce(ctx context.Context, out chan Item) { ... }
```

## Package Naming

- Short, lowercase, single-word names: `http`, `user`, `store`
- No underscores, no camelCase: `httputil` not `http_util` or `httpUtil`
- No generic names: `util`, `common`, `misc`, `helpers` -- put functions in the package that owns the domain
- Package name should not repeat the import path: `store.Store` is fine, `store.StoreService` stutters

## init() Functions

Avoid `init()`. It runs implicitly, makes testing hard, and hides dependencies. Prefer explicit initialization in `main()` or constructor functions. If `init()` is truly needed (e.g., registering a database driver), add a comment explaining why.

## Return Early

Guard-clause style (handle edge cases first, keep the happy path unnested) is covered by the default coder profile — it applies in Go too. Go's idiom of returning right after `if err != nil` is the same principle.

## Struct Tags

Keep struct tags consistent in format and validated by `go vet`. Always use the canonical tag format.

```go
type User struct {
    ID        string `json:"id"        db:"id"`
    FirstName string `json:"firstName" db:"first_name"`
    CreatedAt time.Time `json:"createdAt" db:"created_at"`
}
```

## Testing

Use table-driven tests as the default testing pattern.

```go
func TestParseSize(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    int64
        wantErr bool
    }{
        {name: "bytes", input: "100B", want: 100},
        {name: "kilobytes", input: "2KB", want: 2048},
        {name: "invalid", input: "abc", wantErr: true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseSize(tt.input)
            if (err != nil) != tt.wantErr {
                t.Fatalf("ParseSize(%q) error = %v, wantErr %v", tt.input, err, tt.wantErr)
            }
            if got != tt.want {
                t.Errorf("ParseSize(%q) = %d, want %d", tt.input, got, tt.want)
            }
        })
    }
}
```

Use `t.Helper()` in test helper functions so failure messages point to the caller.
