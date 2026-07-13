# Anti-Slop UI Catalog — slop tells, detection & fixes

The reference behind [`coder.md`](coder.md) (build to these) and [`reviewer.md`](reviewer.md)
(audit against these). Each **tell** is a pattern that makes generated UI recognizable as
machine-made. Universal and framework-agnostic: the detections use Tailwind/shadcn/CSS
because that is the lingua franca of AI-generated UI, but the principle holds for any
stack. Fixes always resolve to the **project's own** tokens/design system.

**Severity:** `ban` (always wrong — fix) · `system` (systemic check — align to the
system) · `flag` (raise as a question, don't hard-fail).

**Medium:** `code` (grep/read the source — most reliable) · `visual` (screenshot/render,
for what grep can't catch: rhythm, composition, accent area). **[grep]** marks a
deterministic static check.

**Weight** = how many independent research sources document the tell (see
[Sources](#sources)); **[original]** marks a tell we add that isn't in the external
literature. A grep match is a *candidate*, never a verdict — see
[Calibration](#calibration--the-new-default-is-the-next-tell).

---

## Bans (fix whenever present)

### T6 · Default-palette accent / unbriefed gradient — ban · weight 6/6 (most-cited)
- **Looks like:** primary in default Tailwind indigo/violet; blue-violet diagonal
  gradients. Documented origin: Tailwind UI shipped `bg-indigo-500` buttons by default,
  and models converged on that safe average.
- **Detect [grep]** `code`: exact hexes `#6366f1 #4f46e5 #4338ca #3730a3 #8b5cf6 #7c3aed
  #a855f7` (+`#818cf8`; `#7F5AF0` is a commonly-cited but weakly-sourced "AI purple" — low confidence) outside `:root`/theme tokens; `bg-indigo-* bg-violet-*
  bg-purple-*` on interactive elements; `linear-gradient(135deg` indigo→blue; the combo
  `bg-clip-text text-transparent bg-gradient-to-r` (gradient-on-text).
- **Fix:** one ownable accent from the project's tokens/`DESIGN.md`. No tokens → ask for
  the brand color; never substitute your own.

### T16 · Untouched shadcn/Tailwind kit — ban · weight 4/6 (#1 in complaint data)
- **Looks like:** default zinc/slate base, `--radius: 0.5rem`, a card as
  `rounded-2xl shadow-lg p-6` straight from the box.
- **Detect [grep]** `code`: shadcn default theme values with no customization;
  `rounded-2xl shadow-lg` carpeted across cards.
- **Fix:** the theme MUST be touched (palette, radii, type from the project's system).
  The kit is a start, not a finish.

### T1 · Colored border-left accent strip — ban · weight 4/6 ("canonical AI dashboard tile")
- **Looks like:** a colored bar down the left of a card/toast, clipped by the corner radius.
- **Detect [grep]** `code`: `border-l-4` / `border-left:` with a color + `rounded`.
- **Fix:** drop either the radius or the strip; convey status with fill, an icon, or a
  full outline. (A neutral 1px divider between controls is not this.)

### T2 · Emoji instead of icons in UI chrome — ban · weight 4/6
- **Looks like:** 🔥📊💵✨🚀 in stat cards, features, steps, bullets.
- **Detect [grep]** `code`: emoji outside user-generated content; mixing 2+ icon libraries
  is the same tell.
- **Fix:** one project icon library, one size, token color. Emoji only in user content.

### T17 · 100vh centered hero / universal landing template — ban · weight 4/6
- **Looks like:** `min-height:100vh` hero with everything centered; the formula
  hero → 3 feature cards → stats → testimonials → pricing → CTA.
- **Detect [grep]** `code`: `min-h-screen` + centering on a hero; exactly 3 icon-topped
  cards in a row. `visual`: the recognizable section rhythm.
- **Fix:** element count from the content (2/4/5 are fine), structure from the task, not a
  template; asymmetry as a deliberate choice.

### T10 · Country flags in operational tables — ban · [original]
- **Looks like:** a flag next to a region (US-East, EU-West) in a table/list.
- **Detect [grep]** `code`: flag emoji/icons next to region names. `visual`: colored flags
  in rows.
- **Fix:** region as text or a neutral glyph in token color.

### T23 · Pulsing status dot (fake live/online indicator) — ban · [original, frequent reflex]
- **Looks like:** a small colored dot with a perpetual animation (`animate-ping` ring or
  `animate-pulse` breathing) next to "Live / Online / Active / Running". A reflex to seem
  alive.
- **Detect [grep]** `code`: `animate-ping`/`animate-pulse` on small `rounded-full`
  (`h-2/h-3/w-2/w-3`); `@keyframes ping|pulse` bound to indicators. `visual`: a dot that
  breathes or rings with no real event behind it.
- **Fix:** remove the animation; the dot is static (solid, state token). Pulse/ping only
  on a real live event (a recording in progress, an arriving event), never as permanent
  decor. Clean the pill itself per T4.

### T24 · Underline as button/action affordance — ban · [original]
- **Looks like:** an action control ("Add credits", "Load more", "Clear filters", a
  toolbar action) styled as underlined text or given `underline` on hover. In mature
  products underline is the convention for an inline link in prose, not a button in UI
  chrome.
- **Detect [grep]** `code`: `text-decoration: underline` / util `underline` /
  `hover:underline` on action roles (`<button>`, `[role=button]`, `.btn*`, onClick with no
  href); `text-underline-offset` on a non-`<a>` element.
- **Fix:** button affordance via color, weight, fill/border, target size (ghost-hover
  background). Reserve underline for a real inline `<a>` inside paragraphs.

---

## System checks (align to the system)

### T14 · Default font with no pairing — system · weight 5/6
- **Looks like:** Inter/Roboto/Open Sans/Poppins/Lato/Geist or the system stack, flat
  across everything.
- **Detect [grep]** `code`: `font-family` from the default list; >3 families on a page.
- **Fix:** pair an expressive display with a restrained body; ≤3 families, outlier ≤2
  slots. The font ranks low in complaints but the fix is the cheapest way out of slop.

### T3 · Uppercase micro-label — system · weight 3/6
- **Looks like:** `UPPERCASE + tracking` on every label (fields, table heads, eyebrows).
- **Detect [grep]** `code`: (a) uppercase WITHOUT `letter-spacing ≥ 0.06em` — a lint
  error; (b) caps+tracking in 2+ roles — slop density.
- **Fix:** caps in at most one role; every caps run carries `letter-spacing ≥ 0.06em`;
  everything else sentence case.

### T4 · Default pastel status pills — system · [original] (proxy in packs: pastel-everything)
- **Looks like:** "● Running" in a pastel pill `bg-green-100 text-green-800 rounded-full`,
  identical across all states.
- **Detect [grep]** `code`: a pastel pill — `bg-{green|red|yellow|gray}-100` + matching
  `text-{…}-800` + `rounded-full` on statuses (illustrative; reviewer.md has the runnable
  alternation).
- **Fix:** statuses from state tokens; shape/treatment a decision, not a reflex; replace
  the hundred-level pastels.

### T5 · Shadows with no system — system · weight 4/6
- **Looks like:** `shadow-sm/md` on every card; floating elements with excessive shadows;
  uniform `rounded-2xl shadow-lg`.
- **Detect [grep]** `code`: shadow on >60% of a level's containers; >2 shadow levels.
- **Fix:** one elevation system, ≤2 meaningful levels, or flat with borders.

### T19 · Reflexive motion — system · weight 5/6
- **Looks like:** `transition-all`; blanket `hover:scale-105`; bouncy overshoot on UI;
  fade-up-on-scroll on every section; "dead hovers" (effect, no meaning); a copied "Linear
  glow".
- **Detect [grep]** `code`: `transition-all`, mass `hover:scale-105`, carpeted scroll
  animations. Motion quality is `visual`.
- **Fix:** transition specific properties only; one memorable micro-interaction instead of
  a carpet (a button nudges 2px, a number counts up).

### T20 · Color extremes & unrequested modes — system · weight 3/6 (neon dark mode)
- **Looks like:** pure `#000`/`#fff` as base colors; pastel-everything; cyan-on-dark; a
  dark mode with neon glow (and a dark mode nobody asked for).
- **Detect [grep]** `code`: `#000`/`#fff` outside tokens; neon glow shadows on dark.
- **Fix:** base colors with a slight warm/cool mix; body contrast 4.5:1 (or APCA Lc ≥ 75);
  modes as a decision. **Color is role-based tokens that resolve per theme** (surface /
  on-surface) — don't bake one theme's literal values into components, or the other mode
  breaks. Default to a slightly-tinted neutral *unless the brand chooses* pure black/white.

### T8 · Flat action weights — system · [original]
- **Looks like:** Open / Stop / Destroy as identical outline buttons.
- **Detect [grep]** `code`: destructive labels (delete/destroy/remove) styled as an
  ordinary button; >1 primary in a row.
- **Fix:** set destructive apart (danger token, position, confirmation); one primary per row.

### T9 · Accent on decoration / accent budget — system · weight 3/6
- **Looks like:** decorative icons filled with the accent; accent smeared across the screen.
- **Detect [grep]** `code`: the accent token appears 3–5× on one screen = soft-flag, 6+ =
  hard-flag (design target is ≤2); accent on non-interactive elements. Area share (cap
  ~5% of viewport, atmospheric genres up to 20%) is `visual`.
- **Fix:** accent ≤2 visible uses per screen, only on interactive elements or a key figure;
  decoration is muted.

### T11 · Jumping height on identical rows — system · [original]
- **Looks like:** a row in provisioning/empty state at a different height; rows jump.
- **Detect** `code`: conditional content changes the size of repeating rows; no
  `min-height` on the slot.
- **Fix:** fixed slot size; states live inside a container of one size.

### T12 · Reflexive hover shadow — system · (subset of T19, kept separate as a frequent web reflex)
- **Detect [grep]** `code`: mass `hover:shadow-*` with no background/border change.
- **Fix:** hover via background/border tokens; shadow only where the element truly lifts.

### T13 · Baseline drift — system · [original]
- **Looks like:** text in adjacent cells/blocks not on one horizontal line.
- **Detect** `code`: mixed `items-center/baseline/start` in one row; different line-heights
  on neighbors.
- **Fix:** one alignment principle per row; one type scale (body ≥16px, line-height
  1.5–1.8, prose 45–75ch).

### T25 · Mismatched adjacent control heights — system · [original]
- **Looks like:** interactive elements of different heights in one row (input 38, button
  40, chip 34, select 34). In mature products adjacent controls are almost always equal
  height; an input equals the button beside it.
- **Detect [grep]** `code`: different `height` on adjacent `input`/`button`/`select`/`.chip`
  in one row (toolbar, form row, input-group); no control-height tokens.
- **Fix:** one control-height scale (e.g. 40 default / 36 compact / 44 hero) in tokens; all
  controls in a row equal height; input = the button beside it.

### T26 · Grid desync across sibling cards — system · [original] (kin to T7/T11/T13)
- **Looks like:** a set of semantically identical cards (KPI metrics, stat tiles) whose
  inner elements (mini-chart, sub-label) do NOT sit on shared horizontal axes: charts of
  different heights, captions jumping card to card. The group loses grid continuity.
- **Detect [grep]** `code`: analogous inner slots of sibling cards with different
  `height`/`margin-top`; no fixed slot height for the visual. `visual`: labels on different
  baselines across the set.
- **Fix:** a shared vertical rhythm for the set — fixed slot height for the visual + equal
  spacing, so rows (label / value / visual / caption) align on Y across every card.

### T27 · Landing/SaaS shell on a dense tool — system · [original] (kin to T17)
- **Looks like:** a dense tool (resource console, admin, dashboard) wrapped in a
  lightweight-app shell: top tab-links as the only primary nav + content in a centered
  column (`max-width ~1100–1280; margin: 0 auto`) with big empty side margins. Mature
  consoles (AWS, Vercel, Render, Neon) use a persistent left sidebar + full-width content.
- **Detect [grep]** `code`: `max-width` + `margin: 0 auto` on a tool's root container;
  primary nav as horizontal top-bar `<a>`s; no persistent sidebar. `visual`: wide dead
  margins beside a dense table/dashboard.
- **Fix:** for tools with a growing number of sections and dense data — left sidebar +
  full-width (a large width cap, 1400–1600, not a narrow centered column). Top tabs are OK
  only with a subnav and full-width, not as the sole nav over a centered column.

### T21 · Copywriting slop — system · weight 3/6, fully automatable
- **Looks like:** "Empower your business", "Seamless experience"; generic CTA ("Get
  Started" instead of the product's verb); invented precise numbers; anonymous testimonials.
- **Detect [grep]:** regex `(Elevate|Unlock|Supercharge|Seamless|Empower|Streamline|
  Leverage)`; generic CTA lexicon; em-dash pileups.
- **Fix:** CTA with the product's verb ("Start tracking", not "Get started"); only real
  numbers.

---

## Flags (raise a question, don't cut)

### T7 · Row of identical stat cards — flag
- 4 KPI clones (icon + caps + number). The pattern itself is legal; flag the combination
  T7 + (T2|T3|T5|T9).
- **Fix:** hierarchy (the lead metric larger) or another format (a summary row, sparklines).

### T18 · Everything boxed, everything centered — flag · weight 2/6
- Cards-within-cards; "lazy symmetry without purpose".
- **Fix:** a card only where an entity boundary is needed; alignment from the content.

### T22 · Meme-tells: bento / glassmorphism / aurora — flag, DON'T over-weight · lowest in complaint data
- In Twitter memes these are "the" AI signs; in real complaint data they rank last;
  glassmorphism tops out at "backdrop-blur reflex".
- **Detect [grep]** `code`: carpeted `backdrop-blur`; mesh/aurora gradients.
- **Fix:** only if reflexive and off-brand. Spend weight on T16/T6 (kit, color, gradient
  text) and typography T14, not memes.

---

## Additional tells (2025–2026 wave)

The default moves. These are the tells that emerged *after* the indigo era — including
the "tasteful" replacements that are themselves becoming defaults (see
[Calibration](#calibration--the-new-default-is-the-next-tell)).

### T28 · The post-Inter "tasteful default" — system
- **Looks like:** the font trio Geist + Space Grotesk + Instrument Serif; an oversized
  italic-serif hero H1; a cream/beige surface (`#F4F1EA`/`#F5F1E8` family) paired with a
  serif display and sage/terracotta accents. The 2025–26 default that replaced indigo —
  Anthropic warns its *own* output converges on Space Grotesk "across generations".
- **Detect [grep]** `code`: `font-family` matching `Geist|Space Grotesk|Instrument Serif`;
  background in the `#F4F1EA`/`#F5F1E8` family + a serif display; `h1{font-style:italic}`
  at display size.
- **Fix:** earn the serif/warm palette from the brief; otherwise a confident sans on a
  neutral surface. Swapping indigo→cream is not a fix.
- Src: Anthropic frontend-design; impeccable; JCarterJohnson unslop-ui.

### T29 · Flat type hierarchy — system
- **Looks like:** the largest heading barely bigger than body (< ~1.25×); nothing leads.
- **Detect** `code`: largest-heading : body size ratio < 1.25×; only weights 400/600 in use.
- **Fix:** big size jumps (≈3×) separated by weight extremes (200 vs 800), or lead with
  weight/color, not a timid 16→18→20 ramp. Src: Refactoring UI; Anthropic.

### T30 · Second-order default accent (emerald/sage) — system
- **Looks like:** ban indigo and the model goes emerald/sage — the fallback after the
  fallback — not a brand-derived color.
- **Detect** `code`: accent hue clustering ~150–165° in a project that forbade purple.
- **Fix:** derive the accent from the brand, not from "what's tasteful now".

### T31 · Untinted neutrals & grey-on-color — system
- **Looks like:** zero-chroma slate/zinc greys that never took the brand's temperature;
  washed-out grey text on a colored/dark surface.
- **Detect** `code`: neutrals at OKLCH chroma ≈ 0; grey text color over a non-white bg.
- **Fix:** tint greys warm/cool; for text on a colored bg use a same-hue tint of the
  background, not grey (Refactoring UI).

### T32 · Too-uniform sizing — system (complement to T11)
- **Looks like:** the opposite of jumping rows — identical radius + padding + card height
  everywhere ("default-parameter look"), or one spacing value on >70% of nodes so nothing
  groups.
- **Detect** `code`: near-zero variance in `border-radius`/`padding` across component
  types; one dominant gap value.
- **Fix:** vary by role — tight within a group, loose between; not every surface the same box.

### T33 · Hero-as-dashboard / stat-strip — system (kin to T7/T17)
- **Looks like:** the first viewport crammed with pill clusters, icon rows, and a 3–4
  big-number stat strip.
- **Detect [grep]** `code`: a row of big-number + small-label stats (`justify-content:
  space-around`) above the fold; icon rows + boxed promos in the hero.
- **Fix:** "the first viewport must read as one composition, not a dashboard" (OpenAI); no
  cards in the hero.

### T34 · Decorative sequence markers — flag
- **Looks like:** numbered `01 / 02 / 03` section labels used as ornament.
- **Fix:** keep them only if the content truly is a sequence (a real process/timeline
  where order carries meaning). Src: Anthropic.

### T35 · Shipped placeholders & filler geometry — ban (greppable)
- **Looks like:** placeholder-CDN images (`unsplash.com`, `placehold.co`, `picsum.photos`)
  or empty/missing `src` in the "finished" build; re-drawn fake browser/phone chrome
  (3 traffic-light dots + a URL pill); decorative blob/wave SVGs with no compositional reason.
- **Detect [grep]** `code`: `src=.*(unsplash|placehold|picsum)`; `<img>` with empty/missing
  `src`; 3 small circles + an address-bar element before an image; absolutely-positioned
  `<svg><path>` of smooth beziers behind content.
- **Fix:** real assets or none; drop filler geometry.

### T36 · Motion specifics — system (extends T19)
- **Looks like:** a UI transition/animation > ~300ms; bounce/elastic easing; animating
  layout properties (`width/height/margin/padding`).
- **Detect [grep]** `code`: `transition-duration`/`animation-duration` > 300ms;
  `cubic-bezier` overshoot; `transition:` naming `width|height|margin|padding`.
- **Fix:** ≤ ~200ms interactions; animate `transform`/`opacity` only; standard easing. (Rauno)

### T37 · Invented metrics & AI copy cadence — system (extends T21)
- **Looks like:** "10× faster", "99.9% uptime", "trusted by 50k+"; em-dash pileups; the
  "It's not X, it's Y" cadence; "…theater".
- **Detect [grep]:** `\d+×|\d{2,}k\+|99\.9%|trusted by`; em-dash density; `\btheater\b`.
- **Fix:** real, sourced numbers only; plain product voice.

## Accessibility tells (a11y = anti-slop)

Generated UI ships the happy path; the missing semantics and states are both a11y
failures and slop tells. WCAG 2.2 success criteria in parentheses.

### T38 · Fake interactive elements — ban
- **Looks like:** `<div onClick>` / `<div role="button">` instead of `<button>`; a link
  that performs an action, a button that navigates.
- **Detect [grep]** `code`: `onClick` on a `div`/`span` without `role`+`tabindex`+key
  handlers; `role="button"` on a `div`.
- **Fix:** native `<button>`/`<a>`. "If it changes the URL it's a link; otherwise a
  button." First rule of ARIA: use the HTML element.

### T39 · No visible focus — ban (2.4.7 AA; 2.4.13 AAA)
- **Looks like:** `outline: none` with no replacement; invisible keyboard focus.
- **Detect [grep]** `code`: `outline:\s*(none|0)` with no `:focus-visible` rule nearby.
- **Fix:** a `:focus-visible` ring ≥ 3:1 vs unfocused; use `box-shadow` (respects radius),
  not `outline`.

### T40 · Contrast & target-size failures — system (1.4.3, 1.4.11, 2.5.8 AA)
- **Looks like:** body text < 4.5:1; UI borders/icons/focus rings < 3:1 (non-text
  contrast); tap targets < 24px.
- **Fix:** body ≥ 4.5:1 (large ≥ 3:1); non-text ≥ 3:1; targets ≥ 24px (aim 44–48), no dead
  zones. APCA (`Lc`) as guidance, never a pass/fail gate.

### T41 · Unlabeled controls & broken heading order — system (4.1.2, 2.5.3, 1.3.1)
- **Looks like:** icon-only buttons with no accessible name; inputs with no `<label for>`;
  skipped heading ranks (`h2→h4`); visible label text absent from the accessible name.
- **Detect** `code`: icon `<button>` with no `aria-label`/text; `<input>` with no
  associated label; heading-level jumps.
- **Fix:** a programmatic name on every control; label text inside the accessible name;
  sequential headings; decorative images `alt=""`.

---

## Numeric thresholds (summary)

*Canonical source for these numbers — `coder.md` and `reviewer.md` point here rather than
restating them; if a value changes, change it here.*

- Accent: design target ≤2 visible uses/screen (soft-flag 3–5, hard-flag 6+); ≤5% of
  viewport area (atmospheric genres up to 20%).
- Raw hex outside tokens: ≤12 → beyond that "tokens not respected".
- Fonts: ≤3 families; outlier ≤2 slots; body ≥16px; line-height 1.5–1.8; prose 45–75ch.
- Uppercase: `letter-spacing ≥ 0.06em` required; one role.
- Shadows: ≤2 meaningful elevation levels.
- Body contrast: WCAG 4.5:1 or APCA Lc ≥ 75 (90 preferred). (Lc 60 ≈ the AA 4.5:1 floor,
  below APCA's body level — don't use it for body.)
- Control heights: adjacent interactive elements equal height; one scale (e.g. 40/36/44).
- Underline: only on inline `<a>` in prose, not on buttons/actions.
- Sibling cards: shared vertical rhythm; value/visual/caption aligned across cards.
- Smoke: no horizontal scroll from 320–1920px.

---

## Positive references (what to clean toward)

- Metadata and captions lifted out of the table, not overloading the rows.
- Object interactions (SSH, endpoint) given their own zone.
- Sticky position for the total row/card; filters and alternate views.
- The 80/20 formula: ~80% proven patterns + ~20% one bold move (type, color, or
  proportion) + one memorable micro-interaction + a voice in the microcopy.
- The main complaint about AI design is holistic ("they all look the same") — so cleanup
  without added character doesn't close it. A final "where to add your own" is mandatory.

---

## Calibration — the new default is the next tell

Grep yields candidates; the verdict "this default wasn't chosen on purpose" needs context.

- **A documented brand decision is not slop.** Indigo/pill/caps/serif that lives in the
  tokens or `DESIGN.md` is a choice — don't re-flag it, and don't re-flag after an explicit
  "this is deliberate".
- **Swapping one default for another is not unslopping.** The 2024 tell was the purple
  gradient; the 2026 tell is cream + serif display + sage (the current "tasteful AI" look).
  Anthropic flags three default clusters of its *own* output — cream+serif+terracotta,
  near-black+acid-green, broadsheet-hairline — as "defaults rather than choices". A
  checklist that only recolors purple→cream produces the next template. The fix is a
  brief-specific **decision**, not a new palette (T28).
- **The real defect is the absence of intent, not any one pattern.** "The problem is that
  nobody made any decisions… genericness is a symptom of missing constraints" (Forgehouse).
  If a screenshot could belong to any product, it has no point of view — that is what to fix.
- **Detectors have false positives (~5–10%), and "looks AI" drifts toward "looks
  conventional".** A preprint (arXiv) study finds the features that statistically distinguish
  AI text don't predict which work gets *accused* — accusation is becoming social
  gatekeeping. Flag patterns; don't equate "conventional" with "bad".
- **Don't over-weight meme-tells.** Bento / glassmorphism / aurora rank near the bottom of
  real complaint data (JCarterJohnson's finding, **not** Krebs's) and are legitimate when
  chosen (Apple's Liquid Glass; area-based bento hierarchy; mesh gradients). BUT don't
  over-defend the two that *are* data-backed: the purple/gradient-text tell (T6) and
  centered-hero-plus-three-cards (T17). Spend weight on the kit, color, and typography.

---

## Sources

**Studies & catalogs**
- **vibecoded-design-tells** (JCarterJohnson) — Reddit study: ~3.2M posts / 47 subreddits →
  3,033 comments from 125 threads. Top tells: shadcn defaults · "AI purple" gradient ·
  gradient hero text · centered hero + three cards · neon glow. Trust the *relative*
  ordering over exact percentages. Ships the `unslop-ui` skill.
  https://github.com/JCarterJohnson/vibecoded-design-tells
- **adriankrebs.ch/blog/design-slop** — Playwright study of ~1,590 Show HN landing pages,
  16 deterministic DOM/CSS checks (~5–10% false positives): 22% trip 4+ patterns, 32% trip
  2–3, 46% trip 0–1. https://adriankrebs.ch/blog/design-slop
- **impeccable** (Paul Bakaus) — deterministic detector (46 rules, no LLM key) + LLM
  critique + CI gate; named the side-tab accent border "the most recognizable tell"; flags
  glassmorphism only when decorative. https://impeccable.style/slop
- **Refero** (`refero_skill`, MIT) — research-first anti-slop skill backed by 150K+ real
  app screens (Refero MCP). https://github.com/referodesign/refero_skill
- **nexu-io/open-design** — an `anti-ai-slop` lint ("cardinal sins" of generated UI) inside
  a local-first design app. https://github.com/nexu-io/open-design
- **avoid-ai-design** (funboy322) — a Claude Code audit+rewrite skill (NOT the ~1590-site
  study — that is Krebs, above). https://github.com/funboy322/avoid-ai-design
- **Hallmark** (Nutlope) — 57 slop-test gates + pre-emit self-critique; SKILL lives at
  `skills/hallmark/SKILL.md`. https://github.com/nutlope/hallmark

**Vendor / practitioner guidance**
- **Anthropic — Frontend Aesthetics Cookbook** + official `frontend-design` skill:
  "converge toward generic, on-distribution outputs… the 'AI slop' aesthetic"; size jumps
  3×+ not 1.5×; weight extremes; "spend your boldness in one place"; the "For calibration"
  three-cluster warning. https://platform.claude.com/cookbook (coding → frontend aesthetics)
- **OpenAI — Designing delightful frontends (GPT-5.4):** "the first viewport must read as
  one composition, not a dashboard"; two typefaces max, one accent; 2–3 intentional
  motions. https://developers.openai.com/blog/designing-delightful-frontends-with-gpt-5-4
- **Rauno Freiberg — Web Interface Guidelines:** motion ≤ 200ms; input font ≥ 16px (iOS
  zoom); focus ring via `box-shadow` not `outline`; `tabular-nums`; disable a button after
  submit; clicking a label focuses its input. https://interfaces.rauno.me
- **Refactoring UI** (Wathan/Schoger) — hierarchy by weight/color; rank buttons by
  importance; never grey text on a colored bg (same-hue tint); design all states.
  https://refactoringui.com
- **shadcn/ui theming** — the kit is a start: customize CSS variables, base color, one
  `--radius`. https://ui.shadcn.com/docs/theming
- **Adam Wathan** (origin of the indigo tell): "I'd like to formally apologize for making
  every button in Tailwind UI `bg-indigo-500` five years ago…"

**Calibration**
- **JCarterJohnson `unslop-ui`:** "replacing one default with another is not unslopping…
  the 2026 tell is cream + serif display + sage."
- **Forgehouse:** "the problem is that nobody made any decisions… genericness is a symptom
  of missing constraints." https://forgehouse.ai/guides/avoid-ai-slop-design
- **arXiv 2606.12073 "That's AI Slop, You Bot!":** the prose features that distinguish AI
  text don't predict which text gets *accused*; accusation is drifting toward social
  gatekeeping. https://arxiv.org/abs/2606.12073

Provenance: several of these catalogs overlap in their rule sets; weight reflects
independent research lines, not raw citation count.

> Living catalog: new confirmed tells are appended with the next T-number.
