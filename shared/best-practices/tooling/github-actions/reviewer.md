# GitHub Actions Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
GitHub Actions-specific review checklist and tooling. Applied on top of the default reviewer profile.
Security-first: CI workflows are a top supply-chain attack surface — treat unpinned
actions and injectable expressions as exploitable, not stylistic.

## Static Analysis Tools

### actionlint

Workflow linter — catches YAML errors, invalid syntax, bad expressions, shellcheck
issues inside `run:`, and unknown contexts. Run first.

```bash
# Install
brew install actionlint   # macOS
# or: go install github.com/rhysd/actionlint/cmd/actionlint@latest

# Run (auto-discovers .github/workflows/)
actionlint
```

actionlint runs `shellcheck` on `run:` blocks when shellcheck is installed — keep it
present to catch shell-level bugs and some injection patterns.

### zizmor (or octoscan) — Security Audit

Static security auditor for workflows. Detects script injection, dangerous triggers
(`pull_request_target` misuse), unpinned actions, overscoped permissions, and credential
persistence.

```bash
# Install
pip install zizmor          # or: cargo install zizmor / brew install zizmor

# Run against the repo
zizmor .github/workflows/

# --pedantic raises sensitivity (adds code-quality nits) — separate from online mode
zizmor --pedantic .github/workflows/

# Online mode (audits referenced remote actions) is enabled by a token, not a flag
GH_TOKEN=$GITHUB_TOKEN zizmor .github/workflows/
```

`octoscan` is an equivalent alternative — use whichever is already in the project CI;
both are not required.

### pinact — Verify SHA Pins

Verifies and applies full-SHA pinning of actions referenced by tag/branch.

```bash
# Install
go install github.com/suzuki-shunsuke/pinact/cmd/pinact@latest

# Verify only — fails if any action is not SHA-pinned (use in CI)
pinact run --verify

# Auto-fix: rewrite tags to SHAs with version comments
pinact run
```

### gitleaks — Secret Scanning

Scans for hardcoded secrets in workflow files and the wider repo.

```bash
# Install
brew install gitleaks

# Scan working tree
gitleaks detect --source . --redact

# Scan only the changes under review
gitleaks protect --staged --redact
```

## Review Checklist

### Action Pinning
- [ ] Every third-party action pinned to a full 40-char commit SHA — no tags, no branches
- [ ] Version recorded in a trailing comment for each pinned action
- [ ] Docker-based `uses:` pinned by digest (`image@sha256:...`), not tag
- [ ] Reusable workflows from other repos pinned by SHA
- [ ] First-party `actions/*` pinned by SHA for sensitive repos
- [ ] `persist-credentials: false` on checkouts that don't push back to the repo
- [ ] Published actions/release tags are immutable (Marketplace immutable releases; tags never moved)

### Permissions
- [ ] Explicit `permissions:` block present (workflow level), defaulting to `contents: read`
- [ ] No `permissions: write-all` and no missing block on workflows handling untrusted input
- [ ] Write scopes (`contents`, `packages`, `pull-requests`, `id-token`) granted per job, not workflow-wide
- [ ] Build/test-only jobs hold no write scopes

### Dangerous Triggers
- [ ] `pull_request_target` does **not** check out or execute the PR head
- [ ] No secrets exposed to fork-PR code; untrusted builds use plain `pull_request`
- [ ] Privileged follow-up on fork artifacts uses a separate `workflow_run` job
- [ ] `workflow_dispatch`/`workflow_call` inputs are not trusted in privileged contexts
- [ ] Artifacts from untrusted `pull_request`/`workflow_run` treated as attacker-controlled — never executed/sourced; download paths validated against traversal

### Script Injection
- [ ] No `${{ github.event.* }}`, `github.head_ref`, or untrusted `inputs.*` interpolated directly into `run:`
- [ ] Untrusted values bound to `env:` and referenced as quoted shell variables
- [ ] `actions/github-script` reads untrusted values from `process.env`, not templated into the body

### Secrets
- [ ] No hardcoded tokens, keys, or passwords in workflow YAML
- [ ] Secrets never `echo`/`cat`/`print`ed; passed via `env:` to the consuming tool
- [ ] `secrets: inherit` used only for fully trusted callee workflows
- [ ] Production deploys gated behind `environment:` with required reviewers

### Cloud Auth
- [ ] Cloud auth uses OIDC (`id-token: write`), not long-lived access keys stored as secrets
- [ ] Cloud trust policy scoped to specific repo/branch/environment (`sub` claim), not the whole org

### Reliability and Cost
- [ ] `timeout-minutes` set on every job
- [ ] `concurrency` group set; `cancel-in-progress` appropriate to workflow type
- [ ] Runner version pinned (`ubuntu-24.04`, not `ubuntu-latest`)
- [ ] Cache keys include a lockfile hash and `runner.os`; `restore-keys` fallback present
- [ ] No secrets cached
- [ ] Matrix minimal, impossible combos excluded; `fail-fast` set intentionally

### Hygiene
- [ ] Shared logic factored into reusable workflows, not copy-pasted
- [ ] Triggers scoped with `paths:`/`branches:` filters
- [ ] `continue-on-error: true` only on genuinely optional steps
- [ ] actionlint, zizmor/octoscan, pinact, and gitleaks pass

## Severity Mapping for GitHub Actions Findings

Extends the orchestrator's severity table with GitHub Actions-specific entries.

| Finding | Severity |
|---------|----------|
| `${{ github.event.* }}` / untrusted input interpolated into `run:` (script injection) | **BLOCKER** |
| `pull_request_target` + untrusted PR-head checkout + secrets | **BLOCKER** |
| Hardcoded secret/token/key in workflow YAML | **BLOCKER** |
| Secret echoed/printed to logs | **BLOCKER** |
| Untrusted input in `actions/github-script` body | **BLOCKER** |
| Untrusted artifact executed/sourced, or extracted without path-traversal validation | **BLOCKER** |
| Unpinned third-party action (tag/branch) | **MAJOR** (BLOCKER for sensitive repos) |
| Reusable workflow from another repo unpinned | **MAJOR** (BLOCKER for sensitive repos) |
| `permissions: write-all` or missing block on untrusted-input workflow | **MAJOR** |
| Write scopes granted workflow-wide instead of per job | **MAJOR** |
| Long-lived cloud access keys instead of OIDC | **MAJOR** |
| OIDC trust policy scoped to whole org, not repo/branch | **MAJOR** |
| `secrets: inherit` to an untrusted/third-party reusable workflow | **MAJOR** |
| Docker `uses:` pinned by tag instead of digest | **MAJOR** |
| `persist-credentials` left default on a checkout that doesn't push | **MINOR** |
| Published action/release tag mutable (movable, no immutable release) | **MINOR** |
| Missing job `timeout-minutes` | **MINOR** |
| `ubuntu-latest` / unpinned runner | **MINOR** |
| Missing `concurrency` group on PR/branch CI | **MINOR** |
| Cache key without lockfile hash or `runner.os` | **MINOR** |
| Unscoped triggers (no `paths:`/`branches:` where appropriate) | **MINOR** |
| `continue-on-error: true` on a non-optional step | **MINOR** |
| Copy-pasted jobs that should be a reusable workflow | **MINOR** |
| actionlint error | **MAJOR** |
| actionlint warning | **MINOR** |
| zizmor/octoscan finding (High/Critical) | **MAJOR** (BLOCKER if script-injection or dangerous-trigger class) |
| zizmor/octoscan finding (Medium/Low) | **MINOR** |
| gitleaks detection | **BLOCKER** |
| pinact `--verify` failure | **MAJOR** |
