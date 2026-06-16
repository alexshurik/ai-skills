# Terraform Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Terraform-specific review checklist and tools. Applied on top of the default reviewer profile.
Based on official HashiCorp guidance.

## Static Analysis Tools

### terraform validate

Syntax and configuration validation. Run first — catches structural errors before deeper analysis.

```bash
terraform init -backend=false
terraform validate
```

### terraform fmt -check

Formatting compliance check. Fails if any file is not canonically formatted.

```bash
terraform fmt -check -recursive
```

### tflint

Linter with cloud-provider-specific plugins. Catches deprecated syntax, invalid resource arguments, naming violations.

```bash
# Install
brew install tflint   # macOS
# or: curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Run
tflint --init    # install plugins from .tflint.hcl
tflint --recursive
```

Enable provider plugins as appropriate:

```hcl
# .tflint.hcl
plugin "aws" {
  enabled = true
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
  version = "0.40.0"  # pin to a current release; check the ruleset's releases page, do not copy this verbatim
}
```

### checkov

Security and compliance scanning. Checks for misconfigurations against CIS benchmarks and cloud best practices.

```bash
# Install
pip install checkov

# Run
checkov -d . --framework terraform
```

### tfsec (trivy)

Security scanner (now part of Trivy). Catches insecure defaults, open security groups, unencrypted storage.

```bash
# Install
brew install trivy   # macOS

# Run
trivy config .
```

Use either checkov or tfsec/trivy — both are not required. Pick whichever is already in the project CI.

### OpenTofu (`tofu`)

For OpenTofu codebases the same tools apply via the `tofu` CLI (`tofu validate`, `tofu fmt -check`); tflint/checkov/trivy read the identical HCL. CI should use `opentofu/setup-opentofu` rather than `setup-terraform`. Verify client-side **state encryption** is configured (`terraform { encryption { ... } }`) when state holds sensitive values.

## Review Checklist

### Module Structure

- [ ] Standard files present: `main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`
- [ ] Resources grouped by logical concern — no monolithic `main.tf` with unrelated resources
- [ ] Module nesting depth is two levels or fewer
- [ ] No thin wrapper modules that pass through variables without adding abstraction

### Variables and Outputs

- [ ] Every variable has a `description` and explicit `type`
- [ ] Every output has a `description`
- [ ] Sensitive variables marked with `sensitive = true`
- [ ] Variables with constrained values use `validation` blocks
- [ ] No unused variables or outputs

### Provider Configuration

- [ ] `required_providers` block present with version constraints
- [ ] No unbounded provider versions (missing `version` or using `>= 0.0.0`)
- [ ] `required_version` set for the Terraform/OpenTofu CLI version
- [ ] `terraform {}` block (constraints, `required_providers`, backend) in `versions.tf`; `provider "..." {}` config in `providers.tf` — not split across both
- [ ] (OpenTofu) client-side state encryption configured when state holds sensitive values

### State Management

- [ ] Remote backend configured for shared infrastructure
- [ ] State locking enabled (S3 `use_lockfile = true` — the DynamoDB table is deprecated as of TF 1.11; GCS/Terraform Cloud lock built-in)
- [ ] State encryption enabled
- [ ] No local state for team or CI-managed infrastructure

### Resource Quality

- [ ] No hardcoded IDs, AMIs, ARNs, or account numbers — use data sources or variables
- [ ] AMI lookups pinned by versioned name/ID — no `most_recent = true` with a wildcard filter (non-reproducible)
- [ ] No hardcoded IP addresses or CIDR blocks — use variables
- [ ] `for_each` or `count` used instead of copy-pasted resources
- [ ] `for_each` preferred over `count` for resources with meaningful identifiers
- [ ] `locals` used for repeated expressions and computed values
- [ ] snake_case naming for all identifiers
- [ ] Consistent tags applied (provider `default_tags` + required tag set); taggable resources not left untagged
- [ ] `prevent_destroy` on stateful/irreplaceable resources; `ignore_changes` scoped to specific attributes (not `all`)
- [ ] Renames/restructures use `moved` blocks; state-only removals use `removed` blocks — no hand-edited state
- [ ] `precondition`/`postcondition`/`check` blocks assert key runtime invariants where applicable

### CI and Drift

- [ ] Drift detection in CI via `terraform plan -detailed-exitcode` (exit 2 = drift) on deployed environments

### Security

- [ ] No secrets, access keys, or passwords in `.tf` or `.tfvars` files checked into version control
- [ ] No overly permissive IAM policies (`*` actions or resources without justification)
- [ ] No open security groups (`0.0.0.0/0` ingress without justification)
- [ ] Encryption enabled for storage (S3, EBS, RDS, etc.)
- [ ] Logging enabled where applicable (CloudTrail, flow logs)

### Formatting and Validation

- [ ] `terraform fmt` produces no changes
- [ ] `terraform validate` passes
- [ ] tflint produces no errors

## Anti-Patterns

Flag these as findings:

| Anti-Pattern | Severity | Description |
|--------------|----------|-------------|
| Inline provisioners (`provisioner "local-exec"`, `provisioner "remote-exec"`) | **Major** | Provisioners are a last resort — use cloud-native tools (user_data, cloud-init, configuration management) |
| Hardcoded AMIs/IDs | **Major** | Use data sources to look up dynamic values |
| `most_recent = true` AMI lookup with a wildcard filter | **Major** | Non-reproducible — resolves to a new image silently; pin the version |
| Rename/restructure without a `moved` block | **Major** | Causes destroy/recreate of live resources; express the move in code |
| `ignore_changes = all` | **Minor** | Hides all drift; scope to specific attributes |
| No description on variables | **Major** | Every variable needs a description for maintainability |
| Deeply nested modules (> 2 levels) | **Major** | Flatten module hierarchy — deep nesting obscures resource relationships |
| `terraform apply` without plan | **Major** | Always generate and review a plan before applying |
| Unbounded provider versions | **Major** | Missing or `>= 0.0.0` constraints allow breaking provider upgrades |
| Local state for shared infra | **Major** | Shared infrastructure must use remote state with locking |
| `count` with list index for named resources | **Minor** | Prefer `for_each` for stable resource addresses |
| Commented-out resources | **Minor** | Delete unused code — version control preserves history |
| Empty `default = ""` on required variables | **Minor** | Omit `default` to make the variable truly required |
| Wildcard IAM actions without justification | **Blocker** | `"Action": "*"` is a security risk |
| Credentials in `.tf` files | **Blocker** | Use environment variables, Vault, or cloud secret managers |

## Severity Mapping for Tool Findings

| Tool | Finding Type | Severity |
|------|-------------|----------|
| terraform validate | Any error | **Blocker** |
| terraform fmt | Formatting diff | **Minor** |
| tflint | Error-level rule | **Major** |
| tflint | Warning-level rule | **Minor** |
| checkov | Failed check (HIGH/CRITICAL) | **Major** |
| checkov | Failed check (MEDIUM) | **Minor** |
| checkov | Failed check (LOW) | **Nitpick** |
| tfsec/trivy | CRITICAL/HIGH severity | **Major** |
| tfsec/trivy | MEDIUM severity | **Minor** |
| tfsec/trivy | LOW severity | **Nitpick** |
