from __future__ import annotations

import json
from pathlib import Path

from runtime_state.support import JsonObject, RuntimeCase, array_at, json_object, object_at


class MigrationTests(RuntimeCase):
    def test_repair_allows_migration_after_partial_first_record(self) -> None:
        runtime = self.base / "partial-migration"
        runtime.mkdir()
        legacy = {"schema_version": 1, "change": "partial-migration", "phase": "setup"}
        (runtime / "state.json").write_text(json.dumps(legacy) + "\n")
        (runtime / "events.jsonl").write_bytes(b'{"partial"')

        code, _, errors = self.invoke("repair", "--runtime-dir", str(runtime))
        self.assertEqual(code, 1)
        self.assertIn("valid non-empty event journal", errors)
        state = self.expect_ok(
            "migrate-v1",
            "--runtime-dir",
            str(runtime),
            "--workflow",
            "sk-team-feature",
            "--policy-revision",
            "test-policy",
        )
        assert state is not None
        self.assertEqual(state["revision"], 1)
        self.assertEqual(json.loads((runtime / "state.v1.json").read_text()), legacy)

    def migrate(self, name: str, legacy: dict[str, object], *extra: str) -> tuple[Path, JsonObject]:
        runtime = self.base / name
        runtime.mkdir()
        (runtime / "state.json").write_text(json.dumps(legacy) + "\n")
        state = self.expect_ok(
            "migrate-v1",
            "--runtime-dir",
            str(runtime),
            "--workflow",
            "sk-team-feature",
            "--policy-revision",
            "test-policy",
            *extra,
        )
        assert state is not None
        code, _, errors = self.invoke("validate", "--runtime-dir", str(runtime))
        self.assertEqual(code, 0, errors)
        self.assertTrue((runtime / "state.v1.json").exists())
        return runtime, state

    def test_running_agents_map_preserves_active_attempt(self) -> None:
        _, state = self.migrate(
            "running-agents",
            {
                "schema_version": 1,
                "change": "running-agents",
                "phase": "review",
                "running_agents": {"security": "/root/security"},
            },
        )
        self.assertEqual(object_at(state, "control")["join"], "detached")
        task = object_at(state, "workflow", "stages", "review", "tasks", "security")
        self.assertEqual(json_object(array_at(task, "attempts")[0])["status"], "running")

    def test_agent_threads_and_top_level_sets_preserve_statuses(self) -> None:
        _, state = self.migrate(
            "thread-sets",
            {
                "schema_version": 1,
                "phase": "testing",
                "agent_threads": {
                    "spawned": ["/root/active", "/root/done"],
                    "running": ["/root/active"],
                    "completed": ["/root/done"],
                },
                "execution_status": "foreground_join",
                "join": ["/root/active"],
            },
        )
        self.assertEqual(object_at(state, "control")["join"], "foreground")
        tasks = object_at(state, "workflow", "stages", "testing", "tasks")
        statuses = {
            json_object(attempt)["status"]
            for task in tasks.values()
            for attempt in array_at(task, "attempts")
        }
        self.assertEqual(statuses, {"running", "succeeded"})

    def test_top_level_agent_sets_preserve_active_and_completed(self) -> None:
        _, state = self.migrate(
            "top-level-sets",
            {
                "schema_version": 1,
                "phase": "testing",
                "spawned": ["/root/active", "/root/done"],
                "running": ["/root/active"],
                "completed": ["/root/done"],
                "execution_status": "background_detached",
            },
        )
        tasks = object_at(state, "workflow", "stages", "testing", "tasks")
        statuses = {json_object(array_at(task, "attempts")[0])["status"] for task in tasks.values()}
        self.assertEqual(statuses, {"running", "succeeded"})
        self.assertEqual(object_at(state, "control")["join"], "detached")

    def test_join_only_wait_is_preserved(self) -> None:
        _, state = self.migrate(
            "join-only",
            {
                "schema_version": 1,
                "phase": "review",
                "execution_status": "background_detached",
                "join": ["/root/reviewer"],
            },
        )
        self.assertEqual(object_at(state, "control")["attempt_ids"], ["legacy-attempt-1"])
        self.assertEqual(object_at(state, "control")["join"], "detached")

    def test_background_checkpoint_and_wait_budget_require_real_stage(self) -> None:
        _, state = self.migrate(
            "checkpoint",
            {
                "schema_version": 1,
                "phase": "background_work_active",
                "background_checkpoint": {"stage": "review", "running_agent": "/root/reviewer"},
                "wait_budget": {"remaining": 0},
            },
        )
        self.assertEqual(object_at(state, "workflow")["current_stage"], "review")
        self.assertEqual(object_at(state, "control")["detach_reason"], "legacy_wait_budget")

    def test_legacy_stage_override_recovers_checkpoint_without_stage(self) -> None:
        _, state = self.migrate(
            "checkpoint-override",
            {
                "schema_version": 1,
                "phase": "background_work_active",
                "background_checkpoint": {"running_agents": ["/root/reviewer"]},
            },
            "--legacy-stage",
            "review",
        )
        self.assertEqual(object_at(state, "workflow")["current_stage"], "review")

    def test_blockers_migrate_to_blocked_control(self) -> None:
        _, state = self.migrate(
            "blocked",
            {"schema_version": 1, "phase": "planning", "blockers": ["one", "two"]},
        )
        self.assertEqual(
            object_at(state, "control"),
            {"kind": "blocked", "blocker_ids": ["legacy-blocker-1", "legacy-blocker-2"]},
        )

    def test_ambiguous_background_state_fails_closed(self) -> None:
        runtime = self.base / "ambiguous"
        runtime.mkdir()
        legacy = {
            "schema_version": 1,
            "phase": "background_work_active",
            "running_agents": {"reviewer": "/root/reviewer"},
        }
        (runtime / "state.json").write_text(json.dumps(legacy) + "\n")
        code, _, errors = self.invoke(
            "migrate-v1",
            "--runtime-dir",
            str(runtime),
            "--workflow",
            "sk-team-feature",
            "--policy-revision",
            "test-policy",
        )
        self.assertEqual(code, 1)
        self.assertIn("--legacy-stage", errors)
        self.assertEqual(json.loads((runtime / "state.json").read_text()), legacy)

    def test_running_agents_and_blockers_require_reconciliation(self) -> None:
        runtime = self.base / "conflict"
        runtime.mkdir()
        legacy = {
            "schema_version": 1,
            "phase": "review",
            "running_agents": {"reviewer": "/root/reviewer"},
            "blockers": ["user input"],
        }
        (runtime / "state.json").write_text(json.dumps(legacy) + "\n")
        code, _, errors = self.invoke(
            "migrate-v1",
            "--runtime-dir",
            str(runtime),
            "--workflow",
            "sk-team-feature",
            "--policy-revision",
            "test-policy",
        )
        self.assertEqual(code, 1)
        self.assertIn("reconcile", errors)

    def test_migration_is_idempotent(self) -> None:
        runtime, state = self.migrate(
            "idempotent", {"schema_version": 1, "change": "idempotent", "phase": "setup"}
        )
        replayed = self.expect_ok(
            "migrate-v1",
            "--runtime-dir",
            str(runtime),
            "--workflow",
            "sk-team-feature",
            "--policy-revision",
            "test-policy",
        )
        assert replayed is not None
        self.assertEqual(replayed["revision"], state["revision"])
        self.assertEqual(len((runtime / "events.jsonl").read_text().splitlines()), 1)
