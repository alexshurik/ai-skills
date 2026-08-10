from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import ClassVar

import jsonschema

from runtime_state.support import ROOT, SK_STATE, TOOL_PATH, RuntimeCase

DIGEST = "a" * 64
VALID_DATA: dict[str, dict[str, object]] = {
    "workflow.started": {
        "run": {
            "id": "run-1",
            "change": "change",
            "workflow": "sk-team-feature",
            "policy_revision": "policy",
            "created_at": "2026-01-01T00:00:00Z",
        },
        "repositories": {},
    },
    "workflow.migrated_from_v1": {"source_sha256": DIGEST, "state": {}},
    "stage.entered": {"stage": "review"},
    "stage.completed": {"stage": "review", "outcome": "succeeded"},
    "gate.requested": {"stage": "review", "gate": "approval", "reason": "needed"},
    "gate.decided": {
        "stage": "review",
        "gate": "approval",
        "decision": "approved",
        "decided_by": "user",
        "reason": "approved",
    },
    "task.created": {
        "stage": "review",
        "task": "security",
        "role": "reviewer",
        "required": True,
    },
    "agent.attempt.started": {
        "stage": "review",
        "task": "security",
        "attempt_id": "security-1",
        "host_thread_id": "/root/security",
        "input_fingerprint": DIGEST,
    },
    "agent.result.recorded": {
        "stage": "review",
        "task": "security",
        "attempt_id": "security-1",
        "outcome": "succeeded",
        "verdict": "clean",
        "artifact": "review.md",
        "sha256": DIGEST,
    },
    "agent.late_result.recorded": {
        "attempt_id": "security-1",
        "verdict": "late",
        "artifact": "late.md",
        "sha256": DIGEST,
    },
    "check.recorded": {
        "stage": "review",
        "check": "ruff",
        "status": "passed",
        "required": True,
        "evidence": "clean",
        "sha256": DIGEST,
    },
    "artifact.recorded": {
        "name": "review",
        "path": "review.md",
        "sha256": DIGEST,
        "kind": "review",
        "stage": "review",
    },
    "workflow.waiting_for_agents": {
        "attempt_ids": ["security-1"],
        "join": "foreground",
        "reason_code": "review",
    },
    "workflow.waiting_for_user": {"gate_ids": ["review/approval"], "reason_code": "approval"},
    "workflow.blocked": {"blocker_id": "external", "reason": "blocked", "required_action": "wait"},
    "workflow.blocker_resolved": {"blocker_id": "external"},
    "workflow.completed": {"outcome": "completed"},
    "review.lease.granted": {
        "lease_id": "review-lease-1",
        "stage": "review",
        "holder_attempt_id": "orchestrator-1",
        "holder_actor_id": "review-root",
    },
    "review.lease.released": {"lease_id": "review-lease-1"},
}


class EventContractTests(RuntimeCase):
    schema: ClassVar[dict[str, object]]

    @classmethod
    def setUpClass(cls) -> None:
        schema_path = ROOT / "workflow/agents/shared/runtime-state/event.schema.json"
        cls.schema = json.loads(schema_path.read_text())
        jsonschema.validators.validator_for(cls.schema).check_schema(cls.schema)

    def event(self, event_type: str, data: dict[str, object]) -> dict[str, object]:
        return {
            "event_schema_version": 1,
            "seq": 1,
            "id": "event-1",
            "type": event_type,
            "recorded_at": "2026-01-01T00:00:00Z",
            "actor": {"kind": "orchestrator", "id": "root"},
            "command_id": "schema-parity",
            "data": data,
        }

    def assert_both_accept(self, event: dict[str, object]) -> None:
        jsonschema.validate(event, self.schema)
        SK_STATE.validate_event(event, 1)

    def assert_both_reject(self, event: dict[str, object]) -> None:
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(event, self.schema)
        with self.assertRaises(SK_STATE.StateError):
            SK_STATE.validate_event(event, 1)

    def test_schema_and_executable_accept_every_payload_shape(self) -> None:
        self.assertEqual(set(VALID_DATA), set(SK_STATE.EVENT_TYPES))
        for event_type, data in VALID_DATA.items():
            with self.subTest(event_type=event_type):
                self.assert_both_accept(self.event(event_type, data))

    def test_schema_and_executable_reject_missing_extra_and_wrong_types(self) -> None:
        for event_type, valid_data in VALID_DATA.items():
            required = next(iter(SK_STATE.EVENT_SPECS[event_type].required))
            malformed = copy.deepcopy(valid_data)
            del malformed[required]
            self.assert_both_reject(self.event(event_type, malformed))
            self.assert_both_reject(self.event(event_type, {**valid_data, "unexpected": "x"}))
            for field in valid_data:
                wrong_type = copy.deepcopy(valid_data)
                wrong_type[field] = None
                self.assert_both_reject(self.event(event_type, wrong_type))

    def test_detached_wait_condition_matches(self) -> None:
        data = copy.deepcopy(VALID_DATA["workflow.waiting_for_agents"])
        data["join"] = "detached"
        self.assert_both_reject(self.event("workflow.waiting_for_agents", data))
        data["detach_reason"] = "host-forced"
        self.assert_both_accept(self.event("workflow.waiting_for_agents", data))

    def test_envelope_and_identifier_arrays_have_parity(self) -> None:
        event = self.event("stage.entered", VALID_DATA["stage.entered"])
        event["seq"] = True
        self.assert_both_reject(event)
        event = self.event(
            "workflow.waiting_for_agents",
            {"attempt_ids": ["/root/not-an-id"], "join": "foreground", "reason_code": "review"},
        )
        self.assert_both_reject(event)

    def test_facade_is_importable_and_executable(self) -> None:
        self.assertTrue(callable(SK_STATE.build_parser))
        completed = subprocess.run(
            [sys.executable, str(TOOL_PATH), "--help"],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("semantic event journal", completed.stdout.lower())

    def load_facade(self, path: Path, name: str) -> ModuleType:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load facade from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_facade_ignores_unrelated_top_level_runtime_module(self) -> None:
        unrelated = ModuleType("_sk_runtime")
        previous = sys.modules.get("_sk_runtime")
        sys.modules["_sk_runtime"] = unrelated
        try:
            facade = self.load_facade(TOOL_PATH, "collision_facade")
            self.assertIsNot(facade._runtime, unrelated)
            self.assertIs(sys.modules["_sk_runtime"], unrelated)
        finally:
            if previous is None:
                sys.modules.pop("_sk_runtime", None)
            else:
                sys.modules["_sk_runtime"] = previous

    def test_facades_from_two_rendered_trees_load_their_own_packages(self) -> None:
        source = TOOL_PATH.parent
        copies = [self.base / name / "runtime-state" for name in ("one", "two")]
        for target in copies:
            shutil.copytree(source, target)

        facades = [
            self.load_facade(target / "sk_state.py", f"tree_facade_{index}")
            for index, target in enumerate(copies, start=1)
        ]
        origins = [Path(facade._runtime.__file__).resolve() for facade in facades]
        self.assertEqual(
            origins, [(target / "_sk_runtime/__init__.py").resolve() for target in copies]
        )
        self.assertIsNot(facades[0]._runtime, facades[1]._runtime)

    def test_facade_cleans_package_modules_after_failed_load(self) -> None:
        target = self.base / "broken" / "runtime-state"
        shutil.copytree(TOOL_PATH.parent, target)
        package_init = target / "_sk_runtime/__init__.py"
        package_init.write_text("from . import model\nraise RuntimeError('broken package')\n")
        before = set(sys.modules)

        with self.assertRaisesRegex(RuntimeError, "broken package"):
            self.load_facade(target / "sk_state.py", "broken_facade")

        inserted = set(sys.modules) - before
        leaked = [
            name
            for name in inserted
            if (file_name := getattr(sys.modules[name], "__file__", None)) is not None
            and Path(file_name).resolve().is_relative_to(target.resolve())
        ]
        self.assertEqual(leaked, [])

    def test_materialized_state_schema_accepts_reducer_output(self) -> None:
        schema_path = ROOT / "workflow/agents/shared/runtime-state/state.schema.json"
        schema = json.loads(schema_path.read_text())
        jsonschema.validators.validator_for(schema).check_schema(schema)
        event = SK_STATE.validate_event(
            self.event("workflow.started", VALID_DATA["workflow.started"]), 1
        )
        state = SK_STATE.apply_event(None, event)
        jsonschema.validate(state, schema)
