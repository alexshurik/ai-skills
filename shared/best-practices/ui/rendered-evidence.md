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

Record the first-pass conclusion before reading the approved intent, component
implementation, or test output. Keep that conclusion immutable in the evidence
record, then read the approved intent and implementation context and perform the
full review. This prevents a plausible specification from explaining away an
obviously weak render.
For a major composition redesign, an independent reviewer may receive unlabeled or
opaque frames for the first pass; ordinary changes do not require that ceremony.

## Bind fidelity to the approved reference

For reference-driven work, identify the approved frame/screen and its version in
the task's acceptance criteria before implementation. Record which aspects it owns
(such as grouping, hierarchy, density, typography, action placement, or behavior)
and which remain owned by the project's design system. Resolve material conflicts
or ambiguous behavior from existing user decisions; ask only when that authority
is missing. Existing implementation, a self-authored plan, or refreshed goldens
cannot silently replace the requested reference.

After the screenshot-first pass, compare each representative render with its
matching reference at comparable viewport and ordinary content density. Record
material deviations and their authority or finding. Stress data supplements this
comparison. A user-reported fidelity defect is part of the requested acceptance
scope even when the defective code predates the current diff.

## Capture the effective scroll extent

Identify the actual scroll owner before capturing evidence:

- When the document owns scrolling, a full-page capture is sufficient.
- When an application shell or nested region owns scrolling, a browser `fullPage`
  screenshot may capture only the viewport. Scroll and stitch that owner or capture
  ordered slices covering its complete extent while preserving fixed chrome once.

Verify that the evidence covers the complete relevant content rather than merely
having a `fullPage` option set. Record the scroll owner and covered extent.
If stitching or hover changes the apparent layout, retain and inspect the raw
viewport slices before classifying the apparent defect or approving the render.

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

Confirm the actual rendered state before capture: for example, the visible heading,
selected tab, open dialog/menu, or settled result of an action. Record an observable
state check; a screenshot filename or intended navigation step is not proof that
the state was reached. Wait for the applicable content, fonts, and transitions.

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

## Reuse acceptance at release

When a workflow publishes a UI artifact, bind reused visual acceptance to that
artifact, the reference/criteria version, and relevant render inputs. A CI-only
diff does not itself prove the released UI. Reuse an unchanged, trusted receipt;
recheck only affected or missing evidence when assets, font delivery, global CSS,
host settings, or criteria change. After deployment, use a focused smoke check for
the affected inputs rather than repeating the entire visual suite.

A reported visual defect invalidates the prior acceptance claim for that scope
until investigated and reverified. A valid identity hash proves identity, not
visual correctness.

## Verify platform-sensitive mobile behavior

When the change affects browser chrome, safe-area insets, fixed/sticky bottom
navigation, dynamic viewport units, keyboard resizing, or `visualViewport`, prefer
the actual target browser/device. If that is unavailable, run the closest
project-appropriate WebKit/mobile approximation and record the residual gap. A
static Chromium screenshot may support composition review but cannot by itself
prove Safari/WebKit viewport or safe-area behavior.

## Compact evidence record

For each representative capture, retain only what another reviewer needs to
reproduce and judge it:

| Screen/journey | Reference/version or N/A reason | Observed state/check | Viewport | Scroll owner/extent | Actual URL/screenshot | Setup/fingerprint | Deviation/authority and result |
|---|---|---|---|---|---|---|---|

Select the applicable screen/state/viewport coverage from the task before declaring
PASS. Missing applicable rows or an unproven state remain `UNVERIFIED`. For work
without a supplied visual reference, name the governing project contract and record
why an external reference is not applicable. Do not create new screenshots solely
to populate irrelevant rows.

Store large images and logs outside model-visible reports when the workflow provides
a runtime artifact location. The verdict should link to them and summarize inspected
states, not paste or duplicate them.
