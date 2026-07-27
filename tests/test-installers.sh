#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_HOME="$(mktemp -d /tmp/sk-installers-test.XXXXXX)"
trap 'rm -rf "$TEST_HOME"' EXIT

mkdir -p "$TEST_HOME/.agents/skills/unrelated"
printf '%s\n' "---" "name: unrelated" "description: keep" "---" \
    > "$TEST_HOME/.agents/skills/unrelated/SKILL.md"
mkdir -p "$TEST_HOME/.agents/skills/best-practices"
printf 'keep\n' > "$TEST_HOME/.agents/skills/best-practices/unrelated.keep"
mkdir -p "$TEST_HOME/.codex/skills/.system"
printf 'keep\n' > "$TEST_HOME/.codex/skills/.system/marker"
mkdir -p "$TEST_HOME/.claude/agents"
printf 'keep\n' > "$TEST_HOME/.claude/agents/unrelated.keep"
mkdir -p "$TEST_HOME/.config/agents/agents/references/best-practices"
printf 'keep\n' \
    > "$TEST_HOME/.config/agents/agents/references/best-practices/unrelated.keep"
mkdir -p "$TEST_HOME/.config/agents/skills"
ln -s "$REPO_DIR/workflow/skills/sk-team-feature" \
    "$TEST_HOME/.config/agents/skills/sk-team-feature"

# Rendering and conflict checks finish before any live target mutation.
CONFLICT_HOME="$TEST_HOME/conflict-home"
mkdir -p "$CONFLICT_HOME/.agents/skills/sk-team-help/SKILL.md"
printf 'keep\n' \
    > "$CONFLICT_HOME/.agents/skills/sk-team-help/SKILL.md/unrelated.keep"
if HOME="$CONFLICT_HOME" "$REPO_DIR/scripts/install-codex.sh"; then
    echo "Expected preflight conflict failure" >&2
    exit 1
fi
test -f "$CONFLICT_HOME/.agents/skills/sk-team-help/SKILL.md/unrelated.keep"
test ! -e "$CONFLICT_HOME/.agents/skills/sk-team-feature"

HOME="$TEST_HOME" "$REPO_DIR/scripts/install-codex.sh"
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-claude-code.sh"
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-kimi.sh"

# Reinstall must be idempotent.
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-codex.sh"

test -f "$TEST_HOME/.agents/skills/sk-team-feature/references/phase-prompts.md"
test -f "$TEST_HOME/.agents/skills/sk-team-feature/agents/openai.yaml"
test -f "$TEST_HOME/.agents/skills/agents/review-evidence/collect-change-evidence.sh"
test -f "$TEST_HOME/.agents/skills/review-steps/abstraction.md"
test -f "$TEST_HOME/.agents/skills/review-steps/imports.md"
test -f "$TEST_HOME/.agents/skills/review-steps/structure.md"
test -L "$TEST_HOME/.claude/skills/sk-team-feature"
test "$(find "$TEST_HOME/.claude/agents/review-steps" -type l | wc -l | tr -d ' ')" = "7"
test -f "$TEST_HOME/.config/agents/agents/references/sk-team-feature.md"
test ! -L "$TEST_HOME/.config/agents/skills/sk-team-feature"
test -f "$TEST_HOME/.config/agents/skills/sk-team-feature/SKILL.md"
grep -q "Retrospective" "$TEST_HOME/.config/agents/agents/references/sk-team-feature.md"
test -f "$TEST_HOME/.agents/skills/best-practices/unrelated.keep"
test -f "$TEST_HOME/.claude/agents/unrelated.keep"
test -f "$TEST_HOME/.config/agents/agents/references/best-practices/unrelated.keep"

# Verification checks complete file content, receipts, and exact symlink targets.
printf '\ndrift\n' >> "$TEST_HOME/.agents/skills/sk-team-help/SKILL.md"
if "$REPO_DIR/scripts/verify-installation.sh" \
    codex "$TEST_HOME/.agents/skills"; then
    echo "Expected Codex drift verification failure" >&2
    exit 1
fi
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-codex.sh"

ln -sfn "$TEST_HOME/wrong-target" \
    "$TEST_HOME/.claude/skills/sk-team-help"
if "$REPO_DIR/scripts/verify-installation.sh" claude "$TEST_HOME/.claude"; then
    echo "Expected Claude symlink verification failure" >&2
    exit 1
fi
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-claude-code.sh"

# Create a legacy duplicate and verify the doctor catches it.
mkdir -p "$TEST_HOME/.codex/skills/sk-code-review"
cp "$REPO_DIR/utilities/sk-code-review/SKILL.md" \
    "$TEST_HOME/.codex/skills/sk-code-review/SKILL.md"
mkdir -p "$TEST_HOME/.codex/skills/sk-developer"
cp "$REPO_DIR/workflow/agents/sk-developer.md" \
    "$TEST_HOME/.codex/skills/sk-developer/SKILL.md"
if HOME="$TEST_HOME" "$REPO_DIR/scripts/doctor-installation.sh"; then
    echo "Expected duplicate doctor failure" >&2
    exit 1
fi

BACKUP="$TEST_HOME/.codex/backups/test-migration"
HOME="$TEST_HOME" "$REPO_DIR/scripts/migrate-legacy-codex.sh" "$BACKUP"
test -f "$BACKUP/sk-code-review/SKILL.md"
test -f "$BACKUP/sk-developer/SKILL.md"
test -f "$TEST_HOME/.codex/skills/.system/marker"
HOME="$TEST_HOME" "$REPO_DIR/scripts/doctor-installation.sh"

# A receipt-owned parent replaced by a symlink cannot redirect uninstall outside.
mv "$TEST_HOME/.agents/skills/sk-team-help" \
    "$TEST_HOME/sk-team-help-owned"
mkdir -p "$TEST_HOME/outside-target"
printf 'outside\n' > "$TEST_HOME/outside-target/SKILL.md"
ln -s "$TEST_HOME/outside-target" \
    "$TEST_HOME/.agents/skills/sk-team-help"
if HOME="$TEST_HOME" "$REPO_DIR/scripts/uninstall.sh"; then
    echo "Expected parent-symlink escape refusal" >&2
    exit 1
fi
test -f "$TEST_HOME/outside-target/SKILL.md"
unlink "$TEST_HOME/.agents/skills/sk-team-help"
mv "$TEST_HOME/sk-team-help-owned" \
    "$TEST_HOME/.agents/skills/sk-team-help"

# Uninstall refuses to delete a modified receipt-owned file.
printf '\nlocal edit\n' >> "$TEST_HOME/.agents/skills/sk-team-help/SKILL.md"
if HOME="$TEST_HOME" "$REPO_DIR/scripts/uninstall.sh"; then
    echo "Expected safe uninstall refusal for modified owned file" >&2
    exit 1
fi
grep -q "local edit" "$TEST_HOME/.agents/skills/sk-team-help/SKILL.md"
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-codex.sh"

HOME="$TEST_HOME" "$REPO_DIR/scripts/uninstall.sh"
test -f "$TEST_HOME/.agents/skills/unrelated/SKILL.md"
test -f "$TEST_HOME/.agents/skills/best-practices/unrelated.keep"
test -f "$TEST_HOME/.codex/skills/.system/marker"
test -f "$TEST_HOME/.claude/agents/unrelated.keep"
test -f "$TEST_HOME/.config/agents/agents/references/best-practices/unrelated.keep"
test ! -e "$TEST_HOME/.agents/skills/sk-team-feature"

echo "OK: installers"
