# Ansible Coder Profile

Ansible-specific coding rules. Applied on top of the default coder profile.
Based on official Ansible documentation and ansible-lint production profile.

## Role-Based Organization

Structure playbooks around roles. A role encapsulates a single responsibility (e.g., `nginx`, `postgresql`, `security`) with a standard directory layout:

```
roles/
  webserver/
    tasks/
      main.yml
    handlers/
      main.yml
    defaults/
      main.yml
    vars/
      main.yml
    templates/
    files/
    meta/
      main.yml
```

- `defaults/` for variables users are expected to override
- `vars/` for internal variables that should not be overridden
- `meta/` for role dependencies and metadata
- `templates/` for Jinja2 templates (`.j2` extension)
- `files/` for static files deployed as-is

Top-level playbooks should be thin orchestrators that assign roles to host groups. Business logic belongs inside roles.

```yaml
# Good -- thin playbook delegates to roles
- name: Configure web servers
  hosts: webservers
  roles:
    - common
    - security
    - webserver
```

## Fully Qualified Collection Names (FQCN)

Use FQCN for **every** module, lookup, and filter. Never use short module names.

```yaml
# Good
- name: Install packages
  ansible.builtin.apt:
    name: "{{ packages }}"
    state: present

- name: Copy configuration
  ansible.builtin.copy:
    src: nginx.conf
    dest: /etc/nginx/nginx.conf

- name: Start service
  ansible.builtin.systemd:
    name: nginx
    state: started
    enabled: true

# Bad -- short names are ambiguous and deprecated by ansible-lint
- name: Install packages
  apt:
    name: "{{ packages }}"
    state: present
```

## Idempotent Tasks — Prefer Modules Over Shell

Every task must produce the same result whether run once or ten times: a second run reports `ok`, not `changed`.

- Use declarative modules (`ansible.builtin.apt`, `.copy`, `.template`, `.user`, `.systemd`) that describe desired state — they are idempotent, report errors, and emit structured output. **Never** use `ansible.builtin.shell`/`.command` when a dedicated module exists (`shell: apt-get install` instead of `ansible.builtin.apt` is a finding).
- When `shell`/`command` is genuinely unavoidable, add `creates`/`removes` (so it self-skips) and/or `changed_when`/`failed_when` (so it reports state accurately).

```yaml
# Good -- idempotent: self-skips once the marker exists
- name: Initialize database
  ansible.builtin.command:
    cmd: /usr/local/bin/init-db.sh
    creates: /var/lib/myapp/db_initialized

# Bad -- runs every time, always reports changed, no module used
- name: Initialize database
  ansible.builtin.shell: /usr/local/bin/init-db.sh
```

## Variable Organization

Use inventory-based variable files. Never scatter `vars:` inline across playbooks.

```
inventory/
  production/
    hosts.yml
    group_vars/
      all.yml
      webservers.yml
      databases.yml
    host_vars/
      web01.yml
```

- `group_vars/all.yml` for universal defaults
- `group_vars/<group>.yml` for group-specific values
- `host_vars/<host>.yml` for host-specific overrides
- Role `defaults/main.yml` for role-level defaults (lowest precedence)

Understand variable precedence (lowest to highest): role defaults < inventory `group_vars/all` < inventory `group_vars/<group>` < inventory `host_vars/<host>` < play `vars` < task `vars` < extra vars (`-e`).

## Secrets Management

Use **`ansible-vault`** for all sensitive data. Never commit plaintext passwords, API keys, tokens, or private keys.

```bash
# Encrypt a variable file
ansible-vault encrypt group_vars/production/vault.yml

# Edit encrypted file
ansible-vault edit group_vars/production/vault.yml

# Encrypt a single string
ansible-vault encrypt_string 'supersecret' --name 'db_password'
```

Prefix vault variables with `vault_` and reference them through a plain variable for clarity:

```yaml
# group_vars/production/vault.yml (encrypted)
vault_db_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...

# group_vars/production/main.yml (plaintext)
db_password: "{{ vault_db_password }}"
```

Vault encrypts secrets **at rest** only. Any task that handles a secret can still print it in plaintext under `-v`/`-vvv` or on failure. Set **`no_log: true`** on every task that receives a secret as an argument:

```yaml
- name: Configure database credentials
  ansible.builtin.template:
    src: db.conf.j2
    dest: /etc/app/db.conf
  no_log: true   # keeps db_password out of -v output and error traces
```

## Handlers for Service Restarts

Notify handlers for service restarts instead of adding restart tasks inline. Handlers run once at the end of the play regardless of how many tasks notify them.

```yaml
# Good -- handler-based restart
tasks:
  - name: Deploy nginx configuration
    ansible.builtin.template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
    notify: Restart nginx

handlers:
  - name: Restart nginx
    ansible.builtin.systemd:
      name: nginx
      state: restarted

# Bad -- inline restart after config change
tasks:
  - name: Deploy nginx configuration
    ansible.builtin.template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf

  - name: Restart nginx
    ansible.builtin.systemd:
      name: nginx
      state: restarted
```

Use `listen` for grouping multiple handlers under a single notification topic:

```yaml
handlers:
  - name: Restart nginx
    ansible.builtin.systemd:
      name: nginx
      state: restarted
    listen: web server changed

  - name: Clear nginx cache
    ansible.builtin.file:
      path: /var/cache/nginx
      state: absent
    listen: web server changed
```

## Tags

Tag tasks and roles for selective execution. Every role inclusion and significant task should have tags.

```yaml
- name: Configure firewall rules
  ansible.builtin.template:
    src: iptables.j2
    dest: /etc/iptables/rules.v4
  tags: [security, firewall]
```

Use tags consistently across the project. Common conventions: `setup`, `deploy`, `config`, `security`, `monitoring`.

Run selectively:

```bash
ansible-playbook site.yml --tags security
ansible-playbook site.yml --skip-tags monitoring
```

## Error Handling

Use `block`/`rescue`/`always` for structured error handling. Never use `ignore_errors: true` to mask failures — it is the single most common way real errors get silently swallowed (use `failed_when` to define what "failure" means, or `register` + `when` for conditional flow).

```yaml
- name: Deploy application
  block:
    - name: Run migrations
      ansible.builtin.command:
        cmd: "{{ app_dir }}/manage.py migrate"
        creates: "{{ app_dir }}/.migrated"
  rescue:
    - name: Roll back to previous version
      ansible.builtin.git: { repo: "{{ app_repo }}", dest: "{{ app_dir }}", version: "{{ previous_version }}" }
  always:
    - name: Notify deploy result
      ansible.builtin.uri: { url: "{{ webhook_url }}", method: POST }
```

## Task Naming

Every task **must** have a descriptive `name` that starts with a verb (`Install monitoring packages`, not missing, not `Do stuff`). Names are the playbook's run-time log — unnamed tasks make output unreadable.

## YAML Style

Lint enforces most of this (see ansible-lint in the reviewer profile); the load-bearing rules:

- No JSON inline syntax — use native YAML maps/lists.
- Quote strings that YAML would otherwise coerce: `"yes"`, `"no"`, `"true"`, `"false"`, `"on"`, `"off"`, and `mode` values (`"0644"`, not `0644`).
- Start every file with `---`.

## Privilege Escalation

Apply `become: true` at the **task level** where needed, not globally on the play. This follows the principle of least privilege.

```yaml
# Good -- become only where needed
- name: Read application config (no privilege needed)
  ansible.builtin.slurp:
    src: /opt/app/config.yml
  register: app_config

- name: Install system package (needs root)
  ansible.builtin.apt:
    name: nginx
    state: present
  become: true

# Bad -- global become when not all tasks need it
- hosts: webservers
  become: true  # every task runs as root unnecessarily
  tasks:
    - name: Read application config
      ansible.builtin.slurp:
        src: /opt/app/config.yml
```

## Conditional Logic

Use `register` + `when` for conditional execution rather than running a task unconditionally.

```yaml
- name: Check if application is installed
  ansible.builtin.stat:
    path: /opt/app/bin/myapp
  register: app_binary

- name: Install application
  ansible.builtin.get_url:
    url: "{{ app_download_url }}"
    dest: /opt/app/bin/myapp
    mode: "0755"
  when: not app_binary.stat.exists
```

## Loops

Use `loop` for iteration — the `with_*` forms are deprecated.

```yaml
- name: Create application directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    mode: "0755"
  loop:
    - /opt/app/logs
    - /opt/app/data
    - /opt/app/config
```

## Check Mode (Dry Run) Discipline

Roles should be safe to run with `--check` (`ansible-playbook --check --diff`) so changes can be previewed in CI.

- A `command`/`shell` task always reports `changed` and, in check mode, may not run at all — set **`changed_when`** to reflect real change, and **`check_mode: false`** for read-only probes that must execute during a dry run (e.g. a `stat`/version query feeding a `when`).
- Set `check_mode: true` to force a task to never alter state.

```yaml
- name: Get current app version (must run even in --check)
  ansible.builtin.command: /opt/app/bin/myapp --version
  register: app_version
  changed_when: false
  check_mode: false
```

## Jinja2 Templates

- Use `.j2` extension for all template files
- Add a managed-by comment at the top of generated files
- Use `{{ variable | default('fallback') }}` for optional values
- Avoid complex logic in templates — compute values in tasks or `vars` and pass them to the template

```jinja2
# {{ ansible_managed }}
# Do not edit this file manually.

server {
    listen {{ nginx_port | default(80) }};
    server_name {{ server_hostname }};
}
```

## Dependency Pinning — `requirements.yml`

Declare external collections and roles in `requirements.yml` with a **pinned `version:`**, never floating to whatever Galaxy serves at install time. Unpinned dependencies make runs non-reproducible and pull in untested upstream changes.

```yaml
# requirements.yml
collections:
  - name: community.general
    version: "10.1.0"        # pinned, not unbounded
roles:
  - name: geerlingguy.postgresql
    version: "3.5.2"
```

Install with `ansible-galaxy install -r requirements.yml`. Commit the file and bump versions deliberately.

## Testing with Molecule

Test roles with **Molecule**, which spins up a throwaway instance (Podman or Docker driver), applies the role, and asserts the result.

```bash
molecule test        # full cycle: create -> converge -> verify -> destroy
molecule converge    # apply the role and leave the instance up for iteration
molecule verify      # run assertions against the converged instance
```

- A role's `converge.yml` applies the role; a **second** converge must report no changes — Molecule's idempotence check fails the build otherwise.
- Put assertions in `verify.yml` (or Testinfra) — check that services run, files exist, and config is correct.
- Use the **Podman** driver where rootless/daemonless CI is preferred; Docker otherwise.
