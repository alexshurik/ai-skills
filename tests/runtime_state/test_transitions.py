from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from runtime_state.support import TOOL_PATH, RuntimeCase, array_at, json_object, object_at

DIGEST = "b" * 64


class PublicTransitionTests(RuntimeCase):
    def test_record_artifact_check_history_and_blocker_lifecycle(self) -> None:
        runtime, _ = self.init_runtime("records")
        self.mutate(runtime, 1, "enter-stage", "--stage", "acceptance")
        state = self.mutate(
            runtime,
            2,
            "record-check",
            "--stage",
            "acceptance",
            "--check",
            "suite",
            "--status",
            "passed",
            "--evidence",
            "all-pass",
        )
        self.assertEqual(
            object_at(state, "workflow", "stages", "acceptance", "checks", "suite")["status"],
            "passed",
        )
        state = self.mutate(
            runtime,
            3,
            "record-artifact",
            "--name",
            "verification",
            "--path",
            "openspec/VERIFICATION.md",
            "--sha256",
            DIGEST,
            "--kind",
            "verification",
            "--stage",
            "acceptance",
        )
        self.assertEqual(object_at(state, "artifacts", "verification")["sha256"], DIGEST)
        self.mutate(
            runtime,
            4,
            "block",
            "--blocker-id",
            "external",
            "--reason",
            "dependency",
            "--required-action",
            "reconcile",
        )
        state = self.mutate(runtime, 5, "resolve-blocker", "--blocker-id", "external")
        self.assertEqual(object_at(state, "control")["kind"], "ready")
        code, history, errors = self.invoke(
            "history", "--runtime-dir", str(runtime), "--type", "artifact.recorded"
        )
        self.assertEqual(code, 0, errors)
        self.assertEqual(json.loads(history)["type"], "artifact.recorded")

    def test_detached_join_late_result_and_successful_completion(self) -> None:
        runtime, _ = self.init_runtime("detached")
        self.mutate(runtime, 1, "enter-stage", "--stage", "acceptance")
        self.mutate(
            runtime, 2, "create-task", "--stage", "acceptance", "--task", "qa", "--role", "reviewer"
        )
        self.mutate(
            runtime,
            3,
            "start-attempt",
            "--stage",
            "acceptance",
            "--task",
            "qa",
            "--attempt-id",
            "qa-1",
            "--host-thread-id",
            "/root/qa",
        )
        state = self.mutate(
            runtime,
            4,
            "wait-agents",
            "--attempt-id",
            "qa-1",
            "--join",
            "detached",
            "--reason-code",
            "host-limit",
            "--detach-reason",
            "host-forced",
        )
        self.assertEqual(object_at(state, "control")["join"], "detached")
        self.mutate(
            runtime,
            5,
            "finish-attempt",
            "--stage",
            "acceptance",
            "--task",
            "qa",
            "--attempt-id",
            "qa-1",
            "--outcome",
            "succeeded",
        )
        state = self.mutate(
            runtime, 6, "record-late-result", "--attempt-id", "qa-1", "--verdict", "duplicate"
        )
        attempt = json_object(
            array_at(state, "workflow", "stages", "acceptance", "tasks", "qa", "attempts")[0]
        )
        self.assertEqual(len(array_at(attempt, "late_results")), 1)
        self.mutate(runtime, 7, "complete-stage", "--stage", "acceptance", "--outcome", "succeeded")
        state = self.mutate(runtime, 8, "complete", "--outcome", "completed")
        self.assertEqual(object_at(state, "control")["outcome"], "completed")

    def test_representative_invalid_transitions_do_not_append(self) -> None:
        runtime, _ = self.init_runtime("invalid")
        self.mutate(runtime, 1, "enter-stage", "--stage", "review")
        self.mutate(
            runtime, 2, "create-task", "--stage", "review", "--task", "one", "--role", "reviewer"
        )
        self.mutate(
            runtime, 3, "create-task", "--stage", "review", "--task", "two", "--role", "reviewer"
        )
        self.mutate(
            runtime,
            4,
            "start-attempt",
            "--stage",
            "review",
            "--task",
            "one",
            "--attempt-id",
            "one-1",
            "--host-thread-id",
            "/root/one",
        )
        self.mutate(
            runtime,
            5,
            "start-attempt",
            "--stage",
            "review",
            "--task",
            "two",
            "--attempt-id",
            "two-1",
            "--host-thread-id",
            "/root/two",
        )
        errors = self.invoke_error(
            runtime,
            6,
            "partial-join",
            "wait-agents",
            "--attempt-id",
            "one-1",
            "--join",
            "foreground",
            "--reason-code",
            "review",
        )
        self.assertIn("every running attempt", errors)
        errors = self.invoke_error(
            runtime,
            6,
            "early-finish",
            "finish-attempt",
            "--stage",
            "review",
            "--task",
            "one",
            "--attempt-id",
            "missing",
            "--outcome",
            "succeeded",
        )
        self.assertIn("not found uniquely", errors)
        self.assertEqual(len((runtime / "events.jsonl").read_text().splitlines()), 6)


class ConcurrentWriterTests(RuntimeCase):
    def test_compare_and_swap_allows_one_concurrent_writer(self) -> None:
        runtime = self.base / "concurrent"
        init = self.run_cli(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "concurrent",
            "--workflow",
            "sk-team-feature",
            "--policy-revision",
            "test-policy",
            "--run-id",
            "run",
        )
        self.assertEqual(init.returncode, 0, init.stderr)
        self.assert_cli_ok(runtime, 1, "enter-stage", "--stage", "testing")
        self.assert_cli_ok(
            runtime, 2, "create-task", "--stage", "testing", "--task", "one", "--role", "tester"
        )
        self.assert_cli_ok(
            runtime, 3, "create-task", "--stage", "testing", "--task", "two", "--role", "tester"
        )
        processes = [self.start_attempt_process(runtime, task) for task in ("one", "two")]
        results = [(*process.communicate(timeout=10), process.returncode) for process in processes]
        self.assertEqual(sorted(result[2] for result in results), [0, 1])
        self.assertTrue(
            any("revision conflict" in result[1] for result in results if result[2] == 1)
        )
        validated = self.run_cli("validate", "--runtime-dir", str(runtime))
        self.assertEqual(validated.returncode, 0, validated.stderr)

    def assert_cli_ok(self, runtime: Path, revision: int, command: str, *arguments: str) -> None:
        result = self.run_cli(
            command,
            "--runtime-dir",
            str(runtime),
            "--expected-revision",
            str(revision),
            "--command-id",
            f"cli-{revision + 1}",
            *arguments,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def start_attempt_process(self, runtime: Path, task: str) -> subprocess.Popen[str]:
        command = [
            sys.executable,
            str(TOOL_PATH),
            "start-attempt",
            "--runtime-dir",
            str(runtime),
            "--expected-revision",
            "4",
            "--command-id",
            f"concurrent-{task}",
            "--stage",
            "testing",
            "--task",
            task,
            "--attempt-id",
            f"{task}-1",
            "--host-thread-id",
            f"/root/{task}",
        ]
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
