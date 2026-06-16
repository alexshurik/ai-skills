# TypeScript Reviewer Profile

TypeScript-specific review checklist. Applied when `tsconfig.json` exists.
TS projects also load the JS reviewer profile — this file adds TS-ONLY checks.

<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->

## tsconfig.json Strict Mode

Verify `strict: true` is present. If missing, flag as **BLOCKER** — all
other TS checks are unreliable without strict mode.

Also check `noUncheckedIndexedAccess: true` and `exactOptionalPropertyTypes: true`
(neither is included in `strict`). If missing, flag as **MINOR**.

## TypeScript Review Checklist

### Type Safety
- [ ] No `any` types — `unknown` with type guards when uncertain
- [ ] Strict null checks honored — `null`/`undefined` handled explicitly
- [ ] Explicit return types on exported functions
- [ ] Discriminated unions for state modeling (not boolean flags)
- [ ] DU `switch` ends in `default: assertNever(x)` — exhaustiveness enforced
- [ ] `const` assertions for literal types
- [ ] Utility types used (`Partial`, `Omit`, `Pick`, `Record`)
- [ ] Branded types for distinct ID/value kinds (no mixing `UserId`/`OrderId`)
- [ ] Untrusted data validated at the boundary — `as` not used to skip a runtime check

### Type System Usage
- [ ] `interface` used for object shapes (not `type` for plain objects)
- [ ] `import type` separates type-only imports from value imports; `export type` for re-exported types
- [ ] No `enum` — uses `as const` objects with derived union types
- [ ] `satisfies` used for type validation with inference where appropriate
- [ ] `readonly` on properties and arrays that should not be mutated
- [ ] Generic functions use `extends` constraints (no `any` in generics)
- [ ] Template literal types for structured strings (routes/event names) where they add safety
- [ ] Conditional types / `infer` confined to reusable utilities — not over-engineered in app code
- [ ] `isolatedModules`/`verbatimModuleSyntax` enabled; published packages ship correct `.d.ts`

### Suppression Hygiene
- [ ] No `@ts-ignore` — uses `@ts-expect-error` with justification comment
- [ ] No `!` non-null assertions — uses narrowing or explicit null checks
- [ ] No `as` type casting without justification — prefers type guards

## Anti-Patterns to Flag

| Pattern | Severity | Fix |
|---------|----------|-----|
| Missing `strict: true` in tsconfig | **BLOCKER** | Enable strict mode |
| `any` type usage | **MAJOR** | Use `unknown` with type guard |
| Unchecked array index access | **MAJOR** | Use optional chaining or bounds check (`noUncheckedIndexedAccess`) |
| `@ts-ignore` usage | **MAJOR** | Replace with `@ts-expect-error` + reason |
| `!` non-null assertion | **MAJOR** | Narrow with null check or guard |
| `as` type cast without guard | **MINOR** | Use type guard function |
| DU `switch` with no `assertNever` default (non-exhaustive) | **MAJOR** | Add `default: assertNever(x)` |
| Mixing distinct ID types (plain `string` for `UserId`/`OrderId`) | **MINOR** | Brand the types |
| Over-engineered conditional/`infer` types in app code | **MINOR** | Use explicit type or generic constraint |
| `enum` declaration | **MINOR** | Convert to `as const` object |
| `type` for plain object shape | **MINOR** | Use `interface` instead |
| Mixed type/value imports | **MINOR** | Separate with `import type` |
| Missing `noUncheckedIndexedAccess` | **MINOR** | Add to tsconfig |
| Missing `isolatedModules`/`verbatimModuleSyntax` | **MINOR** | Enable for independent per-file transpile |
| Published package without/with wrong `.d.ts` | **MAJOR** | Ship correct declarations (verify with `arethetypeswrong`) |

## Tooling

The JS reviewer profile owns lint/audit/dep tooling. TS adds **type-level**
gates on top:

```bash
# The gate: strict type check with no output (CI must run this)
npx tsc --strict --noEmit

# Typed-code percentage — catches `any` creep tsc allows (also in JS profile)
npx type-coverage --detail --at-least 95

# Type-level tests: assert the types themselves, not just runtime behavior
#   tsd / expect-type — assert inferred types match expectations
npx tsd 2>/dev/null

# Published packages: verify emitted types resolve under every module setting
npx @arethetypeswrong/cli --pack 2>/dev/null
```

| Tool | Condition | Severity |
|------|-----------|----------|
| `tsc --strict --noEmit` | any type error | **BLOCKER** |
| type-coverage | new code below project threshold (new `any`) | **MAJOR** |
| tsd / expect-type | type-level assertion fails | **MAJOR** |
| arethetypeswrong | published types misresolve (ESM/CJS) | **MAJOR** |
