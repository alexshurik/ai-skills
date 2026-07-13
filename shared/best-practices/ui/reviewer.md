# UI: Anti-Slop Reviewer Profile

<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Applied on top of any framework/language reviewer profile when the change touches UI
(React, Vue, Svelte, Angular, Solid, Tailwind, or plain HTML/CSS). Full tell-by-tell
detection, fixes, and sources: [`catalog.md`](catalog.md).

## What this pass does

Flags **design slop** — the patterns that make generated UI read as machine-made — in
the changed files, and points each finding at the fix (to the project's own tokens/
system). It does **not** invent a brand or grade taste; it removes the generic and calls
out where a screen is left sterile.

**Severity:** `ban` (always wrong — fix) · `system` (systemic check — align to tokens) ·
`flag` (raise as a question, don't hard-fail).

## Calibration — grep gives a candidate, not a verdict

A pattern match is a **candidate**, not a conviction. The verdict "this default wasn't
chosen on purpose" needs context:

- A documented brand decision (indigo/pill/caps that lives in the tokens or `DESIGN.md`)
  is **not** slop. Don't re-flag it.
- A neutral 1px divider is **not** a "colored border-left accent".
- A pulse on a real in-progress load is **not** a fake live-dot.
- **Do not re-flag** something the author has already confirmed as a deliberate decision.
- **A swapped default is still a default.** Recoloring purple→cream or Inter→Instrument
  Serif is not a fix — today's tasteful default (cream + serif + sage) is tomorrow's tell
  (T28). Flag "no decision was made", not "the wrong palette"; the real defect is the
  absence of intent, not any one pattern.
- **Don't over-weight meme-tells** (glassmorphism / bento / aurora). In real complaint
  data they rank near the bottom; spend the reviewer's credibility on color, the untouched
  kit, typography, and shadows — not on `backdrop-blur`.

## Detection battery (candidates — confirm before flagging)

Run across the changed component and style files. The globs below are illustrative — add
your stack's UI file types (server templates `*.erb *.php *.blade.php *.twig *.j2 *.heex`,
CSS dialects `*.less *.sass *.styl`): `*.vue *.jsx *.tsx *.js *.ts *.svelte *.astro *.css
*.scss *.html`. Each match is a candidate, not an automatic finding.

**Tooling:** the battery assumes GNU grep or ripgrep. Stock macOS/BSD `grep` lacks `-P`
(PCRE) — use `rg` or `ggrep` (`brew install grep`) for the emoji line that needs `\x{}`.

```bash
# Default-palette accent — indigo/violet/purple hexes or utility classes on interactive elements
grep -rniE "#(6366f1|4f46e5|4338ca|3730a3|8b5cf6|7c3aed|a855f7|818cf8)" <files>
grep -rniE "#7f5af0" <files>                                    # low-confidence "AI purple"
grep -rniE "\b(bg|from|to|via|text)-(indigo|violet|purple)-[0-9]{2,3}\b" <files>
grep -rnE "bg-clip-text.*text-transparent|linear-gradient\(135deg" <files>   # gradient-on-text

# Emoji used as icon/status (allow arrows); mixing 2 icon libraries is the same tell
grep -rnP "[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B50}\x{25B6}\x{23F0}]" <files>   # needs rg/ggrep on BSD

# Raw hex / fallback hex / pure black-white in components (should be tokens)
grep -rniE "#[0-9a-f]{3,8}\b" <files> | grep -viE "stroke=|fill=|xmlns"
grep -rniE "(stroke|fill)=[\"']#[0-9a-f]{3,8}" <files>          # hardcoded colored stroke/fill (§7)
grep -rniE "var\(--[a-z0-9-]+,\s*#[0-9a-f]{3,8}\)" <files>                     # fallback hex
grep -rniE "#(000|fff|000000|ffffff)\b" <files>                              # pure #000/#fff

# Inline type / shadow / off-grid spacing / literal radius (should be tokens/scale)
grep -rniE "font-(size|family|weight):\s*[^;]+;|(fontSize|fontFamily|fontWeight)\s*:" <files>                       # inline type
grep -rniE "box-shadow:\s*(inset\s+)?-?[0-9]|boxShadow\s*:" <files>                                       # inline shadow
grep -rniE "(padding|margin|gap):[^;]*[0-9]*\.(375|625|875|125|3125|5625)rem" <files>  # half-steps
grep -rniE "border-radius:\s*[0-9]|borderRadius\s*:" <files> | grep -v "var(--"                # literal radius

# Colored border-left accent strip; default pastel status pills
grep -rniE "border-left:[^;]*(#|rgb|var\(--color)|border-l-[248]\b" <files>
grep -rniE "bg-(green|red|yellow|gray|blue)-100\s+text-(green|red|yellow|gray|blue)-800" <files>

# Reflexive motion; perpetual live-dot; untouched-kit carpet
grep -rniE "transition:\s*all|transition-all|hover:scale-1|hover:shadow" <files>
grep -rniE "animate-(ping|pulse)|animation:[^;]*(ping|pulse)" <files>        # verify: real event?
grep -rniE "rounded-2xl\s+shadow-lg|min-h-screen" <files>                    # kit default / template hero

# Underline as action affordance (allow real <a> in prose); untracked uppercase
grep -rniE "text-decoration:\s*underline|hover:underline|\bunderline\b" <files> | grep -v "no-underline"
grep -rniE "text-transform:\s*uppercase|\buppercase\b" <files>              # verify letter-spacing ≥ 0.06em

# Copywriting slop
grep -rniE "Elevate|Unlock|Supercharge|Seamless|Empower|Streamline|Leverage|Get Started" <files>

# New-wave defaults: post-Inter font trio; cream "tasteful AI" surface (T28)
grep -rniE "Geist|Space Grotesk|Instrument Serif" <files>
grep -rniE "#(f4f1ea|f5f1e8|faf8f3|f3efe6)" <files>

# Shipped placeholders / filler media (T35); invented metrics (T37)
grep -rniE "unsplash\.com|placehold\.co|picsum\.photos|src=[\"']{2}" <files>
grep -rniE "[0-9]+×|[0-9]+x faster|[0-9]{2,}k\+|99\.9%|trusted by [0-9]" <files>

# Motion: animating layout props / slow transitions (T36)
grep -rniE "transition:[^;]*(width|height|margin|padding)|duration-([5-9][0-9]{2}|1000)" <files>

# Fake interactive elements (T38) — grep is line-based; multi-line JSX onClick needs `rg -U` or eslint-plugin-jsx-a11y
grep -rniE "<(div|span)[^>]*onClick|role=[\"']button[\"']" <files>
```

## Review checklist (mirrors coder.md)

*Numeric thresholds are canonical in [`catalog.md`](catalog.md#numeric-thresholds-summary).*

### Bans (flag whenever present, unless documented)
- [ ] **Default-palette accent** — indigo/violet primary or a diagonal indigo→blue
      gradient not backed by brand tokens (`catalog` T6)
- [ ] **Untouched kit** — shadcn/Tailwind defaults shipped as-is (`rounded-2xl shadow-lg`
      carpet, default radius/palette) (T16)
- [ ] **Colored border-left accent strip** clipped by radius (T1)
- [ ] **Emoji as icon/status**, or two icon libraries mixed (T2)
- [ ] **Template landing formula** — 100vh centered hero, exactly 3 icon-topped cards (T17)
- [ ] **Perpetual pulsing "live" dot** with no real event (T23)
- [ ] **Underline as button/action affordance** (not a real inline `<a>`) (T24)
- [ ] **Shipped placeholders / broken media** — unsplash/placehold/picsum or empty `src` (T35)
- [ ] **Fake interactive elements** — `<div onClick>` / `role="button"` instead of `<button>` (T38)

### System checks (align to tokens/scale)
- [ ] **Color:** raw hex / fallback hex / ghost token / pure `#000`/`#fff`; accent over
      budget (target ≤2; soft-flag 3–5, hard-flag 6+) or on decorative elements; one role
      per gray; light-mode hexes baked in so dark breaks (T6/T9/T20/T31)
- [ ] **Type:** default font with no pairing; > 3 families; inline `font-*`; secondary text
      styled ≥ 2 ways; uppercase without `letter-spacing ≥ 0.06em` (T14/T3); new-wave default
      trio (Geist/Space Grotesk/Instrument Serif) or cream+serif+sage shipped as the look
      (T28); flat hierarchy < 1.25× (T29)
- [ ] **Spacing/radius:** off-grid half-steps; literal radii instead of the scale
- [ ] **Elevation:** border+shadow+fill stacked per level; shadow on > ~60% of containers;
      > 2 elevation steps (T5/T12)
- [ ] **Motion:** `transition: all`; blanket `hover:scale`/`hover:shadow` (T19); > 300ms,
      bounce easing, or animating layout props (T36)
- [ ] **Status:** default pastel pills; rainbow of colored states where neutral belongs (T4)
- [ ] **Actions:** destructive styled like a routine button; > 1 primary per row; adjacent
      controls at mismatched heights (T8/T25)
- [ ] **States:** empty/loading/error missing; row height jumps between states (T11)
- [ ] **Copy:** buzzwords; generic "Get started" instead of the product verb (T21)
- [ ] **A11y:** `<div onClick>` instead of `<button>`; `outline: none` with no focus
      replacement; body contrast < 4.5:1; non-text contrast < 3:1; targets < 24px; unlabeled
      inputs/icon-buttons; skipped heading ranks (T38–T41)

### Flags (raise as a question)
- [ ] **Row of identical stat cards** — flag the cluster only when combined with another
      tell (emoji / caps / shadow / accent overspend) (T7)
- [ ] **Everything boxed / centered** — cards-within-cards, symmetry with no purpose (T18)
- [ ] **Dense tool in a landing-page shell** — centered narrow column, top-nav-only, big
      side margins where a sidebar + full-width belongs (T27)

## Audit report format

```
SLOP AUDIT · <target> · <medium: code | screenshot>
Bans:     <T#> <where> → <fix to project tokens>
System:   <T#> <where> → <fix>
Flags:    <T#> <where> → <question / suggestion>
Copy:     <T21 findings>
Clean on: <checked groups with no findings>
Character: <1–2 sentences — where to add one deliberate bold decision (80/20)>
```

The final line is always honest: **the typical slop is removed; taste and bold decisions
stay with the designer.** A cleanup that adds no character does not fully answer the "they
all look the same" complaint — so name one place to add voice.
