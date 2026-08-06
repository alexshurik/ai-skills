#!/usr/bin/env python3
"""Durable semantic event journal and materialized state for sk-* workflows."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


STATE_SCHEMA_VERSION = 2
EVENT_SCHEMA_VERSION = 1
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
TERMINAL_ATTEMPTS = frozenset({"succeeded", "failed", "blocked", "cancelled"})
TERMINAL_STAGES = frozenset({"succeeded", "failed", "skipped"})
EVENT_TYPES = frozenset(
    {
        "workflow.started",
        "workflow.migrated_from_v1",
        "stage.entered",
        "stage.completed",
        "gate.requested",
        "gate.decided",
        "task.created",
        "agent.attempt.started",
        "agent.result.recorded",
        "agent.late_result.recorded",
        "check.recorded",
        "artifact.recorded",
        "workflow.waiting_for_agents",
        "workflow.waiting_for_user",
        "workflow.blocked",
        "workflow.blocker_resolved",
        "workflow.completed",
    }
)
EVENT_DATA_FIELDS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "workflow.started": (frozenset({"run", "repositories"}), frozenset()),
    "workflow.migrated_from_v1": (frozenset({"source_sha256", "state"}), frozenset()),
    "stage.entered": (frozenset({"stage"}), frozenset()),
    "stage.completed": (frozenset({"stage", "outcome"}), frozenset()),
    "gate.requested": (frozenset({"stage", "gate", "reason"}), frozenset()),
    "gate.decided": (
        frozenset({"stage", "gate", "decision", "decided_by"}),
        frozenset({"reason"}),
    ),
    "task.created": (frozenset({"stage", "task", "role"}), frozenset()),
    "agent.attempt.started": (
        frozenset({"stage", "task", "attempt_id", "host_thread_id"}),
        frozenset({"input_fingerprint"}),
    ),
    "agent.result.recorded": (
        frozenset({"stage", "task", "attempt_id", "outcome"}),
        frozenset({"verdict", "artifact", "sha256"}),
    ),
    "agent.late_result.recorded": (
        frozenset({"attempt_id"}),
        frozenset({"verdict", "artifact", "sha256"}),
    ),
    "check.recorded": (
        frozenset({"stage", "check", "status"}),
        frozenset({"evidence", "sha256"}),
    ),
    "artifact.recorded": (
        frozenset({"name", "path", "sha256"}),
        frozenset({"kind", "stage"}),
    ),
    "workflow.waiting_for_agents": (
        frozenset({"attempt_ids", "join", "reason_code"}),
        frozenset({"detach_reason"}),
    ),
    "workflow.waiting_for_user": (
        frozenset({"gate_ids", "reason_code"}),
        frozenset(),
    ),
    "workflow.blocked": (
        frozenset({"blocker_id", "reason", "required_action"}),
        frozenset(),
    ),
    "workflow.blocker_resolved": (frozenset({"blocker_id"}), frozenset()),
    "workflow.completed": (frozenset({"outcome"}), frozenset()),
}


class StateError(ValueError):
    """Raised when the journal, projection, or requested transition is invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def require_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or any(char in value for char in "\0\r\n"):
        raise StateError(f"{name} must be a non-empty single-line string")
    return value


def require_identifier(value: object, name: str) -> str:
    text = require_string(value, name)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:@+-]*", text):
        raise StateError(f"{name} contains unsupported characters: {text!r}")
    return text


def require_hash(value: object, name: str) -> str:
    text = require_string(value, name)
    if not HASH_RE.fullmatch(text):
        raise StateError(f"{name} must be a lowercase SHA-256 hex digest")
    return text


def require_timestamp(value: object, name: str) -> str:
    text = require_string(value, name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise StateError(f"{name} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise StateError(f"{name} must include a timezone")
    return text


def require_object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise StateError(f"{name} must be a JSON object with string keys")
    return value


def require_integer(value: object, name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise StateError(f"{name} must be an integer >= {minimum}")
    return value


def require_string_list(value: object, name: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise StateError(f"{name} must be an array")
    result = [require_string(item, f"{name} item") for item in value]
    if len(result) != len(set(result)):
        raise StateError(f"{name} must not contain duplicates")
    if nonempty and not result:
        raise StateError(f"{name} must not be empty")
    return result


def runtime_paths(runtime_dir: Path) -> tuple[Path, Path, Path]:
    return (
        runtime_dir / "state.json",
        runtime_dir / "events.jsonl",
        runtime_dir / ".state.lock",
    )


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if os.name == "nt":
            import msvcrt

            if os.fstat(descriptor).st_size == 0:
                os.write(descriptor, b"0")
                os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as temporary:
            json.dump(value, temporary, ensure_ascii=False, indent=2, sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
        fsync_directory(path.parent)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def append_event(path: Path, event: dict[str, Any]) -> None:
    payload = (canonical_json(event) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError("event append made no progress")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StateError(f"{path}: invalid JSON: {error}") from error
    return require_object(value, str(path))


def validate_event(event: object, expected_seq: int) -> dict[str, Any]:
    item = require_object(event, f"event {expected_seq}")
    required = {
        "event_schema_version",
        "seq",
        "id",
        "type",
        "recorded_at",
        "actor",
        "command_id",
        "data",
    }
    if set(item) - (required | {"causation_id"}):
        raise StateError(f"event {expected_seq} contains unknown fields")
    if not required.issubset(item):
        raise StateError(f"event {expected_seq} is missing required fields")
    if item["event_schema_version"] != EVENT_SCHEMA_VERSION:
        raise StateError(f"event {expected_seq} uses an unsupported schema version")
    if item["seq"] != expected_seq:
        raise StateError(f"event sequence gap: expected {expected_seq}, got {item['seq']!r}")
    require_identifier(item["id"], f"event {expected_seq} id")
    event_type = require_identifier(item["type"], f"event {expected_seq} type")
    if event_type not in EVENT_TYPES:
        raise StateError(f"event {expected_seq} has unknown type {event_type!r}")
    require_timestamp(item["recorded_at"], f"event {expected_seq} recorded_at")
    actor = require_object(item["actor"], f"event {expected_seq} actor")
    if set(actor) != {"kind", "id"}:
        raise StateError(f"event {expected_seq} actor must contain only kind and id")
    require_identifier(actor["kind"], f"event {expected_seq} actor kind")
    require_identifier(actor["id"], f"event {expected_seq} actor id")
    require_string(item["command_id"], f"event {expected_seq} command_id")
    data = require_object(item["data"], f"event {expected_seq} data")
    required_data, optional_data = EVENT_DATA_FIELDS[event_type]
    if not required_data.issubset(data) or set(data) - (required_data | optional_data):
        raise StateError(f"event {expected_seq} data does not match {event_type}")
    if event_type == "workflow.migrated_from_v1":
        require_hash(data["source_sha256"], f"event {expected_seq} source_sha256")
    if "causation_id" in item:
        require_identifier(item["causation_id"], f"event {expected_seq} causation_id")
    return item


def read_events(path: Path) -> list[dict[str, Any]]:
    try:
        content = path.read_bytes()
    except FileNotFoundError:
        return []
    if content and not content.endswith(b"\n"):
        raise StateError(f"{path}: incomplete final JSONL record; run repair")
    events: list[dict[str, Any]] = []
    command_ids: dict[str, str] = {}
    event_ids: set[str] = set()
    for index, raw_line in enumerate(content.splitlines(), start=1):
        if not raw_line.strip():
            raise StateError(f"{path}:{index}: blank records are not allowed")
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise StateError(f"{path}:{index}: invalid JSON: {error}") from error
        event = validate_event(value, index)
        if event["id"] in event_ids:
            raise StateError(f"{path}:{index}: duplicate event id")
        event_ids.add(event["id"])
        fingerprint = canonical_json({"type": event["type"], "data": event["data"]})
        if event["command_id"] in command_ids:
            if command_ids[event["command_id"]] != fingerprint:
                raise StateError(f"{path}:{index}: command_id was reused with different content")
            raise StateError(f"{path}:{index}: duplicate command_id")
        command_ids[event["command_id"]] = fingerprint
        events.append(event)
    return events


def initial_state(run: dict[str, Any], repositories: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "revision": 0,
        "run": copy.deepcopy(run),
        "repositories": copy.deepcopy(repositories),
        "workflow": {"current_stage": None, "stages": {}},
        "control": {"kind": "ready", "reason_code": "workflow_started"},
        "artifacts": {},
        "blockers": {},
        "last_event": None,
    }


def stage_for(state: dict[str, Any], name: str) -> dict[str, Any]:
    try:
        return state["workflow"]["stages"][name]
    except KeyError as error:
        raise StateError(f"unknown stage {name!r}") from error


def task_for(state: dict[str, Any], stage: str, task: str) -> dict[str, Any]:
    current_stage = stage_for(state, stage)
    try:
        return current_stage["tasks"][task]
    except KeyError as error:
        raise StateError(f"unknown task {stage}/{task}") from error


def find_attempt(state: dict[str, Any], attempt_id: str) -> tuple[str, str, dict[str, Any]]:
    found: list[tuple[str, str, dict[str, Any]]] = []
    for stage_name, stage in state["workflow"]["stages"].items():
        for task_name, task in stage["tasks"].items():
            for attempt in task["attempts"]:
                if attempt["id"] == attempt_id:
                    found.append((stage_name, task_name, attempt))
    if len(found) != 1:
        raise StateError(f"attempt {attempt_id!r} was not found uniquely")
    return found[0]


def require_active_stage(state: dict[str, Any], stage_name: str) -> dict[str, Any]:
    if state["workflow"]["current_stage"] != stage_name:
        raise StateError(f"stage {stage_name!r} is not current")
    stage = stage_for(state, stage_name)
    if stage["status"] not in {"in_progress", "waiting"}:
        raise StateError(f"stage {stage_name!r} is not active")
    return stage


def running_attempt_ids(state: dict[str, Any]) -> list[str]:
    return sorted(
        attempt["id"]
        for stage in state["workflow"]["stages"].values()
        for task in stage["tasks"].values()
        for attempt in task["attempts"]
        if attempt["status"] == "running"
    )


def apply_event(previous: dict[str, Any] | None, event: dict[str, Any]) -> dict[str, Any]:
    event_type = event["type"]
    data = event["data"]
    if event_type == "workflow.started":
        if previous is not None:
            raise StateError("workflow.started must be the first event")
        state = initial_state(
            require_object(data.get("run"), "workflow.started run"),
            require_object(data.get("repositories"), "workflow.started repositories"),
        )
    elif event_type == "workflow.migrated_from_v1":
        if previous is not None:
            raise StateError("workflow.migrated_from_v1 must be the first event")
        state = copy.deepcopy(require_object(data.get("state"), "migration state"))
        state["schema_version"] = STATE_SCHEMA_VERSION
    else:
        if previous is None:
            raise StateError(f"{event_type} cannot be the first event")
        state = copy.deepcopy(previous)

        if event_type == "stage.entered":
            name = require_identifier(data.get("stage"), "stage")
            if state["control"]["kind"] != "ready":
                raise StateError("a stage may be entered only while control is ready")
            current = state["workflow"]["current_stage"]
            if current is not None and current != name:
                current_state = stage_for(state, current)["status"]
                if current_state not in TERMINAL_STAGES:
                    raise StateError(f"cannot enter {name!r}; stage {current!r} is not terminal")
            stages = state["workflow"]["stages"]
            stage = stages.setdefault(
                name,
                {"status": "pending", "entries": 0, "gates": {}, "checks": {}, "tasks": {}},
            )
            if stage["status"] not in {"pending", *TERMINAL_STAGES}:
                raise StateError(f"stage {name!r} is already active")
            stage["entries"] += 1
            stage["status"] = "in_progress"
            stage["entered_event"] = event["seq"]
            stage.pop("completed_event", None)
            state["workflow"]["current_stage"] = name
            state["control"] = {"kind": "ready", "reason_code": "stage_entered"}

        elif event_type == "stage.completed":
            name = require_identifier(data.get("stage"), "stage")
            outcome = require_identifier(data.get("outcome"), "stage outcome")
            if outcome not in TERMINAL_STAGES:
                raise StateError("stage outcome must be succeeded, failed, or skipped")
            if state["workflow"]["current_stage"] != name:
                raise StateError(f"stage {name!r} is not current")
            if state["control"]["kind"] != "ready":
                raise StateError("a stage may be completed only while control is ready")
            if state["blockers"]:
                raise StateError("a stage may not complete with unresolved blockers")
            stage = stage_for(state, name)
            if any(
                attempt["status"] == "running"
                for task in stage["tasks"].values()
                for attempt in task["attempts"]
            ):
                raise StateError(f"stage {name!r} still has running attempts")
            if outcome == "succeeded" and any(
                gate["status"] not in {"approved", "waived"}
                for gate in stage["gates"].values()
                if gate["entry"] == stage["entries"]
            ):
                raise StateError(f"stage {name!r} has an undecided or rejected gate")
            stage["status"] = outcome
            stage["completed_event"] = event["seq"]
            state["control"] = {"kind": "ready", "reason_code": "stage_completed"}

        elif event_type == "gate.requested":
            stage_name = require_identifier(data.get("stage"), "stage")
            gate_name = require_identifier(data.get("gate"), "gate")
            reason = require_string(data.get("reason"), "gate reason")
            stage = require_active_stage(state, stage_name)
            if state["control"]["kind"] != "ready":
                raise StateError("a gate may be requested only while control is ready")
            if gate_name in stage["gates"]:
                raise StateError(f"gate {stage_name}/{gate_name} already exists")
            stage["gates"][gate_name] = {
                "status": "pending",
                "reason": reason,
                "entry": stage["entries"],
                "requested_event": event["seq"],
            }

        elif event_type == "gate.decided":
            stage_name = require_identifier(data.get("stage"), "stage")
            gate_name = require_identifier(data.get("gate"), "gate")
            decision = require_identifier(data.get("decision"), "gate decision")
            if decision not in {"approved", "rejected", "waived"}:
                raise StateError("gate decision must be approved, rejected, or waived")
            stage = require_active_stage(state, stage_name)
            if state["control"]["kind"] not in {"ready", "waiting_user"}:
                raise StateError("a gate may be decided only from ready or waiting_user")
            try:
                gate = stage["gates"][gate_name]
            except KeyError as error:
                raise StateError(f"unknown gate {stage_name}/{gate_name}") from error
            if gate["status"] != "pending":
                raise StateError(f"gate {stage_name}/{gate_name} is already decided")
            gate.update(
                {
                    "status": decision,
                    "decided_by": require_string(data.get("decided_by"), "decided_by"),
                    "decision_event": event["seq"],
                }
            )
            if "reason" in data:
                gate["decision_reason"] = require_string(data["reason"], "decision reason")
            gate_ref = f"{stage_name}/{gate_name}"
            if state["control"].get("kind") == "waiting_user":
                waiting = state["control"]["gate_ids"]
                if gate_ref in waiting:
                    remaining = [item for item in waiting if item != gate_ref]
                    if remaining:
                        state["control"]["gate_ids"] = remaining
                    else:
                        state["control"] = {
                            "kind": "ready",
                            "reason_code": "user_gates_decided",
                        }
                        current = state["workflow"]["current_stage"]
                        if current and stage_for(state, current)["status"] == "waiting":
                            stage_for(state, current)["status"] = "in_progress"

        elif event_type == "task.created":
            stage_name = require_identifier(data.get("stage"), "stage")
            task_name = require_identifier(data.get("task"), "task")
            role = require_identifier(data.get("role"), "role")
            stage = require_active_stage(state, stage_name)
            if state["control"]["kind"] not in {"ready", "waiting_agents"}:
                raise StateError("a task may be created only from ready or waiting_agents")
            if task_name in stage["tasks"]:
                raise StateError(f"task {stage_name}/{task_name} already exists")
            stage["tasks"][task_name] = {
                "role": role,
                "status": "pending",
                "created_entry": stage["entries"],
                "created_event": event["seq"],
                "attempts": [],
            }

        elif event_type == "agent.attempt.started":
            stage_name = require_identifier(data.get("stage"), "stage")
            task_name = require_identifier(data.get("task"), "task")
            attempt_id = require_identifier(data.get("attempt_id"), "attempt_id")
            require_active_stage(state, stage_name)
            if state["control"]["kind"] not in {"ready", "waiting_agents"}:
                raise StateError("an attempt may be started only from ready or waiting_agents")
            task = task_for(state, stage_name, task_name)
            try:
                find_attempt(state, attempt_id)
            except StateError:
                pass
            else:
                raise StateError(f"attempt id {attempt_id!r} already exists")
            if any(item["status"] == "running" for item in task["attempts"]):
                raise StateError(f"task {stage_name}/{task_name} already has a running attempt")
            attempt = {
                "id": attempt_id,
                "ordinal": len(task["attempts"]) + 1,
                "status": "running",
                "agent": {
                    "role": task["role"],
                    "host_thread_id": require_string(data.get("host_thread_id"), "host_thread_id"),
                },
                "stage_entry": require_active_stage(state, stage_name)["entries"],
                "started_event": event["seq"],
                "late_results": [],
            }
            if "input_fingerprint" in data:
                attempt["input_fingerprint"] = require_hash(
                    data["input_fingerprint"], "input_fingerprint"
                )
            task["attempts"].append(attempt)
            task["status"] = "running"
            if state["control"].get("kind") == "waiting_agents":
                state["control"]["attempt_ids"].append(attempt_id)

        elif event_type == "agent.result.recorded":
            stage_name = require_identifier(data.get("stage"), "stage")
            task_name = require_identifier(data.get("task"), "task")
            attempt_id = require_identifier(data.get("attempt_id"), "attempt_id")
            outcome = require_identifier(data.get("outcome"), "attempt outcome")
            if outcome not in TERMINAL_ATTEMPTS:
                raise StateError("attempt outcome is not terminal")
            found_stage, found_task, attempt = find_attempt(state, attempt_id)
            if (found_stage, found_task) != (stage_name, task_name):
                raise StateError("attempt does not belong to the named stage/task")
            if attempt["status"] != "running":
                raise StateError(f"attempt {attempt_id!r} is already terminal")
            result = {"outcome": outcome, "recorded_event": event["seq"]}
            for field in ("verdict", "artifact"):
                if field in data:
                    result[field] = require_string(data[field], field)
            if "sha256" in data:
                result["sha256"] = require_hash(data["sha256"], "sha256")
            attempt["status"] = outcome
            attempt["result"] = result
            task_for(state, stage_name, task_name)["status"] = outcome
            if state["control"].get("kind") == "waiting_agents":
                waiting = state["control"]["attempt_ids"]
                if attempt_id in waiting:
                    remaining = [item for item in waiting if item != attempt_id]
                    if remaining:
                        state["control"]["attempt_ids"] = remaining
                    else:
                        state["control"] = {
                            "kind": "ready",
                            "reason_code": "agent_results_recorded",
                        }
                        current = state["workflow"]["current_stage"]
                        if current and stage_for(state, current)["status"] == "waiting":
                            stage_for(state, current)["status"] = "in_progress"

        elif event_type == "agent.late_result.recorded":
            attempt_id = require_identifier(data.get("attempt_id"), "attempt_id")
            _, _, attempt = find_attempt(state, attempt_id)
            if attempt["status"] not in TERMINAL_ATTEMPTS:
                raise StateError("late result may only be attached to a terminal attempt")
            late = {"recorded_event": event["seq"]}
            for field in ("verdict", "artifact"):
                if field in data:
                    late[field] = require_string(data[field], field)
            if "sha256" in data:
                late["sha256"] = require_hash(data["sha256"], "sha256")
            attempt["late_results"].append(late)

        elif event_type == "check.recorded":
            stage_name = require_identifier(data.get("stage"), "stage")
            check_name = require_identifier(data.get("check"), "check")
            status = require_identifier(data.get("status"), "check status")
            if status not in {"passed", "failed", "unknown"}:
                raise StateError("check status must be passed, failed, or unknown")
            stage = require_active_stage(state, stage_name)
            check = {
                "status": status,
                "entry": stage["entries"],
                "recorded_event": event["seq"],
            }
            if "evidence" in data:
                check["evidence"] = require_string(data["evidence"], "check evidence")
            if "sha256" in data:
                check["sha256"] = require_hash(data["sha256"], "sha256")
            stage["checks"][check_name] = check

        elif event_type == "artifact.recorded":
            name = require_identifier(data.get("name"), "artifact name")
            artifact = {
                "path": require_string(data.get("path"), "artifact path"),
                "sha256": require_hash(data.get("sha256"), "artifact sha256"),
                "recorded_event": event["seq"],
            }
            for field in ("kind", "stage"):
                if field in data:
                    artifact[field] = require_identifier(data[field], field)
            if "stage" in artifact:
                stage_for(state, artifact["stage"])
            state["artifacts"][name] = artifact

        elif event_type == "workflow.waiting_for_agents":
            attempt_ids = require_string_list(data.get("attempt_ids"), "attempt_ids", nonempty=True)
            join = require_identifier(data.get("join"), "join")
            if join not in {"foreground", "detached"}:
                raise StateError("join must be foreground or detached")
            if state["control"]["kind"] not in {"ready", "waiting_agents"}:
                raise StateError("an agent join may start only from ready or waiting_agents")
            for attempt_id in attempt_ids:
                _, _, attempt = find_attempt(state, attempt_id)
                if attempt["status"] != "running":
                    raise StateError(f"cannot wait for terminal attempt {attempt_id!r}")
            running = running_attempt_ids(state)
            if sorted(attempt_ids) != running:
                raise StateError(
                    "agent join must contain every running attempt exactly once; "
                    f"running={running!r}"
                )
            control = {
                "kind": "waiting_agents",
                "join": join,
                "attempt_ids": attempt_ids,
                "reason_code": require_identifier(data.get("reason_code"), "reason_code"),
            }
            if join == "detached":
                control["detach_reason"] = require_identifier(
                    data.get("detach_reason"), "detach_reason"
                )
            elif data.get("detach_reason") is not None:
                raise StateError("foreground waits must not have detach_reason")
            state["control"] = control
            current = state["workflow"]["current_stage"]
            if current:
                stage_for(state, current)["status"] = "waiting"

        elif event_type == "workflow.waiting_for_user":
            if state["control"]["kind"] != "ready":
                raise StateError("a user wait may start only while control is ready")
            if running_attempt_ids(state):
                raise StateError("cannot wait for user while agent attempts are running")
            gate_ids = require_string_list(data.get("gate_ids"), "gate_ids", nonempty=True)
            for gate_id in gate_ids:
                try:
                    stage_name, gate_name = gate_id.split("/", 1)
                    gate = stage_for(state, stage_name)["gates"][gate_name]
                except (ValueError, KeyError) as error:
                    raise StateError(f"unknown gate reference {gate_id!r}") from error
                if gate["status"] != "pending":
                    raise StateError(f"gate {gate_id!r} is not pending")
            state["control"] = {
                "kind": "waiting_user",
                "gate_ids": gate_ids,
                "reason_code": require_identifier(data.get("reason_code"), "reason_code"),
            }
            current = state["workflow"]["current_stage"]
            if current:
                stage_for(state, current)["status"] = "waiting"

        elif event_type == "workflow.blocked":
            if state["control"]["kind"] != "ready":
                raise StateError("workflow may be blocked only while control is ready")
            if running_attempt_ids(state):
                raise StateError("record agent results before blocking the workflow")
            blocker_id = require_identifier(data.get("blocker_id"), "blocker_id")
            blocker = {
                "reason": require_string(data.get("reason"), "blocker reason"),
                "required_action": require_string(data.get("required_action"), "required_action"),
                "recorded_event": event["seq"],
            }
            state["blockers"][blocker_id] = blocker
            state["control"] = {"kind": "blocked", "blocker_ids": sorted(state["blockers"])}

        elif event_type == "workflow.blocker_resolved":
            if state["control"]["kind"] != "blocked":
                raise StateError("a blocker may be resolved only while control is blocked")
            blocker_id = require_identifier(data.get("blocker_id"), "blocker_id")
            if blocker_id not in state["blockers"]:
                raise StateError(f"unknown blocker {blocker_id!r}")
            del state["blockers"][blocker_id]
            if state["blockers"]:
                state["control"] = {
                    "kind": "blocked",
                    "blocker_ids": sorted(state["blockers"]),
                }
            else:
                state["control"] = {
                    "kind": "ready",
                    "reason_code": "blockers_resolved",
                }

        elif event_type == "workflow.completed":
            if state["control"]["kind"] == "complete":
                raise StateError("workflow is already complete")
            outcome = require_identifier(data.get("outcome"), "workflow outcome")
            if outcome not in {"completed", "aborted"}:
                raise StateError("workflow outcome must be completed or aborted")
            running = running_attempt_ids(state)
            if running:
                raise StateError(f"workflow still has running attempts: {', '.join(running)}")
            if outcome == "completed":
                current = state["workflow"]["current_stage"]
                if current is not None and stage_for(state, current)["status"] not in TERMINAL_STAGES:
                    raise StateError("current stage is not terminal")
                if state["blockers"]:
                    raise StateError("workflow still has unresolved blockers")
            state["control"] = {"kind": "complete", "outcome": outcome}

    state["revision"] = event["seq"]
    state["last_event"] = {"seq": event["seq"], "id": event["id"]}
    validate_state(state)
    return state


def replay(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    state: dict[str, Any] | None = None
    for event in events:
        state = apply_event(state, event)
    return state


def validate_repository(value: object, name: str) -> None:
    repository = require_object(value, name)
    allowed = {"root", "worktree", "branch", "base_sha"}
    if set(repository) - allowed or not repository:
        raise StateError(f"{name} contains no supported repository fields")
    for field, item in repository.items():
        require_string(item, f"{name}.{field}")


def validate_state(state: object) -> dict[str, Any]:
    item = require_object(state, "state")
    required = {
        "schema_version",
        "revision",
        "run",
        "repositories",
        "workflow",
        "control",
        "artifacts",
        "blockers",
        "last_event",
    }
    if set(item) != required:
        raise StateError("state contains missing or unknown top-level fields")
    if item["schema_version"] != STATE_SCHEMA_VERSION:
        raise StateError("unsupported state schema version")
    require_integer(item["revision"], "state revision", minimum=1)
    run = require_object(item["run"], "run")
    run_required = {"id", "change", "workflow", "policy_revision", "created_at"}
    if not run_required.issubset(run) or set(run) - (run_required | {"migrated_from"}):
        raise StateError("run contains missing or unknown fields")
    require_string(run["id"], "run.id")
    for field in ("change", "workflow"):
        require_identifier(run[field], f"run.{field}")
    require_string(run["policy_revision"], "run.policy_revision")
    require_timestamp(run["created_at"], "run.created_at")
    if "migrated_from" in run:
        migrated = require_object(run["migrated_from"], "run.migrated_from")
        if migrated != {"schema_version": 1}:
            raise StateError("run.migrated_from must identify schema version 1")
    repositories = require_object(item["repositories"], "repositories")
    for name, repository in repositories.items():
        require_identifier(name, "repository name")
        validate_repository(repository, f"repositories.{name}")
    workflow = require_object(item["workflow"], "workflow")
    if set(workflow) != {"current_stage", "stages"}:
        raise StateError("workflow must contain current_stage and stages")
    if workflow["current_stage"] is not None:
        require_identifier(workflow["current_stage"], "current_stage")
        if workflow["current_stage"] not in require_object(workflow["stages"], "stages"):
            raise StateError("current_stage does not exist")
    stages = require_object(workflow["stages"], "stages")
    attempt_ids: set[str] = set()
    for stage_name, stage_value in stages.items():
        require_identifier(stage_name, "stage name")
        stage = require_object(stage_value, f"stage {stage_name}")
        if not {"status", "entries", "gates", "checks", "tasks"}.issubset(stage):
            raise StateError(f"stage {stage_name} is incomplete")
        if set(stage) - {
            "status", "entries", "gates", "checks", "tasks", "entered_event", "completed_event"
        }:
            raise StateError(f"stage {stage_name} contains unknown fields")
        if stage["status"] not in {"pending", "in_progress", "waiting", *TERMINAL_STAGES}:
            raise StateError(f"stage {stage_name} has invalid status")
        entries = require_integer(stage["entries"], f"stage {stage_name} entries")
        for event_field in ("entered_event", "completed_event"):
            if event_field in stage:
                require_integer(stage[event_field], f"stage {stage_name} {event_field}")
        gates = require_object(stage["gates"], f"stage {stage_name} gates")
        for gate_name, gate_value in gates.items():
            require_identifier(gate_name, "gate name")
            gate = require_object(gate_value, f"gate {stage_name}/{gate_name}")
            allowed_gate = {
                "status", "reason", "entry", "requested_event", "decided_by",
                "decision_event", "decision_reason",
            }
            if not {"status", "reason", "entry", "requested_event"}.issubset(gate) or set(gate) - allowed_gate:
                raise StateError(f"gate {stage_name}/{gate_name} has invalid fields")
            if gate["status"] not in {"pending", "approved", "rejected", "waived"}:
                raise StateError(f"gate {stage_name}/{gate_name} has invalid status")
            require_string(gate["reason"], "gate reason")
            gate_entry = require_integer(gate["entry"], "gate entry", minimum=1)
            if gate_entry > entries:
                raise StateError(f"gate {stage_name}/{gate_name} refers to a future entry")
            require_integer(gate["requested_event"], "gate requested_event")
            if gate["status"] == "pending":
                if "decided_by" in gate or "decision_event" in gate:
                    raise StateError(f"pending gate {stage_name}/{gate_name} has a decision")
            else:
                require_string(gate.get("decided_by"), "gate decided_by")
                require_integer(gate.get("decision_event"), "gate decision_event")
            if "decision_reason" in gate:
                require_string(gate["decision_reason"], "gate decision_reason")
        checks = require_object(stage["checks"], f"stage {stage_name} checks")
        for check_name, check_value in checks.items():
            require_identifier(check_name, "check name")
            check = require_object(check_value, f"check {stage_name}/{check_name}")
            if not {"status", "entry", "recorded_event"}.issubset(check) or set(check) - {
                "status", "entry", "recorded_event", "evidence", "sha256"
            }:
                raise StateError(f"check {stage_name}/{check_name} has invalid fields")
            if check["status"] not in {"passed", "failed", "unknown"}:
                raise StateError(f"check {stage_name}/{check_name} has invalid status")
            check_entry = require_integer(check["entry"], "check entry", minimum=1)
            if check_entry > entries:
                raise StateError(f"check {stage_name}/{check_name} refers to a future entry")
            require_integer(check["recorded_event"], "check recorded_event")
            if "evidence" in check:
                require_string(check["evidence"], "check evidence")
            if "sha256" in check:
                require_hash(check["sha256"], "check sha256")
        tasks = require_object(stage["tasks"], f"stage {stage_name} tasks")
        for task_name, task_value in tasks.items():
            require_identifier(task_name, "task name")
            task = require_object(task_value, f"task {stage_name}/{task_name}")
            if set(task) != {"role", "status", "created_entry", "created_event", "attempts"}:
                raise StateError(f"task {stage_name}/{task_name} has invalid fields")
            require_identifier(task["role"], "task role")
            if task["status"] not in {"pending", "running", *TERMINAL_ATTEMPTS}:
                raise StateError(f"task {stage_name}/{task_name} has invalid status")
            created_entry = require_integer(task["created_entry"], "task created_entry", minimum=1)
            if created_entry > entries:
                raise StateError(f"task {stage_name}/{task_name} refers to a future entry")
            require_integer(task["created_event"], "task created_event")
            if not isinstance(task["attempts"], list):
                raise StateError(f"task {stage_name}/{task_name} attempts must be an array")
            for ordinal, attempt_value in enumerate(task["attempts"], start=1):
                attempt = require_object(attempt_value, "attempt")
                attempt_id = require_identifier(attempt.get("id"), "attempt id")
                if attempt_id in attempt_ids:
                    raise StateError(f"duplicate attempt id {attempt_id!r}")
                attempt_ids.add(attempt_id)
                if attempt.get("ordinal") != ordinal:
                    raise StateError(f"attempt {attempt_id} has invalid ordinal")
                if attempt.get("status") not in {"running", *TERMINAL_ATTEMPTS}:
                    raise StateError(f"attempt {attempt_id} has invalid status")
                allowed_attempt = {
                    "id", "ordinal", "status", "agent", "stage_entry", "started_event",
                    "input_fingerprint", "result", "late_results",
                }
                if set(attempt) - allowed_attempt:
                    raise StateError(f"attempt {attempt_id} contains unknown fields")
                stage_entry = require_integer(attempt.get("stage_entry"), "attempt stage_entry", minimum=1)
                if stage_entry > entries:
                    raise StateError(f"attempt {attempt_id} refers to a future entry")
                require_integer(attempt.get("started_event"), "attempt started_event")
                agent = require_object(attempt.get("agent"), f"attempt {attempt_id} agent")
                if set(agent) != {"role", "host_thread_id"}:
                    raise StateError(f"attempt {attempt_id} agent has invalid fields")
                require_identifier(agent["role"], "attempt agent role")
                require_string(agent["host_thread_id"], "attempt host_thread_id")
                if "input_fingerprint" in attempt:
                    require_hash(attempt["input_fingerprint"], "attempt input_fingerprint")
                if not isinstance(attempt.get("late_results"), list):
                    raise StateError(f"attempt {attempt_id} late_results must be an array")
                if attempt["status"] == "running" and "result" in attempt:
                    raise StateError(f"running attempt {attempt_id} has a result")
                if attempt["status"] != "running" and "result" not in attempt:
                    raise StateError(f"terminal attempt {attempt_id} has no result")
                if "result" in attempt:
                    result = require_object(attempt["result"], f"attempt {attempt_id} result")
                    if not {"outcome", "recorded_event"}.issubset(result) or set(result) - {
                        "outcome", "recorded_event", "verdict", "artifact", "sha256"
                    }:
                        raise StateError(f"attempt {attempt_id} result has invalid fields")
                    if result["outcome"] != attempt["status"]:
                        raise StateError(f"attempt {attempt_id} result outcome does not match status")
                    require_integer(result["recorded_event"], "result recorded_event")
                    for field in ("verdict", "artifact"):
                        if field in result:
                            require_string(result[field], f"result {field}")
                    if "sha256" in result:
                        require_hash(result["sha256"], "result sha256")
                for late_value in attempt["late_results"]:
                    late = require_object(late_value, f"attempt {attempt_id} late result")
                    if "recorded_event" not in late or set(late) - {
                        "recorded_event", "verdict", "artifact", "sha256"
                    }:
                        raise StateError(f"attempt {attempt_id} late result has invalid fields")
                    require_integer(late["recorded_event"], "late result recorded_event", minimum=1)
                    for field in ("verdict", "artifact"):
                        if field in late:
                            require_string(late[field], f"late result {field}")
                    if "sha256" in late:
                        require_hash(late["sha256"], "late result sha256")
            expected_task_status = task["attempts"][-1]["status"] if task["attempts"] else "pending"
            if task["status"] != expected_task_status:
                raise StateError(f"task {stage_name}/{task_name} status does not match latest attempt")
    control = require_object(item["control"], "control")
    kind = require_identifier(control.get("kind"), "control.kind")
    allowed_control = {
        "ready": {"kind", "reason_code"},
        "waiting_agents": {"kind", "join", "attempt_ids", "reason_code", "detach_reason"},
        "waiting_user": {"kind", "gate_ids", "reason_code"},
        "blocked": {"kind", "blocker_ids"},
        "complete": {"kind", "outcome"},
    }
    if kind not in allowed_control or set(control) - allowed_control[kind]:
        raise StateError("control shape does not match its kind")
    if kind == "ready":
        if set(control) != {"kind", "reason_code"}:
            raise StateError("ready control has invalid fields")
        require_identifier(control["reason_code"], "control.reason_code")
    elif kind == "waiting_agents":
        required_wait = {"kind", "join", "attempt_ids", "reason_code"}
        if not required_wait.issubset(control):
            raise StateError("waiting_agents control is incomplete")
        attempt_refs = require_string_list(
            control["attempt_ids"], "control.attempt_ids", nonempty=True
        )
        for attempt_ref in attempt_refs:
            require_identifier(attempt_ref, "control attempt id")
        if sorted(attempt_refs) != running_attempt_ids(item):
            raise StateError("waiting_agents must reference every running attempt")
        if control["join"] not in {"foreground", "detached"}:
            raise StateError("waiting_agents join is invalid")
        require_identifier(control["reason_code"], "control.reason_code")
        if control["join"] == "detached":
            require_identifier(control.get("detach_reason"), "control.detach_reason")
        elif "detach_reason" in control:
            raise StateError("foreground control may not have detach_reason")
    elif kind == "waiting_user":
        if set(control) != {"kind", "gate_ids", "reason_code"}:
            raise StateError("waiting_user control has invalid fields")
        gate_refs = require_string_list(control["gate_ids"], "control.gate_ids", nonempty=True)
        for gate_ref in gate_refs:
            parts = gate_ref.split("/")
            if len(parts) != 2:
                raise StateError(f"invalid gate reference {gate_ref!r}")
            stage_name, gate_name = parts
            try:
                gate = stages[stage_name]["gates"][gate_name]
            except KeyError as error:
                raise StateError(f"unknown gate reference {gate_ref!r}") from error
            if gate["status"] != "pending":
                raise StateError(f"waiting_user gate {gate_ref!r} is not pending")
        if running_attempt_ids(item):
            raise StateError("waiting_user may not coexist with running attempts")
        require_identifier(control["reason_code"], "control.reason_code")
    blockers = require_object(item["blockers"], "blockers")
    for blocker_id, blocker_value in blockers.items():
        require_identifier(blocker_id, "blocker id")
        blocker = require_object(blocker_value, f"blocker {blocker_id}")
        if set(blocker) != {"reason", "required_action", "recorded_event"}:
            raise StateError(f"blocker {blocker_id} has invalid fields")
        require_string(blocker["reason"], "blocker reason")
        require_string(blocker["required_action"], "blocker required_action")
        require_integer(blocker["recorded_event"], "blocker recorded_event")
    if kind == "blocked":
        blocker_refs = require_string_list(control.get("blocker_ids"), "control.blocker_ids", nonempty=True)
        if blocker_refs != sorted(blockers):
            raise StateError("blocked control does not match blockers")
    elif blockers:
        raise StateError("unresolved blockers require blocked control")
    if kind == "complete" and control.get("outcome") not in {"completed", "aborted"}:
        raise StateError("complete control has invalid outcome")
    artifacts = require_object(item["artifacts"], "artifacts")
    for artifact_name, artifact_value in artifacts.items():
        require_identifier(artifact_name, "artifact name")
        artifact = require_object(artifact_value, f"artifact {artifact_name}")
        if not {"path", "sha256", "recorded_event"}.issubset(artifact) or set(artifact) - {
            "path", "sha256", "recorded_event", "kind", "stage"
        }:
            raise StateError(f"artifact {artifact_name} has invalid fields")
        require_string(artifact["path"], "artifact path")
        require_hash(artifact["sha256"], "artifact sha256")
        require_integer(artifact["recorded_event"], "artifact recorded_event")
        if "kind" in artifact:
            require_identifier(artifact["kind"], "artifact kind")
        if "stage" in artifact:
            require_identifier(artifact["stage"], "artifact stage")
            if artifact["stage"] not in stages:
                raise StateError(f"artifact {artifact_name} refers to an unknown stage")
    last_event = require_object(item["last_event"], "last_event")
    if set(last_event) != {"seq", "id"} or last_event["seq"] != item["revision"]:
        raise StateError("last_event does not match revision")
    require_identifier(last_event["id"], "last_event.id")
    return item


def snapshot_status(path: Path, projected: dict[str, Any] | None) -> str:
    if not path.exists():
        return "missing"
    snapshot = read_json(path)
    if snapshot.get("schema_version") == 1:
        return "legacy_v1"
    validate_state(snapshot)
    if projected is None:
        return "orphaned"
    if snapshot == projected:
        return "valid"
    if snapshot["revision"] < projected["revision"]:
        return "stale"
    return "diverged"


def load_runtime(runtime_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str]:
    state_path, events_path, _ = runtime_paths(runtime_dir)
    events = read_events(events_path)
    projected = replay(events)
    return events, projected, snapshot_status(state_path, projected)


def make_event(
    seq: int,
    event_type: str,
    command_id: str,
    data: dict[str, Any],
    actor_kind: str,
    actor_id: str,
    causation_id: str | None,
) -> dict[str, Any]:
    event = {
        "event_schema_version": EVENT_SCHEMA_VERSION,
        "seq": seq,
        "id": str(uuid.uuid4()),
        "type": event_type,
        "recorded_at": utc_now(),
        "actor": {"kind": actor_kind, "id": actor_id},
        "command_id": command_id,
        "data": data,
    }
    if causation_id:
        event["causation_id"] = causation_id
    return validate_event(event, seq)


def emit_state(state: dict[str, Any], *, prefix: str | None = None) -> None:
    if prefix:
        print(prefix, file=sys.stderr)
    json.dump(state, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    print()


def commit_transition(args: argparse.Namespace, event_type: str, data: dict[str, Any]) -> None:
    runtime_dir = Path(args.runtime_dir).resolve()
    state_path, events_path, lock_path = runtime_paths(runtime_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(lock_path):
        events, state, status = load_runtime(runtime_dir)
        if state is None:
            raise StateError("workflow is not initialized")
        if status in {"legacy_v1", "orphaned", "diverged"}:
            raise StateError(f"snapshot status {status}; validate or migrate before mutation")
        candidate_fingerprint = canonical_json({"type": event_type, "data": data})
        for event in events:
            if event["command_id"] == args.command_id:
                existing = canonical_json({"type": event["type"], "data": event["data"]})
                if existing != candidate_fingerprint:
                    raise StateError("command_id already exists with different content")
                if status != "valid":
                    atomic_write_json(state_path, state)
                emit_state(state, prefix=f"idempotent replay: event {event['seq']}")
                return
        expected_revision = args.expected_revision
        if expected_revision != state["revision"]:
            raise StateError(
                f"revision conflict: expected {expected_revision}, current {state['revision']}"
            )
        event = make_event(
            state["revision"] + 1,
            event_type,
            require_string(args.command_id, "command_id"),
            data,
            require_identifier(args.actor_kind, "actor_kind"),
            require_identifier(args.actor_id, "actor_id"),
            args.causation_id,
        )
        next_state = apply_event(state, event)
        append_event(events_path, event)
        try:
            atomic_write_json(state_path, next_state)
        except Exception as error:
            raise StateError(
                "event committed but snapshot update failed; rerun the same command_id to recover"
            ) from error
        emit_state(next_state, prefix=f"recorded event {event['seq']}: {event_type}")


def repository_json(value: str) -> dict[str, Any]:
    try:
        repositories = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"invalid repository JSON: {error}") from error
    try:
        mapping = require_object(repositories, "repositories")
        for name, repository in mapping.items():
            require_identifier(name, "repository name")
            validate_repository(repository, f"repository {name}")
    except StateError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    return mapping


def command_init(args: argparse.Namespace) -> None:
    runtime_dir = Path(args.runtime_dir).resolve()
    state_path, events_path, lock_path = runtime_paths(runtime_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(lock_path):
        if events_path.exists():
            events = read_events(events_path)
            state = replay(events)
            if len(events) != 1 or events[0]["type"] != "workflow.started" or state is None:
                raise StateError("runtime is already initialized")
            started = events[0]["data"]
            run = require_object(started.get("run"), "workflow.started run")
            same_request = (
                events[0]["command_id"] == args.command_id
                and run.get("change") == args.change
                and run.get("workflow") == args.workflow
                and run.get("policy_revision") == args.policy_revision
                and started.get("repositories") == args.repository_json
                and (args.run_id is None or run.get("id") == args.run_id)
            )
            if not same_request:
                raise StateError("runtime is already initialized with different inputs")
            atomic_write_json(state_path, state)
            emit_state(state, prefix="idempotent init replay")
            return
        if state_path.exists():
            raise StateError("state.json exists without an event journal")
        run = {
            "id": args.run_id or f"{args.change}-{uuid.uuid4().hex[:8]}",
            "change": require_identifier(args.change, "change"),
            "workflow": require_identifier(args.workflow, "workflow"),
            "policy_revision": require_string(args.policy_revision, "policy_revision"),
            "created_at": utc_now(),
        }
        data = {"run": run, "repositories": args.repository_json}
        event = make_event(1, "workflow.started", args.command_id, data, args.actor_kind, args.actor_id, None)
        state = apply_event(None, event)
        append_event(events_path, event)
        atomic_write_json(state_path, state)
        emit_state(state, prefix="initialized workflow state v2")


def safe_legacy_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._+-]+", "-", value.strip("/")).strip("-._+")
    return cleaned[:80] or fallback


def normalized_legacy_state(legacy: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    change = legacy.get("change") or legacy.get("fix_name") or Path(args.runtime_dir).name
    change = safe_legacy_name(str(change), "legacy-change")
    run = {
        "id": f"{change}-migrated",
        "change": change,
        "workflow": args.workflow,
        "policy_revision": args.policy_revision,
        "created_at": utc_now(),
        "migrated_from": {"schema_version": 1},
    }
    repositories: dict[str, Any] = {}
    if isinstance(legacy.get("repositories"), dict):
        for name, value in legacy["repositories"].items():
            if isinstance(value, dict):
                repository = {
                    field: str(value[field])
                    for field in ("root", "worktree", "branch", "base_sha")
                    if value.get(field)
                }
                if repository:
                    repositories[safe_legacy_name(str(name), "repository")] = repository
    worktrees = legacy.get("worktrees") if isinstance(legacy.get("worktrees"), dict) else {}
    branches = legacy.get("branches") if isinstance(legacy.get("branches"), dict) else {}
    bases = legacy.get("bases") if isinstance(legacy.get("bases"), dict) else {}
    for name in sorted(set(worktrees) | set(branches) | set(bases)):
        repository = repositories.setdefault(safe_legacy_name(str(name), "repository"), {})
        if worktrees.get(name):
            repository["worktree"] = str(worktrees[name])
        if branches.get(name):
            repository["branch"] = str(branches[name])
        if bases.get(name):
            repository["base_sha"] = str(bases[name])

    phase = str(legacy.get("phase") or "legacy")
    checkpoint = legacy.get("background_checkpoint")
    if phase == "background_work_active" and isinstance(checkpoint, dict):
        phase = str(checkpoint.get("phase") or checkpoint.get("wave") or "legacy")
    phase = safe_legacy_name(phase, "legacy")
    stage = {"status": "in_progress", "entries": 1, "gates": {}, "checks": {}, "tasks": {}}
    approvals = legacy.get("approvals") if isinstance(legacy.get("approvals"), dict) else {}
    for gate_name, approval in approvals.items():
        status = "approved" if approval is True else "pending"
        if isinstance(approval, str) and approval in {"approved", "rejected", "waived", "pending"}:
            status = approval
        if isinstance(approval, dict):
            status = str(approval.get("status") or status)
            if status not in {"approved", "rejected", "waived", "pending"}:
                status = "pending"
        gate = {
            "status": status,
            "reason": "migrated legacy approval",
            "entry": 1,
            "requested_event": 0,
        }
        if status != "pending":
            gate.update({"decided_by": "legacy", "decision_event": 0})
        stage["gates"][safe_legacy_name(str(gate_name), "legacy-gate")] = gate

    spawned: list[str] = []
    threads = legacy.get("agent_threads")
    if isinstance(threads, dict) and isinstance(threads.get("spawned"), list):
        spawned.extend(str(item) for item in threads["spawned"])
    for key in ("running", "completed"):
        if isinstance(legacy.get(key), list):
            spawned.extend(str(item) for item in legacy[key])
        if isinstance(threads, dict) and isinstance(threads.get(key), list):
            spawned.extend(str(item) for item in threads[key])
    spawned = list(dict.fromkeys(spawned))
    running = set(str(item) for item in legacy.get("running", []) if isinstance(item, str))
    completed = set(str(item) for item in legacy.get("completed", []) if isinstance(item, str))
    if isinstance(threads, dict):
        running.update(str(item) for item in threads.get("running", []) if isinstance(item, str))
        completed.update(str(item) for item in threads.get("completed", []) if isinstance(item, str))
    role_by_host = {}
    if isinstance(legacy.get("running_agents"), dict):
        role_by_host = {str(host): str(role) for role, host in legacy["running_agents"].items()}
    host_to_attempt: dict[str, str] = {}
    for ordinal, host in enumerate(spawned, start=1):
        task_name = safe_legacy_name(role_by_host.get(host, f"legacy-agent-{ordinal}"), f"legacy-agent-{ordinal}")
        while task_name in stage["tasks"]:
            task_name = f"{task_name}-{ordinal}"
        attempt_id = f"legacy-attempt-{ordinal}"
        status = "succeeded" if host in completed else "running" if host in running else "cancelled"
        attempt: dict[str, Any] = {
            "id": attempt_id,
            "ordinal": 1,
            "status": status,
            "agent": {"role": task_name, "host_thread_id": host},
            "stage_entry": 1,
            "started_event": 0,
            "late_results": [],
        }
        if status != "running":
            attempt["result"] = {"outcome": status, "recorded_event": 0, "verdict": "migrated"}
        stage["tasks"][task_name] = {
            "role": task_name,
            "status": status,
            "created_entry": 1,
            "created_event": 0,
            "attempts": [attempt],
        }
        host_to_attempt[host] = attempt_id

    stages = {phase: stage}
    counter_fields = {
        "review": ("review_attempts", "review_cycle"),
        "remediation": ("remediation_attempts", "remediation_cycle"),
        "acceptance": ("acceptance_attempts", "acceptance_cycle"),
    }
    for stage_name, fields in counter_fields.items():
        count = max(
            [int(legacy[field]) for field in fields if isinstance(legacy.get(field), int)] or [0]
        )
        if count and stage_name not in stages:
            stages[stage_name] = {
                "status": "succeeded",
                "entries": count,
                "gates": {},
                "checks": {},
                "tasks": {},
            }

    artifacts: dict[str, Any] = {}
    legacy_artifacts = legacy.get("artifacts") if isinstance(legacy.get("artifacts"), dict) else {}
    for name, value in legacy_artifacts.items():
        if not isinstance(value, dict):
            continue
        path = value.get("path") or value.get("artifact")
        digest = value.get("sha256") or value.get("hash")
        if path and isinstance(digest, str) and HASH_RE.fullmatch(digest):
            artifacts[safe_legacy_name(str(name), "legacy-artifact")] = {
                "path": str(path),
                "sha256": digest,
                "kind": "legacy",
                "recorded_event": 0,
            }

    execution_status = legacy.get("execution_status")
    join_hosts = legacy.get("join") if isinstance(legacy.get("join"), list) else []
    attempt_ids = [host_to_attempt[host] for host in join_hosts if host in host_to_attempt]
    if execution_status in {"foreground_join", "background_detached"} and attempt_ids:
        control: dict[str, Any] = {
            "kind": "waiting_agents",
            "join": "foreground" if execution_status == "foreground_join" else "detached",
            "attempt_ids": attempt_ids,
            "reason_code": safe_legacy_name(str(legacy.get("next_action") or "legacy_join"), "legacy_join"),
        }
        if control["join"] == "detached":
            control["detach_reason"] = safe_legacy_name(
                str(legacy.get("detach_reason") or "legacy_wait_budget"), "legacy_wait_budget"
            )
        stage["status"] = "waiting"
    else:
        control = {
            "kind": "ready",
            "reason_code": safe_legacy_name(str(legacy.get("next_action") or "legacy_migration"), "legacy_migration"),
        }
    blockers: dict[str, Any] = {}
    legacy_blockers = legacy.get("blockers")
    if isinstance(legacy_blockers, list):
        for index, value in enumerate(legacy_blockers, start=1):
            blockers[f"legacy-blocker-{index}"] = {
                "reason": str(value),
                "required_action": "review migrated blocker",
                "recorded_event": 0,
            }
    state = {
        "schema_version": STATE_SCHEMA_VERSION,
        "revision": 1,
        "run": run,
        "repositories": repositories,
        "workflow": {"current_stage": phase, "stages": stages},
        "control": control,
        "artifacts": artifacts,
        "blockers": blockers,
        "last_event": {"seq": 1, "id": "migration-placeholder"},
    }
    return state


def command_migrate(args: argparse.Namespace) -> None:
    runtime_dir = Path(args.runtime_dir).resolve()
    state_path, events_path, lock_path = runtime_paths(runtime_dir)
    with exclusive_lock(lock_path):
        if events_path.exists():
            events = read_events(events_path)
            state = replay(events)
            if len(events) != 1 or events[0]["type"] != "workflow.migrated_from_v1" or state is None:
                raise StateError("event journal is not an incomplete v1 migration")
            run = state["run"]
            if (
                events[0]["command_id"] != args.command_id
                or run["workflow"] != args.workflow
                or run["policy_revision"] != args.policy_revision
            ):
                raise StateError("migration was already committed with different inputs")
            backup = runtime_dir / "state.v1.json"
            if not backup.exists():
                raise StateError("committed migration is missing state.v1.json")
            source_sha256 = hashlib.sha256(backup.read_bytes()).hexdigest()
            if events[0]["data"].get("source_sha256") != source_sha256:
                raise StateError("state.v1.json does not match the committed migration")
            atomic_write_json(state_path, state)
            emit_state(state, prefix=f"idempotent migration replay; backup: {backup}")
            return
        if not state_path.exists():
            raise StateError("legacy state.json does not exist")
        legacy = read_json(state_path)
        if legacy.get("schema_version") != 1:
            raise StateError("state.json is not schema_version 1")
        backup = runtime_dir / "state.v1.json"
        if backup.exists():
            if backup.read_bytes() != state_path.read_bytes():
                raise StateError("existing state.v1.json does not match legacy state.json")
        else:
            shutil.copy2(state_path, backup)
        with backup.open("rb") as handle:
            os.fsync(handle.fileno())
        fsync_directory(runtime_dir)
        normalized = normalized_legacy_state(legacy, args)
        source_sha256 = hashlib.sha256(state_path.read_bytes()).hexdigest()
        event = make_event(
            1,
            "workflow.migrated_from_v1",
            args.command_id,
            {"source_sha256": source_sha256, "state": normalized},
            args.actor_kind,
            args.actor_id,
            None,
        )
        state = apply_event(None, event)
        append_event(events_path, event)
        atomic_write_json(state_path, state)
        emit_state(state, prefix=f"migrated v1 state; backup: {backup}")


def command_validate(args: argparse.Namespace) -> None:
    runtime_dir = Path(args.runtime_dir).resolve()
    events, state, status = load_runtime(runtime_dir)
    if not events and status == "legacy_v1":
        raise StateError("legacy schema v1 requires migrate-v1")
    if state is None:
        raise StateError("workflow has no event history")
    if status != "valid":
        raise StateError(f"snapshot status is {status}")
    print(f"OK: schema v2, revision {state['revision']}, {len(events)} events")


def command_status(args: argparse.Namespace) -> None:
    _, state, status = load_runtime(Path(args.runtime_dir).resolve())
    payload = {"snapshot_status": status, "state": state}
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    print()


def command_history(args: argparse.Namespace) -> None:
    events = read_events(runtime_paths(Path(args.runtime_dir).resolve())[1])
    for event in events:
        if args.type and event["type"] != args.type:
            continue
        print(canonical_json(event))


def command_repair(args: argparse.Namespace) -> None:
    runtime_dir = Path(args.runtime_dir).resolve()
    state_path, events_path, lock_path = runtime_paths(runtime_dir)
    with exclusive_lock(lock_path):
        content = events_path.read_bytes()
        if content and not content.endswith(b"\n"):
            boundary = content.rfind(b"\n") + 1
            corrupt_tail = content[boundary:]
            backup = runtime_dir / f"events.corrupt-tail-{uuid.uuid4().hex[:8]}.bin"
            with backup.open("xb") as backup_file:
                backup_file.write(corrupt_tail)
                backup_file.flush()
                os.fsync(backup_file.fileno())
            fsync_directory(runtime_dir)
            with events_path.open("r+b") as handle:
                handle.truncate(boundary)
                handle.flush()
                os.fsync(handle.fileno())
            print(f"preserved incomplete tail at {backup}", file=sys.stderr)
        events = read_events(events_path)
        state = replay(events)
        if state is None:
            raise StateError("cannot repair an empty event history")
        atomic_write_json(state_path, state)
        emit_state(state, prefix="rebuilt state.json from events.jsonl")


def add_mutation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--runtime-dir", required=True)
    parser.add_argument("--expected-revision", required=True, type=int)
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--actor-kind", default="orchestrator")
    parser.add_argument("--actor-id", default="root")
    parser.add_argument("--causation-id")


def transition_handler(event_type: str, fields: tuple[str, ...]):
    def handler(args: argparse.Namespace) -> None:
        data = {field: getattr(args, field) for field in fields if getattr(args, field) is not None}
        commit_transition(args, event_type, data)

    return handler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create a new v2 workflow journal")
    init.add_argument("--runtime-dir", required=True)
    init.add_argument("--change", required=True)
    init.add_argument("--workflow", required=True)
    init.add_argument("--policy-revision", required=True)
    init.add_argument("--run-id")
    init.add_argument("--repository-json", type=repository_json, default={})
    init.add_argument("--command-id", default="workflow-init")
    init.add_argument("--actor-kind", default="orchestrator")
    init.add_argument("--actor-id", default="root")
    init.set_defaults(handler=command_init)

    migrate = commands.add_parser("migrate-v1", help="migrate a legacy state.json")
    migrate.add_argument("--runtime-dir", required=True)
    migrate.add_argument("--workflow", required=True)
    migrate.add_argument("--policy-revision", required=True)
    migrate.add_argument("--command-id", default="migrate-v1")
    migrate.add_argument("--actor-kind", default="orchestrator")
    migrate.add_argument("--actor-id", default="root")
    migrate.set_defaults(handler=command_migrate)

    validate = commands.add_parser("validate", help="validate journal and exact projection")
    validate.add_argument("--runtime-dir", required=True)
    validate.set_defaults(handler=command_validate)
    status = commands.add_parser("status", help="show projected state and snapshot health")
    status.add_argument("--runtime-dir", required=True)
    status.set_defaults(handler=command_status)
    history = commands.add_parser("history", help="print semantic events as JSONL")
    history.add_argument("--runtime-dir", required=True)
    history.add_argument("--type")
    history.set_defaults(handler=command_history)
    repair = commands.add_parser("repair", help="preserve a partial tail and rebuild projection")
    repair.add_argument("--runtime-dir", required=True)
    repair.set_defaults(handler=command_repair)

    definitions: list[tuple[str, str, tuple[tuple[str, dict[str, Any]], ...], tuple[str, ...]]] = [
        ("enter-stage", "stage.entered", (("stage", {"required": True}),), ("stage",)),
        (
            "complete-stage",
            "stage.completed",
            (("stage", {"required": True}), ("outcome", {"required": True, "choices": sorted(TERMINAL_STAGES)})),
            ("stage", "outcome"),
        ),
        (
            "request-gate",
            "gate.requested",
            (("stage", {"required": True}), ("gate", {"required": True}), ("reason", {"required": True})),
            ("stage", "gate", "reason"),
        ),
        (
            "decide-gate",
            "gate.decided",
            (
                ("stage", {"required": True}),
                ("gate", {"required": True}),
                ("decision", {"required": True, "choices": ["approved", "rejected", "waived"]}),
                ("decided_by", {"required": True}),
                ("reason", {}),
            ),
            ("stage", "gate", "decision", "decided_by", "reason"),
        ),
        (
            "create-task",
            "task.created",
            (("stage", {"required": True}), ("task", {"required": True}), ("role", {"required": True})),
            ("stage", "task", "role"),
        ),
        (
            "start-attempt",
            "agent.attempt.started",
            (
                ("stage", {"required": True}),
                ("task", {"required": True}),
                ("attempt_id", {"required": True}),
                ("host_thread_id", {"required": True}),
                ("input_fingerprint", {}),
            ),
            ("stage", "task", "attempt_id", "host_thread_id", "input_fingerprint"),
        ),
        (
            "finish-attempt",
            "agent.result.recorded",
            (
                ("stage", {"required": True}),
                ("task", {"required": True}),
                ("attempt_id", {"required": True}),
                ("outcome", {"required": True, "choices": sorted(TERMINAL_ATTEMPTS)}),
                ("verdict", {}),
                ("artifact", {}),
                ("sha256", {}),
            ),
            ("stage", "task", "attempt_id", "outcome", "verdict", "artifact", "sha256"),
        ),
        (
            "record-late-result",
            "agent.late_result.recorded",
            (("attempt_id", {"required": True}), ("verdict", {}), ("artifact", {}), ("sha256", {})),
            ("attempt_id", "verdict", "artifact", "sha256"),
        ),
        (
            "record-check",
            "check.recorded",
            (
                ("stage", {"required": True}),
                ("check", {"required": True}),
                ("status", {"required": True, "choices": ["passed", "failed", "unknown"]}),
                ("evidence", {}),
                ("sha256", {}),
            ),
            ("stage", "check", "status", "evidence", "sha256"),
        ),
        (
            "record-artifact",
            "artifact.recorded",
            (
                ("name", {"required": True}),
                ("path", {"required": True}),
                ("sha256", {"required": True}),
                ("kind", {}),
                ("stage", {}),
            ),
            ("name", "path", "sha256", "kind", "stage"),
        ),
        (
            "wait-user",
            "workflow.waiting_for_user",
            (),
            ("gate_ids", "reason_code"),
        ),
        (
            "block",
            "workflow.blocked",
            (
                ("blocker_id", {"required": True}),
                ("reason", {"required": True}),
                ("required_action", {"required": True}),
            ),
            ("blocker_id", "reason", "required_action"),
        ),
        (
            "resolve-blocker",
            "workflow.blocker_resolved",
            (("blocker_id", {"required": True}),),
            ("blocker_id",),
        ),
        (
            "complete",
            "workflow.completed",
            (("outcome", {"required": True, "choices": ["completed", "aborted"]}),),
            ("outcome",),
        ),
    ]
    for command_name, event_type, options, fields in definitions:
        command = commands.add_parser(command_name)
        add_mutation_options(command)
        for name, kwargs in options:
            command.add_argument(f"--{name.replace('_', '-')}", dest=name, **kwargs)
        command.set_defaults(handler=transition_handler(event_type, fields))

    wait_user = commands.choices["wait-user"]
    wait_user.add_argument("--gate-id", dest="gate_ids", action="append", required=True)
    wait_user.add_argument("--reason-code", required=True)

    wait_agents = commands.add_parser("wait-agents")
    add_mutation_options(wait_agents)
    wait_agents.add_argument("--attempt-id", dest="attempt_ids", action="append", required=True)
    wait_agents.add_argument("--join", choices=["foreground", "detached"], required=True)
    wait_agents.add_argument("--reason-code", required=True)
    wait_agents.add_argument("--detach-reason")
    wait_agents.set_defaults(
        handler=transition_handler(
            "workflow.waiting_for_agents",
            ("attempt_ids", "join", "reason_code", "detach_reason"),
        )
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.handler(args)
    except (OSError, StateError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
