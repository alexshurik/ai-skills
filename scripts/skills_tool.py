#!/usr/bin/env python3
"""Validate, install, verify, diagnose, and migrate the sk-* skill suite."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from skills_common import Issue, load_manifest, safe_relative, tree_entries
from skills_installation import (
    UninstallRequest,
    compare_expected,
    install,
    uninstall_many,
)
from skills_render import RenderContext, render_tree
from skills_validation import validate


@dataclass(frozen=True)
class MoveCandidate:
    relative: Path


@dataclass(frozen=True)
class BackupDirectory:
    path: Path
    parent_fd: int
    root_fd: int
    identity: tuple[int, int]


def installed_skill_dirs(root: Path) -> dict[str, Path]:
    if not root.exists():
        return {}
    return {
        child.name: child
        for child in root.iterdir()
        if child.name != ".system"
        and child.is_dir()
        and (child / "SKILL.md").is_file()
    }


def skill_digest(path: Path) -> str:
    payload = json.dumps(tree_entries(path), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def catalog_inventory(roots: list[Path]) -> list[tuple[str, Path]]:
    return [
        (name, path)
        for root in roots
        for name, path in installed_skill_dirs(root).items()
    ]


def internal_agent_issues(
    inventory: list[tuple[str, Path]],
    internal_names: set[str],
) -> list[Issue]:
    return [
        Issue(
            "ERROR",
            f"{name}: internal agent is exposed as a catalog skill in {path}",
        )
        for name, path in inventory
        if name in internal_names
    ]


def duplicate_skill_issues(inventory: list[tuple[str, Path]]) -> list[Issue]:
    occurrences: dict[str, list[Path]] = {}
    for name, path in inventory:
        if name.startswith("sk-"):
            occurrences.setdefault(name, []).append(path)
    issues: list[Issue] = []
    for name, paths in sorted(occurrences.items()):
        if len(paths) < 2:
            continue
        digests = {skill_digest(path) for path in paths}
        state = "conflicting content" if len(digests) > 1 else "duplicate content"
        issues.append(
            Issue(
                "ERROR",
                f"{name}: {state} in {', '.join(map(str, paths))}",
            )
        )
    return issues


def doctor(manifest: dict[str, Any], roots: list[Path]) -> list[Issue]:
    inventory = catalog_inventory(roots)
    internal_names = {item["name"] for item in manifest["agents"]}
    return [
        *internal_agent_issues(inventory, internal_names),
        *duplicate_skill_issues(inventory),
    ]


def legacy_skill_names(manifest: dict[str, Any]) -> set[str]:
    groups = ("catalog", "onboarding", "agents")
    return {item["name"] for group in groups for item in manifest[group]}


def legacy_skill_candidates(
    manifest: dict[str, Any],
    legacy_fd: int,
) -> list[MoveCandidate]:
    candidates: list[MoveCandidate] = []
    for name in sorted(legacy_skill_names(manifest)):
        relative = Path(name)
        metadata = relative_entry_metadata(legacy_fd, relative)
        if metadata is None:
            continue
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"legacy skill must be a real directory: {name}")
        skill_file = relative_entry_metadata(legacy_fd, relative / "SKILL.md")
        if skill_file is None or not stat.S_ISREG(skill_file.st_mode):
            raise ValueError(f"legacy skill must contain a regular SKILL.md: {name}")
        candidates.append(MoveCandidate(relative))
    return candidates


def legacy_resource_candidates(
    manifest: dict[str, Any],
    legacy_root: Path,
    legacy_fd: int,
) -> list[MoveCandidate]:
    skill_names = legacy_skill_names(manifest)
    with tempfile.TemporaryDirectory(prefix="sk-legacy-inventory-") as temporary:
        rendered_root = Path(temporary)
        render_tree(
            manifest,
            RenderContext("codex", rendered_root, legacy_root),
        )
        relative_leaves = sorted(tree_entries(rendered_root))
    candidates: list[MoveCandidate] = []
    for name in relative_leaves:
        relative = safe_relative(name)
        if relative.parts[0] in skill_names:
            continue
        metadata = relative_entry_metadata(legacy_fd, relative)
        if metadata is None:
            continue
        if not stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
            raise ValueError(
                f"legacy resource leaf must be a regular file or symlink: {relative}"
            )
        candidates.append(MoveCandidate(relative))
    return candidates


def no_follow_directory_flags() -> int:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if no_follow is None or directory is None:
        raise ValueError("descriptor-relative no-follow migration is unavailable")
    return os.O_RDONLY | no_follow | directory


def open_child_directory(parent_fd: int, name: str, create: bool) -> int:
    flags = no_follow_directory_flags()
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        if not create:
            raise
    except OSError as error:
        raise ValueError(f"directory path contains a symlink/non-directory: {name}") from error
    os.mkdir(name, mode=0o700, dir_fd=parent_fd)
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except OSError as error:
        raise ValueError(f"created directory changed before opening: {name}") from error


def walk_directories(
    starting_fd: int,
    parts: tuple[str, ...],
    create: bool,
) -> int:
    current = starting_fd
    try:
        for part in parts:
            child = open_child_directory(current, part, create)
            os.close(current)
            current = child
        return current
    except (OSError, ValueError):
        os.close(current)
        raise


def open_absolute_directory(directory: Path, create: bool) -> int:
    if not directory.is_absolute():
        raise ValueError(f"directory path must be absolute: {directory}")
    root_fd = os.open(directory.anchor, no_follow_directory_flags())
    return walk_directories(root_fd, directory.parts[1:], create)


def open_relative_directory(root_fd: int, relative: Path, create: bool) -> int:
    safe = safe_relative(relative.as_posix()) if relative.parts else Path(".")
    parts = () if safe == Path(".") else safe.parts
    return walk_directories(os.dup(root_fd), parts, create)


def relative_entry_metadata(
    root_fd: int,
    relative: Path,
) -> os.stat_result | None:
    try:
        parent_fd = open_relative_directory(root_fd, relative.parent, False)
    except FileNotFoundError:
        return None
    try:
        try:
            return os.stat(
                relative.name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return None
    finally:
        os.close(parent_fd)


def relative_entry_exists(root_fd: int, relative: Path) -> bool:
    return relative_entry_metadata(root_fd, relative) is not None


def create_backup_directory(path: Path) -> BackupDirectory:
    if path.name in {"", ".", ".."}:
        raise ValueError(f"invalid backup root: {path}")
    parent_fd = open_absolute_directory(path.parent, True)
    try:
        os.mkdir(path.name, mode=0o700, dir_fd=parent_fd)
    except FileExistsError as error:
        os.close(parent_fd)
        raise ValueError(f"backup root must not already exist: {path}") from error
    except OSError:
        os.close(parent_fd)
        raise
    try:
        root_fd = open_child_directory(parent_fd, path.name, False)
    except (OSError, ValueError):
        os.rmdir(path.name, dir_fd=parent_fd)
        os.close(parent_fd)
        raise
    metadata = os.fstat(root_fd)
    identity = (metadata.st_dev, metadata.st_ino)
    return BackupDirectory(path, parent_fd, root_fd, identity)


def close_backup_directory(backup: BackupDirectory) -> None:
    os.close(backup.root_fd)
    os.close(backup.parent_fd)


def rename_relative(
    source_fd: int,
    destination_fd: int,
    relative: Path,
) -> None:
    source_parent = open_relative_directory(source_fd, relative.parent, False)
    destination_parent = open_relative_directory(
        destination_fd,
        relative.parent,
        True,
    )
    try:
        if relative_entry_exists(destination_parent, Path(relative.name)):
            raise ValueError(f"migration destination already exists: {relative}")
        os.rename(
            relative.name,
            relative.name,
            src_dir_fd=source_parent,
            dst_dir_fd=destination_parent,
        )
    except OSError as error:
        if error.errno == errno.EXDEV:
            raise ValueError("legacy migration requires one filesystem") from error
        raise
    finally:
        os.close(source_parent)
        os.close(destination_parent)


def move_candidate(
    candidate: MoveCandidate,
    legacy_fd: int,
    backup_fd: int,
) -> None:
    rename_relative(legacy_fd, backup_fd, candidate.relative)


def verify_backup_identity(backup: BackupDirectory) -> None:
    metadata = os.stat(
        backup.path.name,
        dir_fd=backup.parent_fd,
        follow_symlinks=False,
    )
    current = (metadata.st_dev, metadata.st_ino)
    if not stat.S_ISDIR(metadata.st_mode) or current != backup.identity:
        raise ValueError("backup root changed during migration")
    try:
        reopened = open_absolute_directory(backup.path, False)
    except (OSError, ValueError) as error:
        raise ValueError("backup root changed during migration") from error
    try:
        reopened_metadata = os.fstat(reopened)
        reopened_identity = (reopened_metadata.st_dev, reopened_metadata.st_ino)
        if reopened_identity != backup.identity:
            raise ValueError("backup root changed during migration")
    finally:
        os.close(reopened)


def rollback_moves(
    moved: list[MoveCandidate],
    legacy_fd: int,
    backup_fd: int,
) -> None:
    for candidate in reversed(moved):
        rename_relative(backup_fd, legacy_fd, candidate.relative)


def apply_legacy_moves(
    candidates: list[MoveCandidate],
    legacy_fd: int,
    backup: BackupDirectory,
) -> None:
    moved: list[MoveCandidate] = []
    try:
        for candidate in candidates:
            move_candidate(candidate, legacy_fd, backup.root_fd)
            moved.append(candidate)
        verify_backup_identity(backup)
    except (OSError, ValueError):
        rollback_moves(moved, legacy_fd, backup.root_fd)
        raise


def migrate_legacy(
    manifest: dict[str, Any],
    legacy_root: Path,
    backup_root: Path,
) -> list[Path]:
    legacy_root = legacy_root.resolve()
    backup_root = backup_root.absolute()
    if legacy_root == backup_root or legacy_root in backup_root.parents:
        raise ValueError("backup root must be outside the legacy discovery root")
    legacy_fd = open_absolute_directory(legacy_root, False)
    try:
        candidates = [
            *legacy_skill_candidates(manifest, legacy_fd),
            *legacy_resource_candidates(manifest, legacy_root, legacy_fd),
        ]
        backup = create_backup_directory(backup_root)
        try:
            apply_legacy_moves(candidates, legacy_fd, backup)
        finally:
            close_backup_directory(backup)
    finally:
        os.close(legacy_fd)
    return [legacy_root / candidate.relative for candidate in candidates]


def print_issues(issues: Iterable[Issue]) -> int:
    collected = list(issues)
    if not collected:
        print("OK")
        return 0
    for issue in collected:
        print(f"{issue.level}: {issue.message}")
    return 1 if any(issue.level == "ERROR" for issue in collected) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    for name in ("install", "verify"):
        command = commands.add_parser(name)
        command.add_argument(
            "--platform",
            choices=("codex", "cursor", "claude", "kimi"),
            required=True,
        )
        command.add_argument("--target", type=Path, required=True)
    doctor_parser = commands.add_parser("doctor")
    doctor_parser.add_argument("--root", action="append", type=Path, required=True)
    uninstall_parser = commands.add_parser("uninstall")
    uninstall_parser.add_argument(
        "--target",
        action="append",
        nargs=2,
        metavar=("PLATFORM", "PATH"),
        required=True,
    )
    uninstall_parser.add_argument("--missing-ok", action="store_true")
    migrate_parser = commands.add_parser("migrate-legacy")
    migrate_parser.add_argument("--legacy-root", type=Path, required=True)
    migrate_parser.add_argument("--backup-root", type=Path, required=True)
    return parser


def run_uninstall(args: argparse.Namespace, manifest: dict[str, Any]) -> int:
    requests = [
        UninstallRequest(platform, Path(target).resolve(), manifest["version"])
        for platform, target in args.target
    ]
    result = print_issues(uninstall_many(requests, args.missing_ok))
    if result == 0:
        print("Removed receipt-owned installed files")
    return result


def run_manifest_command(
    args: argparse.Namespace,
    manifest: dict[str, Any],
) -> int:
    if args.command == "install":
        install(manifest, args.platform, args.target.resolve())
        print(f"Installed {args.platform} tree to {args.target}")
        return 0
    if args.command == "verify":
        return print_issues(
            compare_expected(manifest, args.platform, args.target.resolve())
        )
    if args.command == "doctor":
        return print_issues(doctor(manifest, [root.resolve() for root in args.root]))
    moved = migrate_legacy(manifest, args.legacy_root, args.backup_root)
    for path in moved:
        print(f"Moved {path}")
    print(f"Backup: {args.backup_root.resolve()}")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "uninstall":
            return run_uninstall(args, load_manifest())
        manifest = load_manifest()
        validation_issues = validate(manifest)
        if args.command == "validate" or validation_issues:
            return print_issues(validation_issues)
        return run_manifest_command(args, manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
