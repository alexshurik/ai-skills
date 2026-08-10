from __future__ import annotations

from pathlib import Path

from runtime_state.support import JsonObject, RuntimeCase, array_at, json_object, object_at


class ReviewLeaseTests(RuntimeCase):
    def prepare_review(self, name: str) -> tuple[Path, int]:
        runtime, _ = self.init_runtime(name)
        self.mutate(runtime, 1, "enter-stage", "--stage", "review")
        self.mutate(
            runtime,
            2,
            "create-task",
            "--stage",
            "review",
            "--task",
            "orchestrator",
            "--role",
            "review-orchestrator",
        )
        self.mutate(
            runtime,
            3,
            "start-attempt",
            "--stage",
            "review",
            "--task",
            "orchestrator",
            "--attempt-id",
            "orchestrator-1",
            "--host-thread-id",
            "/root/review",
        )
        self.mutate(
            runtime,
            4,
            "wait-agents",
            "--attempt-id",
            "orchestrator-1",
            "--join",
            "foreground",
            "--reason-code",
            "review",
        )
        return runtime, 5

    def grant(self, runtime: Path, revision: int, lease_id: str = "lease-1") -> JsonObject:
        return self.mutate(
            runtime,
            revision,
            "grant-review-lease",
            "--lease-id",
            lease_id,
            "--stage",
            "review",
            "--holder-attempt-id",
            "orchestrator-1",
            "--holder-actor-id",
            "review-root",
        )

    def leased_mutate(
        self, runtime: Path, revision: int, command: str, *arguments: str
    ) -> JsonObject:
        result = self.expect_ok(
            command,
            "--runtime-dir",
            str(runtime),
            "--expected-revision",
            str(revision),
            "--command-id",
            f"lease-command-{revision + 1}",
            "--actor-kind",
            "review-orchestrator",
            "--actor-id",
            "review-root",
            *arguments,
        )
        assert result is not None
        return result

    def test_lease_bounds_nested_attempt_writes(self) -> None:
        runtime, revision = self.prepare_review("lease")
        state = self.grant(runtime, revision)
        self.assertEqual(object_at(state, "writer_lease")["holder_attempt_id"], "orchestrator-1")
        errors = self.invoke_error(
            runtime,
            6,
            "root-write",
            "create-task",
            "--stage",
            "review",
            "--task",
            "bad",
            "--role",
            "reviewer",
        )
        self.assertIn("lease", errors)
        self.create_and_finish_leaf(runtime)
        state = self.leased_mutate(
            runtime, 9, "record-late-result", "--attempt-id", "security-1", "--verdict", "late"
        )
        self.assertEqual(len(array_at(self.leaf_attempt(state), "late_results")), 1)
        state = self.leased_mutate(runtime, 10, "release-review-lease", "--lease-id", "lease-1")
        self.assertIsNone(state["writer_lease"])
        finished = self.mutate(
            runtime,
            11,
            "finish-attempt",
            "--stage",
            "review",
            "--task",
            "orchestrator",
            "--attempt-id",
            "orchestrator-1",
            "--outcome",
            "succeeded",
        )
        self.assertEqual(object_at(finished, "control")["kind"], "ready")

    def create_and_finish_leaf(self, runtime: Path) -> None:
        self.leased_mutate(
            runtime,
            6,
            "create-task",
            "--stage",
            "review",
            "--task",
            "security",
            "--role",
            "reviewer",
        )
        state = self.leased_mutate(
            runtime,
            7,
            "start-attempt",
            "--stage",
            "review",
            "--task",
            "security",
            "--attempt-id",
            "security-1",
            "--host-thread-id",
            "/root/review/security",
        )
        self.assertEqual(
            object_at(state, "control")["attempt_ids"], ["orchestrator-1", "security-1"]
        )
        state = self.leased_mutate(
            runtime,
            8,
            "finish-attempt",
            "--stage",
            "review",
            "--task",
            "security",
            "--attempt-id",
            "security-1",
            "--outcome",
            "succeeded",
        )
        self.assertEqual(object_at(state, "control")["attempt_ids"], ["orchestrator-1"])

    def leaf_attempt(self, state: JsonObject) -> JsonObject:
        attempts = array_at(state, "workflow", "stages", "review", "tasks", "security", "attempts")
        return json_object(attempts[0])

    def test_wrong_holder_and_forbidden_event_are_rejected(self) -> None:
        runtime, revision = self.prepare_review("lease-errors")
        self.grant(runtime, revision)
        errors = self.invoke_error(
            runtime,
            6,
            "wrong-holder",
            "create-task",
            "--actor-kind",
            "review-orchestrator",
            "--actor-id",
            "another-reviewer",
            "--stage",
            "review",
            "--task",
            "security",
            "--role",
            "reviewer",
        )
        self.assertIn("does not hold", errors)
        errors = self.invoke_error(
            runtime,
            6,
            "forbidden-check",
            "record-check",
            "--actor-kind",
            "review-orchestrator",
            "--actor-id",
            "review-root",
            "--stage",
            "review",
            "--check",
            "lint",
            "--status",
            "passed",
        )
        self.assertIn("only nested attempt", errors)

    def test_lease_rejects_preexisting_sibling_tasks_and_attempts(self) -> None:
        runtime, revision = self.prepare_review("lease-preexisting-sibling")
        self.mutate(
            runtime,
            revision,
            "create-task",
            "--stage",
            "review",
            "--task",
            "pending-sibling",
            "--role",
            "reviewer",
        )
        self.mutate(
            runtime,
            revision + 1,
            "create-task",
            "--stage",
            "review",
            "--task",
            "running-sibling",
            "--role",
            "reviewer",
        )
        self.mutate(
            runtime,
            revision + 2,
            "start-attempt",
            "--stage",
            "review",
            "--task",
            "running-sibling",
            "--attempt-id",
            "sibling-1",
            "--host-thread-id",
            "/root/sibling",
        )
        self.grant(runtime, revision + 3)

        start_errors = self.leased_error(
            runtime,
            revision + 4,
            "start-attempt",
            "--stage",
            "review",
            "--task",
            "pending-sibling",
            "--attempt-id",
            "stolen-1",
            "--host-thread-id",
            "/root/review/stolen",
        )
        self.assertIn("lease lineage", start_errors)

        finish_errors = self.leased_error(
            runtime,
            revision + 4,
            "finish-attempt",
            "--stage",
            "review",
            "--task",
            "running-sibling",
            "--attempt-id",
            "sibling-1",
            "--outcome",
            "cancelled",
        )
        self.assertIn("lease lineage", finish_errors)

    def leased_error(self, runtime: Path, revision: int, command: str, *arguments: str) -> str:
        return self.invoke_error(
            runtime,
            revision,
            f"lease-error-{command}-{revision}",
            command,
            "--actor-kind",
            "review-orchestrator",
            "--actor-id",
            "review-root",
            *arguments,
        )

    def test_detached_resume_releases_and_regrants_lease(self) -> None:
        runtime, revision = self.prepare_review("lease-detached")
        self.grant(runtime, revision, "lease-before-detach")
        self.leased_mutate(runtime, 6, "release-review-lease", "--lease-id", "lease-before-detach")
        detached = self.mutate(
            runtime,
            7,
            "wait-agents",
            "--attempt-id",
            "orchestrator-1",
            "--join",
            "detached",
            "--reason-code",
            "host-limit",
            "--detach-reason",
            "host-forced",
        )
        self.assertEqual(object_at(detached, "control")["join"], "detached")
        self.expect_ok("validate", "--runtime-dir", str(runtime))
        self.mutate(
            runtime,
            8,
            "wait-agents",
            "--attempt-id",
            "orchestrator-1",
            "--join",
            "foreground",
            "--reason-code",
            "resume-review",
        )
        state = self.grant(runtime, 9, "lease-after-resume")
        self.assertEqual(object_at(state, "writer_lease")["id"], "lease-after-resume")
        released = self.leased_mutate(
            runtime, 10, "release-review-lease", "--lease-id", "lease-after-resume"
        )
        self.assertIsNone(released["writer_lease"])

    def test_detach_regrant_preserves_nested_attempt_lineage(self) -> None:
        runtime, revision = self.prepare_review("lease-lineage-resume")
        state = self.start_nested_attempt(runtime, revision)
        task = object_at(state, "workflow", "stages", "review", "tasks", "correctness")
        attempt = json_object(array_at(task, "attempts")[0])
        self.assertEqual(task["lease_holder_attempt_id"], "orchestrator-1")
        self.assertEqual(attempt["lease_holder_attempt_id"], "orchestrator-1")
        self.detach_and_regrant(runtime, revision)
        finished = self.leased_mutate(
            runtime,
            revision + 7,
            "finish-attempt",
            "--stage",
            "review",
            "--task",
            "correctness",
            "--attempt-id",
            "correctness-1",
            "--outcome",
            "succeeded",
        )
        self.assertEqual(object_at(finished, "control")["attempt_ids"], ["orchestrator-1"])

    def start_nested_attempt(self, runtime: Path, revision: int) -> JsonObject:
        self.grant(runtime, revision, "lease-before-detach")
        self.leased_mutate(
            runtime,
            revision + 1,
            "create-task",
            "--stage",
            "review",
            "--task",
            "correctness",
            "--role",
            "reviewer",
        )
        return self.leased_mutate(
            runtime,
            revision + 2,
            "start-attempt",
            "--stage",
            "review",
            "--task",
            "correctness",
            "--attempt-id",
            "correctness-1",
            "--host-thread-id",
            "/root/review/correctness",
        )

    def detach_and_regrant(self, runtime: Path, revision: int) -> None:
        self.leased_mutate(
            runtime,
            revision + 3,
            "release-review-lease",
            "--lease-id",
            "lease-before-detach",
        )
        join_arguments = (
            "--attempt-id",
            "orchestrator-1",
            "--attempt-id",
            "correctness-1",
        )
        self.mutate(
            runtime,
            revision + 4,
            "wait-agents",
            *join_arguments,
            "--join",
            "detached",
            "--reason-code",
            "host-limit",
            "--detach-reason",
            "host-forced",
        )
        self.mutate(
            runtime,
            revision + 5,
            "wait-agents",
            *join_arguments,
            "--join",
            "foreground",
            "--reason-code",
            "resume-review",
        )
        self.grant(runtime, revision + 6, "lease-after-resume")
