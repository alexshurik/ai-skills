# Rendered UI Evidence Contract

Read this contract when user-visible work materially changes page composition,
responsive behavior, navigation, hierarchy, or UI states. Also read it when adding
or updating maintained screenshots, visual regressions, or geometry guards.

Use evidence proportional to the change. A normal UI change usually needs a small
representative set; a release-wide redesign may need an explicit route/state/
viewport matrix. Do not create a gallery, contact-sheet generator, or permanent
harness unless the approved scope or repository policy requires one.

## Start with a screenshot-first pass

Inspect the rendered screen at original/native resolution before reading component
implementation or test output. Record concise answers:

1. What screen or task is this?
2. What information is most important?
3. What is the primary action, or why is no primary action appropriate?
4. What appears redundant, detached, or better moved?

Then read the approved intent and implementation context and perform the full review.
For a major composition redesign, an independent reviewer may receive unlabeled or
opaque frames for the first pass; ordinary changes do not require that ceremony.

## Capture the effective scroll extent

Identify the actual scroll owner before capturing evidence:

- When the document owns scrolling, a full-page capture is sufficient.
- When an application shell or nested region owns scrolling, a browser `fullPage`
  screenshot may capture only the viewport. Scroll and stitch that owner or capture
  ordered slices covering its complete extent while preserving fixed chrome once.

Verify that the evidence covers the complete relevant content rather than merely
having a `fullPage` option set. Record the scroll owner and covered extent.

## Make the render reproducible

Record the runnable URL or artifact path, state/setup, viewport, and exact source
fingerprint. For maintained visual evidence, also control every input that can
change pixels or semantics when applicable:

- device scale, color scheme, locale, timezone, and visible time;
- deterministic fixtures, authentication/permissions, feature flags, cache and
  service-worker state;
- loaded fonts, a content/readiness barrier, reduced-motion preference, and disabled
  non-essential animations;
- unexpected console errors and failed/unmocked network requests.

Hash fixtures, harnesses, builds, or rendered assets only when the repository relies
on reusable visual receipts. For ordinary manual evidence, recording exact setup and
source is enough; do not invent a heavyweight evidence-closure system.

## Combine three kinds of proof

No single proof can accept a composition:

1. **Rendered judgment:** hierarchy, comprehension, density, rhythm, product fit,
   copy in context, and whether responsive layouts preserve priority.
2. **Semantic and geometry assertions:** applicable landmarks/title, visible
   primary-action budget, accessible names/roles/states, overflow, clipping,
   overlap, containment, shared axes, target sizes, stable value/meta tracks, and
   desktop-to-compact order or reflow.
3. **Pixel evidence:** a small stable set of full-composition goldens for states
   whose appearance is intentionally maintained.

Use project contracts for exact selectors, thresholds, axes, and breakpoint widths.
Do not promote one product's measurements into a universal rule.

Include the populated/default state and only behaviorally relevant empty, loading,
error, disabled, focus, hover, or reduced-motion states. Add long-content or extreme-
value fixtures when the layout has constrained text or numeric tracks. Never invent
states that the product does not have merely to fill a matrix.

## Prove guards can fail safely

- Every custom static guard needs a rejecting fixture and a nearby accepted fixture
  that protects against false positives. Cover exclusions for tests, mocks, and
  generated artifacts when those exclusions exist.
- Prefer an AST or established parser for structured source. If a lightweight
  tokenizer or regular expression is justified, test quoting, escaping, nesting,
  selector/attribute boundaries, and valid adjacent counterexamples.
- Every reusable geometry assertion needs a deliberate DOM/style mutation that it
  rejects, plus a valid boundary case it accepts.
- A changed screenshot baseline is not evidence that the change is correct. Require
  fresh screenshot-first review against the exact updated source before accepting a
  baseline update.

Static guards and passing screenshots are supporting evidence. Missing runnable or
complete rendered evidence remains `UNVERIFIED`; source inspection cannot convert it
to a visual pass.

## Compact evidence record

For each representative capture, retain only what another reviewer needs to
reproduce and judge it:

| Screen/journey | State | Viewport | Scroll owner/extent | URL or screenshot | Setup/fingerprint | Result |
|---|---|---|---|---|---|---|

Store large images and logs outside model-visible reports when the workflow provides
a runtime artifact location. The verdict should link to them and summarize inspected
states, not paste or duplicate them.
