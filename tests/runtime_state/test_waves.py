from __future__ import annotations

import hashlib
import json
from pathlib import Path

from runtime_state.support import JsonObject, RuntimeCase, object_at

INPUT_A = "a" * 64
INPUT_B = "b" * 64
RESULT = "c" * 64


class WaveTests(RuntimeCase):
    def init_route(self, name: str, route: str, *budgets: str) -> tuple[Path, JsonObject]:
        runtime = self.base / name
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            name,
            "--workflow",
            "sk-team",
            "--policy-revision",
            "test-policy",
            "--route",
            route,
            *budgets,
        )
        assert state is not None
        return runtime, state

    def member(self, member_id: str, fingerprint: str = INPUT_A) -> str:
        return json.dumps(
            {
                "id": member_id,
                "role": "reviewer",
                "host_thread_id": f"/root/{member_id}",
                "input_fingerprint": fingerprint,
            }
        )

    def create_batch(
        self,
        runtime: Path,
        revision: int,
        stage: str,
        task: str,
        purpose: str,
        *members: str,
    ) -> JsonObject:
        arguments = [
            "--stage",
            stage,
            "--task",
            task,
            "--role",
            "batch",
            "--purpose",
            purpose,
        ]
        for member in members:
            arguments.extend(("--member-json", member))
        state = self.mutate(runtime, revision, "create-task", *arguments)
        assert state is not None
        return state

    def test_foreground_wait_is_transport_only_after_partial_completion(self) -> None:
        runtime, _ = self.init_route("transport-only", "quick")
        self.mutate(runtime, 1, "enter-stage", "--stage", "review")
        self.create_batch(
            runtime,
            2,
            "review",
            "review-1",
            "review",
            self.member("correctness"),
            self.member("quality"),
        )
        first = self.mutate(
            runtime,
            3,
            "wait-agents",
            "--attempt-id",
            "correctness",
            "--attempt-id",
            "quality",
            "--join",
            "foreground",
            "--reason-code",
            "review",
        )
        self.assertEqual(first["revision"], 3)
        self.assertEqual(len((runtime / "events.jsonl").read_text().splitlines()), 3)

        self.mutate(
            runtime,
            3,
            "finish-attempt",
            "--stage",
            "review",
            "--task",
            "review-1",
            "--attempt-id",
            "correctness",
            "--outcome",
            "succeeded",
            "--input-fingerprint",
            INPUT_A,
            "--sha256",
            RESULT,
        )
        second = self.mutate(
            runtime,
            4,
            "wait-agents",
            "--attempt-id",
            "quality",
            "--join",
            "foreground",
            "--reason-code",
            "review",
        )
        self.assertEqual(second["revision"], 4)
        events = [json.loads(line) for line in (runtime / "events.jsonl").read_text().splitlines()]
        self.assertNotIn("workflow.waiting_for_agents", [event["type"] for event in events])

    def test_stale_result_is_rejected(self) -> None:
        runtime, _ = self.init_route("fingerprints", "quick")
        self.mutate(runtime, 1, "enter-stage", "--stage", "implementation")
        self.create_batch(
            runtime,
            2,
            "implementation",
            "implementation-1",
            "implementation",
            self.member("developer"),
        )
        errors = self.invoke_error(
            runtime,
            3,
            "stale-result",
            "finish-attempt",
            "--stage",
            "implementation",
            "--task",
            "implementation-1",
            "--attempt-id",
            "developer",
            "--outcome",
            "succeeded",
            "--input-fingerprint",
            INPUT_B,
            "--sha256",
            RESULT,
        )
        self.assertIn("does not match", errors)

    def test_existing_artifact_fingerprint_is_verified(self) -> None:
        runtime, _ = self.init_route("artifact-fingerprint", "quick")
        self.mutate(runtime, 1, "enter-stage", "--stage", "implementation")
        self.create_batch(
            runtime,
            2,
            "implementation",
            "implementation-1",
            "implementation",
            self.member("developer"),
        )
        artifact = self.base / "implementation.md"
        artifact.write_text("verified result\n")
        errors = self.invoke_error(
            runtime,
            3,
            "bad-artifact",
            "finish-attempt",
            "--stage",
            "implementation",
            "--task",
            "implementation-1",
            "--attempt-id",
            "developer",
            "--outcome",
            "succeeded",
            "--input-fingerprint",
            INPUT_A,
            "--artifact",
            str(artifact),
            "--sha256",
            RESULT,
        )
        self.assertIn("artifact fingerprint mismatch", errors)
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        state = self.mutate(
            runtime,
            3,
            "finish-attempt",
            "--stage",
            "implementation",
            "--task",
            "implementation-1",
            "--attempt-id",
            "developer",
            "--outcome",
            "succeeded",
            "--input-fingerprint",
            INPUT_A,
            "--artifact",
            str(artifact),
            "--sha256",
            digest,
        )
        self.assertEqual(
            object_at(
                state,
                "workflow",
                "stages",
                "implementation",
                "tasks",
                "implementation-1",
            )["status"],
            "succeeded",
        )

    def test_configured_review_and_remediation_budgets_are_enforced(self) -> None:
        runtime, _ = self.init_route(
            "budgets",
            "quick",
            "--attempt-budget",
            "4",
            "--review-round-budget",
            "1",
            "--remediation-budget",
            "1",
        )
        self.mutate(runtime, 1, "enter-stage", "--stage", "review")
        self.create_batch(runtime, 2, "review", "review-1", "review", self.member("reviewer-1"))
        errors = self.invoke_error(
            runtime,
            3,
            "review-over-budget",
            "create-task",
            "--stage",
            "review",
            "--task",
            "review-2",
            "--role",
            "batch",
            "--purpose",
            "review",
            "--member-json",
            self.member("reviewer-2"),
        )
        self.assertIn("review_rounds budget exhausted", errors)
        self.create_batch(
            runtime,
            3,
            "review",
            "remediation-1",
            "remediation",
            self.member("developer-1"),
        )
        errors = self.invoke_error(
            runtime,
            4,
            "remediation-over-budget",
            "create-task",
            "--stage",
            "review",
            "--task",
            "remediation-2",
            "--role",
            "batch",
            "--purpose",
            "remediation",
            "--member-json",
            self.member("developer-2"),
        )
        self.assertIn("remediations budget exhausted", errors)

    def test_configured_attempt_budget_is_enforced(self) -> None:
        limited, _ = self.init_route("attempt-budget", "quick", "--attempt-budget", "1")
        self.mutate(limited, 1, "enter-stage", "--stage", "implementation")
        self.create_batch(limited, 2, "implementation", "one", "implementation", self.member("one"))
        errors = self.invoke_error(
            limited,
            3,
            "attempt-over-budget",
            "create-task",
            "--stage",
            "implementation",
            "--task",
            "two",
            "--role",
            "batch",
            "--purpose",
            "implementation",
            "--member-json",
            self.member("two"),
        )
        self.assertIn("attempt budget exhausted", errors)

    def test_active_full_review_lease_can_be_recovered_after_host_crash(self) -> None:
        runtime, _ = self.init_route("lease-recovery", "full")
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
            "grant-review-lease",
            "--lease-id",
            "lease-1",
            "--stage",
            "review",
            "--holder-attempt-id",
            "orchestrator-1",
            "--holder-actor-id",
            "review-root",
        )
        recovered = self.mutate(
            runtime,
            5,
            "release-review-lease",
            "--lease-id",
            "lease-1",
            "--reason",
            "holder host crashed before release",
        )
        self.assertIsNone(recovered["writer_lease"])
        self.mutate(
            runtime,
            6,
            "finish-attempt",
            "--stage",
            "review",
            "--task",
            "orchestrator",
            "--attempt-id",
            "orchestrator-1",
            "--outcome",
            "cancelled",
        )

    def test_micro_route_completes_without_tasks_attempts_join_or_lease(self) -> None:
        runtime, state = self.init_route("minimal-micro", "micro")
        self.mutate(runtime, 1, "enter-stage", "--stage", "implementation")
        state = self.mutate(
            runtime,
            2,
            "complete-stage",
            "--stage",
            "implementation",
            "--outcome",
            "succeeded",
        )
        self.assertEqual(object_at(state, "workflow", "stages", "implementation", "tasks"), {})
        self.mutate(
            runtime,
            3,
            "record-terminal",
            "--kind",
            "local",
            "--outcome",
            "succeeded",
            "--evidence",
            "root-owned verification",
        )
        completed = self.mutate(runtime, 4, "complete", "--outcome", "completed")
        self.assertIsNone(completed["writer_lease"])
        events = [
            json.loads(line)["type"] for line in (runtime / "events.jsonl").read_text().splitlines()
        ]
        self.assertFalse(
            any(
                event.startswith(("agent.", "review.lease"))
                or event == "workflow.waiting_for_agents"
                for event in events
            )
        )
