#!/bin/bash
# Run the five neutral behavioral prompts in isolated, ephemeral Codex sessions.

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <historical-backend-repo> <empty-output-dir>" >&2
    exit 2
fi

EVAL_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$EVAL_DIR/../.." && pwd)"
SOURCE_REPO="$1"
OUTPUT_DIR="$2"
FIXTURES_DIR="$OUTPUT_DIR/fixtures"
RESPONSES_DIR="$OUTPUT_DIR/responses"

if [ -e "$OUTPUT_DIR" ] && [ -n "$(find "$OUTPUT_DIR" -mindepth 1 -print -quit)" ]; then
    echo "Output directory must be empty: $OUTPUT_DIR" >&2
    exit 2
fi
command -v codex >/dev/null

mkdir -p "$FIXTURES_DIR" "$RESPONSES_DIR"
"$EVAL_DIR/build-historical-fixture.sh" \
    "$SOURCE_REPO" \
    "$FIXTURES_DIR/review"

mkdir -p "$FIXTURES_DIR/architect"
git -C "$SOURCE_REPO" archive ee6100b | tar -x -C "$FIXTURES_DIR/architect"
mkdir -p "$FIXTURES_DIR/architect/cases"
cp "$EVAL_DIR/cases/architect-proposal.md" \
    "$FIXTURES_DIR/architect/cases/architect-proposal.md"
cp -R "$EVAL_DIR/cases/developer-weak-design" "$FIXTURES_DIR/developer"
cp -R "$EVAL_DIR/cases/codestyle-frequency-trap" "$FIXTURES_DIR/codestyle"
cp -R "$EVAL_DIR/cases/retrospective-routing" "$FIXTURES_DIR/retrospective"
cp -R "$EVAL_DIR/cases/local-import-claim" "$FIXTURES_DIR/local-import"
cp -R "$EVAL_DIR/cases/deployment-scope-creep" "$FIXTURES_DIR/deployment"
"$EVAL_DIR/cases/review-scope-baseline/build-fixture.sh" \
    "$FIXTURES_DIR/review-scope"

initialize_fixture() {
    local fixture="$1"
    git -C "$fixture" init -q
    git -C "$fixture" config user.email "skill-eval@example.invalid"
    git -C "$fixture" config user.name "Skill Eval"
    git -C "$fixture" add .
    git -C "$fixture" commit -qm "eval fixture"
}

initialize_fixture "$FIXTURES_DIR/architect"
initialize_fixture "$FIXTURES_DIR/developer"
initialize_fixture "$FIXTURES_DIR/codestyle"
initialize_fixture "$FIXTURES_DIR/retrospective"

git -C "$FIXTURES_DIR/local-import" init -q
git -C "$FIXTURES_DIR/local-import" config user.email "skill-eval@example.invalid"
git -C "$FIXTURES_DIR/local-import" config user.name "Skill Eval"
git -C "$FIXTURES_DIR/local-import" add src/storage.py
git -C "$FIXTURES_DIR/local-import" commit -qm "local-import baseline"

git -C "$FIXTURES_DIR/deployment" init -q
git -C "$FIXTURES_DIR/deployment" config user.email "skill-eval@example.invalid"
git -C "$FIXTURES_DIR/deployment" config user.name "Skill Eval"
git -C "$FIXTURES_DIR/deployment" add AGENTS.md
git -C "$FIXTURES_DIR/deployment" commit -qm "deployment baseline"

run_agent() {
    local name="$1"
    local fixture="$2"
    local prompt_name="$3"
    local prompt="$EVAL_DIR/prompts/$prompt_name.md"
    local response="$RESPONSES_DIR/$name.md"
    {
        sed -n '1,240p' "$prompt"
        printf '\nSkills source: %s\n' "$SKILLS_DIR"
        printf '%s\n' \
            "Do not inspect the eval configuration, expected assertions, or other fixtures."
    } | codex --ask-for-approval never exec \
        --ephemeral \
        --ignore-user-config \
        --sandbox workspace-write \
        --color never \
        --cd "$fixture" \
        --output-last-message "$response" \
        -
}

run_agent architect "$FIXTURES_DIR/architect" architect
run_agent developer "$FIXTURES_DIR/developer" developer
run_agent codestyle "$FIXTURES_DIR/codestyle" codestyle
run_agent review "$FIXTURES_DIR/review" review
run_agent retrospective "$FIXTURES_DIR/retrospective" retrospective
run_agent local-import "$FIXTURES_DIR/local-import" review
run_agent deployment "$FIXTURES_DIR/deployment" review
run_agent review-scope "$FIXTURES_DIR/review-scope" review

echo "Fresh-context responses: $RESPONSES_DIR"
echo "Score them against eval.yaml and record the evidence under results/."
