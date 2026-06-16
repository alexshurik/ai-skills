# Kubernetes / Helm Coder Profile

Kubernetes manifest and Helm chart coding rules. Applied on top of the default coder profile.
Based on the official Kubernetes documentation and Helm best-practices guide.

## Resource Requests and Limits

Set **both** `requests` and `limits` on **every** container (including init containers and sidecars). Requests drive scheduling; limits cap consumption and protect node stability.

- Set `requests.memory` == `limits.memory` so the pod gets the **Guaranteed** QoS class for memory — a container exceeding its memory limit is OOMKilled, so under-provisioning is dangerous.
- Set a CPU `request` always. Be deliberate about CPU `limits`: a CPU limit throttles via CFS quota and can hurt latency. Many teams set CPU requests and omit CPU limits intentionally, but **never** omit memory limits.

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    cpu: "500m"      # optional by policy; memory limit is not
    memory: "256Mi"  # equal to request -> Guaranteed memory
```

Never ship a container with no resources block. Enforce defaults cluster-side with a `LimitRange` and quota with `ResourceQuota`.

## Probes

Configure the three probes for their distinct purposes. Getting them wrong causes cascading restarts.

- **livenessProbe** — restarts the container when it is wedged. It **MUST NOT** check external dependencies (database, cache, downstream APIs). If liveness depends on a database outage, every replica restarts simultaneously and turns a partial outage into a total one. Check only in-process health (an event loop heartbeat, a `/healthz` that returns 200 without touching dependencies).
- **readinessProbe** — gates traffic. It **MUST** check the critical dependencies the pod needs to serve requests. A pod that cannot reach its database should fail readiness (removed from Service endpoints) but **not** liveness (not restarted).
- **startupProbe** — protects slow-starting containers. Use it so liveness/readiness do not fire during a long boot. Set `failureThreshold * periodSeconds` to the worst-case startup time; liveness only begins after the startup probe succeeds.

```yaml
startupProbe:
  httpGet: { path: /healthz, port: 8080 }
  failureThreshold: 30
  periodSeconds: 10        # allows up to 300s to start
livenessProbe:
  httpGet: { path: /healthz, port: 8080 }   # no external deps
  periodSeconds: 10
  failureThreshold: 3
readinessProbe:
  httpGet: { path: /readyz, port: 8080 }     # checks DB/cache reachability
  periodSeconds: 5
  failureThreshold: 3
```

Never point liveness and readiness at the same dependency-checking endpoint.

## Security Context

Set a restrictive `securityContext` at the pod and container level. Target the **`restricted`** Pod Security Standard.

```yaml
securityContext:                 # pod-level
  runAsNonRoot: true
  runAsUser: 10001
  fsGroup: 10001
  seccompProfile:
    type: RuntimeDefault
containers:
  - name: app
    securityContext:             # container-level
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      privileged: false
      capabilities:
        drop: ["ALL"]
```

- `runAsNonRoot: true` and an explicit non-zero `runAsUser` — never run as UID 0.
- `readOnlyRootFilesystem: true` — mount an `emptyDir` for any writable paths (`/tmp`, cache dirs).
- `capabilities.drop: ["ALL"]`; add back only the specific capability required (e.g. `NET_BIND_SERVICE`), never `add: ["ALL"]`.
- `allowPrivilegeEscalation: false` and `privileged: false` always.
- `seccompProfile.type: RuntimeDefault`.
- Never set `hostNetwork`, `hostPID`, `hostIPC`, or `hostPath` mounts without explicit justification.

## Enforce Pod Security Standards at the Namespace

The `securityContext` above only *describes* a hardened pod — nothing rejects a pod that omits it. Enforce the `restricted` standard at admission with a namespace label so non-compliant pods are refused, not just audited.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: app
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted     # surface violations on apply
```

Use `audit`/`warn` modes to dry-run a tightening before flipping `enforce`. System namespaces that genuinely need privileges get `baseline`/`privileged`, never the workload namespace.

## RBAC — Least Privilege

Give each workload its **own** `ServiceAccount` and bind only the permissions it uses.

- A dedicated `ServiceAccount` per workload — never share one or rely on the namespace `default` SA.
- Set **`automountServiceAccountToken: false`** on the SA (or pod) unless the workload actually calls the Kubernetes API — an automounted token is a credential an attacker can use.
- Prefer a namespaced **`Role`** + `RoleBinding` over a cluster-wide `ClusterRole`. Reserve `ClusterRole` for genuinely cluster-scoped needs.
- **No wildcards** in `verbs`, `resources`, or `apiGroups` (`*`); enumerate exactly what is needed. No `cluster-admin` bindings for workloads.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: app }
automountServiceAccountToken: false
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: app }
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]   # not ["*"]
```

## Image Tags

Never use `:latest` or an untagged image — both resolve unpredictably and break rollbacks. Pin by **immutable digest** for production; pin by **specific semantic version** at minimum.

```yaml
# Best — immutable digest
image: registry.example.com/app@sha256:3f5b...c1
# Acceptable — pinned version
image: registry.example.com/app:1.27.3
# Forbidden
image: registry.example.com/app:latest
image: registry.example.com/app
```

Set `imagePullPolicy: IfNotPresent` for digest/versioned tags. Use a private registry with `imagePullSecrets` for non-public images.

## Namespaces, Labels, Annotations

- Deploy workloads into a **dedicated namespace**, never `default`. Namespace per team/app/environment as the project dictates.
- Apply the recommended **`app.kubernetes.io/*`** labels on every object: `name`, `instance`, `version`, `component`, `part-of`, `managed-by`. Helm sets several of these via `{{ include "<chart>.labels" . }}` — use a `_helpers.tpl` partial so every template shares one label set.
- Use **labels** for selection and grouping (queryable); use **annotations** for non-identifying metadata (checksums, descriptions, tooling hints).
- Selectors (`spec.selector.matchLabels`) are immutable on Deployments — keep them minimal and stable; put churning values like `version` only in pod template labels.

## Secrets — Never in ConfigMaps

Never put credentials, tokens, keys, or certificates in a `ConfigMap` — they are stored and surfaced in plaintext. Use a `Secret`, and prefer an external secret manager.

- Source secrets from an external manager: **External Secrets Operator**, **Sealed Secrets**, **SOPS**, or CSI **Secrets Store** (Vault / cloud provider). The Git-committed manifest should reference the secret, not contain its value.
- Base64 in a plain `Secret` is encoding, not encryption — enable **encryption at rest** (`EncryptionConfiguration`) on the cluster.
- Mount secrets as files (volumes) over env vars where possible — env vars leak into logs, crash dumps, and child processes.
- Never commit a populated `Secret` manifest to Git.

## Network Policies — Default Deny

Pods accept all traffic by default. Establish a **default-deny** baseline per namespace, then allow explicitly.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]
```

Then add targeted policies allowing only required ingress/egress (including DNS egress to `kube-dns` on UDP/TCP 53). Verify the cluster CNI enforces NetworkPolicy (Calico, Cilium) — some do not.

## Availability — PDB, Replicas, Spreading

- Run **`replicas: >= 2`** (ideally 3) for any workload that must stay available. A single replica has no availability story during node drains or rollouts.
- Define a **PodDisruptionBudget** so voluntary disruptions (node drains, upgrades) cannot take all replicas at once.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
spec:
  minAvailable: 1            # or maxUnavailable
  selector:
    matchLabels: { app.kubernetes.io/name: app }
```

- Spread replicas across failure domains with **`topologySpreadConstraints`** (preferred) or pod **anti-affinity**, so a single node/zone loss does not take the whole workload.

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels: { app.kubernetes.io/name: app }
```

A PDB with `minAvailable` >= the replica count blocks all drains — keep the budget below the replica count.

## Helm

- **`values.yaml`** is documentation: provide sane, production-safe defaults with a comment on each key. Defaults should run; environment overrides go in separate `values-<env>.yaml` files, never hardcoded in templates.
- **No environment-specific values in templates.** No hardcoded hostnames, image tags, replica counts, or resource sizes in `.yaml` templates — parameterize through `values.yaml`.
- **Template everything that varies:** image repo/tag, replicas, resources, env, ingress hosts. Make `resources` fully overridable (`{{- toYaml .Values.resources | nindent 12 }}`).
- **Quote string values** with `{{ ... | quote }}` and use `nindent`/`indent` correctly so output is valid YAML.
- Use **`_helpers.tpl`** for repeated logic (names, label blocks). Reference labels via the chart's `labels`/`selectorLabels` partials.
- **Chart/app version discipline:** bump `version` (SemVer) on every chart change; set `appVersion` to the application release it deploys. Treat published chart versions as immutable.
- Add a **checksum annotation** so config changes roll pods:
  ```yaml
  annotations:
    checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  ```
- Run **`helm lint`** and **`helm template`** (render and inspect output) before committing. Keep secrets out of `values.yaml` — wire them through the external secret tooling above.
