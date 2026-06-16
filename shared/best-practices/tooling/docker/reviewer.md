# Docker Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Docker- and container-specific review checklist and tooling. Applied on top of the default reviewer profile.
Based on official Docker and OCI guidance.

## Static Analysis Tools

### hadolint (Dockerfile lint)

Primary Dockerfile linter. Catches anti-patterns, unpinned packages, `ADD`/`COPY` misuse, missing `--no-install-recommends`, and embeds ShellCheck for `RUN` scripts.

```bash
# Run (containerized — no install needed)
docker run --rm -i hadolint/hadolint < Dockerfile

# or local binary
brew install hadolint
hadolint Dockerfile
```

Key rules: `DL3007` (`:latest`), `DL3008`/`DL3018` (unpinned apt/apk packages), `DL3009` (no apt list cleanup), `DL3025` (CMD/ENTRYPOINT not in exec form), `DL4006` (no `pipefail`), `DL3002` (last USER is root), `DL3020` (`ADD` instead of `COPY`).

### trivy / grype (image CVE scan)

Scan the built image for known CVEs in OS packages and language dependencies. Run against the final image, not just the Dockerfile.

```bash
# trivy
brew install trivy
trivy image --severity HIGH,CRITICAL myimage:tag

# grype
brew install grype
grype myimage:tag --fail-on high
```

Fail CI on HIGH/CRITICAL. Trivy also scans the Dockerfile itself (`trivy config .`) for misconfigurations.

### dockle (image config / CIS)

Audits the built image against the CIS Docker Benchmark and best practices: running as root, missing `HEALTHCHECK`, secrets/credentials baked into layers, world-writable files, suspicious `ENV`.

```bash
docker run --rm goodwithtech/dockle:latest myimage:tag
# fail on any FATAL/WARN
dockle --exit-code 1 --exit-level warn myimage:tag
```

### docker scout (CVE + policy)

Docker's first-party supply-chain analysis: CVEs, base-image freshness/upgrade recommendations, and policy evaluation against an SBOM.

```bash
docker scout cves myimage:tag
docker scout recommendations myimage:tag   # suggests less-vulnerable base images
docker scout quickview myimage:tag
```

Use trivy/grype **or** docker scout for CVE scanning — both are not required. Pick whichever is in the project CI.

## Review Checklist

### Image Construction

- [ ] Multi-stage build used — build tooling and dev dependencies absent from the final image
- [ ] Base image pinned by **digest** (`@sha256:...`), not `:latest` or a bare mutable tag
- [ ] Minimal base (distroless / `-slim` / `scratch`) appropriate to the workload
- [ ] One concern per image — no process supervisor bundling multiple services
- [ ] Final image contains only runtime artifacts (no source, compilers, test deps)

### Layering and Cache

- [ ] Dependency manifests copied and installed **before** application source
- [ ] Related `RUN` steps combined; package-manager caches cleaned in the same layer
- [ ] `--no-install-recommends` (apt) / `--no-cache` (apk) used
- [ ] `.dockerignore` present and excludes `.git`, `.env`, secrets, `node_modules`, build caches

### Security

- [ ] Explicit non-root `USER` set before the entrypoint (numeric UID for `runAsNonRoot`)
- [ ] No secrets in any layer (`docker history`), `ENV`, or `ARG` — BuildKit `--mount=type=secret` used instead
- [ ] No secrets or sensitive files copied in via `COPY .` (covered by `.dockerignore`)
- [ ] `COPY` used instead of `ADD`; no `ADD` of a remote URL
- [ ] Image designed for read-only root filesystem; writable paths via tmpfs/volumes
- [ ] Plain Docker/compose run drops capabilities (`--cap-drop ALL` / `cap_drop: ["ALL"]`) and sets `no-new-privileges`
- [ ] No new CVE of HIGH/CRITICAL severity introduced (trivy/grype/scout)

### Supply Chain and Metadata

- [ ] SBOM and provenance attestations produced (`--sbom=true --provenance=mode=max`) and pushed to the registry
- [ ] Standard `org.opencontainers.image.source`/`.revision`/`.created` labels set

### Runtime Metadata

- [ ] `EXPOSE` declares listening ports
- [ ] `HEALTHCHECK` defined (or orchestrator probes documented for shell-less images)
- [ ] `ENTRYPOINT`/`CMD` in **exec form** (JSON array), not shell form
- [ ] `ENTRYPOINT` vs `CMD` split correctly (fixed executable vs overridable args)
- [ ] Init/`tini` present (or `--init`/`SIGTERM`-aware app) for correct PID 1 signal handling and zombie reaping

### Dependencies

- [ ] Dependencies installed from a committed lockfile with the frozen/locked install mode
- [ ] No unpinned OS packages (`apt-get install pkg` without a version where reproducibility matters)

## Anti-Patterns

Flag these as findings:

| Anti-Pattern | Severity | Description |
|--------------|----------|-------------|
| Container runs as root (no `USER`, or last `USER` is root/UID 0) | **Blocker** | Privilege escalation surface; violates `runAsNonRoot` |
| Secret baked into an image layer (`RUN echo token`, copied key) | **Blocker** | Recoverable via `docker history`/layer extraction forever |
| Secret in `ENV` or `ARG` | **Blocker** | Readable via `docker inspect`/image metadata |
| HIGH/CRITICAL CVE in the image | **Blocker** | Patch, rebuild on a newer base, or remove the package |
| Base image `:latest` or unpinned/mutable tag | **Major** | Non-reproducible builds; uncontrolled drift |
| `ADD` of a remote URL | **Major** | No checksum/TLS control; use `RUN curl` + checksum or `COPY` |
| `ADD` used where `COPY` suffices | **Major** | Implicit extraction/fetch behavior; use `COPY` |
| Shell-form `ENTRYPOINT`/`CMD` | **Major** | PID 1 becomes `sh -c`; signals not forwarded to the app |
| Build tooling/source shipped in final image (no multi-stage) | **Major** | Bloated image and enlarged attack surface |
| Dependencies installed without a lockfile (`npm install`, `pip install pkg`) | **Major** | Non-reproducible, drift-prone builds |
| Package caches not cleaned in the same layer | **Minor** | Wasted image size (`rm` in a later layer reclaims nothing) |
| Multiple concerns per image (process supervisor) | **Major** | Couples lifecycles; breaks orchestration and scaling |
| Missing `HEALTHCHECK` | **Minor** | Runtime cannot detect a hung-but-running process |
| Missing `EXPOSE` | **Minor** | Lost port documentation/metadata |
| Missing `.dockerignore` | **Minor** | Bloated context; risk of leaking `.git`/secrets |
| No init for PID 1 with child processes | **Minor** | Zombie reaping and `SIGTERM` handling unreliable |
| Writable root filesystem when read-only is feasible | **Minor** | Larger tamper surface |
| Capabilities not dropped on plain Docker/compose (`--cap-drop ALL` / `cap_drop`), or `no-new-privileges` absent | **Minor** | Unnecessary privilege/escalation surface |
| No SBOM/provenance attestations on a published image | **Minor** | Image contents and build are unverifiable downstream |
| Missing `org.opencontainers.image.*` source/revision labels | **Nitpick** | Image not traceable to its source revision |

## Severity Mapping for Tool Findings

Extends the orchestrator's severity table with Docker-specific entries.

| Tool | Finding Type | Severity |
|------|-------------|----------|
| hadolint | `error`-level rule | **Major** |
| hadolint | `warning`-level rule | **Minor** |
| hadolint | `info`/`style`-level rule | **Nitpick** |
| hadolint | `DL3002` (last USER is root) | **Blocker** |
| trivy/grype | CRITICAL / HIGH CVE | **Blocker** |
| trivy/grype | MEDIUM CVE | **Major** |
| trivy/grype | LOW CVE | **Minor** |
| trivy config | Misconfiguration (HIGH/CRITICAL) | **Major** |
| dockle | `FATAL` (e.g. secret in image, root user) | **Blocker** |
| dockle | `WARN` | **Major** |
| dockle | `INFO` | **Minor** |
| docker scout | Critical/High vulnerability | **Blocker** |
| docker scout | Policy violation (base outdated, etc.) | **Major** |
