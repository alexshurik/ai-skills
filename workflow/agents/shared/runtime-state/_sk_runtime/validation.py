"""Materialized projection validation."""

from __future__ import annotations

from .model import (
    STATE_SCHEMA_VERSION,
    TERMINAL_ATTEMPTS,
    JsonObject,
    StateError,
    find_attempt,
    require_boolean,
    require_fields,
    require_hash,
    require_identifier,
    require_integer,
    require_object,
    require_string,
    require_string_list,
    require_timestamp,
    running_attempt_ids,
    stage_for,
)


def validate_repository(value: object, name: str) -> None:
    repository = require_object(value, name)
    allowed = {"root", "worktree", "branch", "base_sha"}
    if not repository or set(repository) - allowed:
        raise StateError(f"{name} must contain only repository identity fields")
    for field, field_value in repository.items():
        require_string(field_value, f"{name}.{field}")


def validate_run(value: object) -> JsonObject:
    run = require_object(value, "run")
    required = {"id", "change", "workflow", "policy_revision", "created_at"}
    require_fields(run, required, required | {"migrated_from"}, "run")
    require_string(run["id"], "run.id")
    require_identifier(run["change"], "run.change")
    require_identifier(run["workflow"], "run.workflow")
    require_string(run["policy_revision"], "run.policy_revision")
    require_timestamp(run["created_at"], "run.created_at")
    if "migrated_from" in run:
        migrated = require_object(run["migrated_from"], "run.migrated_from")
        if migrated != {"schema_version": 1}:
            raise StateError("run.migrated_from must identify schema version 1")
    return run


def validate_gate(value: object, label: str, entries: int) -> None:
    gate = require_object(value, label)
    required = {"status", "reason", "entry", "requested_event"}
    allowed = required | {"decided_by", "decision_event", "decision_reason"}
    require_fields(gate, required, allowed, label)
    status = require_identifier(gate["status"], f"{label}.status")
    if status not in {"pending", "approved", "rejected", "waived"}:
        raise StateError(f"{label} has invalid status")
    require_string(gate["reason"], f"{label}.reason")
    if require_integer(gate["entry"], f"{label}.entry", minimum=1) > entries:
        raise StateError(f"{label} belongs to a future entry")
    require_integer(gate["requested_event"], f"{label}.requested_event")
    decided = {"decided_by", "decision_event"}
    if status == "pending" and decided & set(gate):
        raise StateError(f"{label} pending gate contains decision fields")
    if status != "pending" and not decided.issubset(gate):
        raise StateError(f"{label} decided gate is missing decision fields")
    if "decided_by" in gate:
        require_string(gate["decided_by"], f"{label}.decided_by")
        require_integer(gate["decision_event"], f"{label}.decision_event")
    if "decision_reason" in gate:
        require_string(gate["decision_reason"], f"{label}.decision_reason")


def validate_check(value: object, label: str, entries: int) -> None:
    check = require_object(value, label)
    required = {"status", "required", "entry", "recorded_event"}
    require_fields(check, required, required | {"evidence", "sha256"}, label)
    if require_identifier(check["status"], f"{label}.status") not in {
        "passed",
        "failed",
        "unknown",
    }:
        raise StateError(f"{label} has invalid status")
    require_boolean(check["required"], f"{label}.required")
    if require_integer(check["entry"], f"{label}.entry", minimum=1) > entries:
        raise StateError(f"{label} belongs to a future entry")
    require_integer(check["recorded_event"], f"{label}.recorded_event")
    if "evidence" in check:
        require_string(check["evidence"], f"{label}.evidence")
    if "sha256" in check:
        require_hash(check["sha256"], f"{label}.sha256")


def validate_result(value: object, label: str, status: str) -> None:
    result = require_object(value, label)
    required = {"outcome", "recorded_event"}
    require_fields(result, required, required | {"verdict", "artifact", "sha256"}, label)
    if result["outcome"] != status:
        raise StateError(f"{label} outcome does not match attempt status")
    require_integer(result["recorded_event"], f"{label}.recorded_event")
    for field in ("verdict", "artifact"):
        if field in result:
            require_string(result[field], f"{label}.{field}")
    if "sha256" in result:
        require_hash(result["sha256"], f"{label}.sha256")


def validate_late_result(value: object, label: str) -> None:
    result = require_object(value, label)
    required = {"recorded_event"}
    require_fields(result, required, required | {"verdict", "artifact", "sha256"}, label)
    require_integer(result["recorded_event"], f"{label}.recorded_event", minimum=1)
    for field in ("verdict", "artifact"):
        if field in result:
            require_string(result[field], f"{label}.{field}")
    if "sha256" in result:
        require_hash(result["sha256"], f"{label}.sha256")


def validate_attempt(value: object, label: str, ordinal: int, entries: int) -> str:
    attempt = require_object(value, label)
    required = {"id", "ordinal", "status", "agent", "stage_entry", "started_event", "late_results"}
    allowed = required | {"input_fingerprint", "result", "lease_holder_attempt_id"}
    require_fields(attempt, required, allowed, label)
    attempt_id = require_identifier(attempt["id"], f"{label}.id")
    if require_integer(attempt["ordinal"], f"{label}.ordinal", minimum=1) != ordinal:
        raise StateError(f"{label} ordinal is not contiguous")
    status = require_identifier(attempt["status"], f"{label}.status")
    if status not in {"running", *TERMINAL_ATTEMPTS}:
        raise StateError(f"{label} has invalid status")
    if require_integer(attempt["stage_entry"], f"{label}.stage_entry", minimum=1) > entries:
        raise StateError(f"{label} belongs to a future entry")
    validate_agent(attempt["agent"], f"{label}.agent")
    require_integer(attempt["started_event"], f"{label}.started_event")
    if "input_fingerprint" in attempt:
        require_hash(attempt["input_fingerprint"], f"{label}.input_fingerprint")
    if "lease_holder_attempt_id" in attempt:
        require_identifier(attempt["lease_holder_attempt_id"], f"{label}.lease_holder_attempt_id")
    validate_attempt_result(attempt, label, status)
    validate_late_results(attempt["late_results"], label)
    return attempt_id


def validate_attempt_result(attempt: JsonObject, label: str, status: str) -> None:
    if status == "running":
        if "result" in attempt:
            raise StateError(f"{label} running attempt has a result")
        return
    if "result" not in attempt:
        raise StateError(f"{label} terminal attempt is missing a result")
    validate_result(attempt["result"], f"{label}.result", status)


def validate_late_results(late_results: object, label: str) -> None:
    if not isinstance(late_results, list):
        raise StateError(f"{label}.late_results must be an array")
    for index, late in enumerate(late_results, start=1):
        validate_late_result(late, f"{label}.late_results[{index}]")


def validate_agent(value: object, label: str) -> None:
    agent = require_object(value, label)
    require_fields(agent, {"role", "host_thread_id"}, {"role", "host_thread_id"}, label)
    require_identifier(agent["role"], f"{label}.role")
    require_string(agent["host_thread_id"], f"{label}.host_thread_id")


def validate_task(value: object, label: str, entries: int) -> set[str]:
    task = require_object(value, label)
    required = {"role", "required", "status", "created_entry", "created_event", "attempts"}
    require_fields(task, required, required | {"lease_holder_attempt_id"}, label)
    require_identifier(task["role"], f"{label}.role")
    require_boolean(task["required"], f"{label}.required")
    status = require_identifier(task["status"], f"{label}.status")
    if status not in {"pending", "running", *TERMINAL_ATTEMPTS}:
        raise StateError(f"{label} has invalid status")
    if require_integer(task["created_entry"], f"{label}.created_entry", minimum=1) > entries:
        raise StateError(f"{label} belongs to a future entry")
    require_integer(task["created_event"], f"{label}.created_event")
    owner = task.get("lease_holder_attempt_id")
    if owner is not None:
        require_identifier(owner, f"{label}.lease_holder_attempt_id")
    attempts = task["attempts"]
    if not isinstance(attempts, list):
        raise StateError(f"{label}.attempts must be an array")
    attempt_ids = {
        validate_attempt(attempt, f"{label}.attempts[{index}]", index, entries)
        for index, attempt in enumerate(attempts, start=1)
    }
    if any(attempt.get("lease_holder_attempt_id") != owner for attempt in attempts):
        raise StateError(f"{label} attempts do not match task lease lineage")
    expected_status = attempts[-1]["status"] if attempts else "pending"
    if status != expected_status:
        raise StateError(f"{label} status does not match its latest attempt")
    return attempt_ids


def validate_lease_lineages(state: JsonObject) -> None:
    for stage_name, stage in state["workflow"]["stages"].items():
        for task in stage["tasks"].values():
            owner = task.get("lease_holder_attempt_id")
            if owner is None:
                continue
            holder_stage, holder_task, _ = find_attempt(state, owner)
            holder_role = stage_for(state, holder_stage)["tasks"][holder_task]["role"]
            if holder_stage != stage_name or holder_role not in {
                "review-orchestrator",
                "sk-review-orchestrator",
            }:
                raise StateError("task lease lineage does not identify its stage orchestrator")


def validate_stage(value: object, label: str) -> set[str]:
    stage = require_object(value, label)
    required = {"status", "entries", "gates", "checks", "tasks"}
    allowed = required | {"entered_event", "completed_event"}
    require_fields(stage, required, allowed, label)
    status = require_identifier(stage["status"], f"{label}.status")
    if status not in {"pending", "in_progress", "waiting", "succeeded", "failed", "skipped"}:
        raise StateError(f"{label} has invalid status")
    entries = require_integer(stage["entries"], f"{label}.entries")
    gates = require_object(stage["gates"], f"{label}.gates")
    checks = require_object(stage["checks"], f"{label}.checks")
    tasks = require_object(stage["tasks"], f"{label}.tasks")
    for name, gate in gates.items():
        validate_gate(gate, f"{label}.gates.{require_identifier(name, 'gate name')}", entries)
    for name, check in checks.items():
        validate_check(check, f"{label}.checks.{require_identifier(name, 'check name')}", entries)
    ids: set[str] = set()
    for name, task in tasks.items():
        task_ids = validate_task(
            task, f"{label}.tasks.{require_identifier(name, 'task name')}", entries
        )
        if ids & task_ids:
            raise StateError("attempt IDs must be globally unique")
        ids.update(task_ids)
    for field in ("entered_event", "completed_event"):
        if field in stage:
            require_integer(stage[field], f"{label}.{field}")
    return ids


def validate_control(value: object, state: JsonObject, blockers: JsonObject) -> None:
    control = require_object(value, "control")
    kind = require_identifier(control.get("kind"), "control.kind")
    allowed = control_fields(kind)
    if set(control) - allowed:
        raise StateError("control has invalid fields")
    validate_control_variant(kind, control, state, blockers)
    if kind != "blocked" and blockers:
        raise StateError("unresolved blockers require blocked control")


def control_fields(kind: str) -> set[str]:
    fields = {
        "ready": {"kind", "reason_code"},
        "waiting_agents": {"kind", "join", "attempt_ids", "reason_code", "detach_reason"},
        "waiting_user": {"kind", "gate_ids", "reason_code"},
        "blocked": {"kind", "blocker_ids"},
        "complete": {"kind", "outcome"},
    }
    try:
        return fields[kind]
    except KeyError as error:
        raise StateError("control has invalid fields") from error


def validate_control_variant(
    kind: str, control: JsonObject, state: JsonObject, blockers: JsonObject
) -> None:
    if kind == "ready":
        require_identifier(control.get("reason_code"), "control.reason_code")
    elif kind == "waiting_agents":
        validate_agent_control(control, state)
    elif kind == "waiting_user":
        validate_user_control(control, state)
    elif kind == "blocked":
        refs = require_string_list(control.get("blocker_ids"), "control.blocker_ids", nonempty=True)
        if refs != sorted(blockers):
            raise StateError("blocked control does not match blockers")
    elif require_identifier(control.get("outcome"), "control.outcome") not in {
        "completed",
        "aborted",
    }:
        raise StateError("control outcome is invalid")


def validate_agent_control(control: JsonObject, state: JsonObject) -> None:
    join = require_identifier(control.get("join"), "control.join")
    if join not in {"foreground", "detached"}:
        raise StateError("control.join is invalid")
    refs = require_string_list(control.get("attempt_ids"), "control.attempt_ids", nonempty=True)
    if sorted(refs) != running_attempt_ids(state):
        raise StateError("waiting_agents control does not match running attempts")
    require_identifier(control.get("reason_code"), "control.reason_code")
    if join == "detached":
        require_identifier(control.get("detach_reason"), "control.detach_reason")
    elif "detach_reason" in control:
        raise StateError("foreground control must not contain detach_reason")


def validate_user_control(control: JsonObject, state: JsonObject) -> None:
    refs = require_string_list(control.get("gate_ids"), "control.gate_ids", nonempty=True)
    require_identifier(control.get("reason_code"), "control.reason_code")
    current = state["workflow"]["current_stage"]
    for ref in refs:
        try:
            stage_name, gate_name = ref.split("/", 1)
            stage = state["workflow"]["stages"][stage_name]
            gate = stage["gates"][gate_name]
        except (ValueError, KeyError) as error:
            raise StateError(f"control references unknown gate {ref!r}") from error
        if (
            stage_name != current
            or gate["status"] != "pending"
            or gate["entry"] != stage["entries"]
        ):
            raise StateError(f"control references inactive gate {ref!r}")


def validate_named_records(state: JsonObject) -> JsonObject:
    artifacts = require_object(state["artifacts"], "artifacts")
    for name, value in artifacts.items():
        require_identifier(name, "artifact name")
        artifact = require_object(value, f"artifact {name}")
        required = {"path", "sha256", "recorded_event"}
        require_fields(artifact, required, required | {"kind", "stage"}, f"artifact {name}")
        require_string(artifact["path"], f"artifact {name}.path")
        require_hash(artifact["sha256"], f"artifact {name}.sha256")
        require_integer(artifact["recorded_event"], f"artifact {name}.recorded_event")
    blockers = require_object(state["blockers"], "blockers")
    for name, value in blockers.items():
        require_identifier(name, "blocker name")
        blocker = require_object(value, f"blocker {name}")
        required = {"reason", "required_action", "recorded_event"}
        require_fields(blocker, required, required, f"blocker {name}")
        require_string(blocker["reason"], f"blocker {name}.reason")
        require_string(blocker["required_action"], f"blocker {name}.required_action")
        require_integer(blocker["recorded_event"], f"blocker {name}.recorded_event")
    return blockers


def validate_writer_lease(value: object, state: JsonObject) -> None:
    if value is None:
        return
    lease = require_object(value, "writer_lease")
    required = {
        "id",
        "stage",
        "holder_attempt_id",
        "holder_actor_id",
        "granted_event",
    }
    require_fields(lease, required, required, "writer_lease")
    for field in ("id", "stage", "holder_attempt_id", "holder_actor_id"):
        require_identifier(lease[field], f"writer_lease.{field}")
    require_integer(lease["granted_event"], "writer_lease.granted_event", minimum=1)
    if state["workflow"]["current_stage"] != lease["stage"]:
        raise StateError("writer lease does not belong to the current stage")
    stage_name, task_name, attempt = find_attempt(state, lease["holder_attempt_id"])
    if stage_name != lease["stage"] or attempt["status"] != "running":
        raise StateError("writer lease holder is not a running attempt in its stage")
    role = state["workflow"]["stages"][stage_name]["tasks"][task_name]["role"]
    if role not in {"review-orchestrator", "sk-review-orchestrator"}:
        raise StateError("writer lease holder is not a review orchestrator")
    control = state["control"]
    if control.get("join") != "foreground":
        raise StateError("writer lease requires a foreground agent join")
    if lease["holder_attempt_id"] not in control.get("attempt_ids", []):
        raise StateError("writer lease holder is not present in the foreground join")


def validate_state(state: object) -> JsonObject:
    item = require_object(state, "state")
    required = {
        "schema_version",
        "revision",
        "run",
        "repositories",
        "workflow",
        "control",
        "writer_lease",
        "artifacts",
        "blockers",
        "last_event",
    }
    require_fields(item, required, required, "state")
    if item["schema_version"] != STATE_SCHEMA_VERSION:
        raise StateError("state uses an unsupported schema version")
    revision = require_integer(item["revision"], "revision", minimum=1)
    validate_run(item["run"])
    repositories = require_object(item["repositories"], "repositories")
    for name, repository in repositories.items():
        validate_repository(repository, f"repository {require_identifier(name, 'repository name')}")
    workflow = require_object(item["workflow"], "workflow")
    require_fields(workflow, {"current_stage", "stages"}, {"current_stage", "stages"}, "workflow")
    stages = require_object(workflow["stages"], "workflow.stages")
    all_ids: set[str] = set()
    for name, stage in stages.items():
        ids = validate_stage(stage, f"stage {require_identifier(name, 'stage name')}")
        if all_ids & ids:
            raise StateError("attempt IDs must be globally unique")
        all_ids.update(ids)
    current = workflow["current_stage"]
    if current is not None and require_identifier(current, "workflow.current_stage") not in stages:
        raise StateError("workflow.current_stage does not exist")
    blockers = validate_named_records(item)
    validate_control(item["control"], item, blockers)
    validate_lease_lineages(item)
    validate_writer_lease(item["writer_lease"], item)
    last_event = require_object(item["last_event"], "last_event")
    require_fields(last_event, {"seq", "id"}, {"seq", "id"}, "last_event")
    if require_integer(last_event["seq"], "last_event.seq", minimum=1) != revision:
        raise StateError("last_event.seq must equal revision")
    require_identifier(last_event["id"], "last_event.id")
    return item
