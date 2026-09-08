# UI Composition Contract

Read this contract for a new or materially reworked page, layout, navigation,
responsive flow, or cross-state composition. It complements the local visual
system; it does not prescribe component names, breakpoints, or a product style.

## Name composition owners before building

For each applicable concern, identify one primary owner from approved project
guidance or the feature design:

| Concern | Owner decides |
|---|---|
| Application chrome and effective scroll | landmarks, persistent navigation, fixed regions, and which element owns scrolling |
| Outer page frame | content rail, width mode, page insets, and section rhythm |
| Page title and action region | accessible page title, visible heading treatment, supporting context, and the primary-action slot |
| Major surface | header/content/footer attachment, elevation level, and whether nested surfaces are allowed |
| Route or local navigation | current-state semantics, keyboard behavior, authorization filtering, and responsive form |
| Recurring domain representation | reading order and stable title/value/meta/action tracks for the same entity across screens |
| Specialized interaction | complete keyboard, pointer, focus, loading, disabled, and error behavior for controls such as disclosure, selection, or search |

Use project-native owner names. An owner can be an existing component, layout, or
documented page responsibility; do not create a wrapper merely to fill the table.
Create or extend a shared primitive only when it owns a stable policy or has real
reuse value.

The composition is incomplete when two layers independently decide the same
concern. Common conflicts include:

- both the shell and route define the visible primary action;
- both the frame and route root define outer width, centering, or page padding;
- a surface contains another equally elevated surface by default;
- routes render the same domain entity with incompatible reading or value tracks;
- a page recreates navigation or interaction semantics already owned by a shared
  primitive.

Record intentional exceptions in project authority with a stable ID, exact scope,
rationale, source/decision owner, and expiry or review trigger. An exception is not
permission to copy the pattern elsewhere.

## Preserve hierarchy and action truth

- Define one primary user task and one accessible page title. The `h1` may be
  visually hidden when visible route text would add no information; do not add a
  redundant heading to satisfy a visual quota.
- Allow **at most one visible primary action** in the relevant composition at a
  viewport. Zero is correct for a read-only or inspection surface when no immediate
  action belongs there.
- Treat shell, page, empty-state, and responsive versions of the same action as
  replacements, not simultaneous duplicates.
- Render controls only when their action is available. Recovery controls belong to
  failure states, not permanent navigation.
- Keep primary → secondary → metadata order and a small, intentional set of
  alignment axes through responsive reflow.

## Reuse the nearest domain canon

Before designing a new representation, find the closest existing view of the same
domain entity in a comparable context, not only the nearest generic card or button.
Reuse its information priority, vocabulary, value formatting, interaction model,
and state treatment. If the new context needs a variant, make the difference
explicit and preserve the shared semantic core.

Do not make a new route, viewport, or data source an excuse for a second visual
language. Conversely, do not force unrelated entities into one component merely
because their boxes look alike.

## Treat state and copy as composition

- Internal mechanics are not user content. Do not surface request offsets, cache
  refreshes, successful background work, or implementation terminology unless they
  change the user's next decision.
- Success is quiet by default. Announce it when the result is otherwise ambiguous
  or changes what the user should do next.
- Place errors according to origin: field errors beside the field, action failures
  near the action or in transient feedback, retained-data refresh failures without
  erasing usable content, and initial no-data failures as explicit recoverable
  errors rather than false empty states.
- An empty state explains what belongs there and offers at most one useful next
  action when one exists.
- A skeleton mirrors the destination's meaningful geometry—text lines, metadata,
  values, and actions—so loading does not recompose the page.
- Headings and labels answer the user's immediate question. Use the same term for
  the same entity or outcome across screens; remove defensive or duplicated helper
  copy that does not change understanding.

## Design responsive pressure cases

Responsive proof covers priority and structure, not only the absence of a scrollbar.
For layout-sensitive content, include realistic pressure cases such as long labels,
large or negative values, localization expansion, dense metadata, and retained data
with an error. Critical values and actions must remain perceivable; allow deliberate
wrapping or reflow rather than clipping them to preserve desktop geometry.
