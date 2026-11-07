# Convention Evidence Authority

Use this model whenever a skill derives project-specific coding or review guidance.
Frequency is evidence about a repository, not permission to repeat a pattern.

## Authority classes

### Enforced

A formatter, linter, type checker, test, build, pre-commit hook, or CI command
mechanically enforces the rule.

Record:

- stable ID `ENF-<topic>`;
- exact config path and setting;
- exact verification command;
- scope and exceptions.

This class describes the check's mechanical authority, not proof that it runs
locally, in CI, or as a required merge gate. Collect those facts separately below.

Enforced rules may appear in generated coder and reviewer profiles.

### Approved

Current human-authored repository guidance, an accepted ADR, or an approved
feature design explicitly selects the rule.

Record:

- stable ID `APP-<topic>`;
- source file and section;
- scope;
- any expiry, supersession, or exception.

Approved rules may appear in generated coder and reviewer profiles. When two
approved sources conflict, stop and request resolution; do not choose by frequency.

### Observed

Representative source samples use the pattern, but no enforced or approved source
authorizes it.

Record:

- stable ID `OBS-<topic>`;
- sampled paths and count;
- counterexamples;
- confidence;
- a question if promotion would materially affect future code.

Observed items belong in `evidence.md`, not as instructions in `coder.md` or
review checks in `reviewer.md`.

### Legacy/uncertain

The pattern is inconsistent, contradicted by a higher authority, deprecated, or
cannot be classified confidently.

Record:

- stable ID `LEG-<topic>`;
- evidence and contradiction;
- migration or containment note when known;
- whether new code must avoid it.

Legacy/uncertain items belong in `evidence.md`. A higher approved rule may
explicitly prohibit copying them.

## Authority and enforcement evidence

For each normative `ENF-*` or `APP-*` rule, retain two independently sourced parts:

| Part | Required evidence |
|---|---|
| Authority | Stable ID/class, selected instruction/check, source file/section or config setting, scope, exceptions/supersession |
| Check | Exact command, pinned runner/config, actual checked scope and exclusions; available but unexecuted when no run exists |
| Invocation | Local hook/script and CI job/trigger sources; configured, observed running, absent, or unknown |
| Blocking | Local failure behavior, CI job failure behavior, and required merge-check policy separately; proven, optional/nonblocking, absent, or unknown with sources |
| Freshness | Last checked time, relevant revision/input hashes or receipt; mark stale evidence and unexecuted commands |
| Gaps | Manual review obligations and uncovered requirements, with owner or unknown |

Configuration proves availability and what a checker can inspect. An execution
receipt proves only that run and its inputs. CI config may prove invocation and job
failure behavior; branch protection/required-check policy needs separate evidence.
A job name, local green run, or config file cannot prove merge blocking. If remote
policy is unavailable, record unknown. Stale receipts cannot establish current
coverage. Do not invent a command, invocation, freshness, or blocking status.

An Approved rule remains authoritative when verification is manual or incomplete.
Keep its manual check and gaps visible; do not downgrade it to Observed. Conversely,
mechanical enforcement cannot approve an architectural pattern outside its scope.
Reuse the same rule ID and evidence link in coder/reviewer profiles; do not maintain
two conflicting enforcement records.

## Precedence

Use the following order:

```text
approved specification / ADR / repository guidance
  > enforced tooling
  > approved project profile
  > observed source frequency
```

Tooling wins for the mechanical behavior it actually enforces. An approved source
wins for architecture, ownership, vocabulary, scope, and policy that tooling cannot
decide. Report contradictions rather than silently flattening them.

## Restricted promotion

Never promote these from frequency alone:

- dependency aliases;
- local or dynamic imports;
- wrappers and forwarding helpers;
- top-level constants;
- one-purpose files;
- shared utility placement;
- cross-cutting infrastructure integrations.

These shapes can encode legacy debt or excessive navigation cost. They require an
Enforced or Approved source before becoming a generated instruction.

## Generated artifacts

Generate:

- `coder.md`: Enforced and Approved instructions only;
- `reviewer.md`: checks tied to the same `ENF-*` and `APP-*` IDs;
- `evidence.md`: Observed and Legacy/uncertain evidence, contradictions, and
  promotion questions.

Every normative rule must cite its source. Every sampled pattern must retain its
non-normative classification until a human or accepted decision promotes it.
