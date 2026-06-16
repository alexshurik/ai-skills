# Go Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Go-specific review checklist and tooling. Applied on top of the default reviewer profile.

## Go Review Checklist

### Formatting and Style
- [ ] `gofmt` / `goimports` applied -- no formatting diffs
- [ ] Package names are short, lowercase, no underscores
- [ ] No stutter in exported names (`store.Store` is fine, `store.StoreService` is not)
- [ ] No `init()` functions unless justified with a comment

### Error Handling
- [ ] Every `err != nil` checked immediately after the call
- [ ] Errors wrapped with context: `fmt.Errorf("doing X: %w", err)`
- [ ] No ignored errors (`_ = someFunc()`) without a justifying comment
- [ ] `errors.Is()` / `errors.As()` used instead of direct comparison or type assertion
- [ ] No `panic` in library code -- return errors instead
- [ ] Matchable errors defined -- exported sentinel `var ErrX = errors.New(...)` and/or custom error type, not string matching
- [ ] **No nil-interface gotcha** -- a typed-nil pointer (`*MyError`) never returned through an `error`/interface return (makes `err != nil` falsely true); return `nil` or the interface type explicitly

### Context
- [ ] `context.Context` is first parameter in functions that accept it
- [ ] Context not stored in structs
- [ ] `context.Background()` only at program boundaries (main, top-level handler, test setup)
- [ ] `context.TODO()` only as a temporary placeholder with a comment explaining the plan

### Concurrency
- [ ] No naked goroutines -- every `go` statement has lifetime management (errgroup, WaitGroup, done channel)
- [ ] Errors from goroutines propagated (not silently dropped)
- [ ] Mutex always paired with `defer mu.Unlock()`
- [ ] Directional channel types in function signatures
- [ ] Channels closed by the sender, not the receiver

### Interfaces, Generics, and Types
- [ ] Interfaces are small (1-3 methods), defined at the consumer
- [ ] Accept interfaces, return concrete types
- [ ] Generics used only where an interface would force boxing/lose the concrete type; narrowest constraint (`comparable`, `cmp.Ordered`) -- no generics where a plain interface suffices
- [ ] Struct tags consistent and validated by `go vet`
- [ ] Nil checks before pointer dereference (map miss returns a nil pointer)

### Slice and Map Aliasing
- [ ] `append` not assumed to copy -- sub-slice/parent aliasing handled (`s[a:b:b]` or copy where isolation needed)
- [ ] `range` value copy not mutated expecting it to change the slice -- index in to mutate
- [ ] Large backing array not retained by a small sub-slice -- `slices.Clip`/copy to release

### Resource Management
- [ ] `defer` used for cleanup immediately after resource acquisition
- [ ] HTTP response bodies closed: `defer resp.Body.Close()`
- [ ] Database rows closed: `defer rows.Close()`
- [ ] Deferred `Close()` on a writer surfaces its error (named return), not silently dropped
- [ ] No `defer` inside a loop accumulating to function return -- close per iteration or use a helper
- [ ] `defer f(x)` argument evaluation timing intended (args bind at the `defer`, call runs later)

### Testing
- [ ] Table-driven tests used as default pattern (slice/map of structs with a `name`)
- [ ] `t.Helper()` called in test helper functions
- [ ] Subtests use `t.Run()` for clear failure messages
- [ ] `t.Cleanup()` preferred over `defer` for teardown (defer fires before parallel subtests finish)
- [ ] `t.Parallel()` in parent and subtests where independent
- [ ] `github.com/google/go-cmp` used for struct comparison, not `reflect.DeepEqual`
- [ ] Concurrency/time-dependent tests use `testing/synctest` (stable Go 1.25) for a fake clock and deterministic scheduling — never real `time.Sleep` to coordinate goroutines

### Anti-Patterns to Flag
- [ ] **Ignored errors** -- `_ = f()` without comment is almost always a bug
- [ ] **Naked goroutines** -- `go func()` with no sync or error handling
- [ ] **Mutex without defer** -- `mu.Lock()` followed by logic without `defer mu.Unlock()`
- [ ] **`context.Background()` deep in call chain** -- should propagate from caller
- [ ] **`panic` in library code** -- libraries must return errors, not crash the caller
- [ ] **Empty interface (`interface{}` / `any`) overuse** -- use generics or specific types
- [ ] **`log.Fatal` / `os.Exit` outside main** -- prevents defer cleanup and testing
- [ ] **Channel send without select** -- can block forever if receiver disappears
- [ ] **Goroutine leak** -- goroutine blocked on channel with no cancellation path
- [ ] **Typed-nil through an interface** -- returning `(*T)(nil)` as `error`/interface; `err != nil` is falsely true
- [ ] **`append` aliasing** -- mutating a sub-slice that shares a backing array with live data
- [ ] **Deferred `Close()` error dropped** on a writer -- buffered data can fail to flush
- [ ] **`defer` in a loop** -- resources held until function return, not per iteration

## Static Analysis Tools

### go vet (Built-in)

Ships with Go. Catches subtle bugs: printf format mismatches, unreachable code, incorrect struct tags, copying mutexes.

```bash
go vet ./...
```

### gofmt / goimports (Formatting)

```bash
# Check for formatting issues (non-zero exit = unformatted files)
gofmt -l .

# Format in place
goimports -w .
```

### golangci-lint (Meta-linter)

Runs multiple linters in parallel. The standard for Go CI pipelines.

```bash
# Install
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run with recommended linters
golangci-lint run ./...

# Run with specific linters enabled
golangci-lint run --enable gocritic,gocognit,gocyclo,errcheck,staticcheck,gosimple,ineffassign,unused ./...

# JSON output for CI
golangci-lint run --output.json.path=stdout ./...   # v2 flag; v1 used --out-format json
```

**Recommended linters to enable** in `.golangci.yml`:

| Linter | Purpose |
|--------|---------|
| `errcheck` | Unchecked errors |
| `staticcheck` | Comprehensive static analysis (successor to megacheck) |
| `gosimple` | Code simplification suggestions |
| `ineffassign` | Detects unused variable assignments |
| `unused` | Unused code (functions, types, constants) |
| `gocritic` | Opinionated style and performance checks |
| `gocyclo` | Cyclomatic complexity |
| `gocognit` | Cognitive complexity |
| `govet` | `go vet` checks via golangci-lint |
| `revive` | Extensible linter, successor to golint |
| `prealloc` | Slice preallocation suggestions |
| `noctx` | HTTP requests without context |
| `bodyclose` | Unclosed HTTP response bodies |
| `exhaustive` | Missing cases in enum switch statements |

### gosec (Security Scanner)

```bash
# Install
go install github.com/securego/gosec/v2/cmd/gosec@latest

# Scan project
gosec ./...

# JSON output
gosec -fmt json ./...

# Exclude specific rules
gosec -exclude=G104 ./...
```

### gocognit (Cognitive Complexity)

```bash
# Install
go install github.com/uudashr/gocognit/cmd/gocognit@latest

# Show functions with cognitive complexity over 10
gocognit -over 10 ./...

# Show top 20 most complex functions
gocognit -top 20 -avg ./...
```

### govulncheck (Dependency Vulnerabilities)

```bash
# Install
go install golang.org/x/vuln/cmd/govulncheck@latest

# Check for known vulnerabilities
govulncheck ./...
```

## Severity Mapping for Go Findings

Extends the orchestrator's severity table with Go-specific entries.

| Finding | Severity |
|---------|----------|
| Ignored error without justification | **BLOCKER** |
| `panic` in library code | **BLOCKER** |
| Naked goroutine (no sync, no error handling) | **BLOCKER** |
| Goroutine leak (no cancellation path) | **BLOCKER** |
| `context.Background()` deep in call chain | **MAJOR** |
| Mutex without `defer Unlock()` | **MAJOR** |
| Missing nil check before pointer dereference | **MAJOR** |
| Typed-nil pointer returned through an interface/error | **MAJOR** |
| Deferred writer `Close()` error dropped | **MAJOR** |
| `append`/sub-slice aliasing mutating live data | **MAJOR** |
| `defer` in a loop accumulating to function return | **MAJOR** |
| Error not matchable (no sentinel/type, string-matched) | **MINOR** |
| Large backing array retained by small sub-slice (no `Clip`) | **MINOR** |
| Generics where a plain interface suffices | **MINOR** |
| `log.Fatal` / `os.Exit` outside main | **MAJOR** |
| HTTP response body not closed | **MAJOR** |
| `gofmt` not applied | **MAJOR** |
| Cyclomatic complexity > 15 | **MAJOR** |
| Cognitive complexity > 15 | **MAJOR** |
| Cyclomatic complexity 11-15 | **MINOR** |
| Cognitive complexity 11-15 | **MINOR** |
| `init()` without justifying comment | **MINOR** |
| Name stutter (`pkg.PkgThing`) | **MINOR** |
| Bidirectional channel where directional suffices | **MINOR** |
| gosec high severity | **BLOCKER** |
| gosec medium severity | **MAJOR** |
| gosec low severity | **MINOR** |
| govulncheck critical/high CVE | **BLOCKER** |
| govulncheck moderate CVE | **MAJOR** |
