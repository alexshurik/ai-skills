from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .model import HASH_RE, JsonObject, StateError, utc_now


@dataclass(frozen=True)
class MigrationOptions:
    runtime_dir: Path
    workflow: str
    policy_revision: str
    legacy_stage: str | None = None


@dataclass
class LegacyAgents:
    spawned: list[str]
    running: set[str]
    completed: set[str]
    roles: dict[str, str]


def normalized_legacy_state(legacy: JsonObject, options: MigrationOptions) -> JsonObject:
    change = legacy.get("change") or legacy.get("fix_name") or options.runtime_dir.name
    change_name = safe_legacy_name(str(change), "legacy-change")
    phase, was_background = resolve_legacy_stage(legacy, options)
    agents = collect_legacy_agents(legacy)
    blockers = migrate_blockers(legacy)
    control = migrate_control(legacy, agents, blockers, was_background)
    stage = migrate_current_stage(legacy, agents, control)
    state = {
        "schema_version": 2,
        "revision": 1,
        "run": migrated_run(change_name, options.workflow, options.policy_revision),
        "repositories": migrate_repositories(legacy),
        "workflow": {"current_stage": phase, "stages": migrate_stages(legacy, phase, stage)},
        "control": control,
        "writer_lease": None,
        "artifacts": migrate_artifacts(legacy),
        "blockers": blockers,
        "last_event": {"seq": 1, "id": "migration-placeholder"},
    }
    return state


def safe_legacy_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._+-]+", "-", value.strip("/ ")).strip("-._+")
    return cleaned[:80] or fallback


def migrated_run(change: str, workflow: str, policy_revision: str) -> JsonObject:
    return {
        "id": f"{change}-migrated",
        "change": change,
        "workflow": workflow,
        "policy_revision": policy_revision,
        "created_at": utc_now(),
        "migrated_from": {"schema_version": 1},
    }


def resolve_legacy_stage(legacy: JsonObject, options: MigrationOptions) -> tuple[str, bool]:
    raw_phase = str(legacy.get("phase") or "legacy")
    was_background = raw_phase == "background_work_active"
    if not was_background:
        return safe_legacy_name(raw_phase, "legacy"), False
    checkpoint = legacy.get("background_checkpoint")
    recovered = options.legacy_stage
    if recovered is None and isinstance(checkpoint, dict):
        recovered = checkpoint.get("stage") or checkpoint.get("phase")
    if not isinstance(recovered, str) or not recovered:
        raise StateError(
            "legacy background state does not prove its workflow stage; "
            "reconcile the mailbox and rerun with --legacy-stage"
        )
    return safe_legacy_name(recovered, "legacy"), True


def collect_legacy_agents(legacy: JsonObject) -> LegacyAgents:
    threads = legacy.get("agent_threads")
    thread_map = threads if isinstance(threads, dict) else {}
    checkpoint = legacy.get("background_checkpoint")
    checkpoint_map = checkpoint if isinstance(checkpoint, dict) else {}
    roles = running_agent_roles(legacy.get("running_agents"))
    spawned = values_from(legacy, "spawned") + values_from(thread_map, "spawned")
    running = set(values_from(legacy, "running") + values_from(thread_map, "running"))
    completed = set(values_from(legacy, "completed") + values_from(thread_map, "completed"))
    running.update(roles)
    running.update(checkpoint_agents(checkpoint_map))
    wait_join = values_from(legacy, "join")
    if is_wait_state(legacy):
        running.update(wait_join)
    spawned.extend([*running, *completed, *wait_join])
    running.difference_update(completed)
    return LegacyAgents(list(dict.fromkeys(spawned)), running, completed, roles)


def values_from(mapping: JsonObject, key: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def running_agent_roles(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(host): str(role) for role, host in value.items() if isinstance(host, str)}


def checkpoint_agents(checkpoint: JsonObject) -> set[str]:
    result = set(values_from(checkpoint, "running") + values_from(checkpoint, "running_agents"))
    for field in ("running_agent", "agent_id", "host_thread_id"):
        value = checkpoint.get(field)
        if isinstance(value, str):
            result.add(value)
    return result


def is_wait_state(legacy: JsonObject) -> bool:
    return (
        legacy.get("execution_status") in {"foreground_join", "background_detached"}
        or legacy.get("phase") == "background_work_active"
        or "wait_budget" in legacy
    )


def migrate_current_stage(
    legacy: JsonObject, agents: LegacyAgents, control: JsonObject
) -> JsonObject:
    stage = {"status": "in_progress", "entries": 1, "gates": {}, "checks": {}, "tasks": {}}
    stage["gates"] = migrate_approvals(legacy)
    stage["tasks"] = migrate_tasks(agents)
    if control["kind"] == "waiting_agents":
        stage["status"] = "waiting"
    return stage


def migrate_approvals(legacy: JsonObject) -> JsonObject:
    approvals = legacy.get("approvals")
    if not isinstance(approvals, dict):
        return {}
    gates: JsonObject = {}
    for name, value in approvals.items():
        status = "approved" if value is True else "rejected" if value is False else "pending"
        gate: JsonObject = {
            "status": status,
            "reason": "migrated legacy approval",
            "entry": 1,
            "requested_event": 0,
        }
        if status != "pending":
            gate.update({"decided_by": "legacy", "decision_event": 0})
        gates[safe_legacy_name(str(name), "legacy-gate")] = gate
    return gates


def migrate_tasks(agents: LegacyAgents) -> JsonObject:
    tasks: JsonObject = {}
    for ordinal, host in enumerate(agents.spawned, start=1):
        role = agents.roles.get(host, f"legacy-agent-{ordinal}")
        task_name = unique_task_name(tasks, safe_legacy_name(role, f"legacy-agent-{ordinal}"))
        status = legacy_attempt_status(host, agents)
        attempt = migrated_attempt(host, role, ordinal, status)
        tasks[task_name] = {
            "role": safe_legacy_name(role, task_name),
            "required": True,
            "status": status,
            "created_entry": 1,
            "created_event": 0,
            "attempts": [attempt],
        }
    return tasks


def unique_task_name(tasks: JsonObject, candidate: str) -> str:
    if candidate not in tasks:
        return candidate
    suffix = 2
    while f"{candidate}-{suffix}" in tasks:
        suffix += 1
    return f"{candidate}-{suffix}"


def legacy_attempt_status(host: str, agents: LegacyAgents) -> str:
    if host in agents.completed:
        return "succeeded"
    if host in agents.running:
        return "running"
    return "cancelled"


def migrated_attempt(host: str, role: str, ordinal: int, status: str) -> JsonObject:
    attempt: JsonObject = {
        "id": f"legacy-attempt-{ordinal}",
        "ordinal": 1,
        "status": status,
        "agent": {
            "role": safe_legacy_name(role, f"legacy-agent-{ordinal}"),
            "host_thread_id": host,
        },
        "stage_entry": 1,
        "started_event": 0,
        "late_results": [],
    }
    if status != "running":
        attempt["result"] = {"outcome": status, "recorded_event": 0, "verdict": "migrated"}
    return attempt


def migrate_control(
    legacy: JsonObject,
    agents: LegacyAgents,
    blockers: JsonObject,
    was_background: bool,
) -> JsonObject:
    if blockers and agents.running:
        raise StateError(
            "legacy state has unresolved blockers and running agents; reconcile the mailbox first"
        )
    if blockers:
        return {"kind": "blocked", "blocker_ids": sorted(blockers)}
    attempt_ids = running_attempt_ids(agents)
    if attempt_ids:
        return migrated_wait_control(legacy, attempt_ids, was_background)
    if is_wait_state(legacy):
        raise StateError("legacy wait state contains no running agent to reconcile")
    reason = safe_legacy_name(
        str(legacy.get("next_action") or "legacy_migration"), "legacy_migration"
    )
    return {"kind": "ready", "reason_code": reason}


def running_attempt_ids(agents: LegacyAgents) -> list[str]:
    return [
        f"legacy-attempt-{ordinal}"
        for ordinal, host in enumerate(agents.spawned, start=1)
        if host in agents.running
    ]


def migrated_wait_control(
    legacy: JsonObject, attempt_ids: list[str], was_background: bool
) -> JsonObject:
    is_foreground = legacy.get("execution_status") == "foreground_join" and not was_background
    join = "foreground" if is_foreground else "detached"
    reason = safe_legacy_name(str(legacy.get("next_action") or "legacy_join"), "legacy_join")
    control: JsonObject = {
        "kind": "waiting_agents",
        "join": join,
        "attempt_ids": attempt_ids,
        "reason_code": reason,
    }
    if join == "detached":
        detach = legacy.get("detach_reason") or "legacy_wait_budget"
        control["detach_reason"] = safe_legacy_name(str(detach), "legacy_wait_budget")
    return control


def migrate_blockers(legacy: JsonObject) -> JsonObject:
    values = legacy.get("blockers")
    if not isinstance(values, list):
        return {}
    return {
        f"legacy-blocker-{index}": {
            "reason": str(value),
            "required_action": "review migrated blocker",
            "recorded_event": 0,
        }
        for index, value in enumerate(values, start=1)
    }


def migrate_repositories(legacy: JsonObject) -> JsonObject:
    repositories: JsonObject = {}
    for source, target in (
        ("worktrees", "worktree"),
        ("branches", "branch"),
        ("bases", "base_sha"),
    ):
        values = legacy.get(source)
        if not isinstance(values, dict):
            continue
        for name, value in values.items():
            repositories.setdefault(safe_legacy_name(str(name), "repository"), {})[target] = str(
                value
            )
    return repositories


def migrate_artifacts(legacy: JsonObject) -> JsonObject:
    values = legacy.get("artifacts")
    if not isinstance(values, dict):
        return {}
    artifacts: JsonObject = {}
    for name, value in values.items():
        migrated = migrate_artifact(value)
        if migrated is not None:
            artifacts[safe_legacy_name(str(name), "legacy-artifact")] = migrated
    return artifacts


def migrate_artifact(value: object) -> JsonObject | None:
    if not isinstance(value, dict):
        return None
    path = value.get("path") or value.get("artifact")
    digest = value.get("sha256") or value.get("hash")
    if not path or not isinstance(digest, str) or not HASH_RE.fullmatch(digest):
        return None
    return {"path": str(path), "sha256": digest, "kind": "legacy", "recorded_event": 0}


def migrate_stages(legacy: JsonObject, phase: str, current: JsonObject) -> JsonObject:
    stages = {phase: current}
    counters = {
        "review": ("review_attempts", "review_cycle"),
        "remediation": ("remediation_attempts", "remediation_cycle"),
        "acceptance": ("acceptance_attempts", "acceptance_cycle"),
    }
    for stage_name, fields in counters.items():
        counts = [legacy.get(field) for field in fields]
        count = max((value for value in counts if isinstance(value, int)), default=0)
        if count and stage_name not in stages:
            stages[stage_name] = {
                "status": "succeeded",
                "entries": count,
                "gates": {},
                "checks": {},
                "tasks": {},
            }
    return stages
