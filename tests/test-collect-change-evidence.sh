#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/sk-evidence-test.XXXXXX)"
FIRST_COMMIT_DIR="$(mktemp -d /tmp/sk-evidence-first.XXXXXX)"
ESCAPE_DIR="$(mktemp -d /tmp/sk-evidence-escape.XXXXXX)"
OUTPUT="$(mktemp /tmp/sk-evidence-output.XXXXXX)"
FIRST_OUTPUT="$(mktemp /tmp/sk-evidence-first-output.XXXXXX)"
ARTIFACT_OUTPUT="$(mktemp /tmp/sk-evidence-artifact.XXXXXX)"
RECEIPT_OUTPUT="$(mktemp /tmp/sk-evidence-receipt.XXXXXX)"
trap 'rm -rf "$FIXTURE_DIR" "$FIRST_COMMIT_DIR" "$ESCAPE_DIR"; rm -f "$OUTPUT" "$FIRST_OUTPUT" "$ARTIFACT_OUTPUT" "$RECEIPT_OUTPUT"' EXIT

git -C "$FIXTURE_DIR" init -q
git -C "$FIXTURE_DIR" config user.email "skills-test@example.invalid"
git -C "$FIXTURE_DIR" config user.name "Skills Test"

mkdir -p "$FIXTURE_DIR/src"
printf 'def stable():\n    return True\n' > "$FIXTURE_DIR/src/stable.py"
printf 'def renamed():\n    return True\n' > "$FIXTURE_DIR/src/rename_me.py"
printf 'def removed():\n    return True\n' > "$FIXTURE_DIR/src/delete_me.py"
printf 'def tracked():\n    return True\n' > "$FIXTURE_DIR/src/tracked_link.py"
for number in $(seq 1 300); do
    printf 'value_%s = %s\n' "$number" "$number"
done > "$FIXTURE_DIR/src/threshold.py"
git -C "$FIXTURE_DIR" add src
git -C "$FIXTURE_DIR" commit -qm "baseline"

printf 'COMMITTED = True\n' > "$FIXTURE_DIR/src/committed.py"
git -C "$FIXTURE_DIR" add src/committed.py
git -C "$FIXTURE_DIR" commit -qm "committed change"

git -C "$FIXTURE_DIR" mv src/rename_me.py src/renamed.py
printf 'CHANGED = True\n' >> "$FIXTURE_DIR/src/renamed.py"
git -C "$FIXTURE_DIR" add src/renamed.py
git -C "$FIXTURE_DIR" rm -q src/delete_me.py

printf 'def staged():\n    return False\n' >> "$FIXTURE_DIR/src/stable.py"
git -C "$FIXTURE_DIR" add src/stable.py
printf 'def unstaged():\n    return None\n' >> "$FIXTURE_DIR/src/stable.py"
printf 'value_301 = 301\nvalue_302 = 302\n' >> "$FIXTURE_DIR/src/threshold.py"

{
    printf 'def large_module():\n'
    for number in $(seq 1 301); do
        printf '    value_%s = %s\n' "$number" "$number"
    done
    printf '    from package import dependency\n'
} > "$FIXTURE_DIR/src/large module.py"
printf 'export async function load() {\n  return import("./lazy.js");\n}\n' \
    > "$FIXTURE_DIR/src/lazy.ts"
{
    printf 'from outside import secret\n'
    for number in $(seq 1 301); do
        printf 'outside_%s = %s\n' "$number" "$number"
    done
} > "$ESCAPE_DIR/outside.py"
rm "$FIXTURE_DIR/src/tracked_link.py"
ln -s "$ESCAPE_DIR/outside.py" "$FIXTURE_DIR/src/tracked_link.py"
ln -s "$ESCAPE_DIR/outside.py" "$FIXTURE_DIR/src/untracked_link.py"

"$REPO_DIR/shared/review-evidence/collect-change-evidence.sh" \
    --repo "$FIXTURE_DIR" \
    --format json > "$OUTPUT"

python3 - "$OUTPUT" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as evidence_file:
    data = json.load(evidence_file)

assert "src/large module.py" in data["scope"]["untracked"]
assert "src/lazy.ts" in data["scope"]["untracked"]
assert any(item["path"] == "src/committed.py" for item in data["scope"]["committed"])
assert any(item["path"] == "src/stable.py" for item in data["scope"]["staged"])
assert any(item["path"] == "src/stable.py" for item in data["scope"]["unstaged"])
assert any(item["status"].startswith("R") for item in data["scope"]["staged"])
assert any(item["status"] == "D" for item in data["scope"]["staged"])
assert len(data["fingerprint"]) == 64

files = {item["path"]: item for item in data["files"]}
assert files["src/large module.py"]["over_300"]
assert files["src/large module.py"]["local_imports"][0]["kind"] == "python-local-import"
assert files["src/lazy.ts"]["micro_file_candidate"]
assert files["src/lazy.ts"]["local_imports"][0]["kind"] == "dynamic-import"
assert files["src/stable.py"]["changed_intervals"]
assert files["src/renamed.py"]["base_path"] == "src/rename_me.py"
assert files["src/renamed.py"]["base_lines"] == 2
assert not files["src/renamed.py"]["micro_file_candidate"]
assert files["src/delete_me.py"]["base_lines"] == 2
assert files["src/delete_me.py"]["current_lines"] is None
assert files["src/threshold.py"]["base_lines"] == 300
assert files["src/threshold.py"]["current_lines"] == 302
assert files["src/threshold.py"]["crossed_300"]
for relative in ("src/tracked_link.py", "src/untracked_link.py"):
    assert files[relative]["current_kind"] == "symlink"
    assert files[relative]["current_symlink_target"].endswith("/outside.py")
    assert files[relative]["current_lines"] is None
    assert files[relative]["local_imports"] == []
    assert not files[relative]["over_300"]
PY

# Artifact mode keeps the full payload out of the caller context and returns a
# compact, content-addressed receipt.
"$REPO_DIR/shared/review-evidence/collect-change-evidence.sh" \
    --repo "$FIXTURE_DIR" \
    --format json \
    --output "$ARTIFACT_OUTPUT" > "$RECEIPT_OUTPUT"

python3 - "$ARTIFACT_OUTPUT" "$RECEIPT_OUTPUT" "$OUTPUT" <<'PY'
import json
import sys
from pathlib import Path

with open(sys.argv[1], encoding="utf-8") as artifact_file:
    artifact = json.load(artifact_file)
with open(sys.argv[2], encoding="utf-8") as receipt_file:
    receipt = json.load(receipt_file)
with open(sys.argv[3], encoding="utf-8") as original_file:
    original = json.load(original_file)

assert Path(receipt["artifact"]).resolve() == Path(sys.argv[1]).resolve()
assert receipt["fingerprint"] == artifact["fingerprint"]
assert artifact["fingerprint"] == original["fingerprint"]
assert len(receipt) == 2
PY

FIRST_FINGERPRINT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["fingerprint"])' "$ARTIFACT_OUTPUT")"
printf 'content-sensitive change\n' >> "$FIXTURE_DIR/src/lazy.ts"
"$REPO_DIR/shared/review-evidence/collect-change-evidence.sh" \
    --repo "$FIXTURE_DIR" \
    --format json \
    --output "$ARTIFACT_OUTPUT" > "$RECEIPT_OUTPUT"
SECOND_FINGERPRINT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["fingerprint"])' "$ARTIFACT_OUTPUT")"
test "$FIRST_FINGERPRINT" != "$SECOND_FINGERPRINT"

# A repository with only its first commit has no parent/upstream and must still work.
git -C "$FIRST_COMMIT_DIR" init -q
git -C "$FIRST_COMMIT_DIR" config user.email "skills-test@example.invalid"
git -C "$FIRST_COMMIT_DIR" config user.name "Skills Test"
printf 'first\n' > "$FIRST_COMMIT_DIR/first.txt"
git -C "$FIRST_COMMIT_DIR" add first.txt
git -C "$FIRST_COMMIT_DIR" commit -qm "first"
"$REPO_DIR/shared/review-evidence/collect-change-evidence.sh" \
    --repo "$FIRST_COMMIT_DIR" \
    --format json > "$FIRST_OUTPUT"
python3 - "$FIRST_OUTPUT" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as evidence_file:
    data = json.load(evidence_file)
assert any(item["path"] == "first.txt" for item in data["scope"]["committed"])
PY

echo "OK: change evidence"
