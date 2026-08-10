from __future__ import annotations

import importlib
import json
import os
import tempfile
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .events import validate_event
from .model import (
    EVENT_SCHEMA_VERSION,
    STATE_SCHEMA_VERSION,
    JsonObject,
    StateError,
    canonical_json,
    require_identifier,
    require_object,
    require_string,
    utc_now,
)
from .reducer import apply_event, replay
from .validation import validate_state

_LOCK_MODULE: Any = importlib.import_module("msvcrt" if os.name == "nt" else "fcntl")


@dataclass(frozen=True)
class EventContext:
    command_id: str
    actor_kind: str
    actor_id: str
    causation_id: str | None = None


@dataclass(frozen=True)
class MutationRequest:
    runtime_dir: Path
    expected_revision: int
    event_type: str
    data: JsonObject
    context: EventContext


def runtime_paths(runtime_dir: Path) -> tuple[Path, Path, Path]:
    return runtime_dir / "state.json", runtime_dir / "events.jsonl", runtime_dir / ".state.lock"


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if os.name == "nt":
            with windows_lock(descriptor):
                yield
        else:
            with posix_lock(descriptor):
                yield
    finally:
        os.close(descriptor)


@contextmanager
def windows_lock(descriptor: int) -> Iterator[None]:
    if os.fstat(descriptor).st_size == 0:
        os.write(descriptor, b"0")
    os.lseek(descriptor, 0, os.SEEK_SET)
    _LOCK_MODULE.locking(descriptor, _LOCK_MODULE.LK_LOCK, 1)
    try:
        yield
    finally:
        os.lseek(descriptor, 0, os.SEEK_SET)
        _LOCK_MODULE.locking(descriptor, _LOCK_MODULE.LK_UNLCK, 1)


@contextmanager
def posix_lock(descriptor: int) -> Iterator[None]:
    _LOCK_MODULE.flock(descriptor, _LOCK_MODULE.LOCK_EX)
    try:
        yield
    finally:
        _LOCK_MODULE.flock(descriptor, _LOCK_MODULE.LOCK_UN)


def fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as temporary:
            json.dump(value, temporary, ensure_ascii=False, indent=2, sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        fsync_directory(path.parent)
    finally:
        temporary_path.unlink(missing_ok=True)


def append_event(path: Path, event: JsonObject) -> None:
    payload = (canonical_json(event) + "\n").encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        write_all(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise OSError("event append made no progress")
        offset += written


def read_json(path: Path) -> JsonObject:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StateError(f"{path}: invalid JSON: {error}") from error
    return require_object(value, str(path))


def read_events(path: Path) -> list[JsonObject]:
    try:
        content = path.read_bytes()
    except FileNotFoundError:
        return []
    if content and not content.endswith(b"\n"):
        raise StateError(f"{path}: incomplete final JSONL record; run repair")
    return parse_event_lines(path, content)


def parse_event_lines(path: Path, content: bytes) -> list[JsonObject]:
    events: list[JsonObject] = []
    command_ids: dict[str, str] = {}
    event_ids: set[str] = set()
    for index, raw_line in enumerate(content.splitlines(), start=1):
        event = parse_event_line(path, raw_line, index)
        require_unique_event(path, event, index, event_ids, command_ids)
        events.append(event)
    return events


def parse_event_line(path: Path, raw_line: bytes, index: int) -> JsonObject:
    if not raw_line.strip():
        raise StateError(f"{path}:{index}: blank records are not allowed")
    try:
        value = json.loads(raw_line)
    except json.JSONDecodeError as error:
        raise StateError(f"{path}:{index}: invalid JSON: {error}") from error
    return validate_event(value, index)


def require_unique_event(
    path: Path,
    event: JsonObject,
    index: int,
    event_ids: set[str],
    command_ids: dict[str, str],
) -> None:
    if event["id"] in event_ids:
        raise StateError(f"{path}:{index}: duplicate event id")
    event_ids.add(event["id"])
    fingerprint = event_fingerprint(event["type"], event["data"])
    if event["command_id"] in command_ids:
        if command_ids[event["command_id"]] != fingerprint:
            raise StateError(f"{path}:{index}: command_id was reused with different content")
        raise StateError(f"{path}:{index}: duplicate command_id")
    command_ids[event["command_id"]] = fingerprint


def event_fingerprint(event_type: str, data: JsonObject) -> str:
    return canonical_json({"type": event_type, "data": data})


def snapshot_status(path: Path, projected: JsonObject | None) -> str:
    if not path.exists():
        return "missing"
    try:
        snapshot = read_json(path)
    except StateError:
        return "diverged"
    schema_status = projection_schema_status(snapshot)
    if schema_status is not None:
        return schema_status
    try:
        validate_state(snapshot)
    except StateError:
        return "diverged"
    if projected is None:
        return "orphaned"
    status = "valid"
    if snapshot != projected:
        status = "stale" if snapshot["revision"] < projected["revision"] else "diverged"
    return status


def projection_schema_status(snapshot: JsonObject) -> str | None:
    version = snapshot.get("schema_version")
    if version == 1:
        return "legacy_v1"
    if (
        isinstance(version, int)
        and not isinstance(version, bool)
        and version != STATE_SCHEMA_VERSION
    ):
        return "unsupported_schema"
    return None


def require_repairable_projection(path: Path) -> None:
    if not path.exists():
        return
    try:
        snapshot = read_json(path)
    except StateError:
        return
    if projection_schema_status(snapshot) == "unsupported_schema":
        version = snapshot["schema_version"]
        raise StateError(
            f"state.json schema_version {version} is unsupported; "
            "required action: require-compatible-helper"
        )


def load_runtime(runtime_dir: Path) -> tuple[list[JsonObject], JsonObject | None, str]:
    state_path, events_path, _ = runtime_paths(runtime_dir)
    events = read_events(events_path)
    projected = replay(events)
    return events, projected, snapshot_status(state_path, projected)


def make_event(seq: int, event_type: str, data: JsonObject, context: EventContext) -> JsonObject:
    event: JsonObject = {
        "event_schema_version": EVENT_SCHEMA_VERSION,
        "seq": seq,
        "id": str(uuid.uuid4()),
        "type": event_type,
        "recorded_at": utc_now(),
        "actor": {
            "kind": require_identifier(context.actor_kind, "actor_kind"),
            "id": require_identifier(context.actor_id, "actor_id"),
        },
        "command_id": require_string(context.command_id, "command_id"),
        "data": data,
    }
    if context.causation_id:
        event["causation_id"] = context.causation_id
    return validate_event(event, seq)


def commit_transition(request: MutationRequest) -> JsonObject:
    request.runtime_dir.mkdir(parents=True, exist_ok=True)
    state_path, events_path, lock_path = runtime_paths(request.runtime_dir)
    with exclusive_lock(lock_path):
        events, state, status = load_runtime(request.runtime_dir)
        if state is None:
            raise StateError("workflow is not initialized")
        require_mutable_snapshot(status)
        replayed = idempotent_transition(events, state, status, state_path, request)
        if replayed is not None:
            return replayed
        if request.expected_revision != state["revision"]:
            raise StateError(
                f"revision conflict: expected {request.expected_revision}, current {state['revision']}"
            )
        event = make_event(state["revision"] + 1, request.event_type, request.data, request.context)
        next_state = apply_event(state, event)
        append_event(events_path, event)
        write_projection_after_commit(state_path, next_state)
        return next_state


def require_mutable_snapshot(status: str) -> None:
    if status == "unsupported_schema":
        raise StateError(
            "snapshot schema is unsupported; required action: require-compatible-helper"
        )
    if status in {"legacy_v1", "orphaned", "diverged"}:
        raise StateError(f"snapshot status {status}; validate or migrate before mutation")


def idempotent_transition(
    events: list[JsonObject],
    state: JsonObject,
    status: str,
    state_path: Path,
    request: MutationRequest,
) -> JsonObject | None:
    candidate = event_fingerprint(request.event_type, request.data)
    for event in events:
        if event["command_id"] != request.context.command_id:
            continue
        if event_fingerprint(event["type"], event["data"]) != candidate:
            raise StateError("command_id already exists with different content")
        if status != "valid":
            atomic_write_json(state_path, state)
        return state
    return None


def write_projection_after_commit(path: Path, state: JsonObject) -> None:
    try:
        atomic_write_json(path, state)
    # The journal is already durable, so every ordinary projection failure must
    # become the same idempotent-retry signal without implying the append failed.
    except Exception as error:
        raise StateError(
            "event committed but snapshot update failed; rerun the same command_id to recover"
        ) from error
