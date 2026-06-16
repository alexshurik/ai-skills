# Docker Coder Profile

Docker- and container-specific coding rules. Applied on top of the default coder profile.
Based on official Docker and OCI guidance.

## Multi-Stage Builds

Use multi-stage builds to keep build tooling, compilers, and dev dependencies out of the final image. The runtime stage copies only the built artifact.

```dockerfile
# Good — build tooling stays in the builder stage
FROM golang:1.23 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app/server ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /app/server /server
USER nonroot
ENTRYPOINT ["/server"]

# Bad — ships the full Go toolchain and source in the final image
FROM golang:1.23
WORKDIR /src
COPY . .
RUN go build -o /app/server ./cmd/server
CMD ["/app/server"]
```

Name stages (`AS build`) and copy across with `COPY --from=<stage>`. Use a dedicated stage for tests/lint so they run in the build graph without bloating the runtime image.

## Pin Base Images by Digest

Pin base images by **digest**, not by a mutable tag. `:latest` and even version tags (`:1.23`) are reassignable and produce non-reproducible builds.

```dockerfile
# Good — immutable, reproducible
FROM python:3.12-slim@sha256:1e8c1f1f7b0c5c0f3a8b9d2e7a4c6b1d9e0f2a3b4c5d6e7f8a9b0c1d2e3f4a5b

# Acceptable — version-pinned, but still mutable
FROM python:3.12.8-slim

# Bad — unpinned, non-reproducible
FROM python:latest
```

Keep the human-readable tag as a comment alongside the digest so the version is legible. Update digests deliberately (e.g., via Dependabot/Renovate), not implicitly.

## Minimal Base Images

Prefer the smallest base that runs the workload. Smaller bases mean faster pulls and a smaller CVE surface.

| Base | Use when |
|------|----------|
| `gcr.io/distroless/*` | Static or self-contained binaries (Go, Rust, compiled Java/Node bundles) — no shell, no package manager |
| `*-slim` (e.g. `debian:12-slim`, `python:3.12-slim`) | Interpreted runtimes that need a minimal libc/userland |
| `alpine` | Size-critical images — but verify musl libc compatibility (DNS, glibc-only wheels) |
| full `debian`/`ubuntu` | Only when you genuinely need the full userland |

Distroless and `scratch` have no shell — debug with an ephemeral sidecar (`docker debug` / `kubectl debug`), not by adding a shell back.

## Run as Non-Root

Containers must not run as `root`. Create a dedicated unprivileged user and switch with `USER` before the entrypoint.

```dockerfile
# Good
RUN addgroup --system app && adduser --system --ingroup app app
USER app

# Bad — implicit root (UID 0)
# (no USER instruction — process runs as root)
```

Use a numeric UID (`USER 10001`) when the image runs under Kubernetes `runAsNonRoot`, which cannot resolve usernames. Ensure files the process must write are owned by that UID (`COPY --chown=10001:10001`).

## One Concern Per Image

Each image runs **one** process/concern. Do not bundle app + database + cron + nginx into one image with a process supervisor — compose multiple containers instead.

## Layer Ordering for Cache

Order instructions from least- to most-frequently-changing. Copy dependency manifests and install dependencies **before** copying application source, so a source change does not invalidate the dependency layer.

```dockerfile
# Good — deps cached independently of source
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# Bad — any source edit busts the npm install layer
COPY . .
RUN npm ci
```

Combine related `RUN` steps with `&&` and clean up in the same layer (a separate `RUN rm` does not reclaim space from a prior layer):

```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*
```

## .dockerignore

Always ship a `.dockerignore`. It shrinks the build context, speeds up builds, and prevents secrets/junk (`.git`, `.env`, `node_modules`, build caches) from leaking into the image or COPY.

```
.git
.env
*.pem
node_modules
**/__pycache__
dist
.terraform
```

## No Secrets in Layers or ENV

Never bake secrets into the image. Anything in a layer or `ENV` is recoverable by anyone who pulls the image — `docker history` and layer extraction expose it even if a later layer deletes it.

```dockerfile
# Bad — secret persists in layer history forever, even after rm
RUN echo "$NPM_TOKEN" > .npmrc && npm ci && rm .npmrc

# Bad — readable via `docker inspect`
ENV API_KEY=sk-live-abc123

# Good — BuildKit secret mount; never written to a layer
RUN --mount=type=secret,id=npmtoken \
    NPM_TOKEN="$(cat /run/secrets/npmtoken)" npm ci
```

Build with `docker build --secret id=npmtoken,env=NPM_TOKEN .`. Inject runtime secrets via the orchestrator (env from a secret store, mounted files), never `ENV` in the Dockerfile. Use `ARG` only for non-sensitive build config — `ARG` values are also visible in image metadata.

## COPY over ADD

Use `COPY` for local files. `ADD` has implicit, surprising behavior (URL fetching, auto-extracting tarballs). Reserve `ADD` only for its legitimate use: extracting a **local** tarball.

```dockerfile
# Good
COPY app/ /app/

# Bad — fetching a remote URL with ADD (no checksum, no TLS verification control)
ADD https://example.com/installer.sh /installer.sh
```

To fetch a remote artifact, use `RUN curl`/`wget` with an explicit checksum verification, or `ADD --checksum=sha256:...` if you must.

## Explicit EXPOSE

Declare the listening ports with `EXPOSE 8080` — it is metadata only (does not publish ports), but tooling/orchestrators read it.

## HEALTHCHECK

Define a `HEALTHCHECK` so the runtime can detect a hung-but-running process. Keep the probe cheap and use a tool already present in the image.

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["/healthcheck"]
```

On distroless/`scratch` (no shell, no `curl`), ship a small static healthcheck binary or use the orchestrator's own probes (Kubernetes liveness/readiness) instead.

## ENTRYPOINT vs CMD

- Use **`ENTRYPOINT`** for the fixed executable the image always runs.
- Use **`CMD`** for default arguments that a user can override at `docker run`.
- Always use **exec form** (JSON array) — shell form (`CMD npm start`) wraps the process in `/bin/sh -c`, which breaks signal forwarding.

```dockerfile
# Good — exec form; CMD args are overridable, ENTRYPOINT is fixed
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]

# Bad — shell form: PID 1 is sh, signals never reach nginx
ENTRYPOINT nginx -g "daemon off;"
```

## Signal Handling / PID 1

The entrypoint runs as PID 1, which does not get default signal handlers and does not reap zombies. If your process does not handle `SIGTERM` and reap children, use a minimal init.

```dockerfile
# Good — tini reaps zombies and forwards signals
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "server.js"]
```

Use `docker run --init` (or the compose `init: true` / Kubernetes `shareProcessNamespace` equivalents) as an alternative. Apps that natively handle `SIGTERM` and have no child processes can skip this.

## Deterministic Dependency Installs

Install from a committed **lockfile** in the locked/frozen install mode, never a resolver that can drift. Use the language profile's frozen-install command (e.g. `npm ci`, `uv sync --frozen`, `go mod download` with `go.sum`, `cargo build --locked`).

```dockerfile
# Good — fails if lockfile and manifest disagree
COPY package.json package-lock.json ./
RUN npm ci

# Bad — resolves fresh versions on every build
RUN npm install
```

## Read-Only Root Filesystem

Design the image to run with a read-only root filesystem. Write only to explicitly declared, mounted, writable paths (`tmpfs`, volumes).

```yaml
# compose — enforce read-only root, allow a tmpfs for scratch space
services:
  api:
    read_only: true
    tmpfs:
      - /tmp
```

Avoid processes that write into the image filesystem at runtime (logs go to stdout/stderr; caches go to a mounted volume). This pairs with non-root and dropped capabilities to harden the container.

## Drop Capabilities and Privilege Escalation

Plain `docker run`/compose containers keep a default capability set and can gain privileges. Drop all capabilities and add back only what is required, and disable privilege escalation. (Under Kubernetes this is set via the pod `securityContext` instead.)

```bash
# docker run
docker run --cap-drop ALL --security-opt no-new-privileges --read-only myimage:tag
```

```yaml
# compose
services:
  api:
    cap_drop: ["ALL"]
    # cap_add: ["NET_BIND_SERVICE"]   # only the specific cap needed
    security_opt: ["no-new-privileges:true"]
```

## SBOM and Provenance Attestations

Attach a Software Bill of Materials and build provenance so the image's contents and build process are verifiable downstream (policy gates, supply-chain audits).

```bash
docker buildx build --sbom=true --provenance=mode=max -t myimage:tag --push .
```

Attestations require BuildKit and the containerd image store, and persist reliably only when pushed to a registry. `mode=max` records the full build (all stages, args, source); use `mode=min` to reduce metadata exposure.

## OCI Image Labels

Stamp standard `org.opencontainers.image.*` labels so the image is traceable back to its source revision and build time. Inject the dynamic values via `ARG`.

```dockerfile
ARG VCS_REF
ARG BUILD_DATE
LABEL org.opencontainers.image.source="https://github.com/org/repo" \
      org.opencontainers.image.revision="$VCS_REF" \
      org.opencontainers.image.created="$BUILD_DATE"
```
