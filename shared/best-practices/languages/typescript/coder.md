# TypeScript Coder Profile

TypeScript-specific rules that go beyond the JS profile. Applied when `tsconfig.json` exists.
TS projects also load the JS profile — this file adds TS-ONLY rules.

## Strict Configuration

`tsconfig.json` must have `strict: true`. Never weaken strict checks
to fix type errors — fix the types instead. Also enable
`noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` (neither is part
of `strict`) for meaningful extra safety.

## Type Safety

- No `any` -- use `unknown` with type guards when the type is uncertain
- Strict null checks -- handle `null`/`undefined` explicitly, never assume values exist
- Explicit return types on all exported functions
- `const` assertions for literal types where appropriate
- Discriminated unions for state modeling (prefer over boolean flags or string enums)
- Utility types (`Partial`, `Pick`, `Omit`, `Record`) over manual interface duplication

```typescript
// Good -- discriminated union
type Result =
  | { status: "success"; data: User }
  | { status: "error"; message: string };

function handleResult(result: Result): void {
  switch (result.status) {
    case "success":
      renderUser(result.data);
      break;
    case "error":
      showError(result.message);
      break;
    default:
      assertNever(result); // compile error if a variant is unhandled
  }
}

// Bad -- boolean flags
interface Result {
  success: boolean;
  data?: User;
  error?: string;
}
```

**Exhaustiveness**: every discriminated-union `switch` must end in a `default`
branch that passes the value to `assertNever`. The `never` parameter makes
adding a new variant a compile error until the new case is handled.

```typescript
function assertNever(value: never): never {
  throw new Error(`Unhandled variant: ${JSON.stringify(value)}`);
}
```

```typescript
// Good -- unknown with type guard
function parseInput(value: unknown): string {
  if (typeof value !== "string") {
    throw new TypeError("Expected string input");
  }
  return value.trim();
}

// Bad -- any
function parseInput(value: any): string {
  return value.trim();
}
```

## Validate External Data at Boundaries

A type assertion (`as User`) is a compile-time lie about runtime data — it does
NOT check anything. Data crossing a trust boundary (HTTP responses, request
bodies, env vars, parsed JSON, message payloads) must be validated at runtime
with a schema, then the static type is *inferred* from the schema.

```typescript
// Good — runtime-validated, type inferred from the schema
const UserSchema = z.object({ id: z.string(), email: z.string().email() });
type User = z.infer<typeof UserSchema>;
const user = UserSchema.parse(await res.json()); // throws on bad data

// Bad — a lie: no runtime check, crashes later with a confusing error
const user = (await res.json()) as User;
```

Use a runtime-validation library (zod, valibot). This is the TS equivalent of
Python's "validate at the boundary with Pydantic."

## Prefer `interface` Over `type` for Object Shapes

`interface` is extendable and gives better error messages. Use `type` only
for unions, intersections, mapped types, and conditional types.

```typescript
// Good — extendable
interface UserProfile {
  name: string;
  email: string;
}

// Good — type alias for union
type Result = Success | Failure;

// Bad — type for plain object shape
type UserProfile = {
  name: string;
  email: string;
};
```

## `import type` for Type-Only Imports

Separate type imports from value imports. This enables tree-shaking and
makes the dependency graph clearer.

```typescript
// Good
import type { User, Role } from "./models";
import { createUser } from "./models";

// Bad — mixes types and values
import { User, Role, createUser } from "./models";
```

## Avoid `enum` — Prefer `as const` Objects

Enums add runtime code and have surprising behaviors (numeric enums
allow reverse mapping, const enums behave differently in declaration files).

```typescript
// Good
const Status = {
  Active: "active",
  Inactive: "inactive",
  Suspended: "suspended",
} as const;

type Status = (typeof Status)[keyof typeof Status];

// Bad
enum Status {
  Active = "active",
  Inactive = "inactive",
  Suspended = "suspended",
}
```

## No `!` Non-Null Assertion

Non-null assertions (`!`) bypass the type checker. Use type narrowing
or explicit null handling instead.

```typescript
// Good — narrowing
const element = document.getElementById("root");
if (!element) {
  throw new Error("Root element not found");
}
element.classList.add("loaded");

// Bad — asserts non-null without checking
const element = document.getElementById("root")!;
element.classList.add("loaded");
```

## No `@ts-ignore` — Use `@ts-expect-error` With Reason

`@ts-ignore` silently suppresses all errors, including future regressions.
`@ts-expect-error` fails when the suppressed error no longer exists.

```typescript
// Acceptable — with justification
// @ts-expect-error: library types are incorrect for v3 API
const result = legacyLib.process(data);

// Bad — blanket suppression
// @ts-ignore
const result = legacyLib.process(data);
```

## `satisfies` for Type Validation With Inference

Use `satisfies` when you want to validate a value matches a type while
preserving the narrower inferred type.

```typescript
// Good — validates shape, infers literal types
const config = {
  port: 3000,
  host: "localhost",
  debug: true,
} satisfies Record<string, unknown>;
// config.port is `number`, not `unknown`

// Less good — widens to Record type
const config: Record<string, unknown> = {
  port: 3000,
  host: "localhost",
  debug: true,
};
// config.port is `unknown`
```

## `readonly` for Immutable Data

Mark properties and arrays as `readonly` when they should not be mutated
after creation.

```typescript
interface Config {
  readonly apiUrl: string;
  readonly maxRetries: number;
  readonly allowedOrigins: readonly string[];
}
```

## Generic Constraints Over `any`

Use `extends` constraints to keep type safety in generic functions.

```typescript
// Good — constrained generic
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// Bad — loses type information
function getProperty(obj: any, key: string): any {
  return obj[key];
}
```

## Avoid Type Casting With `as`

`as` is a compile-time assertion, not a runtime check. For **untrusted data**,
validate at the boundary (see above) instead. For **in-process** narrowing,
prefer a type guard. Reserve `as` for definitive external knowledge the
compiler genuinely cannot infer.

```typescript
// Good — type guard for in-process narrowing
function isUser(value: unknown): value is User {
  return typeof value === "object" && value !== null && "email" in value;
}
```

## Branded (Nominal) Types

TypeScript is structurally typed, so two `string` IDs are interchangeable and
easy to mix up. Brand them to make the compiler reject swaps.

```typescript
type Brand<T, B> = T & { readonly __brand: B };
type UserId = Brand<string, "UserId">;
type OrderId = Brand<string, "OrderId">;

declare function getOrder(id: OrderId): Order;
const userId = "u_1" as UserId;
getOrder(userId); // compile error: UserId is not OrderId
```

## Template Literal & Conditional Types

- **Template literal types** model string shapes precisely (routes, event names,
  CSS units) instead of bare `string`.

  ```typescript
  type Route = `/users/${string}`;
  type Event = `on${"Click" | "Hover"}`; // "onClick" | "onHover"
  ```

- **Conditional types / `infer`** earn their place in reusable library
  utilities (unwrapping a type, deriving one type from another). Do NOT reach
  for them in application code where an explicit type or generic constraint is
  clearer — over-engineered type gymnastics are a maintenance cost.

  ```typescript
  type Awaited<T> = T extends Promise<infer U> ? U : T;
  ```

## Declaration Files & Module Emit

- Ship `.d.ts` files for published packages and to describe untyped JS deps;
  keep ambient declarations (`declare module "..."`) minimal and correct.
- Use `export type` (not just `import type`) when re-exporting types, so the
  emit stays value-free.
- Enable `isolatedModules` (or `verbatimModuleSyntax`) so each file transpiles
  independently — this forces `import type`/`export type` on type-only symbols
  and matches how bundlers and `--isolatedDeclarations` process files.
