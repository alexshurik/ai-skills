# UI: Anti-Slop Design Rules

Framework-agnostic rules for building UI that does **not** read as machine-generated.
Applies on top of any framework/language profile whenever the work touches UI
(React, Vue, Svelte, Angular, Solid, Tailwind, or plain HTML/CSS). Detection and
audit detail live in [`catalog.md`](catalog.md); these are the rules you build TO.

## Why AI UI looks generic (read this first)

An LLM writes UI **locally** — each fragment collapses to the **median of the training
data**, which is where indigo gradients, emoji icons, a shadow on every card, `13px`
paddings, and three grays for one label come from. **One disease behind every symptom: a
default instead of a decision.** The cure: decide once, put it in a system primitive
(token, theme value, shared component), then **reuse the primitive, never re-invent the
value in a component.**

> These rules remove the *generic*; they don't add *taste* — that stays with the designer
> (see [Clean ≠ character](#16-clean--character-the-8020-rule)).

**Clean to the project's own system.** Every fix means "use THIS repo's tokens / theme /
components" — the example names below (`--color-accent`, `.text-caption`) are illustrative,
not mandated. If a design system exists, fixes MUST use it; if none does, don't invent
hexes ad hoc — propose a minimal one (capped palette, one type pair, spacing scale) and ask
for the brand accent rather than substituting your own.

---

## 1. One source of truth — decide once, reuse the token

- **Never introduce a raw value where a system primitive exists.** No `#hex`, no raw
  `px`/`rem`, no literal shadow in a component when a token/theme value covers it.
- **If the needed primitive is missing, add the primitive — not a literal in the
  component.** A one-off value in a component is the slop; the fix is a named token.
- **No fallback literals.** `var(--color-danger)`, never `var(--color-danger, #dc2626)`
  — a fallback silently returns an off-system color and hides a typo in the token name.
- **No ghost tokens.** Don't reference a variable that isn't defined; without a fallback
  it silently breaks the property. Reference a token only after it exists.
- **One system, not two.** If a framework theme layer (a MUI/Chakra theme, Tailwind
  config, a `themeOverrides` object) sits alongside a token file, it must *derive from* the
  tokens — never hand-sync two definitions of the same value; they drift.

```css
/* Bad — literal + fallback hex hides a broken token name */
.btn { background: var(--color-primary, #6366f1); border-radius: 10px; }

/* Good — real token, real scale value */
.btn { background: var(--color-accent); border-radius: var(--radius-md); }
```

## 2. Color — one accent, neutral by default

- **One ownable accent.** Exactly one accent color "calls" the user to act; everything
  else is neutral. Don't *default* to the framework's accent (Tailwind `indigo/violet-500`,
  shadcn zinc-on-untouched-theme) — but if the brand genuinely is that hue, that's a
  decision, not slop. With no brand tokens, ask; don't ship the default unexamined.
- **Neutral is the default state.** Color means "look here." A gray row is normal; color
  only what genuinely needs attention. A rainbow of status colors is slop.
- **Accent budget: ≤ 2 visible uses per screen**, only on an interactive element or a
  key figure. Decorative icons are muted, not filled with accent. Accent smeared across
  seven elements stops calling anything.
- **Muted semantics.** Keep danger/success/warning desaturated and systematic; don't
  crank saturation in a component. **Default** base colors to a slightly warm/cool-mixed
  neutral rather than pure `#000`/`#fff` — *unless* the brand deliberately chooses true
  black/white (OLED, brutalist, print-like); a documented choice is not slop.
- **Two grays, each with ONE job.** Pick one token for *supporting text you read*
  (captions, field labels) and one for *de-emphasized meta you skim past* (timestamps,
  placeholders, disabled). One role → one token; never choose a gray by eye per
  component.
- **Color is role-based tokens that resolve per theme.** Reference semantic roles
  (surface / on-surface / accent), not one theme's literal values, so light and dark both
  work. Baking light-mode hexes into components is why AI dark modes break.

## 3. Typography — hierarchy by weight and color, not size

- **Establish hierarchy with weight and color, not font-size** (Refactoring UI). Most
  UIs need ~2–3 weights total; don't invent more. Reserve large sizes for the one or two
  figures that truly lead. When you *do* jump size, make it a real jump (≈3×, not 1.25×)
  reinforced by a weight gap wide enough to read (use the extremes your type family
  actually ships — don't force a 200 that hurts legibility) — a 16→18→20 ramp at one weight
  reads as flat and generated.
- **Secondary text has exactly ONE treatment.** Not `color: gray-500` inline here and a
  muted token there. The role of "secondary" is decided at the class/token level, once.
- **Type is set with classes/tokens only** — no inline `font-size` / `font-weight` /
  `font-family` in components.
- **≤ 3 font families per screen**; pair an expressive display with a restrained body,
  and keep any outlier family (e.g. a mono) to at most two roles (numbers + headings).
  Body ≥ 16px, line-height 1.5–1.8, prose measure 45–75ch. Don't *reflexively* reach for
  the current "tasteful" defaults (Geist, Space Grotesk, Instrument Serif) any more than
  Inter/Roboto — a swap to the new default font is still a default. (If the brand genuinely
  is one of them, choose it; don't fall into it.)
- **Uppercase in at most one role**, and every uppercase run MUST carry
  `letter-spacing ≥ 0.06em` — untracked caps "clump" and read as slop. Everything else
  is sentence case.
- **Numbers use a tabular/number primitive** (`font-variant-numeric: tabular-nums`), set
  once via a class — never hand-assembled as `font-mono + tabular-nums + 600` per site.

```html
<!-- Bad — inline size + a hand-picked gray for secondary text -->
<span style="font-size:0.875rem; color:#6b7280">Not distributed</span>

<!-- Good — the one secondary-text class the system defines -->
<span class="text-caption">Not distributed</span>
```

## 4. Spacing — one 4/8px scale, no off-grid values

- **All spacing comes from one scale** (a 4px or 8px grid, exposed as tokens/theme
  steps). Always reference the scale, even when the value happens to match it.
- **No off-grid half-steps** — `6px`, `10px`, `14px`, `18px`, `0.375rem`, `0.625rem`.
  Numbers that never repeat are the first sign of generation without constraints. Round
  to the scale; don't mint a new value.
- **Space carries meaning (proximity):** space within a component < between components <
  between sections. When unsure, take the gap that feels enough and roughly double it.

## 5. Radius — a scale, bound to element type

- **One radius scale**, and each element type gets a fixed step: inputs/buttons/small
  controls share one, cards/modals a larger one, large sections a larger one, and
  `full` is **only** for avatars/toggles/round badges. Don't make everything a pill.
- No literal radii (`7px`, `1.25rem`, `10px`) mixed through components.

## 6. Elevation, borders & shadows — one separation method per level

This is the "outlines and shadows everywhere" problem. Do **not** stack a full set
(visible border + heavy shadow + fill) on every nesting level. A row inside a card
inside a page should not each get the same treatment.

- **Preference order for separating regions:** whitespace → background shift → soft
  shadow → border, in that order. Reach for the next only when the previous isn't enough.
  (A border-first, dense/enterprise system is a legitimate choice — the rule is against
  *stacking* all four by reflex, not against borders.)
- **One elevation system, ≤ 2 meaningful steps.** Shadow on at most ~60% of a level's
  containers. A shadow on everything is noise, not hierarchy.
- **Shadows come from tokens** — never inline `box-shadow: 0 2px 4px rgba(...)` per
  component.
- **No colored `border-left` accent strip.** A colored bar down the left of a
  card/toast, clipped by the corner radius, is a canonical AI-dashboard tell. Convey
  status with fill, an icon, or a full outline. (A neutral 1px divider between controls
  is fine — that's not this.)

```css
/* Bad — border + shadow + fill stacked on every level */
.row { border: 1px solid var(--border); box-shadow: var(--shadow); background: var(--card); }
/* Good — one method; the row lifts only on hover */
.row { background: var(--surface); }
.row:hover { background: var(--surface-hover); }
```

## 7. Icons — one line set, never emoji

- **No emoji as icons or status** (`✅ 🔥 📊 💵 🚀`). Emoji drag in 5 uncontrolled colors
  each, break the one-accent rule, and read as amateur. Status is color + text (+
  optional icon), not a picture-emoji.
- **One icon library**, one stroke style. Size by context (≈16 in text/rows, 18–20 in
  headings, 24 for large accents) and don't mix sizes in one row. Color via
  `currentColor` or a token — never a hardcoded `stroke="#000"` in markup.
- Mixing two icon libraries on one screen is itself a tell — pick one.
- Emoji are allowed **only inside user-generated content**, never as a control label or
  status indicator.

## 8. Casing & microcopy — one casing, product voice

- **One casing for UI chrome: sentence case** for buttons, menu items, field labels
  ("Add member", "Group settings"). The only uppercase is the single eyebrow role (§3).
  Title Case next to sentence case next to ALL-CAPS on one screen is slop.
- **Verb-first, short.** "Finish", not "Click here to finish". Don't explain the obvious
  with paragraph-long hints.
- **No marketing buzzwords** — Empower, Seamless, Unlock, Supercharge, Streamline,
  Leverage, Elevate. **CTA uses the product's verb** ("Start tracking", not the generic
  "Get started"). Numbers in copy must be real, not invented precision.

## 9. Badges, chips, status — neutral unless meaningful

- Neutral by default; color only on a state that genuinely matters. Not every row a
  differently-colored badge (including the "normal" state, which should be gray).
- No default pastel status pills (`bg-green-100 text-green-800 rounded-full` cloned for
  every state). Derive status styling from state tokens; make shape/treatment a decision.

## 10. Motion — clarify causality, don't decorate

- **Animation exists to clarify cause and effect, not to ornament.** Apply it to a
  specific moment (a section appearing), not to every element.
- **`transition` targets specific properties — never `transition: all`**, and no blanket
  `hover:scale-105` / `hover:shadow` on everything ("dead hovers" with an effect but no
  meaning). One memorable micro-interaction (a button nudges 2px, a number counts up)
  beats a carpet of animation.
- **Keep it fast and cheap.** Interactions ≤ ~200ms; animate `transform`/`opacity` only —
  never layout properties (`width/height/margin/padding`), which thrash. Avoid *reflexive*
  bounce/elastic easing on chrome; spring easing is legitimate when it's the brand's voice.
- **`prefers-reduced-motion` is mandatory** for any non-trivial motion.
- **No perpetual pulsing "live" dots.** A forever-`animate-ping`/`animate-pulse` dot next
  to "Live / Online / Active" is a reflex to seem alive. Pulse/ping only on a real live
  event (a load in progress, an arriving event), never as permanent decor.

## 11. Design all states — not just the happy path

A mature control has ~7 states: **hover, focus, active, disabled, loading, empty,
error.** AI ships one by default. **Designing the missing states is the single strongest
move against app-UI slop** — never forget empty, loading, and error.

- **Rows don't jump between states.** A row in loading/empty/error keeps the same height
  as a filled one — give the slot a fixed `min-height` and let states live inside a
  container of one size.
- **An empty state guides, it doesn't just exist.** A bare "No data" is still slop; a good
  empty state says what the thing is and offers the first action ("Add your first item"),
  optionally a template.

## 12. Affordance & control sizing

- **Underline is not a button affordance.** `text-decoration: underline` (including on
  `:hover`) is the convention for an inline link in prose, not for a button/action in UI
  chrome. Actions call via color, weight, fill/border, and target size (ghost-hover with
  a background). Reserve underline for a real `<a>` inside a paragraph.
- **Destructive ≠ ordinary.** "Delete / Leave" must not look like a routine action: use a
  danger token, separate its position, confirm it. **One primary action per row.** Add
  the variant to the shared component — don't re-style a button at the call site.
- **Adjacent controls share height.** In one row, an input, the button beside it, and a
  select are the same height — not 38 / 40 / 34. Keep control heights on a token scale
  (e.g. 40 default / 36 compact / 44 hero) and pull from it, never set height by eye.
- **Focus ring via `box-shadow`, not `outline`** — a shadow ring follows the border
  radius; `outline` doesn't. Never `outline: none` without a visible replacement.
- **Form ergonomics.** Input font ≥ 16px (smaller triggers iOS zoom-on-focus); clicking a
  label focuses its input; wrap inputs in a `<form>` so Enter submits; disable a submit
  button after submit to prevent a double-submit.

```css
/* Bad — three heights in one row */
.input { height: 38px } .btn { height: 40px } .select { height: 34px }
/* Good — one control-height token */
.input, .btn, .select { height: var(--control-h); }
```

## 13. Don't reinvent the canon

Slop also comes from **duplication**: the model writes a new component not knowing the
canonical one already exists.

- **Before writing a new UI block, check for an existing one** (component library,
  shared styles, the design system). If a toggle/checkbox/card/number treatment exists,
  use it — don't roll your own with a different border token.
- **Numbers use the number primitive**, never hand-assembled per site.
- **Missing a variant** (e.g. a `danger` button)? **Add the variant to the component**,
  don't override the base component at the usage site.

## 14. Structure — from content, not a template

- **Avoid reflexive cards-within-cards.** Separate regions with whitespace and a
  background shift, not nested boxes. Box only what is semantically a container (an input,
  one raised surface) — a selected card holding sub-items is sometimes legitimate.
- **Element counts come from the content**, not a template — 2/4/5 cards are fine;
  "exactly 3 icon-topped feature cards" is the landing-page formula.
- **Don't wrap a dense tool in a landing-page shell** — top nav links as the only
  navigation over a narrow centered column with big empty margins. Dense tools
  (consoles, dashboards, admin) want full-width content with persistent navigation —
  usually a sidebar, though a top-nav + command palette or a sub-nav also works.
- **Responsive means reflow, not just shrink.** At small widths, restack, hide-secondary,
  or reposition — a layout that only scales down (no horizontal scroll) but never reflows
  is a prototype tell.

## 15. Accessibility is anti-slop

Generated UI skips the semantics and states that real products ship — so accessibility
and anti-slop pull in the same direction.

- **Semantic HTML.** A real `<button>` for actions, not a `<div onClick>`; real headings
  (don't skip ranks `h2→h4`), lists, and landmarks. A link changes the URL, a button
  performs an action — don't swap them. A fake button is both an a11y bug and a slop tell.
- **Visible focus.** Keep a clear `:focus-visible` style; never `outline: none` without a
  replacement. Keyboard users must see where they are.
- **Overlays manage focus.** A modal/popover traps focus, returns it to the trigger on
  close, dismisses on `Escape`, and locks background scroll — focus *management*, not just
  a ring.
- **Contrast.** Body text meets WCAG 4.5:1 (large text ≥ 3:1); non-text — UI borders,
  icons, focus rings — meets ≥ 3:1 (or APCA Lc as guidance). This rules out low-gray
  captions and neon-on-dark that read as generated.
- **Target size.** Interactive targets ≥ ~24–44px; don't ship tap targets only a mouse
  can hit.
- **Labels & motion.** Every input has a programmatic label; icon-only buttons have an
  accessible name; motion respects `prefers-reduced-motion` (§10).

## 16. Clean ≠ character (the 80/20 rule)

Removing slop is only half. The core complaint about AI design is holistic — "they all
look the same." A sterile-but-neutral screen still reads as generated. So after cleanup:

- **~80%** proven, restrained patterns (everything above).
- **~20% — one bold decision per screen:** a characterful type pairing, an unusual
  proportion, one deliberate accent move — chosen, not reflexive.
- **+ one memorable micro-interaction** and **a voice in the microcopy** (§8).

This profile removes the typical; it does not supply taste. Where cleanup leaves a screen
empty and sterile, that is the place for a bold decision — not one more neutral default.

**Swapping one default for another is not de-slopping.** The old tell was the purple
gradient; the current one is cream + serif + sage (the "tasteful AI" look). A screen that
could belong to any product still has no point of view. The fix is a decision that fits
*this* brief — not the next fashionable palette. If you can't tell which product a
screenshot is from, it isn't done.

---

## Numeric thresholds (cheat sheet)

*Canonical values live in [`catalog.md`](catalog.md#numeric-thresholds-summary); this is a
quick copy — if they ever disagree, catalog wins.*

- Accent: ≤ 2 visible uses/screen; ≤ ~5% of viewport area (atmospheric/marketing up to ~20%).
- Raw hex outside tokens/theme: target 0 in components.
- Fonts: ≤ 3 families; outlier ≤ 2 roles; body ≥ 16px; line-height 1.5–1.8; prose 45–75ch.
- Uppercase: `letter-spacing ≥ 0.06em`; one role.
- Shadows: ≤ 2 elevation steps; shadow on ≤ ~60% of a level's containers.
- Spacing: 4/8px scale only, no half-steps.
- Adjacent controls: equal height.
- Body contrast: WCAG 4.5:1 or APCA Lc ≥ 75 (90 preferred).
- Smoke test: no horizontal scroll from 320–1920px.

## Pre-build checklist

- [ ] No emoji as icons/status; one icon set, one size per context, token color
- [ ] No `#hex` in components — tokens/theme only; no fallback hexes; no ghost tokens
- [ ] Secondary text has one treatment; no inline `font-size`/`weight`/`family`
- [ ] Hierarchy by weight + color, not size; ≤ 3 families; caps carry ≥ 0.06em tracking
- [ ] Spacing from the scale, no off-grid half-steps; radii from the scale
- [ ] One separation method per level; no border+shadow stacked everywhere; no colored border-left
- [ ] Accent ≤ 2 uses/screen; neutral is the default; no rainbow status pills
- [ ] One casing (sentence case); no buzzwords; CTA uses the product verb
- [ ] All states designed: hover/focus/active/disabled/loading/empty/error; rows don't jump
- [ ] Underline ≠ button; destructive is set apart; adjacent controls share height
- [ ] Canon checked before writing a new block; numbers via the number primitive
- [ ] Regions separated by space + bg shift, not nested boxes; layout from content
- [ ] Semantic HTML, visible focus, 4.5:1 contrast, adequate target size
- [ ] One deliberate bold decision left on the screen (80/20)

Full tell-by-tell detection and fixes: [`catalog.md`](catalog.md). Review-side checks:
[`reviewer.md`](reviewer.md).
