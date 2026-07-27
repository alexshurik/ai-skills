#!/usr/bin/env python3
"""Validate, install, verify, diagnose, and migrate the sk-* skill suite."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable

from skills_common import Issue, load_manifest, tree_entries
from skills_installation import compare_expected, install, uninstall
from skills_validation import validate


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


def doctor(manifest: dict[str, Any], roots: list[Path]) -> list[Issue]:
    issues: list[Issue] = []
    occurrences: dict[str, list[Path]] = {}
    internal_names = {item["name"] for item in manifest["agents"]}
    for root in roots:
        for name, path in installed_skill_dirs(root).items():
            if name.startswith("sk-"):
                occurrences.setdefault(name, []).append(path)
            if name in internal_names:
                issues.append(
                    Issue(
                        "ERROR",
                        f"{name}: internal agent is exposed as a catalog skill in {path}",
                    )
                )
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


def migrate_legacy(
    manifest: dict[str, Any],
    legacy_root: Path,
    backup_root: Path,
) -> list[Path]:
    legacy_root = legacy_root.resolve()
    backup_root = backup_root.resolve()
    if legacy_root == backup_root or legacy_root in backup_root.parents:
        raise ValueError("backup root must be outside the legacy discovery root")
    names = [item["name"] for item in manifest["catalog"]]
    names += [item["name"] for item in manifest["onboarding"]]
    names += [item["name"] for item in manifest["agents"]]
    candidates = [
        legacy_root / name
        for name in names
        if (legacy_root / name / "SKILL.md").is_file()
    ]
    markers = {
        "agents": "sk-developer.md",
        "review-steps": "security.md",
        "shared": "handoff-protocol.md",
        "best-practices": "resolver.md",
    }
    candidates += [
        legacy_root / directory
        for directory, marker in markers.items()
        if (legacy_root / directory / marker).exists()
    ]
    backup_root.mkdir(parents=True, exist_ok=True)
    for candidate in candidates:
        destination = backup_root / candidate.name
        if destination.exists():
            raise ValueError(f"backup destination already exists: {destination}")
    for candidate in candidates:
        shutil.move(str(candidate), str(backup_root / candidate.name))
    return candidates


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
            choices=("codex", "claude", "kimi"),
            required=True,
        )
        command.add_argument("--target", type=Path, required=True)
    doctor_parser = commands.add_parser("doctor")
    doctor_parser.add_argument("--root", action="append", type=Path, required=True)
    uninstall_parser = commands.add_parser("uninstall")
    uninstall_parser.add_argument("--target", type=Path, required=True)
    migrate_parser = commands.add_parser("migrate-legacy")
    migrate_parser.add_argument("--legacy-root", type=Path, required=True)
    migrate_parser.add_argument("--backup-root", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = load_manifest()
    try:
        if args.command == "validate":
            return print_issues(validate(manifest))
        if args.command == "install":
            install(manifest, args.platform, args.target.resolve())
            print(f"Installed {args.platform} tree to {args.target}")
            return 0
        if args.command == "verify":
            return print_issues(
                compare_expected(manifest, args.platform, args.target.resolve())
            )
        if args.command == "doctor":
            roots = [root.resolve() for root in args.root]
            return print_issues(doctor(manifest, roots))
        if args.command == "uninstall":
            result = print_issues(uninstall(args.target.resolve()))
            if result == 0:
                print("Removed receipt-owned installed files")
            return result
        if args.command == "migrate-legacy":
            moved = migrate_legacy(manifest, args.legacy_root, args.backup_root)
            for path in moved:
                print(f"Moved {path}")
            print(f"Backup: {args.backup_root.resolve()}")
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
