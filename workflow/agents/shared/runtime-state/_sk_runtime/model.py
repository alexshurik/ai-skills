from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

JsonObject = dict[str, Any]

STATE_SCHEMA_VERSION = 3
EVENT_SCHEMA_VERSION = 2
LEGACY_EVENT_SCHEMA_VERSION = 1
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@+-]*$")
TERMINAL_ATTEMPTS = frozenset({"succeeded", "failed", "blocked", "cancelled"})
TERMINAL_STAGES = frozenset({"succeeded", "failed", "skipped"})
ROUTES = frozenset({"micro", "quick", "full"})
ASSURANCE_LEVELS = frozenset({"standard", "elevated"})
AUTHORIZATION_MODES = frozenset({"manual", "checkpoints", "yolo"})
WORKSPACE_POLICIES = frozenset({"current", "worktree", "auto"})
WORKSPACE_RESOLUTIONS = frozenset({"pending", "current", "worktree"})
DESTINATION_KINDS = frozenset({"local", "commit", "pr", "merge", "deploy"})
STOP_REASON_CODES = frozenset(
    {
        "decision.material_product",
        "decision.material_scope",
        "boundary.external_access",
        "boundary.destructive_or_irreversible",
        "boundary.live_cost_or_value",
        "boundary.terminal_not_authorized",
        "evidence.unverifiable",
        "budget.exhausted",
        "control.user_reset",
    }
)


class StateError(ValueError):
    """Raised when a journal, projection, or requested transition is invalid."""


class UnsupportedEventSchemaError(StateError):
    """Raised when the journal requires a newer runtime helper."""

    def __init__(self, sequence: int, version: int) -> None:
        self.validated_events = sequence - 1
        super().__init__(
            f"event {sequence} uses unsupported schema version {version}; "
            "required action: require-compatible-helper"
        )


def utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def require_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or any(char in value for char in "\0\r\n"):
        raise StateError(f"{name} must be a non-empty single-line string")
    return value


def require_identifier(value: object, name: str) -> str:
    text = require_string(value, name)
    if not IDENTIFIER_RE.fullmatch(text):
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


def require_object(value: object, name: str) -> JsonObject:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise StateError(f"{name} must be a JSON object with string keys")
    return value


def require_integer(value: object, name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise StateError(f"{name} must be an integer >= {minimum}")
    return value


def require_boolean(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise StateError(f"{name} must be a boolean")
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


def require_fields(
    value: JsonObject,
    required: set[str] | frozenset[str],
    allowed: set[str] | frozenset[str],
    name: str,
) -> None:
    if not required.issubset(value) or set(value) - allowed:
        raise StateError(f"{name} has missing or unknown fields")


def default_charter(run: JsonObject) -> JsonObject:
    workflow = run["workflow"]
    legacy = workflow in {"sk-team-feature", "sk-team-quick"}
    route = "full" if workflow == "sk-team-feature" else "quick"
    workspace = "worktree" if workflow == "sk-team-feature" else "auto"
    resolved = "worktree" if workspace == "worktree" else "pending"
    scope = hashlib.sha256(run["change"].encode()).hexdigest()
    return {
        "revision": 1,
        "route": route,
        "assurance": "standard",
        "authorization": "manual" if legacy else "checkpoints",
        "scope_sha256": scope,
        "workspace": {"requested": workspace, "resolved": resolved},
        "destination": {"kind": "local"},
        "budgets": default_budgets(route),
        "updated_event": 1,
    }


def default_budgets(route: str) -> JsonObject:
    if route == "micro":
        return {"attempts": 1, "review_rounds": 1, "remediations": 1}
    if route == "quick":
        return {"attempts": 6, "review_rounds": 3, "remediations": 2}
    return {"attempts": 20, "review_rounds": 3, "remediations": 2}


def initial_state(run: JsonObject, repositories: JsonObject, charter: JsonObject) -> JsonObject:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "revision": 0,
        "run": copy.deepcopy(run),
        "charter": copy.deepcopy(charter),
        "repositories": copy.deepcopy(repositories),
        "workflow": {"current_stage": None, "stages": {}},
        "control": {"kind": "ready", "reason_code": "workflow_started"},
        "delivery": {"status": "pending"},
        "writer_lease": None,
        "artifacts": {},
        "blockers": {},
        "last_event": None,
    }


def stage_for(state: JsonObject, name: str) -> JsonObject:
    try:
        stage: JsonObject = state["workflow"]["stages"][name]
    except KeyError as error:
        raise StateError(f"unknown stage {name!r}") from error
    return stage


def task_for(state: JsonObject, stage: str, task: str) -> JsonObject:
    try:
        result: JsonObject = stage_for(state, stage)["tasks"][task]
    except KeyError as error:
        raise StateError(f"unknown task {stage}/{task}") from error
    return result


def find_attempt(state: JsonObject, attempt_id: str) -> tuple[str, str, JsonObject]:
    found = [
        (stage_name, task_name, attempt)
        for stage_name, stage in state["workflow"]["stages"].items()
        for task_name, task in stage["tasks"].items()
        for attempt in task["attempts"]
        if attempt["id"] == attempt_id
    ]
    if len(found) != 1:
        raise StateError(f"attempt {attempt_id!r} was not found uniquely")
    return found[0]


def require_active_stage(state: JsonObject, stage_name: str) -> JsonObject:
    if state["workflow"]["current_stage"] != stage_name:
        raise StateError(f"stage {stage_name!r} is not current")
    stage = stage_for(state, stage_name)
    if stage["status"] not in {"in_progress", "waiting"}:
        raise StateError(f"stage {stage_name!r} is not active")
    return stage


def running_attempt_ids(state: JsonObject) -> list[str]:
    return sorted(
        attempt["id"]
        for stage in state["workflow"]["stages"].values()
        for task in stage["tasks"].values()
        for attempt in task["attempts"]
        if attempt["status"] == "running"
    )


def attempt_count(state: JsonObject) -> int:
    return sum(
        len(task["attempts"])
        for stage in state["workflow"]["stages"].values()
        for task in stage["tasks"].values()
    )


def batch_count(state: JsonObject, purpose: str) -> int:
    return sum(
        task.get("purpose") == purpose
        for stage in state["workflow"]["stages"].values()
        for task in stage["tasks"].values()
    )


def require_successful_stage_work(stage: JsonObject, name: str) -> None:
    unfinished = unfinished_required_tasks(stage)
    if unfinished:
        raise StateError(
            f"stage {name!r} has unsuccessful tasks (required): {', '.join(unfinished)}"
        )

    failed_checks = failed_required_checks(stage)
    if failed_checks:
        raise StateError(
            f"stage {name!r} has unsuccessful checks (required): {', '.join(failed_checks)}"
        )


def unfinished_required_tasks(stage: JsonObject) -> list[str]:
    return sorted(
        task_name
        for task_name, task in stage["tasks"].items()
        if task["created_entry"] == stage["entries"]
        and task["required"]
        and task["status"] != "succeeded"
    )


def failed_required_checks(stage: JsonObject) -> list[str]:
    return sorted(
        check_name
        for check_name, check in stage["checks"].items()
        if check["entry"] == stage["entries"] and check["required"] and check["status"] != "passed"
    )
