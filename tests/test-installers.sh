#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_HOME="$(mktemp -d /tmp/sk-installers-test.XXXXXX)"
TEST_HOME="$(cd "$TEST_HOME" && pwd -P)"
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
CURSOR_DIR="$TEST_HOME/cursor-project/.cursor/skills"
mkdir -p "$CURSOR_DIR/best-practices"
printf 'keep\n' > "$CURSOR_DIR/best-practices/unrelated.keep"

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

LEAF_CONFLICT_HOME="$TEST_HOME/leaf-conflict-home"
mkdir -p "$LEAF_CONFLICT_HOME/.agents/skills/sk-team-help"
printf 'keep\n' > "$LEAF_CONFLICT_HOME/.agents/skills/sk-team-help/SKILL.md"
if HOME="$LEAF_CONFLICT_HOME" "$REPO_DIR/scripts/install-codex.sh"; then
    echo "Expected unowned leaf conflict failure" >&2
    exit 1
fi
grep -q '^keep$' "$LEAF_CONFLICT_HOME/.agents/skills/sk-team-help/SKILL.md"
test ! -e "$LEAF_CONFLICT_HOME/.agents/skills/sk-team-feature"

SYMLINK_CONFLICT_HOME="$TEST_HOME/symlink-conflict-home"
mkdir -p "$SYMLINK_CONFLICT_HOME/.agents/skills/sk-team-help"
printf 'outside\n' > "$SYMLINK_CONFLICT_HOME/outside.md"
ln -s "$SYMLINK_CONFLICT_HOME/outside.md" \
    "$SYMLINK_CONFLICT_HOME/.agents/skills/sk-team-help/SKILL.md"
if HOME="$SYMLINK_CONFLICT_HOME" "$REPO_DIR/scripts/install-codex.sh"; then
    echo "Expected unowned symlink conflict failure" >&2
    exit 1
fi
grep -q '^outside$' "$SYMLINK_CONFLICT_HOME/outside.md"
test -L "$SYMLINK_CONFLICT_HOME/.agents/skills/sk-team-help/SKILL.md"

# CLI uninstall pairs each target with an explicit platform. A valid receipt
# from another platform must not authorize deletion.
WRONG_PLATFORM_TARGET="$TEST_HOME/wrong-platform-target"
python3 "$REPO_DIR/scripts/skills_tool.py" install \
    --platform kimi \
    --target "$WRONG_PLATFORM_TARGET"
if python3 "$REPO_DIR/scripts/skills_tool.py" uninstall \
    --target codex "$WRONG_PLATFORM_TARGET"; then
    echo "Expected wrong-platform uninstall refusal" >&2
    exit 1
fi
test -f "$WRONG_PLATFORM_TARGET/.sk-skills-install.json"
test -f "$WRONG_PLATFORM_TARGET/skills/sk-team-help/SKILL.md"
python3 "$REPO_DIR/scripts/skills_tool.py" uninstall \
    --target kimi "$WRONG_PLATFORM_TARGET"

# Legacy resource migration must not traverse a parent symlink and move an
# unrelated file outside the discovery root.
MIGRATION_ESCAPE_HOME="$TEST_HOME/migration-escape-home"
mkdir -p "$MIGRATION_ESCAPE_HOME/.codex/skills"
mkdir -p "$MIGRATION_ESCAPE_HOME/outside-best-practices"
printf 'outside\n' \
    > "$MIGRATION_ESCAPE_HOME/outside-best-practices/resolver.md"
ln -s "$MIGRATION_ESCAPE_HOME/outside-best-practices" \
    "$MIGRATION_ESCAPE_HOME/.codex/skills/best-practices"
if HOME="$MIGRATION_ESCAPE_HOME" \
    "$REPO_DIR/scripts/migrate-legacy-codex.sh" \
    "$MIGRATION_ESCAPE_HOME/backup"; then
    echo "Expected legacy parent-symlink escape refusal" >&2
    exit 1
fi
grep -q '^outside$' \
    "$MIGRATION_ESCAPE_HOME/outside-best-practices/resolver.md"
test -L "$MIGRATION_ESCAPE_HOME/.codex/skills/best-practices"
test ! -e "$MIGRATION_ESCAPE_HOME/backup/best-practices/resolver.md"

# The requested backup path itself must not redirect migration through a
# symlinked parent.
BACKUP_ESCAPE_HOME="$TEST_HOME/backup-escape-home"
mkdir -p "$BACKUP_ESCAPE_HOME/.codex/skills/sk-code-review"
cp "$REPO_DIR/utilities/sk-code-review/SKILL.md" \
    "$BACKUP_ESCAPE_HOME/.codex/skills/sk-code-review/SKILL.md"
mkdir -p "$BACKUP_ESCAPE_HOME/outside-backup"
ln -s "$BACKUP_ESCAPE_HOME/outside-backup" \
    "$BACKUP_ESCAPE_HOME/backup-link"
if HOME="$BACKUP_ESCAPE_HOME" \
    "$REPO_DIR/scripts/migrate-legacy-codex.sh" \
    "$BACKUP_ESCAPE_HOME/backup-link/nested"; then
    echo "Expected legacy backup parent-symlink refusal" >&2
    exit 1
fi
test -f "$BACKUP_ESCAPE_HOME/.codex/skills/sk-code-review/SKILL.md"
test ! -e "$BACKUP_ESCAPE_HOME/outside-backup/nested"

HOME="$TEST_HOME" "$REPO_DIR/scripts/install-codex.sh"
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-claude-code.sh"
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-kimi.sh"
CURSOR_SKILLS_DIR="$CURSOR_DIR" "$REPO_DIR/scripts/install-cursor.sh"

# Reinstall must be idempotent.
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-codex.sh"

test -f "$TEST_HOME/.agents/skills/sk-team-feature/references/phase-prompts.md"
test -f "$TEST_HOME/.agents/skills/sk-team-feature/agents/openai.yaml"
test -f "$TEST_HOME/.agents/skills/agents/review-evidence/collect-change-evidence.sh"
test -f "$TEST_HOME/.agents/skills/agents/review-evidence/review-map.sh"
test -f "$TEST_HOME/.agents/skills/agents/review-evidence/review_map.py"
test -f "$TEST_HOME/.agents/skills/shared/scope-governance.md"
test -f "$TEST_HOME/.agents/skills/agents/templates/deferred.md"
test ! -e "$TEST_HOME/.agents/skills/agents/review-evidence/__pycache__"
test -f "$TEST_HOME/.agents/skills/review-steps/architecture-design.md"
test -f "$TEST_HOME/.agents/skills/review-steps/correctness-safety.md"
test -f "$TEST_HOME/.agents/skills/review-steps/engineering-quality.md"
grep -Fq \
    "$TEST_HOME/.agents/skills/best-practices/project-conventions-guide.md" \
    "$TEST_HOME/.agents/skills/sk-explore-codebase/SKILL.md"
grep -Fq \
    "$TEST_HOME/.agents/skills/best-practices/convention-evidence-model.md" \
    "$TEST_HOME/.agents/skills/sk-explore-codebase/SKILL.md"
test -f "$CURSOR_DIR/sk-team-feature/SKILL.md"
test -f "$CURSOR_DIR/sk-team-feature/references/phase-prompts.md"
test -f "$CURSOR_DIR/best-practices/unrelated.keep"
test -L "$TEST_HOME/.claude/skills/sk-team-feature"
test -f "$TEST_HOME/.claude/agents/shared/scope-governance.md"
test -f "$TEST_HOME/.claude/agents/templates/deferred.md"
test "$(find "$TEST_HOME/.claude/agents/review-steps" -type l | wc -l | tr -d ' ')" = "3"
test -f "$TEST_HOME/.config/agents/agents/references/sk-team-feature.md"
test -f "$TEST_HOME/.config/agents/agents/sk-review-architecture-design.yaml"
test -f "$TEST_HOME/.config/agents/agents/sk-review-correctness-safety.yaml"
test -f "$TEST_HOME/.config/agents/agents/sk-review-engineering-quality.yaml"
test -f "$TEST_HOME/.config/agents/agents/references/shared/scope-governance.md"
test -f "$TEST_HOME/.config/agents/agents/references/templates/deferred.md"
test ! -L "$TEST_HOME/.config/agents/skills/sk-team-feature"
test -f "$TEST_HOME/.config/agents/skills/sk-team-feature/SKILL.md"
grep -q "Retrospective" "$TEST_HOME/.config/agents/agents/references/sk-team-feature.md"
grep -Fq '${KIMI_AGENTS_MD}' \
    "$TEST_HOME/.config/agents/agents/references/sk-team-feature.md"
grep -q "Embedded phase prompts" \
    "$TEST_HOME/.config/agents/agents/references/sk-team-feature.md"
grep -Fq \
    "$TEST_HOME/.config/agents/agents/references/best-practices/project-conventions-guide.md" \
    "$TEST_HOME/.config/agents/skills/sk-explore-codebase/SKILL.md"
grep -q "kimi_cli.tools.agent:Agent" \
    "$TEST_HOME/.config/agents/agents/sk-developer.yaml"
grep -q "review-architecture-design:" "$TEST_HOME/.config/agents/agents/sk-team.yaml"
grep -q "Kimi execution override" \
    "$TEST_HOME/.config/agents/agents/references/sk-team-feature.md"
if grep -R -q "kimi_cli.tools.multiagent:Task" \
    "$TEST_HOME/.config/agents/agents"; then
    echo "Removed Kimi Task tool identifier was rendered" >&2
    exit 1
fi
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
mkdir -p "$TEST_HOME/.codex/skills/best-practices"
cp "$REPO_DIR/shared/best-practices/resolver.md" \
    "$TEST_HOME/.codex/skills/best-practices/resolver.md"
printf 'keep\n' \
    > "$TEST_HOME/.codex/skills/best-practices/unrelated.keep"
if HOME="$TEST_HOME" "$REPO_DIR/scripts/doctor-installation.sh"; then
    echo "Expected duplicate doctor failure" >&2
    exit 1
fi

BACKUP="$TEST_HOME/.codex/backups/test-migration"
HOME="$TEST_HOME" "$REPO_DIR/scripts/migrate-legacy-codex.sh" "$BACKUP"
test -f "$BACKUP/sk-code-review/SKILL.md"
test -f "$BACKUP/sk-developer/SKILL.md"
test -f "$BACKUP/best-practices/resolver.md"
test -f "$TEST_HOME/.codex/skills/best-practices/unrelated.keep"
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

# All targets are preflighted before a multi-platform uninstall mutates any of them.
printf '\nlocal edit\n' \
    >> "$TEST_HOME/.config/agents/skills/sk-team-help/SKILL.md"
if HOME="$TEST_HOME" "$REPO_DIR/scripts/uninstall.sh"; then
    echo "Expected later-target drift to block every uninstall" >&2
    exit 1
fi
test -f "$TEST_HOME/.agents/skills/sk-team-feature/SKILL.md"
test -L "$TEST_HOME/.claude/skills/sk-team-feature"
HOME="$TEST_HOME" "$REPO_DIR/scripts/install-kimi.sh"

HOME="$TEST_HOME" "$REPO_DIR/scripts/uninstall.sh"
test -f "$TEST_HOME/.agents/skills/unrelated/SKILL.md"
test -f "$TEST_HOME/.agents/skills/best-practices/unrelated.keep"
test -f "$TEST_HOME/.codex/skills/.system/marker"
test -f "$TEST_HOME/.claude/agents/unrelated.keep"
test -f "$TEST_HOME/.config/agents/agents/references/best-practices/unrelated.keep"
test ! -e "$TEST_HOME/.agents/skills/sk-team-feature"

python3 "$REPO_DIR/scripts/skills_tool.py" uninstall \
    --target cursor "$CURSOR_DIR"
test -f "$CURSOR_DIR/best-practices/unrelated.keep"
test ! -e "$CURSOR_DIR/sk-team-feature"

# A single-platform installation can be removed, and repeated uninstall is a no-op.
SINGLE_HOME="$TEST_HOME/single-platform-home"
HOME="$SINGLE_HOME" "$REPO_DIR/scripts/install-kimi.sh"
HOME="$SINGLE_HOME" "$REPO_DIR/scripts/uninstall.sh"
test ! -e "$SINGLE_HOME/.config/agents/skills/sk-team-feature"
HOME="$SINGLE_HOME" "$REPO_DIR/scripts/uninstall.sh"

echo "OK: installers"
