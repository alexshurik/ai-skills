# Ansible Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Ansible-specific review checklist and tooling. Applied on top of the default reviewer profile.

## Ansible Review Checklist

### FQCN Usage
- [ ] **All modules use FQCN** -- `ansible.builtin.copy`, not `copy`; `ansible.builtin.shell`, not `shell`
- [ ] Lookups and filters use FQCN where applicable
- [ ] No short module names anywhere in the codebase

### Idempotency
- [ ] Every task produces the same result on repeated runs
- [ ] `ansible.builtin.shell` / `ansible.builtin.command` tasks have `creates` or `removes` conditions
- [ ] No unconditional shell commands that modify system state
- [ ] Tasks that check state use `changed_when: false` when they never change anything
- [ ] Read-only probes feeding a `when` use `check_mode: false` so they run under `--check`; role is dry-run safe

### Variable Management
- [ ] Variables organized in `group_vars/` and `host_vars/`, not scattered as inline `vars:`
- [ ] Variable precedence is correct: `defaults/` < `group_vars/all` < `group_vars/<group>` < `host_vars/<host>` < play vars < extra vars
- [ ] No variable name collisions between role defaults and inventory vars
- [ ] Role defaults are in `defaults/main.yml`, internal role vars in `vars/main.yml`

### Secrets and Vault
- [ ] No plaintext passwords, API keys, tokens, or private keys in any YAML file
- [ ] Sensitive variables encrypted with `ansible-vault`
- [ ] Vault variables prefixed with `vault_` and referenced through plain variables
- [ ] No secrets passed via command-line arguments (visible in process list)
- [ ] `no_log: true` on every task that receives a secret as an argument (vault is at-rest only)

### Hardcoded Values
- [ ] No hardcoded IP addresses or hostnames in playbooks or roles -- use inventory
- [ ] No hardcoded paths that should be variables
- [ ] No hardcoded package versions without a variable (makes upgrades painful)
- [ ] Ports, URLs, and environment-specific values come from variables

### Handler Usage
- [ ] Service restarts use handlers, not inline restart tasks after configuration changes
- [ ] Handlers are notified via `notify`, not called directly as tasks
- [ ] Handler names are descriptive and match the service they manage
- [ ] `listen` is used when multiple handlers should trigger from one notification

### Role Structure
- [ ] Roles have the standard directory layout: `tasks/`, `handlers/`, `defaults/`, `vars/`, `templates/`, `files/`, `meta/`
- [ ] `meta/main.yml` declares role dependencies
- [ ] Role `defaults/main.yml` exists with documented default values
- [ ] No business logic in top-level playbooks -- delegated to roles

### Task Quality
- [ ] Every task has a `name` field
- [ ] Task names are descriptive and start with a verb
- [ ] No `ansible.builtin.shell` or `ansible.builtin.command` when a dedicated module exists
- [ ] `become: true` applied at task level, not globally on the play (unless every task needs it)
- [ ] Tags present on roles and significant tasks for selective execution

### Dependencies and Testing
- [ ] External collections/roles declared in `requirements.yml` with a pinned `version:` (not floating)
- [ ] Roles have a Molecule scenario; `molecule test` converges and passes the idempotence check (second converge reports no `changed`)

### YAML Style
- [ ] No JSON inline syntax in YAML files
- [ ] Strings that could be misinterpreted are quoted: `"yes"`, `"no"`, `"true"`, `"false"`
- [ ] Files start with `---`
- [ ] Consistent 2-space indentation
- [ ] `mode` values are quoted strings: `"0644"`, not `0644` (avoids octal parsing issues)

### Anti-Patterns to Flag
- [ ] **`ignore_errors: true`** without justification -- masks real failures
- [ ] **`shell: |` when a module exists** -- `shell: apt-get install` instead of `ansible.builtin.apt`
- [ ] **Missing `name` on tasks** -- makes output unreadable and debugging impossible
- [ ] **`when: result|success`** / **`when: result|failed`** -- deprecated; use `result is succeeded` / `result is failed`
- [ ] **`with_*` loops** -- deprecated; use `loop` with filters
- [ ] **`become: true` on entire play** when only some tasks need root
- [ ] **Plaintext secrets** in version control
- [ ] **`command` / `shell` without `changed_when`** -- always reports `changed` even when nothing changed
- [ ] **Complex Jinja2 logic in templates** -- compute in tasks, pass results to templates

## Static Analysis Tools

### ansible-lint (Primary Linter)

The primary tool for Ansible code quality. Use the `production` profile for strict checking.

```bash
# Run with production profile (strictest)
ansible-lint --profile production

# Run with specific rules
ansible-lint -R -r fqcn

# Run on a specific playbook
ansible-lint playbooks/site.yml

# List all available rules
ansible-lint -L

# Show rule details
ansible-lint -R -r <rule-id>
```

**Key ansible-lint profiles** (from least to most strict):

| Profile | Scope |
|---------|-------|
| `min` | Syntax and parsing errors only |
| `basic` | Core best practices |
| `moderate` | Formatting and style |
| `safety` | Security-focused rules |
| `shared` | Rules for shared/published content |
| `production` | All rules -- use this for reviews |

**Critical rules to verify:**

| Rule | What it catches |
|------|----------------|
| `fqcn` | Missing fully qualified collection names |
| `name[missing]` | Tasks without a `name` field |
| `no-changed-when` | Commands/shell without `changed_when` |
| `command-instead-of-module` | Shell/command when a module exists |
| `risky-shell-pipe` | Shell pipes without `set -o pipefail` |
| `no-handler` | Inline service restart instead of handler |
| `yaml` | YAML formatting issues |
| `jinja` | Jinja2 syntax and spacing |
| `var-naming` | Variable naming convention violations |

### ansible-playbook --syntax-check

Quick syntax validation before deeper analysis.

```bash
# Syntax check a playbook
ansible-playbook --syntax-check playbooks/site.yml

# Check all playbooks
for pb in playbooks/*.yml; do ansible-playbook --syntax-check "$pb"; done
```

### ansible-playbook --check (Dry Run)

Verify what changes a playbook would make without applying them.

```bash
# Dry run
ansible-playbook playbooks/site.yml --check --diff

# Dry run with verbose output
ansible-playbook playbooks/site.yml --check --diff -v
```

### gitleaks — Secret Scanning

Scan for hardcoded secrets (passwords, API keys, tokens, private keys) in unencrypted YAML and the wider repo. Vault-encrypted blocks (`$ANSIBLE_VAULT`) are ciphertext and will not trip it.

```bash
brew install gitleaks
gitleaks detect --source . --redact      # full working tree
gitleaks protect --staged --redact       # only the changes under review
```

### molecule — Role Testing

Run the role's Molecule scenario to confirm it converges and is idempotent.

```bash
molecule test         # create -> converge -> idempotence -> verify -> destroy
```

A second converge that reports `changed` fails the idempotence check — flag any role whose Molecule run is not idempotent, or that ships without a scenario.

## Severity Mapping for Ansible Findings

Extends the orchestrator's severity table with Ansible-specific entries.

| Finding | Severity |
|---------|----------|
| Plaintext secrets in version control | **BLOCKER** |
| `ignore_errors: true` without justification | **BLOCKER** |
| Secret-handling task without `no_log: true` (leaks under `-v`) | **MAJOR** |
| Shell/command when a dedicated module exists | **MAJOR** |
| Role fails Molecule idempotence (second converge reports `changed`) | **MAJOR** |
| External collection/role unpinned in `requirements.yml` | **MINOR** |
| Shell/command without `creates`/`removes`/`changed_when` | **MAJOR** |
| Missing FQCN on module calls | **MAJOR** |
| Missing `name` on tasks | **MAJOR** |
| Hardcoded IP addresses or hostnames | **MAJOR** |
| `become: true` on entire play unnecessarily | **MAJOR** |
| Inline service restart instead of handler | **MAJOR** |
| `with_*` loops instead of `loop` | **MINOR** |
| Missing tags on roles/tasks | **MINOR** |
| Variable defined inline instead of in `group_vars`/`host_vars` | **MINOR** |
| Missing `---` at file start | **MINOR** |
| JSON inline syntax in YAML | **MINOR** |
| Unquoted `mode` values | **MINOR** |
| ansible-lint violation (general `production`-profile rule) | **MAJOR** (default; override by specific rule) |
| ansible-lint violation in a `safety`-category rule | **BLOCKER** (classify by rule category — the `safety` rules are a subset of `production`, so a safety finding is BLOCKER even when surfaced under the production profile) |
