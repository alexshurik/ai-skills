# Terraform Coder Profile

Terraform-specific coding rules. Applied on top of the default coder profile.
Based on official HashiCorp guidance.

## File Naming and Structure

Use the standard module structure for every module and root configuration:

| File | Purpose |
|------|---------|
| `main.tf` | Primary resources |
| `variables.tf` | Input variable declarations |
| `outputs.tf` | Output declarations |
| `providers.tf` | Provider `provider "..." {}` configuration blocks (regions, `default_tags`, aliases) |
| `locals.tf` | Local value expressions |
| `data.tf` | Data source lookups |
| `versions.tf` | The `terraform {}` block: `required_version`, `required_providers`, backend |

Keep the `terraform {}` block (version constraints, `required_providers`, backend) in **`versions.tf`**, and the `provider "..." {}` configuration in **`providers.tf`**. One convention — do not split `required_providers` across both files.

Split resources across additional files when a single `main.tf` grows beyond readability. Name files by logical grouping (e.g., `networking.tf`, `iam.tf`, `storage.tf`). Keep unrelated resources in separate files — never cram everything into `main.tf`.

## Naming Conventions

- **snake_case** for all resource names, variable names, output names, locals, and data sources
- Names should describe what the resource is, not its type — the type is already in the block label

```hcl
# Good
resource "aws_s3_bucket" "artifacts" { ... }

# Bad — redundant type in name
resource "aws_s3_bucket" "s3_bucket_artifacts" { ... }
```

## Variables

Every variable must have a **`description`** and an explicit **`type`**. No untyped variables.

Use `validation` blocks for variables with constrained value sets.

Use `sensitive = true` for secrets passed as variables.

```hcl
# Good
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# Bad — missing description and type
variable "environment" {}
```

## Outputs

Every output must have a **`description`**. Mark sensitive outputs with `sensitive = true`.

```hcl
output "cluster_endpoint" {
  description = "EKS cluster API endpoint URL"
  value       = aws_eks_cluster.main.endpoint
}
```

## Locals

Use `locals` blocks for:
- Computed values derived from variables
- Repeated expressions (DRY — define once, reference everywhere)
- Complex expressions that benefit from a readable name

```hcl
locals {
  common_tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
    Project     = var.project_name
  }

  is_production = var.environment == "prod"
}
```

## Tagging

Apply a consistent tag set to every taggable resource — required for cost allocation, ownership, and automation. Set baseline tags once via the provider's **`default_tags`** rather than repeating them on each resource, and require a known set (e.g. `Environment`, `Owner`, `Project`, `ManagedBy`).

```hcl
# providers.tf
provider "aws" {
  default_tags {
    tags = local.common_tags   # Environment, Owner, Project, ManagedBy = "terraform"
  }
}
```

Per-resource `tags` merge with (and override) `default_tags`. Use `merge(local.common_tags, { Name = "..." })` for resource-specific additions. Some resource types do not inherit `default_tags` — tag those explicitly.

## Data Sources Over Hardcoding

Use `data` blocks to look up existing resources instead of hardcoding IDs, ARNs, or AMIs.

```hcl
# Good — looks up a pinned AMI version; reproducible across applies
data "aws_ami" "ubuntu" {
  owners = ["099720109477"]

  filter {
    name   = "name"
    values = [var.ubuntu_ami_name]   # e.g. "ubuntu/images/.../ubuntu-noble-24.04-amd64-server-20250115"
  }
}

resource "aws_instance" "web" {
  ami = data.aws_ami.ubuntu.id
  # ...
}

# Bad — hardcoded AMI
resource "aws_instance" "web" {
  ami = "ami-0abcdef1234567890"
}
```

Avoid `most_recent = true` with a wildcard filter: it silently resolves to a different AMI whenever the upstream publishes a new image, so the same code produces a different instance on the next apply (non-reproducible, surprise replacements). Pin the AMI by a versioned name pattern (or pass the AMI ID in as a variable) and bump it deliberately.

## Provider Version Constraints

Always pin provider versions with bounded constraints in `required_providers` (in `versions.tf`). Use pessimistic constraints (`~>`) to allow patch updates while preventing breaking changes.

```hcl
# versions.tf
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

Never leave provider versions unbounded.

## Iteration — No Copy-Paste

Use `count` or `for_each` to create multiple similar resources. Never duplicate resource blocks with minor differences.

Prefer `for_each` over `count` when resources have meaningful identifiers — `for_each` produces stable addresses that survive reordering.

```hcl
# Good — for_each with a map
resource "aws_iam_user" "team" {
  for_each = toset(var.team_members)
  name     = each.value
}

# Bad — copy-pasted resources
resource "aws_iam_user" "alice" { name = "alice" }
resource "aws_iam_user" "bob" { name = "bob" }
resource "aws_iam_user" "carol" { name = "carol" }
```

## Refactoring — `moved` and `removed` Blocks

When you rename or restructure resources, use **`moved`** blocks so existing state follows the new address instead of being destroyed and recreated. Use **`removed`** blocks to drop a resource from configuration while keeping the real infrastructure (`terraform state rm` as code).

```hcl
moved {
  from = aws_instance.web
  to   = aws_instance.app   # renamed; no destroy/create
}

removed {
  from = aws_instance.legacy
  lifecycle { destroy = false }   # forget from state, keep the real resource
}
```

Never hand-edit state or `terraform state mv` when a `moved` block expresses the change reviewably in code.

## `lifecycle` Meta-Argument

Use `lifecycle` to control how Terraform handles changes:

- **`prevent_destroy = true`** on stateful/irreplaceable resources (databases, prod buckets) to block accidental destruction.
- **`create_before_destroy = true`** for zero-downtime replacement of resources that must not have a gap.
- **`ignore_changes = [...]`** for attributes mutated out-of-band (e.g. autoscaling-managed `desired_count`) — scope it to specific attributes, never the blunt `all`.

```hcl
resource "aws_db_instance" "main" {
  # ...
  lifecycle {
    prevent_destroy = true
    ignore_changes  = [password]   # rotated externally
  }
}
```

## Runtime Invariants — `precondition`/`postcondition` and `check`

Assert assumptions instead of letting a bad value fail deep in an apply.

- **`precondition`** (in a resource/data `lifecycle`) validates inputs before create/update.
- **`postcondition`** validates the result after.
- A standalone **`check`** block asserts cross-resource or external invariants on every plan/apply without blocking it (warning, not error).

```hcl
data "aws_ami" "app" {
  # ...
  lifecycle {
    postcondition {
      condition     = self.architecture == "x86_64"
      error_message = "AMI must be x86_64."
    }
  }
}

check "endpoint_healthy" {
  data "http" "health" { url = "https://${aws_lb.main.dns_name}/healthz" }
  assert {
    condition     = data.http.health.status_code == 200
    error_message = "Load balancer health check did not return 200."
  }
}
```

## OpenTofu

OpenTofu is the open-source fork of Terraform. The `tofu` CLI is a drop-in replacement (`tofu init/plan/apply`), reads the same HCL, and maintains broad feature parity. In CI use **`opentofu/setup-opentofu`** in place of `setup-terraform`.

Its key differentiator is **client-side state encryption**: state and plan files are encrypted on the runner before they reach the backend (via PBKDF2, AWS/GCP KMS, OpenBao, etc.), unlike Terraform's backend-only at-rest encryption. Configure it in the `terraform {}` block when state contains sensitive values:

```hcl
terraform {
  encryption {
    key_provider "aws_kms" "this" { kms_key_id = var.state_kms_key_arn, key_spec = "AES_256" }
    method "aes_gcm" "this" { keys = key_provider.aws_kms.this }
    state { method = method.aes_gcm.this }
    plan  { method = method.aes_gcm.this }
  }
}
```

## Module Design

- Keep module trees **flat** — avoid thin wrapper modules that add no real abstraction
- A module should encapsulate a logical unit of infrastructure, not just a single resource
- Limit nesting to **two levels** maximum (root -> module -> nested module)
- Every module needs its own `variables.tf`, `outputs.tf`, and a description in a header comment or `README.md`

## State Management

- Use **remote state** (S3, GCS, Azure Blob, Terraform Cloud) for any shared infrastructure — never local state
- Enable **state locking**. For S3, use native lockfile-based locking (`use_lockfile = true`, Terraform 1.10+) — the separate DynamoDB table is deprecated as of 1.11. GCS/Terraform Cloud lock built-in.
- Use separate state files per environment or component to limit blast radius

```hcl
terraform {
  backend "s3" {
    bucket       = "myproject-tfstate"
    key          = "prod/networking/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true   # S3-native locking; replaces the deprecated dynamodb_table
    encrypt      = true
  }
}
```

## Environment Separation

Separate environments via **directory structure** or **workspaces** — not conditionals scattered through resources.

```
environments/
  dev/
    main.tf
    terraform.tfvars
  staging/
    main.tf
    terraform.tfvars
  prod/
    main.tf
    terraform.tfvars
modules/
  networking/
  compute/
```

Avoid large `count = var.environment == "prod" ? 1 : 0` patterns to toggle resources per environment.

## Formatting and Validation

- Run **`terraform fmt`** before every commit — all code must be format-compliant
- Run **`terraform validate`** before every commit to catch syntax and configuration errors
- Use consistent alignment of `=` signs within blocks (handled by `terraform fmt`)

## Drift Detection

Detect configuration drift in CI with **`terraform plan -detailed-exitcode`**: exit `0` = no changes, `2` = drift (changes pending), `1` = error. Run it on a schedule against deployed environments and fail/alert on exit `2` so out-of-band changes surface before the next apply.

```bash
terraform plan -detailed-exitcode -lock=false  # exit 2 => drift detected
```

## Comments

Comments only where logic is non-obvious. Do not comment every resource or attribute — the HCL is already declarative and self-describing.

```hcl
# Good — explains a non-obvious workaround
# The ALB requires at least two subnets in different AZs,
# even when only one is actively used for routing.
resource "aws_lb" "main" { ... }

# Bad — restates the obvious
# Create an S3 bucket for artifacts
resource "aws_s3_bucket" "artifacts" { ... }
```

## Sensitive Data

- Never commit secrets, access keys, or credentials in `.tf` files or `.tfvars`
- Use `sensitive` variable flag and consider external secret management (Vault, AWS Secrets Manager)
- Add `*.tfvars` containing secrets to `.gitignore` (keep a `*.tfvars.example` template)
- Never store sensitive values in state without encryption — enable backend encryption
