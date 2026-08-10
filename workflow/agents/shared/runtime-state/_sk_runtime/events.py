from __future__ import annotations

from dataclasses import dataclass

from .model import (
    EVENT_SCHEMA_VERSION,
    JsonObject,
    StateError,
    UnsupportedEventSchemaError,
    require_boolean,
    require_fields,
    require_hash,
    require_identifier,
    require_integer,
    require_object,
    require_string,
    require_string_list,
    require_timestamp,
)


@dataclass(frozen=True)
class EventSpec:
    required: frozenset[str]
    optional: frozenset[str] = frozenset()


EVENT_SPECS = {
    "workflow.started": EventSpec(frozenset({"run", "repositories"})),
    "workflow.migrated_from_v1": EventSpec(frozenset({"source_sha256", "state"})),
    "stage.entered": EventSpec(frozenset({"stage"})),
    "stage.completed": EventSpec(frozenset({"stage", "outcome"})),
    "gate.requested": EventSpec(frozenset({"stage", "gate", "reason"})),
    "gate.decided": EventSpec(
        frozenset({"stage", "gate", "decision", "decided_by"}), frozenset({"reason"})
    ),
    "task.created": EventSpec(frozenset({"stage", "task", "role"}), frozenset({"required"})),
    "agent.attempt.started": EventSpec(
        frozenset({"stage", "task", "attempt_id", "host_thread_id"}),
        frozenset({"input_fingerprint"}),
    ),
    "agent.result.recorded": EventSpec(
        frozenset({"stage", "task", "attempt_id", "outcome"}),
        frozenset({"verdict", "artifact", "sha256"}),
    ),
    "agent.late_result.recorded": EventSpec(
        frozenset({"attempt_id"}), frozenset({"verdict", "artifact", "sha256"})
    ),
    "check.recorded": EventSpec(
        frozenset({"stage", "check", "status"}),
        frozenset({"required", "evidence", "sha256"}),
    ),
    "artifact.recorded": EventSpec(
        frozenset({"name", "path", "sha256"}), frozenset({"kind", "stage"})
    ),
    "workflow.waiting_for_agents": EventSpec(
        frozenset({"attempt_ids", "join", "reason_code"}), frozenset({"detach_reason"})
    ),
    "workflow.waiting_for_user": EventSpec(frozenset({"gate_ids", "reason_code"})),
    "workflow.blocked": EventSpec(frozenset({"blocker_id", "reason", "required_action"})),
    "workflow.blocker_resolved": EventSpec(frozenset({"blocker_id"})),
    "workflow.completed": EventSpec(frozenset({"outcome"})),
    "review.lease.granted": EventSpec(
        frozenset({"lease_id", "stage", "holder_attempt_id", "holder_actor_id"})
    ),
    "review.lease.released": EventSpec(frozenset({"lease_id"})),
}
EVENT_TYPES = frozenset(EVENT_SPECS)

IDENTIFIER_FIELDS = frozenset(
    {
        "stage",
        "outcome",
        "gate",
        "decision",
        "task",
        "role",
        "attempt_id",
        "check",
        "status",
        "name",
        "kind",
        "join",
        "reason_code",
        "detach_reason",
        "blocker_id",
        "lease_id",
        "holder_attempt_id",
        "holder_actor_id",
    }
)
STRING_FIELDS = frozenset(
    {
        "reason",
        "decided_by",
        "host_thread_id",
        "verdict",
        "artifact",
        "evidence",
        "path",
        "required_action",
    }
)
HASH_FIELDS = frozenset({"source_sha256", "input_fingerprint", "sha256"})
OBJECT_FIELDS = frozenset({"run", "repositories", "state"})
ENUMS = {
    ("stage.completed", "outcome"): {"succeeded", "failed", "skipped"},
    ("gate.decided", "decision"): {"approved", "rejected", "waived"},
    ("agent.result.recorded", "outcome"): {"succeeded", "failed", "blocked", "cancelled"},
    ("check.recorded", "status"): {"passed", "failed", "unknown"},
    ("workflow.waiting_for_agents", "join"): {"foreground", "detached"},
    ("workflow.completed", "outcome"): {"completed", "aborted"},
}


def validate_data_value(event_type: str, field: str, value: object) -> None:
    label = f"{event_type} data.{field}"
    if field in {"attempt_ids", "gate_ids"}:
        validate_reference_list(field, value, label)
        return
    if field in IDENTIFIER_FIELDS:
        checked: object = require_identifier(value, label)
    elif field in STRING_FIELDS:
        checked = require_string(value, label)
    elif field in HASH_FIELDS:
        checked = require_hash(value, label)
    elif field in OBJECT_FIELDS:
        checked = require_object(value, label)
    elif field == "required":
        checked = require_boolean(value, label)
    else:
        raise StateError(f"{label} has no validator")

    allowed_values = ENUMS.get((event_type, field))
    if allowed_values is not None and checked not in allowed_values:
        raise StateError(f"{label} has an unsupported value")


def validate_reference_list(field: str, value: object, label: str) -> None:
    checked = require_string_list(value, label, nonempty=True)
    if field == "gate_ids":
        validate_gate_references(checked)
        return
    for item in checked:
        require_identifier(item, f"{label} item")


def validate_gate_references(value: object) -> None:
    for gate_ref in value if isinstance(value, list) else []:
        parts = gate_ref.split("/")
        if len(parts) != 2:
            raise StateError("workflow.waiting_for_user data.gate_ids has an invalid reference")
        require_identifier(parts[0], "gate reference stage")
        require_identifier(parts[1], "gate reference name")


def validate_event_data(event_type: str, value: object) -> JsonObject:
    data = require_object(value, f"{event_type} data")
    spec = EVENT_SPECS[event_type]
    require_fields(data, spec.required, spec.required | spec.optional, f"{event_type} data")
    for field, field_value in data.items():
        validate_data_value(event_type, field, field_value)

    join = data.get("join")
    if join == "detached" and "detach_reason" not in data:
        raise StateError("detached waits require detach_reason")
    if join == "foreground" and "detach_reason" in data:
        raise StateError("foreground waits must not have detach_reason")
    return data


def validate_event(event: object, expected_seq: int) -> JsonObject:
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
    require_fields(item, required, required | {"causation_id"}, f"event {expected_seq}")
    version = require_integer(item["event_schema_version"], f"event {expected_seq} schema version")
    if version != EVENT_SCHEMA_VERSION:
        raise UnsupportedEventSchemaError(expected_seq, version)
    sequence = require_integer(item["seq"], f"event {expected_seq} sequence", minimum=1)
    if sequence != expected_seq:
        raise StateError(f"event sequence gap: expected {expected_seq}, got {item['seq']!r}")

    require_identifier(item["id"], f"event {expected_seq} id")
    event_type = require_identifier(item["type"], f"event {expected_seq} type")
    if event_type not in EVENT_TYPES:
        raise StateError(f"event {expected_seq} has unknown type {event_type!r}")
    require_timestamp(item["recorded_at"], f"event {expected_seq} recorded_at")
    validate_actor(item["actor"], expected_seq)
    require_string(item["command_id"], f"event {expected_seq} command_id")
    validate_event_data(event_type, item["data"])
    if "causation_id" in item:
        require_identifier(item["causation_id"], f"event {expected_seq} causation_id")
    return item


def validate_actor(value: object, expected_seq: int) -> None:
    actor = require_object(value, f"event {expected_seq} actor")
    require_fields(actor, {"kind", "id"}, {"kind", "id"}, f"event {expected_seq} actor")
    require_identifier(actor["kind"], f"event {expected_seq} actor kind")
    require_identifier(actor["id"], f"event {expected_seq} actor id")
