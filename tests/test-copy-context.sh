#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COPY_SCRIPT="$REPO_DIR/context/sk-copy-context/scripts/copy-context.sh"
TEST_ROOT="$(mktemp -d /tmp/sk-copy-context.XXXXXX)"
trap 'rm -rf "$TEST_ROOT"' EXIT

run_case() {
    local command_name="$1"
    local expected_args="$2"
    local case_root="$TEST_ROOT/$command_name"
    local command_path="$case_root/bin/$command_name"
    mkdir -p "$case_root/bin"
    {
        echo '#!/bin/bash'
        echo 'printf "%s" "$*" > "$CAPTURE_ARGS"'
        echo '/bin/cat > "$CAPTURE_INPUT"'
    } > "$command_path"
    chmod +x "$command_path"

    PATH="$case_root/bin:/bin" \
        CAPTURE_ARGS="$case_root/args" \
        CAPTURE_INPUT="$case_root/input" \
        /bin/bash "$COPY_SCRIPT" "$PAYLOAD"

    cmp "$PAYLOAD" "$case_root/input"
    test "$(cat "$case_root/args")" = "$expected_args"
}

PAYLOAD="$TEST_ROOT/payload"
printf '%s\n' \
    'portable context' \
    'CONTEXT' \
    "\$(touch $TEST_ROOT/must-not-run)" \
    '`echo not-shell-source` ; $HOME * ? [x]' > "$PAYLOAD"

test -x "$COPY_SCRIPT"
run_case pbcopy ""
run_case wl-copy ""
run_case xclip "-selection clipboard"
run_case powershell.exe '-NoProfile -NonInteractive -Command $input | Set-Clipboard'
run_case powershell '-NoProfile -NonInteractive -Command $input | Set-Clipboard'
test ! -e "$TEST_ROOT/must-not-run"

EMPTY_PATH="$TEST_ROOT/empty-bin"
mkdir -p "$EMPTY_PATH"
if PATH="$EMPTY_PATH" /bin/bash "$COPY_SCRIPT" "$PAYLOAD" \
    > "$TEST_ROOT/no-backend.out" 2> "$TEST_ROOT/no-backend.err"; then
    echo "Expected missing clipboard backend to fail" >&2
    exit 1
fi
grep -q "No supported clipboard command" "$TEST_ROOT/no-backend.err"

FAIL_ROOT="$TEST_ROOT/failing"
mkdir -p "$FAIL_ROOT"
{
    echo '#!/bin/bash'
    echo 'exit 19'
} > "$FAIL_ROOT/pbcopy"
chmod +x "$FAIL_ROOT/pbcopy"
set +e
PATH="$FAIL_ROOT" /bin/bash "$COPY_SCRIPT" "$PAYLOAD" \
    > "$TEST_ROOT/failing.out" 2> "$TEST_ROOT/failing.err"
FAIL_STATUS="$?"
set -e
test "$FAIL_STATUS" -eq 19
test ! -s "$TEST_ROOT/failing.out"

echo "OK: portable context clipboard"
