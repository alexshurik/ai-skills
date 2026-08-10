from __future__ import annotations

import copy
from collections.abc import Callable

from .model import (
    TERMINAL_ATTEMPTS,
    TERMINAL_STAGES,
    JsonObject,
    StateError,
    find_attempt,
    initial_state,
    require_active_stage,
    require_identifier,
    require_object,
    require_successful_stage_work,
    running_attempt_ids,
    stage_for,
    task_for,
)
from .validation import validate_state

Reducer = Callable[[JsonObject, JsonObject], None]
LEASED_EVENT_TYPES = frozenset(
    {
        "task.created",
        "agent.attempt.started",
        "agent.result.recorded",
        "agent.late_result.recorded",
        "review.lease.released",
    }
)
LEASE_LINEAGE_FIELD = "lease_holder_attempt_id"


def apply_event(previous: JsonObject | None, event: JsonObject) -> JsonObject:
    event_type = event["type"]
    if event_type in {"workflow.started", "workflow.migrated_from_v1"}:
        state = reduce_first_event(previous, event)
    else:
        if previous is None:
            raise StateError(f"{event_type} cannot be the first event")
        authorize_writer(previous, event)
        state = copy.deepcopy(previous)
        try:
            reducer = REDUCERS[event_type]
        except KeyError as error:
            raise StateError(f"event type {event_type!r} has no reducer") from error
        reducer(state, event)

    state["revision"] = event["seq"]
    state["last_event"] = {"seq": event["seq"], "id": event["id"]}
    validate_state(state)
    return state


def reduce_first_event(previous: JsonObject | None, event: JsonObject) -> JsonObject:
    if previous is not None:
        raise StateError(f"{event['type']} must be the first event")
    data = event["data"]
    if event["type"] == "workflow.started":
        return initial_state(
            require_object(data["run"], "workflow.started run"),
            require_object(data["repositories"], "workflow.started repositories"),
        )
    state = copy.deepcopy(require_object(data["state"], "migration state"))
    state.setdefault("writer_lease", None)
    return state


def authorize_writer(state: JsonObject, event: JsonObject) -> None:
    lease = state["writer_lease"]
    actor = event["actor"]
    if lease is None:
        if actor["kind"] == "review-orchestrator":
            raise StateError("review orchestrator has no active writer lease")
        return
    if event["type"] not in LEASED_EVENT_TYPES:
        raise StateError("only nested attempt events are allowed while a writer lease is active")
    expected_actor = {"kind": "review-orchestrator", "id": lease["holder_actor_id"]}
    if actor != expected_actor:
        raise StateError("event actor does not hold the active writer lease")
    if event["type"] != "review.lease.released":
        event_stage = nested_event_stage(state, event)
        if event_stage != lease["stage"]:
            raise StateError("leased event does not belong to the leased stage")
        require_lease_lineage(state, event, lease)
    if (
        event["type"] == "agent.result.recorded"
        and event["data"]["attempt_id"] == lease["holder_attempt_id"]
    ):
        raise StateError("review orchestrator must release its writer lease before finishing")


def require_lease_lineage(state: JsonObject, event: JsonObject, lease: JsonObject) -> None:
    if event["type"] == "task.created":
        return

    if event["type"] == "agent.attempt.started":
        task = task_for(state, event["data"]["stage"], event["data"]["task"])
        owner = task.get(LEASE_LINEAGE_FIELD)
    else:
        _, _, attempt = find_attempt(state, event["data"]["attempt_id"])
        owner = attempt.get(LEASE_LINEAGE_FIELD)

    if owner != lease["holder_attempt_id"]:
        raise StateError("leased event target is outside the holder's lease lineage")


def nested_event_stage(state: JsonObject, event: JsonObject) -> str:
    if "stage" in event["data"]:
        return require_identifier(event["data"]["stage"], "leased event stage")
    stage_name, _, _ = find_attempt(state, event["data"]["attempt_id"])
    return stage_name


def reduce_stage_entered(state: JsonObject, event: JsonObject) -> None:
    name = event["data"]["stage"]
    if state["control"]["kind"] != "ready":
        raise StateError("a stage may be entered only while control is ready")
    current = state["workflow"]["current_stage"]
    if (
        current is not None
        and current != name
        and stage_for(state, current)["status"] not in TERMINAL_STAGES
    ):
        raise StateError(f"cannot enter {name!r}; stage {current!r} is not terminal")
    stage = state["workflow"]["stages"].setdefault(name, empty_stage())
    if stage["status"] not in {"pending", *TERMINAL_STAGES}:
        raise StateError(f"stage {name!r} is already active")
    stage["entries"] += 1
    stage["status"] = "in_progress"
    stage["entered_event"] = event["seq"]
    stage.pop("completed_event", None)
    state["workflow"]["current_stage"] = name
    state["control"] = {"kind": "ready", "reason_code": "stage_entered"}


def empty_stage() -> JsonObject:
    return {"status": "pending", "entries": 0, "gates": {}, "checks": {}, "tasks": {}}


def reduce_stage_completed(state: JsonObject, event: JsonObject) -> None:
    name = event["data"]["stage"]
    outcome = event["data"]["outcome"]
    if state["workflow"]["current_stage"] != name:
        raise StateError(f"stage {name!r} is not current")
    if state["control"]["kind"] != "ready" or state["blockers"]:
        raise StateError("a stage may complete only while ready and unblocked")
    stage = stage_for(state, name)
    if any_attempt_running(stage):
        raise StateError(f"stage {name!r} still has running attempts")
    if outcome == "succeeded":
        require_approved_gates(stage, name)
        require_successful_stage_work(stage, name)
    stage["status"] = outcome
    stage["completed_event"] = event["seq"]
    state["control"] = {"kind": "ready", "reason_code": "stage_completed"}


def any_attempt_running(stage: JsonObject) -> bool:
    return any(
        attempt["status"] == "running"
        for task in stage["tasks"].values()
        for attempt in task["attempts"]
    )


def require_approved_gates(stage: JsonObject, name: str) -> None:
    is_rejected = any(
        gate["status"] not in {"approved", "waived"}
        for gate in stage["gates"].values()
        if gate["entry"] == stage["entries"]
    )
    if is_rejected:
        raise StateError(f"stage {name!r} has an undecided or rejected gate")


def reduce_gate_requested(state: JsonObject, event: JsonObject) -> None:
    data = event["data"]
    stage = require_active_stage(state, data["stage"])
    if state["control"]["kind"] != "ready":
        raise StateError("a gate may be requested only while control is ready")
    if data["gate"] in stage["gates"]:
        raise StateError(f"gate {data['stage']}/{data['gate']} already exists")
    stage["gates"][data["gate"]] = {
        "status": "pending",
        "reason": data["reason"],
        "entry": stage["entries"],
        "requested_event": event["seq"],
    }


def reduce_gate_decided(state: JsonObject, event: JsonObject) -> None:
    data = event["data"]
    stage = require_active_stage(state, data["stage"])
    if state["control"]["kind"] not in {"ready", "waiting_user"}:
        raise StateError("a gate may be decided only from ready or waiting_user")
    try:
        gate = stage["gates"][data["gate"]]
    except KeyError as error:
        raise StateError(f"unknown gate {data['stage']}/{data['gate']}") from error
    if gate["status"] != "pending" or gate["entry"] != stage["entries"]:
        raise StateError("only a pending gate from the current entry may be decided")
    gate.update(
        {
            "status": data["decision"],
            "decided_by": data["decided_by"],
            "decision_event": event["seq"],
        }
    )
    if "reason" in data:
        gate["decision_reason"] = data["reason"]
    release_decided_gate(state, f"{data['stage']}/{data['gate']}")


def release_decided_gate(state: JsonObject, gate_ref: str) -> None:
    if state["control"]["kind"] != "waiting_user":
        return
    remaining = [item for item in state["control"]["gate_ids"] if item != gate_ref]
    if remaining:
        state["control"]["gate_ids"] = remaining
        return
    state["control"] = {"kind": "ready", "reason_code": "user_gates_decided"}
    resume_current_stage(state)


def reduce_task_created(state: JsonObject, event: JsonObject) -> None:
    data = event["data"]
    stage = require_active_stage(state, data["stage"])
    if state["control"]["kind"] not in {"ready", "waiting_agents"}:
        raise StateError("a task may be created only from ready or waiting_agents")
    if data["task"] in stage["tasks"]:
        raise StateError(f"task {data['stage']}/{data['task']} already exists")
    task = {
        "role": data["role"],
        "required": data.get("required", True),
        "status": "pending",
        "created_entry": stage["entries"],
        "created_event": event["seq"],
        "attempts": [],
    }
    if event["actor"]["kind"] == "review-orchestrator":
        task[LEASE_LINEAGE_FIELD] = state["writer_lease"]["holder_attempt_id"]
    stage["tasks"][data["task"]] = task


def reduce_attempt_started(state: JsonObject, event: JsonObject) -> None:
    data = event["data"]
    stage = require_active_stage(state, data["stage"])
    if state["control"]["kind"] not in {"ready", "waiting_agents"}:
        raise StateError("an attempt may be started only from ready or waiting_agents")
    task = task_for(state, data["stage"], data["task"])
    require_unique_attempt(state, data["attempt_id"])
    if any(item["status"] == "running" for item in task["attempts"]):
        raise StateError(f"task {data['stage']}/{data['task']} already has a running attempt")
    attempt = new_attempt(task, stage, data, event["seq"])
    task["attempts"].append(attempt)
    task["status"] = "running"
    if state["control"]["kind"] == "waiting_agents":
        state["control"]["attempt_ids"].append(data["attempt_id"])
        state["control"]["attempt_ids"].sort()


def require_unique_attempt(state: JsonObject, attempt_id: str) -> None:
    try:
        find_attempt(state, attempt_id)
    except StateError:
        return
    raise StateError(f"attempt id {attempt_id!r} already exists")


def new_attempt(task: JsonObject, stage: JsonObject, data: JsonObject, seq: int) -> JsonObject:
    attempt = {
        "id": data["attempt_id"],
        "ordinal": len(task["attempts"]) + 1,
        "status": "running",
        "agent": {"role": task["role"], "host_thread_id": data["host_thread_id"]},
        "stage_entry": stage["entries"],
        "started_event": seq,
        "late_results": [],
    }
    if "input_fingerprint" in data:
        attempt["input_fingerprint"] = data["input_fingerprint"]
    if LEASE_LINEAGE_FIELD in task:
        attempt[LEASE_LINEAGE_FIELD] = task[LEASE_LINEAGE_FIELD]
    return attempt


def reduce_result_recorded(state: JsonObject, event: JsonObject) -> None:
    data = event["data"]
    stage_name, task_name, attempt = find_attempt(state, data["attempt_id"])
    if (stage_name, task_name) != (data["stage"], data["task"]):
        raise StateError("attempt does not belong to the named stage/task")
    if attempt["status"] != "running":
        raise StateError(f"attempt {data['attempt_id']!r} is already terminal")
    result = {"outcome": data["outcome"], "recorded_event": event["seq"]}
    copy_result_fields(result, data)
    attempt["status"] = data["outcome"]
    attempt["result"] = result
    task_for(state, stage_name, task_name)["status"] = data["outcome"]
    remove_waited_attempt(state, data["attempt_id"])


def copy_result_fields(target: JsonObject, data: JsonObject) -> None:
    for field in ("verdict", "artifact", "sha256"):
        if field in data:
            target[field] = data[field]


def remove_waited_attempt(state: JsonObject, attempt_id: str) -> None:
    if state["control"]["kind"] != "waiting_agents":
        return
    remaining = [item for item in state["control"]["attempt_ids"] if item != attempt_id]
    if remaining:
        state["control"]["attempt_ids"] = remaining
        return
    state["control"] = {"kind": "ready", "reason_code": "agent_results_recorded"}
    resume_current_stage(state)


def resume_current_stage(state: JsonObject) -> None:
    current = state["workflow"]["current_stage"]
    if current and stage_for(state, current)["status"] == "waiting":
        stage_for(state, current)["status"] = "in_progress"


def reduce_late_result(state: JsonObject, event: JsonObject) -> None:
    _, _, attempt = find_attempt(state, event["data"]["attempt_id"])
    if attempt["status"] not in TERMINAL_ATTEMPTS:
        raise StateError("late result may only be attached to a terminal attempt")
    late = {"recorded_event": event["seq"]}
    copy_result_fields(late, event["data"])
    attempt["late_results"].append(late)


def reduce_check_recorded(state: JsonObject, event: JsonObject) -> None:
    data = event["data"]
    stage = require_active_stage(state, data["stage"])
    check = {
        "status": data["status"],
        "required": data.get("required", True),
        "entry": stage["entries"],
        "recorded_event": event["seq"],
    }
    copy_result_fields(check, data)
    check.pop("artifact", None)
    check.pop("verdict", None)
    stage["checks"][data["check"]] = check


def reduce_artifact_recorded(state: JsonObject, event: JsonObject) -> None:
    data = event["data"]
    artifact = {"path": data["path"], "sha256": data["sha256"], "recorded_event": event["seq"]}
    for field in ("kind", "stage"):
        if field in data:
            artifact[field] = data[field]
    if "stage" in artifact:
        stage_for(state, artifact["stage"])
    state["artifacts"][data["name"]] = artifact


def reduce_waiting_for_agents(state: JsonObject, event: JsonObject) -> None:
    data = event["data"]
    if state["control"]["kind"] not in {"ready", "waiting_agents"}:
        raise StateError("an agent join may start only from ready or waiting_agents")
    for attempt_id in data["attempt_ids"]:
        if find_attempt(state, attempt_id)[2]["status"] != "running":
            raise StateError(f"cannot wait for terminal attempt {attempt_id!r}")
    running = running_attempt_ids(state)
    if sorted(data["attempt_ids"]) != running:
        raise StateError(
            f"agent join must contain every running attempt exactly once; running={running!r}"
        )
    control = {
        "kind": "waiting_agents",
        "join": data["join"],
        "attempt_ids": sorted(data["attempt_ids"]),
        "reason_code": data["reason_code"],
    }
    if "detach_reason" in data:
        control["detach_reason"] = data["detach_reason"]
    state["control"] = control
    mark_current_stage_waiting(state)


def mark_current_stage_waiting(state: JsonObject) -> None:
    current = state["workflow"]["current_stage"]
    if current:
        stage_for(state, current)["status"] = "waiting"


def reduce_waiting_for_user(state: JsonObject, event: JsonObject) -> None:
    if state["control"]["kind"] != "ready" or running_attempt_ids(state):
        raise StateError("a user wait requires ready control and no running attempts")
    current = state["workflow"]["current_stage"]
    if current is None:
        raise StateError("cannot wait for user without a current stage")
    stage = require_active_stage(state, current)
    for gate_id in event["data"]["gate_ids"]:
        validate_waited_gate(stage, current, gate_id)
    state["control"] = {
        "kind": "waiting_user",
        "gate_ids": event["data"]["gate_ids"],
        "reason_code": event["data"]["reason_code"],
    }
    mark_current_stage_waiting(state)


def validate_waited_gate(stage: JsonObject, current: str, gate_id: str) -> None:
    stage_name, gate_name = gate_id.split("/", 1)
    if stage_name != current:
        raise StateError(f"gate {gate_id!r} does not belong to the current stage")
    try:
        gate = stage["gates"][gate_name]
    except KeyError as error:
        raise StateError(f"unknown gate reference {gate_id!r}") from error
    if gate["status"] != "pending" or gate["entry"] != stage["entries"]:
        raise StateError(f"gate {gate_id!r} is not pending in the current entry")


def reduce_blocked(state: JsonObject, event: JsonObject) -> None:
    if state["control"]["kind"] != "ready":
        raise StateError("workflow may be blocked only while control is ready")
    if running_attempt_ids(state):
        raise StateError("record agent results before blocking the workflow")
    data = event["data"]
    state["blockers"][data["blocker_id"]] = {
        "reason": data["reason"],
        "required_action": data["required_action"],
        "recorded_event": event["seq"],
    }
    state["control"] = {"kind": "blocked", "blocker_ids": sorted(state["blockers"])}


def reduce_blocker_resolved(state: JsonObject, event: JsonObject) -> None:
    if state["control"]["kind"] != "blocked":
        raise StateError("a blocker may be resolved only while control is blocked")
    blocker_id = event["data"]["blocker_id"]
    if blocker_id not in state["blockers"]:
        raise StateError(f"unknown blocker {blocker_id!r}")
    del state["blockers"][blocker_id]
    if state["blockers"]:
        state["control"] = {"kind": "blocked", "blocker_ids": sorted(state["blockers"])}
    else:
        state["control"] = {"kind": "ready", "reason_code": "blockers_resolved"}


def reduce_workflow_completed(state: JsonObject, event: JsonObject) -> None:
    if state["control"]["kind"] == "complete":
        raise StateError("workflow is already complete")
    if running_attempt_ids(state):
        raise StateError("workflow still has running attempts")
    if event["data"]["outcome"] == "completed":
        current = state["workflow"]["current_stage"]
        if current is None or stage_for(state, current)["status"] != "succeeded":
            raise StateError("workflow completion requires a successful current stage")
        if state["blockers"]:
            raise StateError("workflow still has unresolved blockers")
    state["control"] = {"kind": "complete", "outcome": event["data"]["outcome"]}


def reduce_lease_granted(state: JsonObject, event: JsonObject) -> None:
    data = event["data"]
    if event["actor"]["kind"] != "orchestrator":
        raise StateError("only the global orchestrator may grant a writer lease")
    if state["writer_lease"] is not None:
        raise StateError("a writer lease is already active")
    if state["control"].get("join") != "foreground":
        raise StateError("review writer lease requires a foreground join")
    stage_name, task_name, attempt = find_attempt(state, data["holder_attempt_id"])
    task = task_for(state, stage_name, task_name)
    if stage_name != data["stage"] or attempt["status"] != "running":
        raise StateError("writer lease holder must be running in the leased stage")
    if task["role"] not in {"review-orchestrator", "sk-review-orchestrator"}:
        raise StateError("writer lease holder must have the review-orchestrator role")
    state["writer_lease"] = {
        "id": data["lease_id"],
        "stage": data["stage"],
        "holder_attempt_id": data["holder_attempt_id"],
        "holder_actor_id": data["holder_actor_id"],
        "granted_event": event["seq"],
    }


def reduce_lease_released(state: JsonObject, event: JsonObject) -> None:
    lease = state["writer_lease"]
    if lease is None or event["data"]["lease_id"] != lease["id"]:
        raise StateError("review writer lease does not match the active lease")
    state["writer_lease"] = None


REDUCERS: dict[str, Reducer] = {
    "stage.entered": reduce_stage_entered,
    "stage.completed": reduce_stage_completed,
    "gate.requested": reduce_gate_requested,
    "gate.decided": reduce_gate_decided,
    "task.created": reduce_task_created,
    "agent.attempt.started": reduce_attempt_started,
    "agent.result.recorded": reduce_result_recorded,
    "agent.late_result.recorded": reduce_late_result,
    "check.recorded": reduce_check_recorded,
    "artifact.recorded": reduce_artifact_recorded,
    "workflow.waiting_for_agents": reduce_waiting_for_agents,
    "workflow.waiting_for_user": reduce_waiting_for_user,
    "workflow.blocked": reduce_blocked,
    "workflow.blocker_resolved": reduce_blocker_resolved,
    "workflow.completed": reduce_workflow_completed,
    "review.lease.granted": reduce_lease_granted,
    "review.lease.released": reduce_lease_released,
}


def replay(events: list[JsonObject]) -> JsonObject | None:
    state: JsonObject | None = None
    for event in events:
        state = apply_event(state, event)
    return state
