#!/usr/bin/env python3
"""Exercise the semantic journal, projection recovery, and v1 migration."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = ROOT / "workflow/agents/shared/runtime-state/sk_state.py"
SPEC = importlib.util.spec_from_file_location("sk_state", TOOL_PATH)
assert SPEC and SPEC.loader
SK_STATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SK_STATE)


def invoke(*arguments: str) -> tuple[int, str, str]:
    output = io.StringIO()
    errors = io.StringIO()
    with redirect_stdout(output), redirect_stderr(errors):
        parser = SK_STATE.build_parser()
        args = parser.parse_args(list(arguments))
        try:
            args.handler(args)
        except (OSError, SK_STATE.StateError) as error:
            print(f"ERROR: {error}", file=errors)
            return 1, output.getvalue(), errors.getvalue()
    return 0, output.getvalue(), errors.getvalue()


def expect_ok(*arguments: str) -> dict[str, object] | None:
    code, output, errors = invoke(*arguments)
    assert code == 0, errors
    if output.startswith("{"):
        return json.loads(output)
    return None


def mutate(runtime: Path, revision: int, command: str, *arguments: str) -> dict[str, object]:
    result = expect_ok(
        command,
        "--runtime-dir",
        str(runtime),
        "--expected-revision",
        str(revision),
        "--command-id",
        f"command-{revision + 1}",
        *arguments,
    )
    assert result is not None
    return result


def lifecycle_test(base: Path) -> None:
    runtime = base / "lifecycle"
    state = expect_ok(
        "init",
        "--runtime-dir",
        str(runtime),
        "--change",
        "home-lists",
        "--workflow",
        "sk-team-feature",
        "--policy-revision",
        "test-policy",
        "--repository-json",
        '{"backend":{"worktree":"/tmp/backend","branch":"feature/home-lists","base_sha":"abc"}}',
    )
    assert state and state["revision"] == 1
    replayed = expect_ok(
        "init",
        "--runtime-dir",
        str(runtime),
        "--change",
        "home-lists",
        "--workflow",
        "sk-team-feature",
        "--policy-revision",
        "test-policy",
        "--repository-json",
        '{"backend":{"worktree":"/tmp/backend","branch":"feature/home-lists","base_sha":"abc"}}',
    )
    assert replayed and replayed["revision"] == 1
    assert len((runtime / "events.jsonl").read_text().splitlines()) == 1
    state = mutate(runtime, 1, "enter-stage", "--stage", "testing")
    state = mutate(
        runtime,
        2,
        "request-gate",
        "--stage",
        "testing",
        "--gate",
        "test-plan",
        "--reason",
        "approval-required",
    )
    state = mutate(
        runtime,
        3,
        "wait-user",
        "--gate-id",
        "testing/test-plan",
        "--reason-code",
        "await-test-plan",
    )
    assert state["control"]["kind"] == "waiting_user"
    state = mutate(
        runtime,
        4,
        "decide-gate",
        "--stage",
        "testing",
        "--gate",
        "test-plan",
        "--decision",
        "approved",
        "--decided-by",
        "user",
    )
    assert state["control"]["kind"] == "ready"
    state = mutate(
        runtime,
        5,
        "create-task",
        "--stage",
        "testing",
        "--task",
        "tdd-red",
        "--role",
        "sk-tester",
    )
    state = mutate(
        runtime,
        6,
        "start-attempt",
        "--stage",
        "testing",
        "--task",
        "tdd-red",
        "--attempt-id",
        "tdd-red-1",
        "--host-thread-id",
        "/root/home-lists-tdd-red",
    )
    state = mutate(
        runtime,
        7,
        "wait-agents",
        "--attempt-id",
        "tdd-red-1",
        "--join",
        "foreground",
        "--reason-code",
        "await-tdd-red",
    )
    assert state["control"]["kind"] == "waiting_agents"
    stale_snapshot = json.loads((runtime / "state.json").read_text())
    state = mutate(
        runtime,
        8,
        "finish-attempt",
        "--stage",
        "testing",
        "--task",
        "tdd-red",
        "--attempt-id",
        "tdd-red-1",
        "--outcome",
        "succeeded",
        "--verdict",
        "red-confirmed",
    )
    assert state["control"] == {"kind": "ready", "reason_code": "agent_results_recorded"}
    assert state["workflow"]["stages"]["testing"]["tasks"]["tdd-red"]["attempts"][0]["status"] == "succeeded"

    # Retrying the exact command after an uncertain response is idempotent even with
    # the original expected revision.
    code, output, errors = invoke(
        "finish-attempt",
        "--runtime-dir",
        str(runtime),
        "--expected-revision",
        "8",
        "--command-id",
        "command-9",
        "--stage",
        "testing",
        "--task",
        "tdd-red",
        "--attempt-id",
        "tdd-red-1",
        "--outcome",
        "succeeded",
        "--verdict",
        "red-confirmed",
    )
    assert code == 0, errors
    assert json.loads(output)["revision"] == 9
    assert len((runtime / "events.jsonl").read_text().splitlines()) == 9

    # A stale projection is detected and safely rebuilt from the journal.
    (runtime / "state.json").write_text(json.dumps(stale_snapshot) + "\n")
    status = expect_ok("status", "--runtime-dir", str(runtime))
    assert status and status["snapshot_status"] == "stale"
    code, _, errors = invoke("validate", "--runtime-dir", str(runtime))
    assert code == 1 and "stale" in errors
    repaired = expect_ok("repair", "--runtime-dir", str(runtime))
    assert repaired and repaired["revision"] == 9
    code, _, errors = invoke("validate", "--runtime-dir", str(runtime))
    assert code == 0, errors

    # A partial final event is never silently accepted; repair preserves its bytes.
    with (runtime / "events.jsonl").open("ab") as journal:
        journal.write(b'{"partial"')
    code, _, errors = invoke("validate", "--runtime-dir", str(runtime))
    assert code == 1 and "incomplete final JSONL record" in errors
    repaired = expect_ok("repair", "--runtime-dir", str(runtime))
    assert repaired and repaired["revision"] == 9
    tails = list(runtime.glob("events.corrupt-tail-*.bin"))
    assert len(tails) == 1 and tails[0].read_bytes() == b'{"partial"'


def migration_test(base: Path) -> None:
    runtime = base / "migration"
    runtime.mkdir()
    digest = "a" * 64
    legacy = {
        "schema_version": 1,
        "change": "webapp-home-lists",
        "phase": "testing",
        "next_action": "await_tdd_red_evidence",
        "execution_status": "foreground_join",
        "join": ["/root/home_lists_tdd_red"],
        "worktrees": {"backend": "/tmp/backend-worktree"},
        "branches": {"backend": "feature/home-lists"},
        "bases": {"backend": "abc123"},
        "approvals": {"test_plan": True},
        "artifacts": {"test_plan": {"path": "openspec/test-plan.md", "sha256": digest}},
        "agent_threads": {
            "spawned": ["/root/home_lists_tdd_red"],
            "running": ["/root/home_lists_tdd_red"],
            "completed": [],
        },
        "running_agents": {"tdd_red": "/root/home_lists_tdd_red"},
    }
    (runtime / "state.json").write_text(json.dumps(legacy) + "\n")
    state = expect_ok(
        "migrate-v1",
        "--runtime-dir",
        str(runtime),
        "--workflow",
        "sk-team-feature",
        "--policy-revision",
        "test-policy",
    )
    assert state and state["schema_version"] == 2
    assert state["control"]["kind"] == "waiting_agents"
    assert state["control"]["join"] == "foreground"
    attempts = state["workflow"]["stages"]["testing"]["tasks"]["tdd_red"]["attempts"]
    assert attempts[0]["agent"]["host_thread_id"] == "/root/home_lists_tdd_red"
    assert (runtime / "state.v1.json").exists()
    replayed = expect_ok(
        "migrate-v1",
        "--runtime-dir",
        str(runtime),
        "--workflow",
        "sk-team-feature",
        "--policy-revision",
        "test-policy",
    )
    assert replayed and replayed["revision"] == 1
    assert len((runtime / "events.jsonl").read_text().splitlines()) == 1
    code, _, errors = invoke("validate", "--runtime-dir", str(runtime))
    assert code == 0, errors


def transition_invariant_test(base: Path) -> None:
    runtime = base / "invariants"
    state = expect_ok(
        "init",
        "--runtime-dir",
        str(runtime),
        "--change",
        "parallel-wave",
        "--workflow",
        "sk-team-feature",
        "--policy-revision",
        "test-policy",
    )
    assert state
    state = mutate(runtime, 1, "enter-stage", "--stage", "review")
    state = mutate(runtime, 2, "create-task", "--stage", "review", "--task", "security", "--role", "reviewer")
    state = mutate(runtime, 3, "start-attempt", "--stage", "review", "--task", "security", "--attempt-id", "security-1", "--host-thread-id", "/root/security")
    state = mutate(runtime, 4, "create-task", "--stage", "review", "--task", "architecture", "--role", "reviewer")
    state = mutate(runtime, 5, "start-attempt", "--stage", "review", "--task", "architecture", "--attempt-id", "architecture-1", "--host-thread-id", "/root/architecture")

    code, _, errors = invoke(
        "wait-agents",
        "--runtime-dir",
        str(runtime),
        "--expected-revision",
        "6",
        "--command-id",
        "incomplete-join",
        "--attempt-id",
        "security-1",
        "--join",
        "foreground",
        "--reason-code",
        "await-review",
    )
    assert code == 1 and "every running attempt" in errors
    assert json.loads((runtime / "state.json").read_text())["revision"] == 6

    state = mutate(
        runtime,
        6,
        "wait-agents",
        "--attempt-id",
        "security-1",
        "--attempt-id",
        "architecture-1",
        "--join",
        "foreground",
        "--reason-code",
        "await-review",
    )
    code, _, errors = invoke(
        "block",
        "--runtime-dir",
        str(runtime),
        "--expected-revision",
        "7",
        "--command-id",
        "unsafe-block",
        "--blocker-id",
        "review-blocked",
        "--reason",
        "reviewers still running",
        "--required-action",
        "wait",
    )
    assert code == 1 and "only while control is ready" in errors
    state = mutate(runtime, 7, "finish-attempt", "--stage", "review", "--task", "security", "--attempt-id", "security-1", "--outcome", "succeeded")
    assert state["control"]["attempt_ids"] == ["architecture-1"]
    state = mutate(runtime, 8, "finish-attempt", "--stage", "review", "--task", "architecture", "--attempt-id", "architecture-1", "--outcome", "succeeded")
    assert state["control"]["kind"] == "ready"
    state = mutate(runtime, 9, "request-gate", "--stage", "review", "--gate", "review-approval-1", "--reason", "first review")
    state = mutate(runtime, 10, "decide-gate", "--stage", "review", "--gate", "review-approval-1", "--decision", "rejected", "--decided-by", "user")
    state = mutate(runtime, 11, "complete-stage", "--stage", "review", "--outcome", "failed")
    state = mutate(runtime, 12, "enter-stage", "--stage", "review")
    assert state["workflow"]["stages"]["review"]["entries"] == 2
    state = mutate(runtime, 13, "request-gate", "--stage", "review", "--gate", "review-approval-2", "--reason", "redo review")
    state = mutate(runtime, 14, "decide-gate", "--stage", "review", "--gate", "review-approval-2", "--decision", "approved", "--decided-by", "user")
    state = mutate(runtime, 15, "complete-stage", "--stage", "review", "--outcome", "succeeded")
    gates = state["workflow"]["stages"]["review"]["gates"]
    assert gates["review-approval-1"]["entry"] == 1
    assert gates["review-approval-2"]["entry"] == 2


def concurrent_cli_test(base: Path) -> None:
    runtime = base / "concurrent-cli"

    def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL_PATH), *arguments],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )

    init = run_cli(
        "init", "--runtime-dir", str(runtime), "--change", "cas-test",
        "--workflow", "sk-team-feature", "--policy-revision", "test-policy",
        "--run-id", "cas-test-run",
    )
    assert init.returncode == 0, init.stderr
    for revision, command, arguments in (
        (1, "enter-stage", ("--stage", "testing")),
        (2, "create-task", ("--stage", "testing", "--task", "one", "--role", "tester")),
        (3, "create-task", ("--stage", "testing", "--task", "two", "--role", "tester")),
    ):
        result = run_cli(
            command, "--runtime-dir", str(runtime), "--expected-revision", str(revision),
            "--command-id", f"cli-{revision + 1}", *arguments,
        )
        assert result.returncode == 0, result.stderr

    common = [
        sys.executable, str(TOOL_PATH), "start-attempt", "--runtime-dir", str(runtime),
        "--expected-revision", "4", "--stage", "testing",
    ]
    commands = []
    for task in ("one", "two"):
        command = common + [
            "--command-id", f"concurrent-{task}", "--task", task,
            "--attempt-id", f"{task}-1", "--host-thread-id", f"/root/{task}",
        ]
        commands.append(subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
    results = [process.communicate(timeout=10) + (process.returncode,) for process in commands]
    assert sorted(result[2] for result in results) == [0, 1], results
    assert any("revision conflict" in result[1] for result in results if result[2] == 1)
    validated = run_cli("validate", "--runtime-dir", str(runtime))
    assert validated.returncode == 0, validated.stderr
    state = json.loads((runtime / "state.json").read_text())
    assert state["revision"] == 5

    try:
        import jsonschema
    except ModuleNotFoundError:
        return
    schema_root = ROOT / "workflow/agents/shared/runtime-state"
    state_schema = json.loads((schema_root / "state.schema.json").read_text())
    event_schema = json.loads((schema_root / "event.schema.json").read_text())
    jsonschema.validators.validator_for(state_schema).check_schema(state_schema)
    jsonschema.validators.validator_for(event_schema).check_schema(event_schema)
    jsonschema.validate(state, state_schema)
    for event in (json.loads(line) for line in (runtime / "events.jsonl").read_text().splitlines()):
        jsonschema.validate(event, event_schema)


def contract_test() -> None:
    for name in ("state.schema.json", "event.schema.json"):
        path = ROOT / "workflow/agents/shared/runtime-state" / name
        schema = json.loads(path.read_text())
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert all("timeout" not in event for event in SK_STATE.EVENT_TYPES)
    policy = (ROOT / "workflow/agents/shared/runtime-state-policy.md").read_text()
    for phrase in (
        "events.jsonl",
        "state.json",
        "authoritative append-only semantic history",
        "expected-revision",
        "command-id",
        "transport-only",
        "Gates, checks, and attempts",
        "migrate-v1",
    ):
        assert phrase.lower() in policy.lower(), phrase

    # Exercise the real executable boundary as well as the imported command
    # handlers so lock release and process termination cannot regress unnoticed.
    completed = subprocess.run(
        [sys.executable, str(TOOL_PATH), "--help"],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert "semantic event journal" in completed.stdout.lower()


def main() -> None:
    contract_test()
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        lifecycle_test(base)
        migration_test(base)
        transition_invariant_test(base)
        concurrent_cli_test(base)
    print("OK: runtime state")


if __name__ == "__main__":
    main()
