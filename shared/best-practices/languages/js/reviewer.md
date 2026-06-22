# JavaScript Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Applied on top of default reviewer checklist when the project contains `package.json`. **TypeScript type-system checks live in the `typescript` reviewer profile** (loaded on top of this one for TS projects).

## Linting

> **Match the project's package manager** for every command below: the snippets show
> `npm`/`npx`, but if the repo has `pnpm-lock.yaml` use `pnpm exec`/`pnpm run`, with
> `yarn.lock` use `yarn`. Running the wrong manager (or a global tool) can resolve a
> different version than the lockfile pins. See "Running Static-Analysis Tools" in the
> default profile.

Run project lint scripts first, then targeted checks:

```bash
# Project lint script
if [ -f package.json ]; then
  npm run lint 2>/dev/null || yarn lint 2>/dev/null || pnpm lint 2>/dev/null || echo "No lint script found"
fi

# TypeScript type check
if [ -f tsconfig.json ]; then
  npx tsc --noEmit 2>/dev/null || echo "TypeScript check skipped"
fi
```

### eslint (primary linter)

eslint with TypeScript plugin is the primary static analysis tool. If the project has an eslint config, use it as-is. Config should be **flat config** (`eslint.config.js`) — the legacy `.eslintrc*` format is deprecated as of ESLint v9 (flag a new project still on `.eslintrc`). Key rule sets to verify are configured:

- `@typescript-eslint/recommended` -- base TS rules
- `@typescript-eslint/strict` -- stricter type-safety rules
- `@typescript-eslint/recommended-type-checked` + `no-floating-promises` -- typed lint catches unhandled/forgotten promises (a missing `await`), the highest-value async bug class; flag a floating promise as **MAJOR**
- `eslint-plugin-sonarjs` -- cognitive complexity and code smell detection
- `eslint-plugin-security` + `eslint-plugin-no-unsanitized` -- flags DOM-based XSS sinks (`innerHTML`, `dangerouslySetInnerHTML`, `eval`, unsanitized `insertAdjacentHTML`)

```bash
# Run eslint with JSON output for parsing
npx eslint --format json ./src 2>/dev/null | head -500
```

> **Fast alternatives (stack choice, not an add-on):** **Biome** and **oxlint** (Rust) lint/format far faster than ESLint+Prettier and can run alongside ESLint for speed or replace it. If the project already uses one, run it instead of ESLint; don't stack redundant linters.

## Deep Analysis Tools

### npm audit -- dependency vulnerabilities

```bash
npm audit --json 2>/dev/null | head -200
# or for pnpm/yarn:
pnpm audit --json 2>/dev/null | head -200
yarn npm audit --all --recursive --json 2>/dev/null | head -200   # Yarn 2+; `yarn audit` only exists in Yarn Classic (v1)
```

### dependency-cruiser / madge -- circular deps + layer rules

Prefer **dependency-cruiser**: it detects cycles AND enforces layer/forbidden-import
rules (an architecture fitness function), not just cycles. `madge` is the fallback.

```bash
# Preferred: cycles + orphans + custom layer rules (npm i -D dependency-cruiser)
npx depcruise src --include-only "^src" --output-type err 2>/dev/null
# Fallback — cycles only:
madge --circular --extensions ts,tsx,js,jsx src/ 2>/dev/null
```

### knip -- unused files, exports, types AND dependencies (supersedes depcheck)

Prefer `knip` over `depcheck`: it finds unused files, exports, exported types, and
dependencies in one pass. `depcheck` is the fallback when knip isn't configured.

```bash
# Install: npm install -D knip
npx knip --reporter json 2>/dev/null | head -300
# Fallback if knip is unavailable:
npx depcheck 2>/dev/null
```

### type-coverage -- typed-code percentage

Catches `any` creep that `tsc` allows. Flag a project-wide drop or new files well below the project threshold.

```bash
npx type-coverage --detail --at-least 95 2>/dev/null | tail -40
```

### stylelint -- CSS / SCSS / SFC `<style>` linting

```bash
# Install: npm install -D stylelint stylelint-config-standard
npx stylelint "**/*.{css,scss,vue}" --formatter json 2>/dev/null | head -200
```

### sonarjs -- cognitive complexity

If `eslint-plugin-sonarjs` is configured in the project's eslint config, findings appear in the eslint output above. If not configured, note it as a recommendation.

## Web-App Budgets (run when the project builds a browser bundle)

These need a built app or a running dev server — run them when available, otherwise note as not-run.

### @axe-core/playwright -- automated accessibility

Run an axe audit inside e2e tests; fail on serious/critical violations.

```js
import AxeBuilder from '@axe-core/playwright';
const results = await new AxeBuilder({ page }).analyze();
// assert results.violations filtered to impact in ['serious','critical'] is empty
```

### Lighthouse CI -- Core Web Vitals / perf / a11y budgets

```bash
# Install: npm install -g @lhci/cli
lhci autorun 2>/dev/null | tail -40   # gate on perf/a11y/best-practices/SEO budgets in lighthouserc
```

### size-limit -- bundle-size budget

```bash
# Install: npm install -D size-limit @size-limit/preset-app
npx size-limit 2>/dev/null   # fails when a bundle exceeds its configured budget
```

> TypeScript `tsconfig` strict-mode and type-system checks are owned by the **`typescript` reviewer profile** — not duplicated here.

## JavaScript Code Review Checklist

### Correctness
- [ ] `===`/`!==` used (never `==`/`!=`)
- [ ] Optional chaining (`?.`) and nullish coalescing (`??`) used
- [ ] No `var` -- only `const`/`let`
- [ ] `async`/`await` used (not raw `.then()` chains)
- [ ] Destructuring for object/array access
- [ ] Event listeners properly cleaned up
- [ ] `Number.isNaN` (not global `isNaN`); `=== null` check (not `typeof`-only)
- [ ] No mutation of args/shared state; copy before `.sort()`/`.reverse()`
- [ ] `structuredClone` for deep copy (not `JSON.parse(JSON.stringify(...))`)
- [ ] No timer used to "wait for" a promise (microtasks run before timers)
- [ ] `Intl` for number/date/currency formatting (not hand-rolled)
- [ ] No `for...in` over arrays
- [ ] Money in integer minor units / decimal lib; `BigInt` for large ints
- [ ] No side-effectful ESM imports

### Anti-Patterns to Flag

| Pattern | Severity | Fix |
|---------|----------|-----|
| Missing error handling in async | **MAJOR** | Add try-catch around async calls |
| Implicit type coercion (`==`, `!=`) | **MAJOR** | Use `===` / `!==` |
| Mutating a function arg or shared object/array | **MAJOR** | Copy first (spread); use `.toSorted()`/`.toReversed()` |
| Float arithmetic for money | **MAJOR** | Integer minor units or decimal library |
| Circular imports | **MAJOR** | Restructure module dependencies |
| Global `isNaN()` instead of `Number.isNaN` | **MINOR** | Use `Number.isNaN` (no coercion) |
| `JSON.parse(JSON.stringify(...))` deep copy | **MINOR** | Use `structuredClone` |
| `for...in` over an array | **MINOR** | Use `for...of` / array methods |
| Hand-rolled number/date/currency formatting | **MINOR** | Use `Intl` |
| Side-effectful ESM import | **MINOR** | Keep imports declaration-only |
| Default exports | **MINOR** | Use named exports |
| `.then()` chains (>2 levels) | **MINOR** | Convert to async/await |
| String concatenation with `+` | **MINOR** | Use template literals |
| `var` declaration | **MAJOR** | Use `const` or `let` |
| Unhandled promise rejection | **MAJOR** | Add error handling or void annotation |
| `|| ` for defaults (falsy trap) | **MINOR** | Use `??` for nullish coalescing |

## Tool Finding Severity Mapping

| Tool | Condition | Severity |
|------|-----------|----------|
| npm/pnpm audit | critical/high CVE | **BLOCKER** |
| npm/pnpm audit | moderate CVE | **MAJOR** |
| eslint | error-level rule | **MAJOR** |
| eslint | warning-level rule | **MINOR** |
| madge | any circular dependency | **MAJOR** |
| knip / depcheck | unused dependency / export / file | **MINOR** |
| type-coverage | new code below project threshold (new `any`) | **MAJOR** |
| eslint-plugin-security / no-unsanitized | DOM XSS sink on untrusted data | **BLOCKER** |
| stylelint | error-level rule | **MINOR** |
| sonarjs | cognitive complexity >15 | **MAJOR** |
| sonarjs | cognitive complexity >10 | **MINOR** |
| tsc --noEmit | type error | **BLOCKER** |
| @axe-core/playwright | serious/critical a11y violation | **MAJOR** |
| Lighthouse CI | budget regression (perf/a11y) | **MAJOR** |
| size-limit | bundle over budget | **MAJOR** |
