# Deriving the Project Convention Profile

How to produce `.agents/best-practices/project/coder.md` (and `reviewer.md`) — the
**highest-precedence** layer in the profile chain (see `resolver.md`). This layer is
where a SPECIFIC repo's conventions live, so generated code matches the project
instead of the model's generic defaults.

This is the single source of truth for the extraction logic. It is referenced by
`sk-explore-codebase` (onboarding generates it) and by `sk-developer` (which
generates it on first run if missing). Both inline the essentials; keep them in sync
with this file.

> **Not a violation of "skills produce universal rules."** The universal profiles in
> this repo stay universal. The profile produced here is project-specific and is
> written **into the target repo** (`.agents/best-practices/project/`), never into
> the skills repo. It complements the universal layer; it does not replace it.

---

## When to (re)generate

Generate when `.agents/best-practices/project/coder.md` is ABSENT. Three cases:

1. **Established repo (code + config present)** — derive from evidence (below).
2. **Repo with code but thin/no tooling config** — derive from sampled files only.
3. **Greenfield (no code yet)** — you cannot observe conventions, so ASK. Return a
   `## NEEDS USER INPUT` block (per the interaction protocol) covering the decisions
   below, then write the profile from the answers. Do NOT invent conventions silently.

Persist the result and show it to the user for a quick confirm — it is a reviewable
artifact, not a hidden cache.

---

## Sources, in authority order

1. **Tooling config = conventions-as-code (highest authority).** These are
   machine-enforced, so they win over anything you infer:
   - Python: `pyproject.toml` `[tool.ruff]`/`[tool.ruff.lint]`/`[tool.mypy]`,
     `ruff.toml`, `setup.cfg`, `.flake8`, `mypy.ini`
   - JS/TS: `eslint.config.*`/`.eslintrc*`, `.prettierrc*`, `tsconfig.json`,
     `biome.json`
   - Cross-language: `.editorconfig`
   - Go: `.golangci.yml`, `gofmt` (implicit) · Rust: `rustfmt.toml`, `clippy.toml`
   Record the **exact selected rule sets / options** — they tell you naming rules,
   line length, quote style, import order, docstring policy, etc.
2. **`AGENTS.md` / `CLAUDE.md` / `.cursor/rules/`** — explicit human-written rules.
3. **The code itself** — sample 8–15 representative, non-generated files across the
   main packages. Count, don't guess: "module docstrings present in 0/14 files →
   rule: no module docstrings." Cite the evidence in the profile.

When a source conflicts with your inference from the code, the **config wins** and
the human-written rules win over raw sampling.

---

## What to capture (only project-specific signal)

Capture what DEVIATES from or SPECIALISES the universal profiles — do not restate
universal rules. For each, record the observation AND the evidence count:

- **Naming** — classes, functions, modules/files, constants, test files. (Catches
  "classes are PascalCase, never `_Private` at module scope.")
- **Docstrings** — module/class/function: present or not, and which style
  (Google/NumPy/reST/one-line). (Catches "no module/file docstrings here.")
- **Imports & file layout** — grouping, absolute vs relative, `__init__` re-exports,
  one-class-per-file vs grouped.
- **Typing** — how strict; `Any` tolerated?; runtime-validation lib (pydantic/attrs)?
- **Error handling** — exception hierarchy, custom base, Result-type vs raise.
- **Tests** — framework, file location/naming, fixture style, assertion style.
- **Framework idioms** — DI pattern, router/controller layout, ORM/session usage.
- **Tooling commands** — the EXACT format/lint/type/test commands through the
  project runner (e.g. `uv run ruff format`, `uv run ruff check --fix`,
  `uv run mypy src/`). `sk-developer` runs these on its own output.

---

## Profile template (`.agents/best-practices/project/coder.md`)

```markdown
# Project Coder Profile — <repo name>

> Auto-derived on <date> from tooling config + N sampled files. Highest-precedence
> layer: these rules OVERRIDE the generic language/framework examples on any
> conflict. Re-generate after major style changes. Evidence counts shown inline.

## Authoritative tooling (run these; they enforce most style)
- Format: `<cmd>`   Lint: `<cmd>`   Types: `<cmd>`   Tests: `<cmd>`
- Key lint rule sets enabled: <list from config>

## Naming (observed)
- Classes: <PascalCase> (18/18) · Functions: <snake_case> (…) · Files: <…>
- <any project-specific exception>

## Docstrings (observed)
- Module/file: <NONE — 0/14> · Class: <…> · Function: <style, when present>

## Imports & layout · Typing · Error handling · Tests · Framework idioms
- <observed rule + evidence, one line each — only where project-specific>

## When unsure
Match the nearest existing file in the same package. This profile overrides the
generic profile examples; the project's own linter/formatter is the final arbiter.
```

Also write a short `reviewer.md` mirroring the same rules as review checks (so the
reviewer flags deviations), or a one-line pointer back to this file.
