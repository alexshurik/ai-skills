from __future__ import annotations

import json
from pathlib import Path

from runtime_state.support import RuntimeCase, object_at


class LifecycleTests(RuntimeCase):
    def test_repair_allows_init_after_partial_first_record(self) -> None:
        runtime = self.base / "partial-init"
        runtime.mkdir()
        (runtime / "events.jsonl").write_bytes(b'{"partial"')

        code, _, errors = self.invoke("repair", "--runtime-dir", str(runtime))
        self.assertEqual(code, 1)
        self.assertIn("valid non-empty event journal", errors)
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "partial-init",
            "--workflow",
            "sk-team-feature",
            "--policy-revision",
            "test-policy",
        )
        assert state is not None
        self.assertEqual(state["revision"], 1)
        self.assertEqual(len(list(runtime.glob("events.corrupt-tail-*.bin"))), 1)

    def test_gate_wait_and_idempotent_attempt_result(self) -> None:
        runtime, _ = self.init_runtime("lifecycle")
        self.approve_gate(runtime)
        self.complete_joined_attempt(runtime)

    def approve_gate(self, runtime: Path) -> None:
        self.mutate(runtime, 1, "enter-stage", "--stage", "testing")
        self.mutate(
            runtime,
            2,
            "request-gate",
            "--stage",
            "testing",
            "--gate",
            "plan",
            "--reason",
            "approval",
        )
        waited = self.mutate(
            runtime, 3, "wait-user", "--gate-id", "testing/plan", "--reason-code", "plan"
        )
        self.assertEqual(object_at(waited, "control")["kind"], "waiting_user")
        self.mutate(
            runtime,
            4,
            "decide-gate",
            "--stage",
            "testing",
            "--gate",
            "plan",
            "--decision",
            "approved",
            "--decided-by",
            "user",
        )

    def complete_joined_attempt(self, runtime: Path) -> None:
        self.mutate(
            runtime, 5, "create-task", "--stage", "testing", "--task", "suite", "--role", "tester"
        )
        self.mutate(
            runtime,
            6,
            "start-attempt",
            "--stage",
            "testing",
            "--task",
            "suite",
            "--attempt-id",
            "suite-1",
            "--host-thread-id",
            "/root/suite",
        )
        self.mutate(
            runtime,
            7,
            "wait-agents",
            "--attempt-id",
            "suite-1",
            "--join",
            "foreground",
            "--reason-code",
            "suite",
        )
        state = self.mutate(
            runtime,
            8,
            "finish-attempt",
            "--stage",
            "testing",
            "--task",
            "suite",
            "--attempt-id",
            "suite-1",
            "--outcome",
            "succeeded",
        )
        self.assertEqual(object_at(state, "control")["kind"], "ready")
        replayed = self.expect_ok(
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
            "suite",
            "--attempt-id",
            "suite-1",
            "--outcome",
            "succeeded",
        )
        assert replayed is not None
        self.assertEqual(replayed["revision"], 9)
        self.assertEqual(len((runtime / "events.jsonl").read_text().splitlines()), 9)

    def test_repair_rebuilds_stale_projection_and_preserves_partial_tail(self) -> None:
        runtime, stale = self.init_runtime("repair")
        self.mutate(runtime, 1, "enter-stage", "--stage", "testing")
        (runtime / "state.json").write_text(json.dumps(stale) + "\n")
        status = self.expect_ok("status", "--runtime-dir", str(runtime))
        assert status is not None
        self.assertEqual(status["snapshot_status"], "stale")
        code, _, errors = self.invoke("validate", "--runtime-dir", str(runtime))
        self.assertEqual(code, 1)
        self.assertIn("stale", errors)
        self.expect_ok("repair", "--runtime-dir", str(runtime))
        with (runtime / "events.jsonl").open("ab") as journal:
            journal.write(b'{"partial"')
        self.expect_ok("repair", "--runtime-dir", str(runtime))
        tails = list(runtime.glob("events.corrupt-tail-*.bin"))
        self.assertEqual(len(tails), 1)
        self.assertEqual(tails[0].read_bytes(), b'{"partial"')

    def test_repair_upgrades_an_older_v2_projection_from_the_journal(self) -> None:
        runtime, _ = self.init_runtime("older-v2")
        self.mutate(runtime, 1, "enter-stage", "--stage", "testing")
        self.mutate(
            runtime, 2, "create-task", "--stage", "testing", "--task", "suite", "--role", "tester"
        )
        snapshot = json.loads((runtime / "state.json").read_text())
        del snapshot["writer_lease"]
        del snapshot["workflow"]["stages"]["testing"]["tasks"]["suite"]["required"]
        (runtime / "state.json").write_text(json.dumps(snapshot) + "\n")
        status = self.expect_ok("status", "--runtime-dir", str(runtime))
        assert status is not None
        self.assertEqual(status["snapshot_status"], "diverged")
        repaired = self.expect_ok("repair", "--runtime-dir", str(runtime))
        assert repaired is not None
        self.assertIsNone(repaired["writer_lease"])
        task = object_at(repaired, "workflow", "stages", "testing", "tasks", "suite")
        self.assertTrue(task["required"])

    def test_malformed_projection_with_valid_history_is_repairable(self) -> None:
        runtime, _ = self.init_runtime("malformed-with-history")
        malformed = b'{"schema_version": 2, "broken"'
        state_path = runtime / "state.json"
        state_path.write_bytes(malformed)

        report = self.expect_ok("status", "--runtime-dir", str(runtime))
        assert report is not None
        self.assertEqual(report["snapshot_status"], "diverged")
        self.assertEqual(report["recommended_action"], "repair")
        self.assertEqual(state_path.read_bytes(), malformed)

        code, _, errors = self.invoke("validate", "--runtime-dir", str(runtime))
        self.assertEqual(code, 1)
        self.assertIn("recommended action: repair", errors)
        self.assertEqual(state_path.read_bytes(), malformed)

        repaired = self.expect_ok("repair", "--runtime-dir", str(runtime))
        assert repaired is not None
        self.assertEqual(repaired["revision"], 1)

    def test_malformed_projection_without_history_fails_closed(self) -> None:
        runtime = self.base / "malformed-without-history"
        runtime.mkdir()
        malformed = b'{"schema_version": 2, "broken"'
        state_path = runtime / "state.json"
        state_path.write_bytes(malformed)

        report = self.expect_ok("status", "--runtime-dir", str(runtime))
        assert report is not None
        self.assertEqual(report["snapshot_status"], "diverged")
        self.assertEqual(report["recommended_action"], "recover-journal-or-reinitialize")
        self.assertEqual(state_path.read_bytes(), malformed)

        code, _, errors = self.invoke("repair", "--runtime-dir", str(runtime))
        self.assertEqual(code, 1)
        self.assertIn("valid non-empty event journal", errors)
        self.assertEqual(state_path.read_bytes(), malformed)

    def test_future_projection_fails_closed_and_is_preserved(self) -> None:
        runtime, _ = self.init_runtime("future-schema")
        future_projection = (
            b'{\n  "schema_version": 3,\n  "future_contract": {"preserve": true}\n}\n'
        )
        state_path = runtime / "state.json"
        state_path.write_bytes(future_projection)

        report = self.expect_ok("status", "--runtime-dir", str(runtime))
        assert report is not None
        self.assertEqual(report["snapshot_status"], "unsupported_schema")
        self.assertEqual(report["recommended_action"], "require-compatible-helper")
        self.assertEqual(state_path.read_bytes(), future_projection)

        code, _, errors = self.invoke("validate", "--runtime-dir", str(runtime))
        self.assertEqual(code, 1)
        self.assertIn("require-compatible-helper", errors)
        self.assertEqual(state_path.read_bytes(), future_projection)

        code, _, errors = self.invoke("repair", "--runtime-dir", str(runtime))
        self.assertEqual(code, 1)
        self.assertIn("require-compatible-helper", errors)
        self.assertEqual(state_path.read_bytes(), future_projection)

    def test_future_event_schema_requires_compatible_helper_and_preserves_runtime(self) -> None:
        runtime, _ = self.init_runtime("future-event-schema")
        journal_path = runtime / "events.jsonl"
        state_path = runtime / "state.json"
        event = json.loads(journal_path.read_text())
        event["event_schema_version"] = 2
        future_journal = (json.dumps(event, sort_keys=True) + "\n").encode()
        journal_path.write_bytes(future_journal)
        projection = state_path.read_bytes()

        report = self.expect_ok("status", "--runtime-dir", str(runtime))
        assert report is not None
        self.assertEqual(report["snapshot_status"], "unsupported_schema")
        self.assertEqual(report["recommended_action"], "require-compatible-helper")

        for command in ("validate", "history", "repair"):
            code, _, errors = self.invoke(command, "--runtime-dir", str(runtime))
            self.assertEqual(code, 1, command)
            self.assertIn("require-compatible-helper", errors, command)
            self.assertEqual(journal_path.read_bytes(), future_journal, command)
            self.assertEqual(state_path.read_bytes(), projection, command)

    def test_status_reports_the_complete_recovery_action_matrix(self) -> None:
        runtime, initial = self.init_runtime("status-matrix")
        self.assert_status_action(runtime, "valid", "validate")
        self.mutate(runtime, 1, "enter-stage", "--stage", "testing")
        (runtime / "state.json").write_text(json.dumps(initial) + "\n")
        self.assert_status_action(runtime, "stale", "repair")
        (runtime / "state.json").write_text('{"schema_version": 2}\n')
        self.assert_status_action(runtime, "diverged", "repair")
        (runtime / "state.json").unlink()
        self.assert_status_action(runtime, "missing", "repair")

        orphaned, orphaned_state = self.init_runtime("orphaned")
        (orphaned / "events.jsonl").unlink()
        self.assert_status_action(orphaned, "orphaned", "recover-journal-or-reinitialize")
        missing = self.base / "missing"
        self.assert_status_action(missing, "missing", "recover-journal-or-reinitialize")
        diverged = self.base / "diverged-without-history"
        diverged.mkdir()
        (diverged / "state.json").write_text('{"schema_version": 2}\n')
        self.assert_status_action(diverged, "diverged", "recover-journal-or-reinitialize")
        legacy = self.base / "legacy"
        legacy.mkdir()
        (legacy / "state.json").write_text('{"schema_version": 1}\n')
        self.assert_status_action(legacy, "legacy_v1", "migrate-v1")
        (runtime / "state.json").write_text('{"schema_version": 1}\n')
        self.assert_status_action(runtime, "legacy_v1", "repair")
        self.assertEqual(orphaned_state["revision"], 1)

    def assert_status_action(self, runtime: Path, status: str, action: str) -> None:
        report = self.expect_ok("status", "--runtime-dir", str(runtime))
        assert report is not None
        self.assertEqual(report["snapshot_status"], status)
        self.assertEqual(report["recommended_action"], action)

    def test_required_work_blocks_success_while_optional_work_does_not(self) -> None:
        runtime, _ = self.init_runtime("closure")
        self.prepare_required_and_optional_tasks(runtime)
        self.assert_check_closure(runtime)

    def prepare_required_and_optional_tasks(self, runtime: Path) -> None:
        self.mutate(runtime, 1, "enter-stage", "--stage", "testing")
        self.mutate(
            runtime,
            2,
            "create-task",
            "--stage",
            "testing",
            "--task",
            "required",
            "--role",
            "tester",
        )
        errors = self.invoke_error(
            runtime,
            3,
            "pending-required",
            "complete-stage",
            "--stage",
            "testing",
            "--outcome",
            "succeeded",
        )
        self.assertIn("unsuccessful tasks", errors)
        self.mutate(
            runtime,
            3,
            "create-task",
            "--stage",
            "testing",
            "--task",
            "optional",
            "--role",
            "tester",
            "--optional",
        )
        self.finish_required_task(runtime)

    def assert_check_closure(self, runtime: Path) -> None:
        self.mutate(
            runtime,
            6,
            "record-check",
            "--stage",
            "testing",
            "--check",
            "mypy",
            "--status",
            "failed",
        )
        errors = self.invoke_error(
            runtime,
            7,
            "failed-required-check",
            "complete-stage",
            "--stage",
            "testing",
            "--outcome",
            "succeeded",
        )
        self.assertIn("unsuccessful checks", errors)
        self.mutate(
            runtime,
            7,
            "record-check",
            "--stage",
            "testing",
            "--check",
            "mypy",
            "--status",
            "passed",
        )
        self.mutate(
            runtime,
            8,
            "record-check",
            "--stage",
            "testing",
            "--check",
            "advisory",
            "--status",
            "failed",
            "--optional",
        )
        self.mutate(runtime, 9, "complete-stage", "--stage", "testing", "--outcome", "succeeded")
        completed = self.mutate(runtime, 10, "complete", "--outcome", "completed")
        self.assertEqual(completed["control"], {"kind": "complete", "outcome": "completed"})

    def finish_required_task(self, runtime: Path) -> None:
        self.mutate(
            runtime,
            4,
            "start-attempt",
            "--stage",
            "testing",
            "--task",
            "required",
            "--attempt-id",
            "required-1",
            "--host-thread-id",
            "/root/required",
        )
        self.mutate(
            runtime,
            5,
            "finish-attempt",
            "--stage",
            "testing",
            "--task",
            "required",
            "--attempt-id",
            "required-1",
            "--outcome",
            "succeeded",
        )

    def test_failed_final_stage_cannot_close_as_completed(self) -> None:
        runtime, _ = self.init_runtime("failed-workflow")
        self.mutate(runtime, 1, "enter-stage", "--stage", "review")
        self.mutate(runtime, 2, "complete-stage", "--stage", "review", "--outcome", "failed")
        errors = self.invoke_error(
            runtime, 3, "false-success", "complete", "--outcome", "completed"
        )
        self.assertIn("successful current stage", errors)
        aborted = self.mutate(runtime, 3, "complete", "--outcome", "aborted")
        self.assertEqual(object_at(aborted, "control")["outcome"], "aborted")

    def test_historical_and_prior_entry_gates_cannot_be_waited(self) -> None:
        runtime, _ = self.init_runtime("historical-gates")
        self.mutate(runtime, 1, "enter-stage", "--stage", "planning")
        self.mutate(
            runtime, 2, "request-gate", "--stage", "planning", "--gate", "old", "--reason", "user"
        )
        self.mutate(runtime, 3, "complete-stage", "--stage", "planning", "--outcome", "failed")
        self.mutate(runtime, 4, "enter-stage", "--stage", "testing")
        errors = self.invoke_error(
            runtime,
            5,
            "historical",
            "wait-user",
            "--gate-id",
            "planning/old",
            "--reason-code",
            "bad",
        )
        self.assertIn("current stage", errors)
        self.mutate(runtime, 5, "complete-stage", "--stage", "testing", "--outcome", "failed")
        self.mutate(runtime, 6, "enter-stage", "--stage", "planning")
        errors = self.invoke_error(
            runtime,
            7,
            "prior-entry",
            "wait-user",
            "--gate-id",
            "planning/old",
            "--reason-code",
            "bad",
        )
        self.assertIn("current entry", errors)
