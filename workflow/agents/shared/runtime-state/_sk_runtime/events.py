from __future__ import annotations

from dataclasses import dataclass

from .model import (
    EVENT_SCHEMA_VERSION,
    LEGACY_EVENT_SCHEMA_VERSION,
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
    "workflow.started": EventSpec(frozenset({"run", "repositories", "charter"})),
    "workflow.migrated_from_v1": EventSpec(frozenset({"source_sha256", "state"})),
    "workflow.migrated_from_v2": EventSpec(frozenset({"source_sha256", "state"})),
    "charter.authorization_changed": EventSpec(
        frozenset({"authorization", "source"}), frozenset({"reason"})
    ),
    "charter.route_escalated": EventSpec(frozenset({"route", "assurance", "reason"})),
    "charter.scope_changed": EventSpec(frozenset({"scope_sha256", "authority_ref", "reason"})),
    "charter.workspace_resolved": EventSpec(frozenset({"resolved"}), frozenset({"path", "reason"})),
    "charter.destination_changed": EventSpec(
        frozenset({"kind", "source"}), frozenset({"target", "reason"})
    ),
    "stage.entered": EventSpec(frozenset({"stage"})),
    "stage.completed": EventSpec(frozenset({"stage", "outcome"})),
    "gate.requested": EventSpec(frozenset({"stage", "gate", "reason", "kind", "reason_code"})),
    "gate.decided": EventSpec(
        frozenset({"stage", "gate", "decision", "decided_by", "decision_source"}),
        frozenset({"reason"}),
    ),
    "task.created": EventSpec(
        frozenset({"stage", "task", "role"}),
        frozenset({"required", "purpose", "members"}),
    ),
    "agent.attempt.started": EventSpec(
        frozenset({"stage", "task", "attempt_id", "host_thread_id", "input_fingerprint"}),
    ),
    "agent.result.recorded": EventSpec(
        frozenset({"stage", "task", "attempt_id", "outcome", "input_fingerprint"}),
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
    "workflow.blocked": EventSpec(
        frozenset({"blocker_id", "reason_code", "reason", "required_action"})
    ),
    "workflow.blocker_resolved": EventSpec(frozenset({"blocker_id"})),
    "workflow.completed": EventSpec(frozenset({"outcome"})),
    "terminal.recorded": EventSpec(
        frozenset({"kind", "outcome"}), frozenset({"target", "evidence"})
    ),
    "review.lease.granted": EventSpec(
        frozenset({"lease_id", "stage", "holder_attempt_id", "holder_actor_id"})
    ),
    "review.lease.released": EventSpec(frozenset({"lease_id"}), frozenset({"reason"})),
}
EVENT_TYPES = frozenset(EVENT_SPECS)

LEGACY_EVENT_SPECS = {
    "workflow.started": EventSpec(frozenset({"run", "repositories"})),
    "workflow.migrated_from_v1": EventSpec(frozenset({"source_sha256", "state"})),
    "stage.entered": EVENT_SPECS["stage.entered"],
    "stage.completed": EVENT_SPECS["stage.completed"],
    "gate.requested": EventSpec(frozenset({"stage", "gate", "reason"})),
    "gate.decided": EventSpec(
        frozenset({"stage", "gate", "decision", "decided_by"}), frozenset({"reason"})
    ),
    "task.created": EVENT_SPECS["task.created"],
    "agent.attempt.started": EventSpec(
        frozenset({"stage", "task", "attempt_id", "host_thread_id"}),
        frozenset({"input_fingerprint"}),
    ),
    "agent.result.recorded": EventSpec(
        frozenset({"stage", "task", "attempt_id", "outcome"}),
        frozenset({"verdict", "artifact", "sha256"}),
    ),
    "agent.late_result.recorded": EVENT_SPECS["agent.late_result.recorded"],
    "check.recorded": EVENT_SPECS["check.recorded"],
    "artifact.recorded": EVENT_SPECS["artifact.recorded"],
    "workflow.waiting_for_agents": EVENT_SPECS["workflow.waiting_for_agents"],
    "workflow.waiting_for_user": EVENT_SPECS["workflow.waiting_for_user"],
    "workflow.blocked": EventSpec(frozenset({"blocker_id", "reason", "required_action"})),
    "workflow.blocker_resolved": EVENT_SPECS["workflow.blocker_resolved"],
    "workflow.completed": EVENT_SPECS["workflow.completed"],
    "review.lease.granted": EVENT_SPECS["review.lease.granted"],
    "review.lease.released": EVENT_SPECS["review.lease.released"],
}

IDENTIFIER_FIELDS = frozenset(
    {
        "stage",
        "outcome",
        "gate",
        "decision",
        "task",
        "role",
        "attempt_id",
        "purpose",
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
        "authorization",
        "source",
        "route",
        "assurance",
        "resolved",
        "decision_source",
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
        "authority_ref",
        "target",
    }
)
HASH_FIELDS = frozenset({"source_sha256", "input_fingerprint", "sha256", "scope_sha256"})
OBJECT_FIELDS = frozenset({"run", "repositories", "state", "charter"})
ENUMS = {
    ("stage.completed", "outcome"): {"succeeded", "failed", "skipped"},
    ("gate.decided", "decision"): {"approved", "rejected", "waived"},
    ("agent.result.recorded", "outcome"): {"succeeded", "failed", "blocked", "cancelled"},
    ("task.created", "purpose"): {"implementation", "review", "remediation", "acceptance"},
    ("check.recorded", "status"): {"passed", "failed", "unknown"},
    ("workflow.waiting_for_agents", "join"): {"foreground", "detached"},
    ("workflow.completed", "outcome"): {"completed", "aborted"},
    ("charter.authorization_changed", "authorization"): {"manual", "checkpoints", "yolo"},
    ("charter.authorization_changed", "source"): {"user", "policy", "repository"},
    ("charter.route_escalated", "route"): {"quick", "full"},
    ("charter.route_escalated", "assurance"): {"standard", "elevated"},
    ("charter.workspace_resolved", "resolved"): {"current", "worktree"},
    ("charter.destination_changed", "kind"): {"local", "commit", "pr", "merge", "deploy"},
    ("charter.destination_changed", "source"): {"user", "policy", "repository"},
    ("gate.requested", "kind"): {
        "authority_decision",
        "sensitive_action",
        "terminal_action",
        "ceremony",
    },
    ("gate.decided", "decision_source"): {"user", "policy", "repository"},
    ("terminal.recorded", "kind"): {"local", "commit", "pr", "merge", "deploy"},
    ("terminal.recorded", "outcome"): {"succeeded", "failed", "skipped"},
}


def validate_data_value(event_type: str, field: str, value: object) -> None:
    label = f"{event_type} data.{field}"
    if field == "members":
        validate_batch_members(value, label)
        return
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


def validate_batch_members(value: object, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise StateError(f"{label} must be a non-empty array")
    member_ids: list[str] = []
    for index, value_member in enumerate(value, start=1):
        member = require_object(value_member, f"{label}[{index}]")
        required = {"id", "role", "host_thread_id", "input_fingerprint"}
        require_fields(member, required, required | {"required"}, f"{label}[{index}]")
        member_ids.append(require_identifier(member["id"], f"{label}[{index}].id"))
        require_identifier(member["role"], f"{label}[{index}].role")
        require_string(member["host_thread_id"], f"{label}[{index}].host_thread_id")
        require_hash(member["input_fingerprint"], f"{label}[{index}].input_fingerprint")
        if "required" in member:
            require_boolean(member["required"], f"{label}[{index}].required")
    if len(member_ids) != len(set(member_ids)):
        raise StateError(f"{label} contains duplicate member IDs")


def validate_gate_references(value: object) -> None:
    for gate_ref in value if isinstance(value, list) else []:
        parts = gate_ref.split("/")
        if len(parts) != 2:
            raise StateError("workflow.waiting_for_user data.gate_ids has an invalid reference")
        require_identifier(parts[0], "gate reference stage")
        require_identifier(parts[1], "gate reference name")


def validate_event_data(version: int, event_type: str, value: object) -> JsonObject:
    data = require_object(value, f"{event_type} data")
    specs = LEGACY_EVENT_SPECS if version == LEGACY_EVENT_SCHEMA_VERSION else EVENT_SPECS
    spec = specs[event_type]
    require_fields(data, spec.required, spec.required | spec.optional, f"{event_type} data")
    for field, field_value in data.items():
        validate_data_value(event_type, field, field_value)

    join = data.get("join")
    if event_type == "task.created" and ("members" in data) != ("purpose" in data):
        raise StateError("batched task creation requires both purpose and members")
    if join == "detached" and "detach_reason" not in data:
        raise StateError("detached waits require detach_reason")
    if join == "foreground" and "detach_reason" in data:
        raise StateError("foreground waits must not have detach_reason")
    if (
        version == EVENT_SCHEMA_VERSION
        and event_type == "agent.result.recorded"
        and data["outcome"] == "succeeded"
        and "sha256" not in data
    ):
        raise StateError(f"{event_type} successful result requires sha256")
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
    if version not in {LEGACY_EVENT_SCHEMA_VERSION, EVENT_SCHEMA_VERSION}:
        raise UnsupportedEventSchemaError(expected_seq, version)
    sequence = require_integer(item["seq"], f"event {expected_seq} sequence", minimum=1)
    if sequence != expected_seq:
        raise StateError(f"event sequence gap: expected {expected_seq}, got {item['seq']!r}")

    require_identifier(item["id"], f"event {expected_seq} id")
    event_type = require_identifier(item["type"], f"event {expected_seq} type")
    event_types = LEGACY_EVENT_SPECS if version == LEGACY_EVENT_SCHEMA_VERSION else EVENT_SPECS
    if event_type not in event_types:
        raise StateError(f"event {expected_seq} has unknown type {event_type!r}")
    require_timestamp(item["recorded_at"], f"event {expected_seq} recorded_at")
    validate_actor(item["actor"], expected_seq)
    require_string(item["command_id"], f"event {expected_seq} command_id")
    validate_event_data(version, event_type, item["data"])
    if "causation_id" in item:
        require_identifier(item["causation_id"], f"event {expected_seq} causation_id")
    return item


def validate_actor(value: object, expected_seq: int) -> None:
    actor = require_object(value, f"event {expected_seq} actor")
    require_fields(actor, {"kind", "id"}, {"kind", "id"}, f"event {expected_seq} actor")
    require_identifier(actor["kind"], f"event {expected_seq} actor kind")
    require_identifier(actor["id"], f"event {expected_seq} actor id")
