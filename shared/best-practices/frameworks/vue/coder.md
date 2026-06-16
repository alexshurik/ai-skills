# Vue 3 Coding Rules

Applied on top of the JS/TS language profile when the project imports `vue`.

## Composition API with `<script setup>`

Always use `<script setup>` syntax in single-file components. Never use Options API in new code.

```vue
<!-- Good -- <script setup> -->
<script setup lang="ts">
import { ref, computed } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)
</script>

<!-- Bad -- Options API -->
<script>
export default {
  data() {
    return { count: 0 }
  },
  computed: {
    doubled() { return this.count * 2 }
  }
}
</script>
```

## Props and Emits Typing

Use type-based declarations with `defineProps` and `defineEmits`. In Vue 3.5 **reactive props destructure** is stable and on by default: destructuring `defineProps()` keeps each prop reactive (the compiler rewrites accesses to `props.x`), and a destructuring default replaces `withDefaults`.

```typescript
// Good (3.5) -- reactive destructure with native defaults; no withDefaults
const { title, count = 0 } = defineProps<{
  title: string
  count?: number
}>()
// `count` stays reactive — read it directly in computed/watch/template

// Good -- typed emits
const emit = defineEmits<{
  update: [value: string]
  close: []
}>()
```

Caveat: a destructured prop is reactive on *access*, but passing it into a function or composable snapshots its current value. To pass it reactively, wrap in a getter (`() => count`) or `toRef(() => count)` — do **not** reach for the old `toRefs(props)` workaround.

Never mutate props. Props are one-way data flow from the parent and are read-only by contract; mutating them silently desyncs parent and child and breaks on the parent's next re-render. To accept a value the child writes back, use `defineModel()` (the v-model contract); otherwise copy the prop into local state.

### `defineModel()` for v-model (3.4+)

`defineModel()` returns a writable ref wired to the parent's `v-model` — assigning to `model.value` emits the update. Do **not** hand-wire the obsolete `modelValue` prop + `update:modelValue` emit boilerplate.

```typescript
// Good -- defineModel(): one line, two-way bound, no manual emit
const model = defineModel<string>()                 // parent: <Field v-model="name" />
function onInput(e: Event) {
  model.value = (e.target as HTMLInputElement).value // assignment emits update
}

// Named / multiple models
const first = defineModel<string>('first')           // v-model:first
const count = defineModel<number>('count', { default: 0 })

// Bad -- obsolete manual wiring (defineModel replaces this entirely)
const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

// Good -- copy into local state when the child genuinely owns a draft (not a v-model)
const { initialValue } = defineProps<{ initialValue: string }>()
const draft = ref(initialValue)
```

## Reactive State

Use `ref()` for primitives and single values, `reactive()` for complex objects only when the whole object is local state. Prefer `ref()` as the default.

```typescript
// Good -- ref for most cases
const isLoading = ref(false)
const userName = ref('')
const items = ref<Item[]>([])

// Good -- computed for derived state
const activeItems = computed(() => items.value.filter(item => item.isActive))

// Bad -- reactive loses reactivity when destructured
const state = reactive({ count: 0 })
const { count } = state // count is NOT reactive
```

Destructuring a `reactive()` object detaches the fields from the proxy — use `toRefs()` (or access via the object). Props are the exception in 3.5: destructuring `defineProps()` stays reactive (see Props and Emits Typing), so `toRefs(props)` is no longer needed.

```typescript
// Good -- toRefs keeps a reactive() object's fields reactive when destructured
const state = reactive({ count: 0, name: '' })
const { count, name } = toRefs(state)
```

Never reassign a `reactive()` object -- reassignment replaces the reactive proxy and breaks every existing reference. Mutate in place, or use `ref()` when the whole value needs to be swapped.

```typescript
// Bad -- reassignment breaks reactivity, watchers/templates keep the old proxy
let state = reactive({ items: [] as Item[] })
state = reactive({ items: newItems }) // template still tracks the old object

// Good -- mutate in place
const state = reactive({ items: [] as Item[] })
state.items = newItems

// Good -- ref when the whole value is replaced
const items = ref<Item[]>([])
items.value = newItems
```

Use `shallowRef` / `shallowReactive` for large or externally-managed payloads (big data tables, chart datasets, third-party class instances). Deep reactivity on large structures costs CPU and memory for no benefit; shallow tracks only the top-level `.value` reassignment.

```typescript
// Good -- shallowRef for a large immutable snapshot replaced wholesale
const rows = shallowRef<Row[]>([])
rows.value = await fetchTenThousandRows() // triggers update; rows are not deeply tracked

// Good -- shallowReactive for a non-reactive third-party instance
const editor = shallowReactive({ instance: new MonacoEditor() })
```

## Pinia for Client / Global State

Pinia is the recommended store for shared client state (auth session, UI preferences, cross-component app state) — it is a stack choice, not a Vue rule, but it's the default for new apps. Whatever you choose, do not roll an ad-hoc reactive singleton (a `reactive()`/`ref()` exported from a module): it bypasses devtools, SSR request isolation, and HMR. Keep the client/server split — Pinia for *client* state, a server-cache library for *server* state.

Prefer the setup-store style -- it reads like a composable and types inference-cleanly.

```typescript
// stores/auth.ts -- Good, setup store
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => user.value !== null)

  function setUser(next: User | null) {
    user.value = next
  }

  return { user, isAuthenticated, setUser }
})

// Bad -- ad-hoc reactive singleton shared across the app
export const authState = reactive({ user: null as User | null })
```

When destructuring a store, wrap state and getters in `storeToRefs()` -- the store is a reactive object, so plain destructuring loses reactivity (same rule as `reactive()`). Actions are plain functions and can be destructured directly.

```typescript
// Good -- storeToRefs keeps state/getters reactive
const store = useAuthStore()
const { user, isAuthenticated } = storeToRefs(store)
const { setUser } = store // actions destructure fine

// Bad -- destructuring state off the store drops reactivity
const { user } = useAuthStore() // user is NOT reactive
```

## Vue Query for Server State

TanStack Vue Query (`useQuery`/`useMutation`) is the recommended way to manage server state (caching, dedup, background refetch, invalidation) — again a stack choice, not a Vue mandate. When the project uses it, route server reads/writes through it rather than hand-rolling fetch-in-`onMounted` with manual loading/error/cache state.

```typescript
// Good -- useQuery composable
export function useUsers(filters: Ref<UserFilters>) {
  return useQuery<User[], ApiError>({
    queryKey: computed(() => ['users', toValue(filters)]),
    queryFn: () => userApi.list(toValue(filters)),
  })
}

// Bad -- manual fetch in lifecycle
onMounted(async () => {
  const response = await fetch('/api/users')
  users.value = await response.json()
})
```

Mutations with optimistic updates and cache invalidation:

```typescript
export function useCreateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateUserInput) => userApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
```

## Composables

Extract reusable logic into composables (`use*` naming). Composables are the primary reuse mechanism in Composition API.

```typescript
// Good -- extracted composable
export function useDebounce<T>(value: Ref<T>, delayMs: number): Ref<T> {
  const debounced = ref(value.value) as Ref<T>
  let timeout: ReturnType<typeof setTimeout>

  watch(value, (newValue) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => {
      debounced.value = newValue
    }, delayMs)
  })

  return debounced
}
```

Rules for composables:
- Name starts with `use`
- Return reactive refs or computed values, not raw data
- Accept `Ref<T> | T` parameters for flexibility (use `toValue()` internally)
- Place in `composables/` directory

## Watchers: `watch` vs `watchEffect`

Reach for derived state (`computed`) first; use watchers only for *side effects* (fetching, logging, imperative DOM, syncing to storage).

- `watch(source, cb)` -- explicit dependencies, gives you old and new values, lazy by default. Use when you need the previous value or want to react to a specific source.
- `watchEffect(cb)` -- auto-tracks every reactive read inside, runs immediately. Use for "keep this in sync" effects where the dependency set is obvious and you don't need the old value.

```typescript
// Good -- watch when you need old/new and an explicit source
watch(userId, (id, prevId) => {
  if (id !== prevId) analytics.track('user_changed', { id })
})

// Good -- watchEffect for auto-tracked sync, with cleanup
watchEffect((onCleanup) => {
  const controller = new AbortController()
  fetchProfile(userId.value, controller.signal)
  onCleanup(() => controller.abort())
})
```

Control timing with `flush`: default `'pre'` runs before DOM update; use `flush: 'post'` when the callback must read the updated DOM (e.g. measuring an element). Always clean up timers, listeners, and in-flight requests via `onCleanup` (or `onUnmounted`) to avoid leaks.

## Provide / Inject

Use typed `InjectionKey` for deep dependency injection. Always provide a fallback or throw on missing injection.

```typescript
// keys.ts
export const API_CLIENT_KEY: InjectionKey<ApiClient> = Symbol('apiClient')

// Provider component
provide(API_CLIENT_KEY, apiClient)

// Consumer composable
export function useApiClient(): ApiClient {
  const client = inject(API_CLIENT_KEY)
  if (!client) {
    throw new Error('ApiClient not provided -- wrap component tree with provider')
  }
  return client
}
```

## Component Size and Responsibility

- Single responsibility -- one component does one thing
- Extract when component exceeds 200 lines of `<script setup>`
- Split complex templates into child components
- Extract business logic into composables, keep components thin

## Router

Lazy-load route components to reduce initial bundle size:

```typescript
const routes: RouteRecordRaw[] = [
  {
    path: '/dashboard',
    component: () => import('@/views/DashboardView.vue'),
  },
  {
    path: '/users/:id',
    component: () => import('@/views/UserDetailView.vue'),
    props: true,
  },
]
```

Route params arrive as raw `string` (or `string[]`) and are never type-safe by default. Type and coerce them at the boundary -- prefer `props: true` so the param enters the component as a typed prop, or validate explicitly when reading `useRoute()`.

```typescript
// Good -- param becomes a typed, validated prop
const props = defineProps<{ id: string }>()
const userId = computed(() => Number(props.id))

// Bad -- raw, untyped, unvalidated
const route = useRoute()
const id = route.params.id // string | string[], could be anything
```

## API Client

Centralize HTTP communication in a typed API client with interceptors. Components and composables never call `fetch`/`axios` directly.

```typescript
// api/client.ts -- single instance, configured once
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: REQUEST_TIMEOUT_MS,
})

// api/endpoints/users.ts -- typed endpoint functions
export const userApi = {
  list: (filters: UserFilters) => apiClient.get<User[]>('/users', { params: filters }),
  get: (id: string) => apiClient.get<User>(`/users/${id}`),
  create: (data: CreateUserInput) => apiClient.post<User>('/users', data),
}
```

## Template Rules

- No direct DOM manipulation -- use template refs and Vue bindings. Bind template refs with `useTemplateRef('name')` (3.5), not a manually-named `ref(null)` matched to the `ref="name"` attribute.
- Read the DOM only after Vue has flushed updates: `await nextTick()` (or a `flush: 'post'` watcher) before measuring/focusing an element you just changed.
- Use `v-for` with `:key` always (unique, stable keys -- not array index)
- Keep template expressions simple -- move complex logic to computed properties
- Use `v-show` for frequent toggles, `v-if` for conditional rendering

```typescript
import { useTemplateRef, nextTick } from 'vue'

const inputEl = useTemplateRef('input')   // <input ref="input">
async function focusAfterUpdate() {
  show.value = true
  await nextTick()                         // wait for the element to render
  inputEl.value?.focus()
}
```

```vue
<!-- Good -- computed for complex condition -->
<template>
  <div v-if="shouldShowBanner">...</div>
  <ul>
    <li v-for="user in activeUsers" :key="user.id">{{ user.name }}</li>
  </ul>
</template>

<script setup lang="ts">
const shouldShowBanner = computed(() => !user.value.dismissed && isNewUser.value)
const activeUsers = computed(() => users.value.filter(u => u.isActive))
</script>

<!-- Bad -- complex logic in template -->
<template>
  <div v-if="!user.dismissed && Date.now() - user.createdAt < 86400000">...</div>
  <li v-for="(user, index) in users" :key="index">...</li>
</template>
```

## Security: `v-html` and XSS

Vue escapes mustache interpolation (`{{ }}`) and bound text automatically, so `{{ userInput }}` is safe. `v-html` is the opposite: it injects raw HTML and is the #1 XSS vector in Vue apps. Never pass untrusted or user-influenced data to `v-html`.

```vue
<!-- Bad -- untrusted HTML straight into the DOM, executes injected scripts/handlers -->
<div v-html="comment.body" />

<!-- Good -- escaped text interpolation, no HTML injection -->
<div>{{ comment.body }}</div>

<!-- Good -- when rich HTML is genuinely required, sanitize first -->
<script setup lang="ts">
import DOMPurify from 'dompurify'
const safeHtml = computed(() => DOMPurify.sanitize(comment.body))
</script>
<template>
  <div v-html="safeHtml" />
</template>
```

Only use `v-html` for content you fully control or output from a server-side sanitizer. Also avoid binding untrusted strings into `:href`/`:src` (a `javascript:` URL is executable) -- validate the protocol.

## Accessibility

- Use semantic elements (`<button>`, `<nav>`, `<main>`, `<label>`) over `<div>`/`<span>` with handlers -- they bring focusability, keyboard activation, and roles for free.
- Any element with a `@click` that is not a native interactive element must also be keyboard-operable: add `tabindex="0"`, a `role`, and a paired `@keydown` (Enter/Space). Prefer just using a `<button>`.
- Provide `aria-*` only to fill gaps semantics can't: `aria-label` for icon-only controls, `aria-expanded`/`aria-controls` for disclosure widgets, `aria-live` for async status.
- Manage focus on route changes, dialog open/close, and dynamic content -- move focus to the new context and restore it on close.

```vue
<!-- Bad -- div as a button: not focusable, not keyboard-operable, no role -->
<div class="btn" @click="submit">Save</div>

<!-- Good -- native button -->
<button type="button" @click="submit">Save</button>

<!-- Good -- icon-only control labelled, focus restored on close -->
<button :aria-label="t('close')" @click="close">
  <CloseIcon aria-hidden="true" />
</button>
```

## Performance

Defer optimization until you measure, but reach for the built-ins when a real cost shows up:

- `v-once` for content that renders once and never updates (static headers, rendered markdown).
- `v-memo` to skip re-rendering large list rows when their dependencies are unchanged.
- Virtualize long lists (e.g. `vue-virtual-scroller`, TanStack Virtual) -- render only visible rows instead of thousands of nodes.
- `defineAsyncComponent` to code-split heavy or rarely-used components (modals, editors, charts) so they load on demand.

```typescript
// Good -- code-split a heavy component out of the initial bundle
const ChartPanel = defineAsyncComponent(() => import('@/components/ChartPanel.vue'))
```

```vue
<!-- Good -- v-memo skips rows whose tracked values are unchanged -->
<div v-for="row in rows" :key="row.id" v-memo="[row.id, row.selected]">
  {{ row.label }}
</div>
```

## Async Setup and Error Boundaries

A component may `await` directly in `<script setup>` (top-level await makes it an async component). Render such components inside `<Suspense>` so a parent controls the loading state via the `#fallback` slot, instead of every child managing its own spinner.

```vue
<!-- Parent -->
<template>
  <Suspense>
    <UserDashboard />
    <template #fallback><Spinner /></template>
  </Suspense>
</template>
```

Errors thrown during render, in lifecycle hooks, or in a resolving async setup propagate up the component tree. Catch them with `onErrorCaptured` in an ancestor to build an error boundary — return `false` to stop propagation and show a fallback UI instead of a blank screen. (Vue Query / try-catch handle *data* errors; this catches *render/setup* errors that data libraries can't.)

```typescript
const error = ref<unknown>(null)
onErrorCaptured((err) => {
  error.value = err     // show fallback UI
  return false          // stop the error from propagating further
})
```

## Testing

Test components through their public behavior -- rendered DOM, user interaction, emitted events -- not internal refs, computeds, or method calls. Use Vitest with Vue Testing Library (preferred for behavior-first queries) or `@vue/test-utils`. Query by role/label/text the way a user would; never assert on `wrapper.vm` internals.

```typescript
// Good -- behavior through the DOM (Vue Testing Library + Vitest)
import { render, screen } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import Counter from './Counter.vue'

test('increments and emits on click', async () => {
  const { emitted } = render(Counter, { props: { start: 0 } })

  await userEvent.click(screen.getByRole('button', { name: /increment/i }))

  expect(screen.getByText('Count: 1')).toBeInTheDocument()
  // Counter declares `defineEmits(['change'])` and emits the new value
  expect(emitted('change')?.[0]).toEqual([1])
})

// Bad -- reaching into internals couples the test to implementation
const wrapper = mount(Counter)
expect(wrapper.vm.count).toBe(0) // breaks on any refactor, asserts nothing a user sees
```

## Scoped Styles

Always use `<style scoped>` to prevent style leakage. Use `:deep()` sparingly when styling child component internals.

```vue
<style scoped>
.container {
  padding: 1rem;
}

/* Only when unavoidable */
:deep(.child-class) {
  color: red;
}
</style>
```
