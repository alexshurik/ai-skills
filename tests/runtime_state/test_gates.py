from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema

from runtime_state.support import (
    ROOT,
    SK_STATE,
    JsonObject,
    RuntimeCase,
    array_at,
    json_object,
    object_at,
)

STATE_SCHEMA = ROOT / "workflow/agents/shared/runtime-state/state.schema.json"
GATE = "execution-checkpoint"


class GateReentryTests(RuntimeCase):
    def request_gate(self, runtime: Path, revision: int, reason: str) -> JsonObject:
        return self.mutate(
            runtime,
            revision,
            "request-gate",
            "--stage",
            "planning",
            "--gate",
            GATE,
            "--reason",
            reason,
        )

    def run_approved_planning_entry(self, runtime: Path, revision: int) -> int:
        self.mutate(runtime, revision, "enter-stage", "--stage", "planning")
        self.request_gate(runtime, revision + 1, f"plan ready at revision {revision}")
        self.mutate(
            runtime,
            revision + 2,
            "decide-gate",
            "--stage",
            "planning",
            "--gate",
            GATE,
            "--decision",
            "approved",
            "--decided-by",
            "user",
        )
        self.mutate(
            runtime, revision + 3, "complete-stage", "--stage", "planning", "--outcome", "succeeded"
        )
        return revision + 4

    def reentered_state(self) -> tuple[Path, JsonObject]:
        runtime, _ = self.init_runtime("gate-reentry")
        revision = self.run_approved_planning_entry(runtime, 1)
        revision = self.run_approved_planning_entry(runtime, revision)
        self.mutate(runtime, revision, "enter-stage", "--stage", "planning")
        return runtime, self.request_gate(runtime, revision + 1, "plan ready on entry 3")

    def test_reentered_stage_may_request_the_same_gate_name(self) -> None:
        runtime, state = self.reentered_state()

        gate = object_at(state, "workflow", "stages", "planning", "gates", GATE)
        self.assertEqual(gate["entry"], 3)
        self.assertEqual(gate["status"], "pending")
        prior = [json_object(record) for record in array_at(gate, "prior_entries")]
        self.assertEqual([record["entry"] for record in prior], [1, 2])
        self.assertEqual({record["status"] for record in prior}, {"approved"})
        self.assertTrue(all("prior_entries" not in record for record in prior))
        jsonschema.validate(state, json.loads(STATE_SCHEMA.read_text()))
        self.expect_ok("validate", "--runtime-dir", str(runtime))

        errors = self.invoke_error(
            runtime,
            11,
            "unapproved",
            "complete-stage",
            "--stage",
            "planning",
            "--outcome",
            "succeeded",
        )
        self.assertIn("undecided or rejected gate", errors)

    def test_duplicate_gate_name_within_one_entry_is_rejected(self) -> None:
        runtime, _ = self.init_runtime("gate-duplicate")
        self.mutate(runtime, 1, "enter-stage", "--stage", "planning")
        self.request_gate(runtime, 2, "first request")

        errors = self.invoke_error(
            runtime,
            3,
            "duplicate",
            "request-gate",
            "--stage",
            "planning",
            "--gate",
            GATE,
            "--reason",
            "second request",
        )

        self.assertIn(f"planning/{GATE} already exists in stage entry 1", errors)
        self.assertIn("distinct gate name", errors)
        self.assertEqual(len((runtime / "events.jsonl").read_text().splitlines()), 3)

    def test_projection_rejects_malformed_prior_entries(self) -> None:
        _, state = self.reentered_state()
        SK_STATE.validate_state(state)

        def corrupted(change: Callable[[list[Any]], None]) -> Any:
            # Index the deep copy directly: the support helpers return copies.
            candidate: Any = copy.deepcopy(state)
            change(candidate["workflow"]["stages"]["planning"]["gates"][GATE]["prior_entries"])
            return candidate

        def nest(records: list[Any]) -> None:
            records[1]["prior_entries"] = [copy.deepcopy(records[0])]

        def move_into_current_entry(records: list[Any]) -> None:
            records[1]["entry"] = 3

        cases = (
            (nest, r"prior_entries\[2\] has missing or unknown fields"),
            (lambda records: records.reverse(), "increasing entry order"),
            (move_into_current_entry, "future entry"),
        )
        for change, message in cases:
            with (
                self.subTest(message=message),
                self.assertRaisesRegex(SK_STATE.StateError, message),
            ):
                SK_STATE.validate_state(corrupted(change))


class BatchPurposeTests(RuntimeCase):
    def test_purpose_without_members_explains_batch_only_usage(self) -> None:
        runtime, _ = self.init_runtime("purpose-single")
        self.mutate(runtime, 1, "enter-stage", "--stage", "review")

        errors = self.invoke_error(
            runtime,
            2,
            "single-purpose",
            "create-task",
            "--stage",
            "review",
            "--task",
            "solo",
            "--role",
            "reviewer",
            "--purpose",
            "review",
        )

        self.assertIn("requires both purpose and members", errors)
        self.assertIn("omit --purpose and record start-attempt", errors)
        self.assertEqual(len((runtime / "events.jsonl").read_text().splitlines()), 2)
        self.mutate(
            runtime, 2, "create-task", "--stage", "review", "--task", "solo", "--role", "reviewer"
        )
        state = self.mutate(
            runtime,
            3,
            "start-attempt",
            "--stage",
            "review",
            "--task",
            "solo",
            "--attempt-id",
            "solo-1",
            "--host-thread-id",
            "/root/solo",
        )
        task = object_at(state, "workflow", "stages", "review", "tasks", "solo")
        self.assertNotIn("purpose", task)
        self.assertEqual(task["status"], "running")
