# JavaScript Coding Rules

Applied on top of default coding rules when the project contains `package.json`. **TypeScript-specific rules (type safety, `any`/`unknown`, discriminated unions, return types) live in the `typescript` profile**, which loads on top of this one for TS projects.

## Strict Equality and Nullish Handling

- `===` / `!==` always -- never `==` / `!=`
- Optional chaining (`?.`) for safe property access
- Nullish coalescing (`??`) over logical OR for defaults -- `||` treats `0`, `""`, `false` as falsy

```js
// Good
const name = user?.profile?.displayName ?? "Anonymous";

// Bad -- || treats empty string as falsy
const name = user && user.profile && user.profile.displayName || "Anonymous";
```

## Equality and Coercion Gotchas

- `NaN !== NaN` -- test with `Number.isNaN(x)`, never the global `isNaN()` (which coerces its argument first)
- `typeof null === "object"` -- check `value === null` explicitly, don't rely on `typeof`
- `Object.is(x, y)` for edge cases the `===` operator gets wrong (`Object.is(NaN, NaN) === true`, `Object.is(0, -0) === false`)

```js
// Good
if (Number.isNaN(value)) { ... }

// Bad -- global isNaN coerces: isNaN("foo") is true, isNaN("") is false
if (isNaN(value)) { ... }
```

## Variable Declarations

- `const` by default
- `let` only when reassignment is needed
- Never `var`

## Immutability

- Never mutate objects or arrays you don't own (function args, shared state) -- copy first via spread (`{ ...obj }`, `[...arr]`)
- `Object.freeze` module-level constants so accidental writes throw in strict mode
- `.sort()`, `.reverse()`, `.splice()`, `.push()` mutate in place -- copy before sorting shared data (or use `.toSorted()` / `.toReversed()`)

```js
// Good -- copy before sorting
const ordered = [...items].sort((a, b) => a.rank - b.rank);

// Bad -- mutates the caller's array
const ordered = items.sort((a, b) => a.rank - b.rank);
```

## Deep Copy

- `structuredClone(value)` for deep copies -- handles Dates, Maps, Sets, and cycles
- Never `JSON.parse(JSON.stringify(value))`: it drops `undefined`, functions, and `Symbol`s, turns `Date` into a string, and throws on cycles

## Async Patterns

- `async`/`await` over `.then()` chains
- Narrow try-catch around the specific async call that can fail
- Always handle promise rejections -- no unhandled promises

```js
// Good -- async/await with narrow try
async function fetchUser(userId) {
  let response;
  try {
    response = await fetch(`/api/users/${userId}`);
  } catch (error) {
    throw new NetworkError(`Failed to reach API: ${error.message}`);
  }
  if (!response.ok) {
    throw new ApiError(`User fetch failed: ${response.status}`);
  }
  return response.json();
}

// Bad -- .then() chain, broad catch swallows the error
function fetchUser(userId) {
  return fetch(`/api/users/${userId}`)
    .then(r => r.json())
    .catch(() => null);
}
```

## Event-Loop Ordering

- Microtasks (resolved promises, `queueMicrotask`) run before macrotasks (`setTimeout`, even `setTimeout(fn, 0)`) -- never rely on a timer to "wait for" a promise
- Don't assume ordering between independent async sources; `await` what you actually depend on

```js
setTimeout(() => console.log("timer"), 0);
Promise.resolve().then(() => console.log("microtask"));
// Logs: "microtask" then "timer"
```

## Numbers and Precision

- Floats can't represent decimals exactly (`0.1 + 0.2 !== 0.3`) -- for money, compute in integer minor units (cents) or use a decimal library
- `BigInt` (`123n`) for integers beyond `Number.MAX_SAFE_INTEGER` (e.g. DB bigint IDs, large counters)

## Formatting

- Use `Intl` for number/date/currency formatting -- it is locale-aware; never hand-roll

```js
// Good
new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(1234.5);
// "$1,234.50"
```

## Array Iteration

- Never `for...in` over arrays -- it iterates string keys including inherited/extra properties and skips holes in order-undefined ways
- Use `for...of`, `.map`/`.filter`/`.reduce`, or `.forEach`

## Destructuring

- Destructure objects/arrays for cleaner access; destructure params when accessing multiple properties

```js
// Good
function formatUser({ name, email, role }) {
  return `${name} <${email}> [${role}]`;
}
```

## String Handling

- Template literals over `+` concatenation

```js
const greeting = `Hello, ${user.name}!`;
```

## Modules (ESM)

- No side-effectful imports -- importing a module should not run observable effects beyond defining exports
- Dynamic `import()` for lazy/conditional loading (code splitting, optional deps)
- Top-level `await` is available in ESM modules -- use it for module init that must complete before exports are used
- Know your CJS/ESM interop: a CJS `module.exports = x` lands on the default import; named imports from CJS may not resolve

## Exports

- Named exports over default exports -- they enable better refactoring and auto-imports
- Barrel exports (`index.js` re-exports) only at package boundaries, not within internal modules

```js
// Good -- named export
export function createUser(data) { ... }

// Bad -- default export
export default function createUser(data) { ... }
```

## Error Handling

- Narrow try blocks -- wrap only the call that can throw
- Type guards in catch: `if (error instanceof SpecificError)`
- For async code: catch specific rejection reasons, not blanket catch
- Event listeners must be cleaned up (return cleanup functions or use `AbortController`)

```js
// Good -- AbortController for cleanup
function setupListener(element, signal) {
  element.addEventListener("click", handleClick, { signal });
}

// Good -- cleanup in framework lifecycle
onMounted(() => {
  const controller = new AbortController();
  window.addEventListener("resize", handleResize, { signal: controller.signal });
  onUnmounted(() => controller.abort());
});
```
