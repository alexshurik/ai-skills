#!/bin/bash
# Generate AGENTS.md from all skills
# Creates a cross-platform agent documentation file

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$REPO_DIR/AGENTS.md"
CHECK_ONLY=false

if [ "${1:-}" = "--check" ]; then
    CHECK_ONLY=true
    OUTPUT="$(mktemp /tmp/sk-agents-md.XXXXXX)"
    trap 'rm -f "$OUTPUT"' EXIT
elif [ "${1:-}" = "--output" ]; then
    if [ -z "${2:-}" ]; then
        echo "Usage: $0 [--check | --output <path>]" >&2
        exit 2
    fi
    OUTPUT="$2"
elif [ "$#" -ne 0 ]; then
    echo "Usage: $0 [--check | --output <path>]" >&2
    exit 2
fi

echo "Generating AGENTS.md candidate..."

cat > "$OUTPUT" << 'HEADER'
# AGENTS.md

> Auto-generated. Provides context for AI coding agents.
> Compatible with: OpenAI Codex, Claude Code, Cursor, and Kimi Code CLI

## Available Commands

HEADER

python3 "$REPO_DIR/scripts/manifest_inventory.py" all \
    --format agents-document >> "$OUTPUT"
echo "" >> "$OUTPUT"

cat >> "$OUTPUT" << 'ORCHESTRATION'
## Multi-Agent Orchestration

- Give each child one bounded deliverable. New phases, redo, remediation, and
  independent review use clean contexts; on Codex use `fork_turns="none"` and omit
  model/reasoning overrides so children inherit the parent profile.
- Keep nesting at depth 2. Only a named orchestrator with an explicit child budget
  may spawn; review lenses are leaves. Stable Kimi children cannot nest, so its
  generated root team dispatches review lenses directly.
- Agents return compact `FINAL` or `BLOCKED` messages to their immediate parent.
  Full reports, evidence, diffs, and logs live in shared artifacts; messages carry
  paths and fingerprints.
- Durable change artifacts live under `openspec/changes/<name>/`; heavy runtime
  state lives under `$(git rev-parse --git-path sk-workflow)/<name>/`. The global
  root owns the semantic `events.jsonl` journal and derived `state.json` projection;
  the bounded nested-review lease may record leaf attempts through the same helper.
  Stages own gates/tasks and tasks own attempt history.
- Planning separates required work, explicit non-goals, and individually approved
  Scope Delta IDs. Review keeps severity separate from `required_fix`,
  `user_decision`, `backlog`, and `baseline`; remediation receives only an approved
  finding-ID allowlist.
- Optional/rejected proposals stage in change-local `DEFERRED.md`. Promote only
  user-selected items to the repository tracker or `openspec/backlog/` fallback.
- Full review uses a deterministic lossless review map and exactly three independent
  lenses in one wave: architecture-design, correctness-safety, and engineering-quality.
  Root runs gates once per snapshot; validated scope-manifest union covers every path.
- Launch a full wave before waiting. Keep required children in a foreground join and
  use the longest event-driven mailbox wait permitted by the host and higher-priority
  policy. Record one semantic foreground attempt join; transport-only timeouts are
  not workflow retries, budget events, or runtime-state writes. Never
  list, nudge, or chatter between routine returns. Detach only on explicit user
  request, a forced host deadline, or unavailable/failing wait support; persist the
  reason. Notifications are observability, not workflow continuation. Drain ready
  completions before launching new work.

Canonical policies: `workflow/agents/shared/orchestration-policy.md`,
`workflow/agents/shared/handoff-protocol.md`, and
`workflow/agents/shared/scope-governance.md`. Runtime transitions and migration are
defined by `workflow/agents/shared/runtime-state-policy.md`.
The runtime helper requires Python 3.10+ and resolves `python3`, `python`, or `py -3`.

ORCHESTRATION

# Best-practice profiles (review-steps live under workflow/agents/review-steps/ and are
# internal sub-passes of sk-review-orchestrator, intentionally not listed as top-level agents)
cat >> "$OUTPUT" << 'BPHEADER'
## Best Practices Profiles

Stack-specific coding and review rules live in `shared/best-practices/`, organized by
language, framework, and tooling, plus a framework-agnostic UI (anti-slop design)
profile that loads for any React/Vue/Svelte/Angular/Tailwind/HTML+CSS work. The review orchestrator and developer resolve the
project stack via `shared/best-practices/index.yaml` and load matching profiles
automatically (precedence: project > tooling > framework > language > default).
Downstream projects override or extend profiles via `.agents/best-practices/project/`.
Project `coder.md`/`reviewer.md` contain Enforced and Approved rules only;
`evidence.md` keeps Observed and Legacy/uncertain patterns non-normative.

Available profiles:

BPHEADER

for category in languages frameworks tooling; do
    dir="$REPO_DIR/shared/best-practices/$category"
    [ -d "$dir" ] || continue
    names=$(find "$dir" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort | paste -sd ',' - | sed 's/,/, /g')
    [ -n "$names" ] && echo "- **$category**: $names" >> "$OUTPUT"
done
# Framework-agnostic UI/design profile lives at top level, not under a single framework
[ -d "$REPO_DIR/shared/best-practices/ui" ] && \
    echo "- **ui** (framework-agnostic): anti-slop UI/design rules (coder + reviewer)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

cat >> "$OUTPUT" << 'FOOTER'

## Usage

### Claude Code
```bash
./scripts/install-claude-code.sh
```

### OpenAI Codex
```bash
./scripts/install-codex.sh
```

### Cursor
```bash
CURSOR_SKILLS_DIR=/path/to/project/.cursor/skills ./scripts/install-cursor.sh
./scripts/generate-cursor-rules.sh
cp -R adapters/cursor/.cursor /path/to/project/
```

## Quick Start

Invocation syntax depends on the host:

- **Claude Code:** `/sk-team-feature Add user authentication`
- **OpenAI Codex:** `$sk-team-feature Add user authentication`
- **Kimi Code CLI:** `/skill:sk-team-feature Add user authentication`
- **Cursor and other agents:** mention `sk-team-feature` in chat

## License

MIT
FOOTER

if [ "$CHECK_ONLY" = true ]; then
    if cmp -s "$OUTPUT" "$REPO_DIR/AGENTS.md"; then
        echo "AGENTS.md is current."
    else
        echo "AGENTS.md is stale. Run scripts/generate-agents-md.sh." >&2
        diff -u "$REPO_DIR/AGENTS.md" "$OUTPUT" || true
        exit 1
    fi
else
    echo "Generated: $OUTPUT"
    echo "Lines: $(wc -l < "$OUTPUT" | tr -d ' ')"
fi
