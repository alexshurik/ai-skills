# Kubernetes / Helm Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Kubernetes manifest and Helm chart review checklist and tooling. Applied on top of the default reviewer profile.
Based on the official Kubernetes documentation and Helm best-practices guide.

## Static Analysis Tools

### kubeconform (schema validation)

Validates manifests against the Kubernetes OpenAPI schemas. Run first — catches invalid API versions, fields, and types before deeper analysis. (`kubeval` is the older, now largely unmaintained equivalent; prefer `kubeconform`.)

```bash
# Install
brew install kubeconform   # macOS

# Validate raw manifests
kubeconform -strict -summary manifests/

# Validate rendered Helm output (incl. CRDs from upstream schemas)
helm template release ./chart | kubeconform -strict -summary \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'
```

`-strict` rejects unknown fields (typos). Always validate **rendered** output for Helm charts, not the templates.

### kube-linter (best-practice linting)

Static checks for production-readiness and security: missing resources, root users, `:latest` tags, missing probes, missing PDBs.

```bash
# Install
brew install kube-linter   # macOS

# Lint manifests or a chart directly
kube-linter lint manifests/
kube-linter lint ./chart
```

### kube-score (best-practice scoring)

Scores manifests on probes, resource limits, security context, anti-affinity, PDBs, and network policies. Complements kube-linter.

```bash
# Install
brew install kube-score   # macOS

# Score rendered output
helm template release ./chart | kube-score score -
kube-score score manifests/*.yaml
```

### trivy (security scanning)

Scans manifests and live clusters for misconfigurations (CIS, Pod Security Standards) and embedded secrets. `checkov` is the alternative policy-as-code scanner.

```bash
# Install
brew install trivy   # macOS

# Scan manifests / chart directory
trivy config manifests/
trivy config ./chart

# Scan a live cluster
trivy k8s --report summary cluster

# Alternative: checkov
checkov -d . --framework kubernetes helm
```

Use either trivy or checkov — both are not required. Pick whichever is already in the project CI.

### helm lint

Validates chart structure, `Chart.yaml`, and template rendering with default values.

```bash
helm lint ./chart
helm lint ./chart --strict                       # warnings become errors
helm lint ./chart -f values-prod.yaml            # lint against an env's values

# Always inspect rendered output as part of review
helm template release ./chart | less
```

### polaris (policy dashboard / admission)

Audits clusters and manifests against a configurable best-practice policy set (health checks, images, security, networking).

```bash
polaris audit --audit-path ./manifests --format pretty
polaris audit --audit-path ./chart
```

## Review Checklist

### Resources

- [ ] Every container (incl. init/sidecar) sets `requests` **and** `limits`
- [ ] Memory `limit` set and equal to `request` (Guaranteed QoS); no missing memory limit
- [ ] CPU `request` set; CPU limit policy is deliberate and consistent
- [ ] `LimitRange` / `ResourceQuota` present at namespace level where mandated

### Probes

- [ ] `livenessProbe`, `readinessProbe`, and (for slow starters) `startupProbe` configured
- [ ] `livenessProbe` checks **only** in-process health — no database/cache/downstream dependency calls
- [ ] `readinessProbe` checks critical dependencies (fails -> removed from endpoints)
- [ ] Liveness and readiness do not point at the same dependency-checking endpoint
- [ ] `startupProbe` budget (`failureThreshold * periodSeconds`) covers worst-case boot time

### Security Context

- [ ] `runAsNonRoot: true` with explicit non-zero `runAsUser`
- [ ] `readOnlyRootFilesystem: true` (writable paths via `emptyDir`)
- [ ] `capabilities.drop: ["ALL"]`; only specific caps added back
- [ ] `allowPrivilegeEscalation: false`, `privileged: false`
- [ ] `seccompProfile.type: RuntimeDefault`
- [ ] No `hostNetwork`/`hostPID`/`hostIPC`/`hostPath` without justification

### Pod Security and RBAC

- [ ] Workload namespace labelled `pod-security.kubernetes.io/enforce: restricted` (not merely `audit`/`warn`)
- [ ] Dedicated `ServiceAccount` per workload — not the namespace `default` SA
- [ ] `automountServiceAccountToken: false` unless the workload calls the Kubernetes API
- [ ] Namespaced `Role` preferred over `ClusterRole`; no `cluster-admin` for workloads
- [ ] No wildcard (`*`) `verbs`/`resources`/`apiGroups` in Roles

### Images

- [ ] No `:latest` and no untagged images
- [ ] Images pinned by digest (prod) or specific version
- [ ] `imagePullPolicy` appropriate (`IfNotPresent` for pinned tags)

### Metadata

- [ ] Workload in a dedicated namespace, not `default`
- [ ] Recommended `app.kubernetes.io/*` labels present on all objects
- [ ] Labels used for selection, annotations for non-identifying metadata
- [ ] Deployment `selector.matchLabels` minimal and stable (no churning values)

### Secrets

- [ ] No credentials/tokens/keys/certs in any `ConfigMap`
- [ ] Secrets sourced from an external manager (ESO, Sealed Secrets, SOPS, CSI/Vault)
- [ ] No populated `Secret` manifest committed to Git
- [ ] Encryption at rest enabled; secrets mounted as files over env vars where feasible

### Networking

- [ ] Default-deny `NetworkPolicy` present per namespace
- [ ] Targeted allow policies for required ingress/egress, including DNS egress
- [ ] Cluster CNI actually enforces NetworkPolicy

### Availability

- [ ] `replicas >= 2` for workloads requiring availability
- [ ] `PodDisruptionBudget` defined, with budget **below** replica count
- [ ] `topologySpreadConstraints` or pod anti-affinity across nodes/zones

### Helm

- [ ] `values.yaml` has documented, production-safe defaults
- [ ] No environment-specific values (hosts, tags, replicas, sizes) hardcoded in templates
- [ ] Variable values templated through `values.yaml`; resources overridable
- [ ] Strings quoted; `nindent`/`indent` produce valid YAML
- [ ] Shared `_helpers.tpl` for names and label blocks
- [ ] `version` (SemVer) bumped; `appVersion` set to deployed app release
- [ ] `checksum/config` annotation rolls pods on config change
- [ ] `helm lint` clean; rendered `helm template` output inspected
- [ ] No secrets in `values.yaml`

## Severity Mapping

Extends the orchestrator's severity table with Kubernetes/Helm-specific entries, including tool-finding rows at the end.

| Finding | Severity |
|---------|----------|
| Secret value in a `ConfigMap` | **BLOCKER** |
| Populated `Secret` committed to Git in plaintext | **BLOCKER** |
| Container runs as root (no `runAsNonRoot`/UID 0) | **BLOCKER** |
| `privileged: true` without justification | **BLOCKER** |
| `allowPrivilegeEscalation: true` | **BLOCKER** |
| `hostNetwork`/`hostPID`/`hostIPC` or `hostPath` mount without justification | **BLOCKER** |
| Wildcard (`*`) verbs/resources or `cluster-admin` bound to a workload | **BLOCKER** |
| Missing memory limit | **MAJOR** |
| Missing resource requests/limits generally | **MAJOR** |
| `:latest` or untagged image | **MAJOR** |
| `livenessProbe` checks an external dependency | **MAJOR** |
| Missing liveness/readiness probes | **MAJOR** |
| Liveness and readiness share a dependency-checking endpoint | **MAJOR** |
| `capabilities.drop: ["ALL"]` missing | **MAJOR** |
| `readOnlyRootFilesystem` not set | **MAJOR** |
| `seccompProfile` not `RuntimeDefault` | **MAJOR** |
| Workload namespace not enforcing `restricted` Pod Security Standard | **MAJOR** |
| Shared/`default` ServiceAccount, or token automounted without API use | **MAJOR** |
| `ClusterRole` where a namespaced `Role` would suffice | **MINOR** |
| Single replica for a workload requiring availability | **MAJOR** |
| Environment-specific values hardcoded in Helm templates | **MAJOR** |
| No `NetworkPolicy` (no default-deny baseline) | **MINOR** in low-trust/isolated context; **MAJOR** for multi-tenant/internet-facing/regulated workloads |
| Missing `PodDisruptionBudget` | **MINOR** |
| Missing `topologySpreadConstraints`/anti-affinity | **MINOR** |
| Workload in `default` namespace | **MINOR** |
| Missing recommended `app.kubernetes.io/*` labels | **MINOR** |
| Missing `startupProbe` on a slow-starting container | **MINOR** |
| Missing `checksum/config` annotation | **MINOR** |
| Secrets passed as env vars instead of mounted files | **MINOR** |
| `version`/`appVersion` not bumped on chart change | **MINOR** |

Tool-output mappings:

| Tool | Finding Type | Severity |
|------|-------------|----------|
| kubeconform | Schema/validation error | **BLOCKER** |
| kube-linter | Error-level check | **MAJOR** |
| kube-score | CRITICAL grade | **MAJOR** |
| kube-score | WARNING grade | **MINOR** |
| trivy / checkov | CRITICAL/HIGH | **MAJOR** |
| trivy / checkov | MEDIUM | **MINOR** |
| trivy / checkov | LOW | **NITPICK** |
| helm lint | Error (`[ERROR]`) | **MAJOR** |
| helm lint | Warning (`[WARNING]`) | **MINOR** |
| polaris | danger-level check | **MAJOR** |
| polaris | warning-level check | **MINOR** |
