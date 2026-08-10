from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import uuid
from collections.abc import Callable
from pathlib import Path

from .migration import MigrationOptions, normalized_legacy_state
from .model import (
    JsonObject,
    StateError,
    UnsupportedEventSchemaError,
    require_identifier,
    require_object,
    require_string,
    utc_now,
)
from .reducer import apply_event, replay
from .storage import (
    EventContext,
    MutationRequest,
    append_event,
    atomic_write_json,
    commit_transition,
    exclusive_lock,
    fsync_directory,
    load_runtime,
    make_event,
    read_events,
    read_json,
    require_repairable_projection,
    runtime_paths,
)
from .validation import validate_repository


def emit_state(state: JsonObject, *, message: str | None = None) -> None:
    if message:
        print(message, file=sys.stderr)
    json.dump(state, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    print()


def event_context(args: argparse.Namespace) -> EventContext:
    return EventContext(args.command_id, args.actor_kind, args.actor_id, args.causation_id)


def transition_handler(
    event_type: str, fields: tuple[str, ...]
) -> Callable[[argparse.Namespace], None]:
    def handler(args: argparse.Namespace) -> None:
        data = {field: getattr(args, field) for field in fields if getattr(args, field) is not None}
        request = MutationRequest(
            Path(args.runtime_dir).resolve(),
            args.expected_revision,
            event_type,
            data,
            event_context(args),
        )
        state = commit_transition(request)
        emit_state(state, message=f"recorded or replayed {event_type}")

    return handler


def repository_json(value: str) -> JsonObject:
    try:
        repositories = require_object(json.loads(value), "repositories")
        for name, repository in repositories.items():
            require_identifier(name, "repository name")
            validate_repository(repository, f"repository {name}")
    except (json.JSONDecodeError, StateError) as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    return repositories


def command_init(args: argparse.Namespace) -> None:
    runtime_dir = Path(args.runtime_dir).resolve()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    state_path, events_path, lock_path = runtime_paths(runtime_dir)
    with exclusive_lock(lock_path):
        replayed = replay_existing_init(args, events_path, state_path)
        if replayed is not None:
            emit_state(replayed, message="idempotent init replay")
            return
        if state_path.exists():
            raise StateError("state.json exists without an event journal")
        run = new_run(args)
        context = EventContext(args.command_id, args.actor_kind, args.actor_id)
        event = make_event(
            1, "workflow.started", {"run": run, "repositories": args.repository_json}, context
        )
        state = apply_event(None, event)
        append_event(events_path, event)
        atomic_write_json(state_path, state)
        emit_state(state, message="initialized workflow state v2")


def replay_existing_init(
    args: argparse.Namespace, events_path: Path, state_path: Path
) -> JsonObject | None:
    if not events_path.exists():
        return None
    events = read_events(events_path)
    if not events:
        return None
    state = replay(events)
    if len(events) != 1 or events[0]["type"] != "workflow.started" or state is None:
        raise StateError("runtime is already initialized")
    started = events[0]["data"]
    if not matching_init_request(args, events[0], started):
        raise StateError("runtime is already initialized with different inputs")
    atomic_write_json(state_path, state)
    return state


def matching_init_request(args: argparse.Namespace, event: JsonObject, started: JsonObject) -> bool:
    run = started["run"]
    return bool(
        event["command_id"] == args.command_id
        and run["change"] == args.change
        and run["workflow"] == args.workflow
        and run["policy_revision"] == args.policy_revision
        and started["repositories"] == args.repository_json
        and (args.run_id is None or run["id"] == args.run_id)
    )


def new_run(args: argparse.Namespace) -> JsonObject:
    change = require_identifier(args.change, "change")
    return {
        "id": args.run_id or f"{change}-{uuid.uuid4().hex[:8]}",
        "change": change,
        "workflow": require_identifier(args.workflow, "workflow"),
        "policy_revision": require_string(args.policy_revision, "policy_revision"),
        "created_at": utc_now(),
    }


def command_migrate(args: argparse.Namespace) -> None:
    runtime_dir = Path(args.runtime_dir).resolve()
    state_path, events_path, lock_path = runtime_paths(runtime_dir)
    with exclusive_lock(lock_path):
        replayed = replay_existing_migration(args, runtime_dir, events_path, state_path)
        if replayed is not None:
            emit_state(replayed, message="idempotent migration replay")
            return
        legacy, backup = prepare_legacy_backup(runtime_dir, state_path)
        options = MigrationOptions(
            runtime_dir, args.workflow, args.policy_revision, args.legacy_stage
        )
        normalized = normalized_legacy_state(legacy, options)
        source_digest = hashlib.sha256(backup.read_bytes()).hexdigest()
        context = EventContext(args.command_id, args.actor_kind, args.actor_id)
        event = make_event(
            1,
            "workflow.migrated_from_v1",
            {"source_sha256": source_digest, "state": normalized},
            context,
        )
        state = apply_event(None, event)
        append_event(events_path, event)
        atomic_write_json(state_path, state)
        emit_state(state, message=f"migrated v1 state; backup: {backup}")


def replay_existing_migration(
    args: argparse.Namespace,
    runtime_dir: Path,
    events_path: Path,
    state_path: Path,
) -> JsonObject | None:
    if not events_path.exists():
        return None
    events = read_events(events_path)
    if not events:
        return None
    state = replay(events)
    if len(events) != 1 or events[0]["type"] != "workflow.migrated_from_v1" or state is None:
        raise StateError("event journal is not an incomplete v1 migration")
    backup = runtime_dir / "state.v1.json"
    if not matching_migration(args, events[0], state, backup):
        raise StateError("migration was already committed with different inputs")
    atomic_write_json(state_path, state)
    return state


def matching_migration(
    args: argparse.Namespace, event: JsonObject, state: JsonObject, backup: Path
) -> bool:
    if not backup.exists():
        return False
    digest = hashlib.sha256(backup.read_bytes()).hexdigest()
    run = state["run"]
    return bool(
        event["command_id"] == args.command_id
        and run["workflow"] == args.workflow
        and run["policy_revision"] == args.policy_revision
        and event["data"]["source_sha256"] == digest
    )


def prepare_legacy_backup(runtime_dir: Path, state_path: Path) -> tuple[JsonObject, Path]:
    if not state_path.exists():
        raise StateError("legacy state.json does not exist")
    legacy = read_json(state_path)
    if legacy.get("schema_version") != 1:
        raise StateError("state.json is not schema_version 1")
    backup = runtime_dir / "state.v1.json"
    if backup.exists() and backup.read_bytes() != state_path.read_bytes():
        raise StateError("existing state.v1.json does not match legacy state.json")
    if not backup.exists():
        shutil.copy2(state_path, backup)
    with backup.open("rb") as backup_file:
        os.fsync(backup_file.fileno())
    fsync_directory(runtime_dir)
    return legacy, backup


def command_validate(args: argparse.Namespace) -> None:
    events, state, status = load_runtime(Path(args.runtime_dir).resolve())
    if not events and status == "legacy_v1":
        raise StateError("legacy schema v1 requires migrate-v1")
    if state is None:
        raise StateError("workflow has no valid non-empty event journal")
    if status != "valid":
        action = recovery_action(status, len(events))
        raise StateError(f"snapshot status is {status}; recommended action: {action}")
    print(f"OK: schema v2, revision {state['revision']}, {len(events)} events")


def command_status(args: argparse.Namespace) -> None:
    try:
        events, state, status = load_runtime(Path(args.runtime_dir).resolve())
        event_count = len(events)
    except UnsupportedEventSchemaError as error:
        state = None
        status = "unsupported_schema"
        event_count = error.validated_events
    report = {
        "journal_events": event_count,
        "recommended_action": recovery_action(status, event_count),
        "snapshot_status": status,
        "state": state,
    }
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    print()


def recovery_action(status: str, event_count: int) -> str:
    if status == "valid":
        return "validate"
    if status == "unsupported_schema":
        return "require-compatible-helper"
    if event_count > 0 and status in {"stale", "diverged", "missing", "legacy_v1"}:
        return "repair"
    if status == "legacy_v1":
        return "migrate-v1"
    return "recover-journal-or-reinitialize"


def command_history(args: argparse.Namespace) -> None:
    events_path = runtime_paths(Path(args.runtime_dir).resolve())[1]
    for event in read_events(events_path):
        if args.type is None or event["type"] == args.type:
            print(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def command_repair(args: argparse.Namespace) -> None:
    runtime_dir = Path(args.runtime_dir).resolve()
    state_path, events_path, lock_path = runtime_paths(runtime_dir)
    with exclusive_lock(lock_path):
        require_repairable_projection(state_path)
        if events_path.exists():
            preserve_incomplete_tail(runtime_dir, events_path)
        state = replay(read_events(events_path))
        if state is None:
            raise StateError(
                "cannot repair without a valid non-empty event journal; "
                "recover the journal or explicitly reinitialize and reconfirm workflow state"
            )
        atomic_write_json(state_path, state)
        emit_state(state, message="rebuilt state.json from events.jsonl")


def preserve_incomplete_tail(runtime_dir: Path, events_path: Path) -> None:
    content = events_path.read_bytes()
    if not content or content.endswith(b"\n"):
        return
    boundary = content.rfind(b"\n") + 1
    backup = runtime_dir / f"events.corrupt-tail-{uuid.uuid4().hex[:8]}.bin"
    with backup.open("xb") as backup_file:
        backup_file.write(content[boundary:])
        backup_file.flush()
        os.fsync(backup_file.fileno())
    fsync_directory(runtime_dir)
    with events_path.open("r+b") as journal:
        journal.truncate(boundary)
        journal.flush()
        os.fsync(journal.fileno())
    print(f"preserved incomplete tail at {backup}", file=sys.stderr)


def add_mutation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--runtime-dir", required=True)
    parser.add_argument("--expected-revision", required=True, type=int)
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--actor-kind", default="orchestrator")
    parser.add_argument("--actor-id", default="root")
    parser.add_argument("--causation-id")


def add_stage_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    entered = mutation_parser(commands, "enter-stage")
    entered.add_argument("--stage", required=True)
    entered.set_defaults(handler=transition_handler("stage.entered", ("stage",)))

    completed = mutation_parser(commands, "complete-stage")
    completed.add_argument("--stage", required=True)
    completed.add_argument("--outcome", choices=["succeeded", "failed", "skipped"], required=True)
    completed.set_defaults(handler=transition_handler("stage.completed", ("stage", "outcome")))


def add_gate_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    requested = mutation_parser(commands, "request-gate")
    requested.add_argument("--stage", required=True)
    requested.add_argument("--gate", required=True)
    requested.add_argument("--reason", required=True)
    requested.set_defaults(
        handler=transition_handler("gate.requested", ("stage", "gate", "reason"))
    )

    decided = mutation_parser(commands, "decide-gate")
    decided.add_argument("--stage", required=True)
    decided.add_argument("--gate", required=True)
    decided.add_argument("--decision", choices=["approved", "rejected", "waived"], required=True)
    decided.add_argument("--decided-by", required=True)
    decided.add_argument("--reason")
    fields = ("stage", "gate", "decision", "decided_by", "reason")
    decided.set_defaults(handler=transition_handler("gate.decided", fields))

    waiting = mutation_parser(commands, "wait-user")
    waiting.add_argument("--gate-id", dest="gate_ids", action="append", required=True)
    waiting.add_argument("--reason-code", required=True)
    waiting.set_defaults(
        handler=transition_handler("workflow.waiting_for_user", ("gate_ids", "reason_code"))
    )


def add_task_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    created = mutation_parser(commands, "create-task")
    created.add_argument("--stage", required=True)
    created.add_argument("--task", required=True)
    created.add_argument("--role", required=True)
    created.add_argument("--optional", dest="required", action="store_false", default=True)
    created_fields = ("stage", "task", "role", "required")
    created.set_defaults(handler=transition_handler("task.created", created_fields))

    started = mutation_parser(commands, "start-attempt")
    started.add_argument("--stage", required=True)
    started.add_argument("--task", required=True)
    started.add_argument("--attempt-id", required=True)
    started.add_argument("--host-thread-id", required=True)
    started.add_argument("--input-fingerprint")
    started_fields = ("stage", "task", "attempt_id", "host_thread_id", "input_fingerprint")
    started.set_defaults(handler=transition_handler("agent.attempt.started", started_fields))

    add_result_commands(commands)


def add_result_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    finished = mutation_parser(commands, "finish-attempt")
    for option in ("stage", "task", "attempt-id"):
        finished.add_argument(f"--{option}", required=True)
    finished.add_argument(
        "--outcome", choices=["succeeded", "failed", "blocked", "cancelled"], required=True
    )
    add_result_options(finished)
    fields = ("stage", "task", "attempt_id", "outcome", "verdict", "artifact", "sha256")
    finished.set_defaults(handler=transition_handler("agent.result.recorded", fields))

    late = mutation_parser(commands, "record-late-result")
    late.add_argument("--attempt-id", required=True)
    add_result_options(late)
    late_fields = ("attempt_id", "verdict", "artifact", "sha256")
    late.set_defaults(handler=transition_handler("agent.late_result.recorded", late_fields))


def add_result_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--verdict")
    parser.add_argument("--artifact")
    parser.add_argument("--sha256")


def add_record_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    check = mutation_parser(commands, "record-check")
    check.add_argument("--stage", required=True)
    check.add_argument("--check", required=True)
    check.add_argument("--status", choices=["passed", "failed", "unknown"], required=True)
    check.add_argument("--optional", dest="required", action="store_false", default=True)
    check.add_argument("--evidence")
    check.add_argument("--sha256")
    check_fields = ("stage", "check", "status", "required", "evidence", "sha256")
    check.set_defaults(handler=transition_handler("check.recorded", check_fields))

    artifact = mutation_parser(commands, "record-artifact")
    for option in ("name", "path", "sha256"):
        artifact.add_argument(f"--{option}", required=True)
    artifact.add_argument("--kind")
    artifact.add_argument("--stage")
    artifact_fields = ("name", "path", "sha256", "kind", "stage")
    artifact.set_defaults(handler=transition_handler("artifact.recorded", artifact_fields))


def add_control_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    waiting = mutation_parser(commands, "wait-agents")
    waiting.add_argument("--attempt-id", dest="attempt_ids", action="append", required=True)
    waiting.add_argument("--join", choices=["foreground", "detached"], required=True)
    waiting.add_argument("--reason-code", required=True)
    waiting.add_argument("--detach-reason")
    wait_fields = ("attempt_ids", "join", "reason_code", "detach_reason")
    waiting.set_defaults(handler=transition_handler("workflow.waiting_for_agents", wait_fields))

    blocked = mutation_parser(commands, "block")
    for option in ("blocker-id", "reason", "required-action"):
        blocked.add_argument(f"--{option}", required=True)
    block_fields = ("blocker_id", "reason", "required_action")
    blocked.set_defaults(handler=transition_handler("workflow.blocked", block_fields))

    resolved = mutation_parser(commands, "resolve-blocker")
    resolved.add_argument("--blocker-id", required=True)
    resolved.set_defaults(handler=transition_handler("workflow.blocker_resolved", ("blocker_id",)))

    complete = mutation_parser(commands, "complete")
    complete.add_argument("--outcome", choices=["completed", "aborted"], required=True)
    complete.set_defaults(handler=transition_handler("workflow.completed", ("outcome",)))


def add_lease_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    grant = mutation_parser(commands, "grant-review-lease")
    for option in ("lease-id", "stage", "holder-attempt-id", "holder-actor-id"):
        grant.add_argument(f"--{option}", required=True)
    fields = ("lease_id", "stage", "holder_attempt_id", "holder_actor_id")
    grant.set_defaults(handler=transition_handler("review.lease.granted", fields))

    release = mutation_parser(commands, "release-review-lease")
    release.add_argument("--lease-id", required=True)
    release.set_defaults(handler=transition_handler("review.lease.released", ("lease_id",)))


def mutation_parser(
    commands: argparse._SubParsersAction[argparse.ArgumentParser], name: str
) -> argparse.ArgumentParser:
    parser = commands.add_parser(name)
    add_mutation_options(parser)
    return parser


def add_lifecycle_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
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
    migrate.add_argument("--legacy-stage")
    migrate.add_argument("--command-id", default="migrate-v1")
    migrate.add_argument("--actor-kind", default="orchestrator")
    migrate.add_argument("--actor-id", default="root")
    migrate.set_defaults(handler=command_migrate)


def add_read_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    for name, handler in (
        ("validate", command_validate),
        ("status", command_status),
        ("repair", command_repair),
    ):
        command = commands.add_parser(name)
        command.add_argument("--runtime-dir", required=True)
        command.set_defaults(handler=handler)
    history = commands.add_parser("history")
    history.add_argument("--runtime-dir", required=True)
    history.add_argument("--type")
    history.set_defaults(handler=command_history)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Durable semantic event journal for sk-* workflows"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    add_lifecycle_commands(commands)
    add_read_commands(commands)
    add_stage_commands(commands)
    add_gate_commands(commands)
    add_task_commands(commands)
    add_record_commands(commands)
    add_control_commands(commands)
    add_lease_commands(commands)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.handler(args)
    except (OSError, StateError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0
