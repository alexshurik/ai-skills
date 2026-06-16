# Vue 3 Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Applied on top of the JS/TS reviewer profile when the project imports `vue`.

## Linting

Run Vue-specific checks alongside the JS/TS lint pipeline:

```bash
# Vue-specific eslint plugin (should be in project config)
npx eslint --ext .vue,.ts,.tsx src/ 2>/dev/null | head -500

# vue-tsc — type-check SFC templates + <script setup> (plain `tsc` does NOT check templates)
npx vue-tsc --noEmit 2>/dev/null || echo "vue-tsc check skipped"
```

> The JS/TS reviewer profile's web-app tools apply here too — run **@axe-core/playwright** for accessibility (Vue's a11y plugin only catches static template issues, not runtime DOM) and Lighthouse CI for Core Web Vitals.

### eslint-plugin-vue

Verify the project eslint config includes `plugin:vue/vue3-recommended` (or `vue3-strongly-recommended` at minimum). Key rule sets:

- `vue/component-api-style` -- enforce Composition API
- `vue/define-macros-order` -- consistent ordering of defineProps/defineEmits
- `vue/no-unused-refs` -- detect unused template refs
- `vue/no-mutating-props` -- catch prop mutation
- SFC block ordering (`vue/block-order`) and similar layout rules are lint-owned — leave them to eslint-plugin-vue, don't hand-review them

## Vue 3 Code Review Checklist

### Composition API
- [ ] All new components use `<script setup>` (no Options API)
- [ ] No `this` keyword in `<script setup>` blocks
- [ ] Reactive state uses `ref()` / `computed()` (not standalone `reactive()` for simple values)
- [ ] No destructuring of `reactive()` objects without `toRefs()` (props destructure is reactive in 3.5 — `toRefs(props)` is obsolete)
- [ ] v-model implemented with `defineModel()`, not manual `modelValue` prop + `update:modelValue` emit boilerplate
- [ ] Prop defaults via destructuring default (`const { count = 0 } = defineProps(...)`), not `withDefaults`
- [ ] Template refs bound with `useTemplateRef('name')` (3.5), not a manually-matched `ref(null)`
- [ ] DOM read after a state change waits for flush (`await nextTick()` / `flush: 'post'`)
- [ ] Destructured prop passed into a fn/composable is wrapped (`() => x` / `toRef(() => x)`), not passed by value

### Server State (when the project uses Vue Query — a stack choice, recommended)
- [ ] Server reads/writes routed through Vue Query (`useQuery` / `useMutation`), not hand-rolled fetch-in-`onMounted` with manual loading/error/cache state
- [ ] Query keys are computed refs that react to parameter changes
- [ ] Mutations invalidate relevant query caches on success

### Client / Global State (Pinia recommended — a stack choice)
- [ ] Shared client state in a store, not an ad-hoc `reactive()`/`ref()` singleton (bypasses devtools/SSR/HMR)
- [ ] Stores destructured via `storeToRefs()` (state/getters), not plain destructuring
- [ ] Client/server split kept: store holds client state, server cache holds server state

### Security
- [ ] No `v-html` on untrusted / user-influenced data (sanitized via DOMPurify if rich HTML required)
- [ ] No untrusted strings bound to `:href` / `:src` without protocol validation

### Accessibility
- [ ] Semantic elements used over `<div>`/`<span>` with handlers
- [ ] Non-native interactive elements with `@click` are keyboard-operable (`@keydown`, `tabindex`, `role`)
- [ ] Icon-only controls have `aria-label`; disclosure widgets have `aria-expanded`/`aria-controls`
- [ ] Focus managed on dialogs, route changes, and dynamic content

### Performance
- [ ] Heavy / rarely-used components code-split via `defineAsyncComponent`
- [ ] Long lists virtualized; `v-memo` / `v-once` used for expensive static or stable renders

### Async and Error Boundaries
- [ ] Components with top-level `await` in `<script setup>` rendered inside `<Suspense>` (parent owns the loading fallback)
- [ ] Render/setup errors caught with an `onErrorCaptured` boundary in an ancestor (fallback UI, not a blank screen)

### Testing
- [ ] Components tested through DOM / behavior, not internals (`wrapper.vm`, private refs)
- [ ] Queries by role / label / text (Vue Testing Library or `@vue/test-utils` + Vitest)

### Component Quality
- [ ] Single responsibility -- one concern per component
- [ ] `<script setup>` under 200 lines (extract composables or child components)
- [ ] Props typed with `defineProps<{...}>()`
- [ ] Emits typed with `defineEmits<{...}>()`
- [ ] `v-for` always paired with a stable `:key` (not array index)
- [ ] Complex template expressions moved to computed properties

### Reactivity
- [ ] No destructuring of `reactive()` objects without `toRefs()` / `toRef()` (props excepted — reactive in 3.5)
- [ ] No reassignment of a `reactive()` object (mutate in place or use `ref()`)
- [ ] `watch` / `watchEffect` callbacks cleaned up (no memory leaks)
- [ ] `watch` vs `watchEffect` chosen correctly; `flush: 'post'` when reading updated DOM
- [ ] Side effects use watchers; derived values use `computed` (not watchers)
- [ ] Large / non-reactive payloads use `shallowRef` / `shallowReactive`
- [ ] `Ref<T> | T` accepted in composable parameters (using `toValue()`)
- [ ] Props never mutated (emit to parent or copy to local state)

### Styling
- [ ] `<style scoped>` on all components (no unscoped styles leaking)
- [ ] `:deep()` usage is minimal and justified

### Type Safety
- [ ] `provide` / `inject` use typed `InjectionKey<T>`
- [ ] Missing injection handled (throw or fallback, not silent `undefined`)
- [ ] Route params typed (not raw `string` from `useRoute().params`)

### Structure
- [ ] Composables in `composables/` directory, named `use*`
- [ ] API calls go through centralized client, not direct `fetch`/`axios`
- [ ] Route components lazy-loaded with `() => import()`

## Anti-Patterns to Flag

| Pattern | Severity | Fix |
|---------|----------|-----|
| Options API in new component | **MAJOR** | Rewrite with `<script setup>` Composition API |
| Hand-rolled fetch + manual loading/error/cache where the project standardized on Vue Query | **MAJOR** | Route through `useQuery`/`useMutation` |
| Manual `modelValue` + `update:modelValue` wiring instead of `defineModel()` | **MINOR** | Replace with `defineModel()` |
| `withDefaults` instead of destructuring default (3.5) | **MINOR** | `const { x = 0 } = defineProps(...)` |
| Manually-matched `ref(null)` template ref instead of `useTemplateRef` (3.5) | **MINOR** | Use `useTemplateRef('name')` |
| `toRefs(props)` to "preserve" prop reactivity (obsolete in 3.5) | **MINOR** | Destructure props directly; wrap with `() => x` when passing |
| Top-level `await` component not wrapped in `<Suspense>` | **MAJOR** | Wrap in `<Suspense>` with a `#fallback` |
| No `onErrorCaptured` boundary around render/setup-error-prone subtree | **MINOR** | Add an error boundary with fallback UI |
| Destructured `reactive()` object (lost reactivity) | **BLOCKER** | Use `toRefs()` or access via dot notation |
| `v-html` on untrusted / user-influenced data | **BLOCKER** | Use `{{ }}` interpolation or sanitize (DOMPurify) |
| Reassigning a `reactive()` object | **MAJOR** | Mutate in place or use `ref()` |
| Destructured Pinia store state without `storeToRefs()` | **MAJOR** | Wrap state/getters in `storeToRefs()` |
| Ad-hoc reactive singleton for shared state | **MAJOR** | Use a Pinia store |
| Untrusted string in `:href`/`:src` (e.g. `javascript:`) | **MAJOR** | Validate protocol before binding |
| Non-native interactive element without keyboard support | **MAJOR** | Use `<button>`, or add `@keydown`/`tabindex`/`role` |
| Test asserting on component internals (`wrapper.vm`) | **MINOR** | Test via rendered DOM and emitted events |
| `v-for` without `:key` or with index key | **MAJOR** | Add stable unique key |
| Unscoped `<style>` | **MAJOR** | Add `scoped` attribute |
| Untyped `inject()` without `InjectionKey` | **MAJOR** | Create typed `InjectionKey<T>` |
| Complex expression in template | **MINOR** | Extract to `computed()` |
| `<script setup>` > 200 lines | **MINOR** | Split into smaller components or composables |
| Direct DOM manipulation (`document.querySelector`) | **MAJOR** | Use template refs and Vue bindings |
| Prop mutation (modifying props directly) | **BLOCKER** | Emit event to parent, or use local copy |
| Watchers without cleanup (intervals, listeners) | **MAJOR** | Return cleanup in `onUnmounted` or `watchEffect` |
| `reactive()` for primitive values | **MINOR** | Use `ref()` instead |

## Tool Finding Severity Mapping

| Tool | Condition | Severity |
|------|-----------|----------|
| eslint-plugin-vue | `vue/no-mutating-props` | **BLOCKER** |
| eslint-plugin-vue | `vue/no-v-html` (untrusted source) | **BLOCKER** |
| eslint-plugin-vuejs-accessibility | `click-events-have-key-events` | **MAJOR** |
| eslint-plugin-vue | `vue/no-side-effects-in-computed-properties` | **BLOCKER** |
| eslint-plugin-vue | `vue/require-v-for-key` | **MAJOR** |
| eslint-plugin-vue | `vue/no-unused-components` | **MINOR** |
| eslint-plugin-vue | `vue/component-api-style` violation | **MAJOR** |
| eslint-plugin-vue | `vue/no-unused-refs` | **MINOR** |
| vue-tsc | type error in `.vue` file | **BLOCKER** |
