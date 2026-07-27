"""Staged installation, receipts, verification, and safe uninstallation."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from skills_common import (
    Issue,
    RECEIPT_NAME,
    REPO_ROOT,
    entry_value,
    source_revision,
    tree_entries,
)
from skills_render import render_tree


def read_receipt(target_root: Path) -> dict[str, Any] | None:
    path = target_root / RECEIPT_NAME
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("files"), dict):
        raise ValueError(f"{path}: receipt has no file ownership map")
    return data


def write_receipt(
    manifest: dict[str, Any],
    platform: str,
    target_root: Path,
    files: dict[str, str],
) -> None:
    commit, dirty = source_revision()
    receipt = {
        "manifest_version": manifest["version"],
        "platform": platform,
        "source_root": str(REPO_ROOT),
        "source_commit": commit,
        "source_dirty": dirty,
        "files": files,
    }
    target_root.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=".sk-skills-receipt-",
        dir=target_root,
        text=True,
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as temporary:
            json.dump(receipt, temporary, indent=2, sort_keys=True)
            temporary.write("\n")
        os.replace(temporary_name, target_root / RECEIPT_NAME)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def safe_relative(value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"unsafe receipt/render path: {value!r}")
    return relative


def legacy_parent_links(target_root: Path, relative: Path) -> list[str]:
    links: list[str] = []
    current = target_root
    for index, part in enumerate(relative.parts[:-1]):
        current /= part
        if current.is_symlink():
            resolved = current.resolve()
            if resolved != REPO_ROOT and REPO_ROOT not in resolved.parents:
                raise ValueError(f"install parent symlink is not source-owned: {current}")
            links.append(Path(*relative.parts[: index + 1]).as_posix())
            break
        if current.exists() and not current.is_dir():
            raise ValueError(f"install parent is not a real directory: {current}")
    return links


def reject_symlink_parents(target_root: Path, relative: Path) -> None:
    current = target_root
    for part in relative.parts[:-1]:
        current /= part
        if current.is_symlink():
            raise ValueError(f"receipt-owned path escapes through symlink: {current}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"receipt-owned parent is not a directory: {current}")


def preflight(
    target_root: Path,
    expected: dict[str, str],
    previous: dict[str, str],
) -> tuple[list[str], list[str]]:
    if target_root.exists() and not target_root.is_dir():
        raise ValueError(f"install target is not a directory: {target_root}")
    legacy_links: set[str] = set()
    for name in expected:
        relative = safe_relative(name)
        legacy_links.update(legacy_parent_links(target_root, relative))
        destination = target_root / relative
        if destination.exists() and destination.is_dir() and not destination.is_symlink():
            raise ValueError(
                f"refusing to replace unowned/non-leaf directory: {destination}"
            )
    stale = sorted(set(previous) - set(expected))
    for name in stale:
        relative = safe_relative(name)
        reject_symlink_parents(target_root, relative)
        destination = target_root / relative
        current = entry_value(destination)
        if current is not None and current != previous[name]:
            raise ValueError(
                f"stale manifest-owned path was modified; preserving it: {destination}"
            )
    return stale, sorted(legacy_links)


def copy_leaf(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or destination.is_file():
        destination.unlink()
    if source.is_symlink():
        destination.symlink_to(source.readlink())
        return
    handle, temporary_name = tempfile.mkstemp(
        prefix=".sk-skills-file-",
        dir=destination.parent,
    )
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def remove_empty_parents(path: Path, target_root: Path) -> None:
    current = path.parent
    while current != target_root and target_root in current.parents:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def snapshot(paths: set[str], target_root: Path, backup_root: Path) -> set[str]:
    existing: set[str] = set()
    for name in sorted(paths):
        source = target_root / safe_relative(name)
        if entry_value(source) is None:
            continue
        existing.add(name)
        copy_leaf(source, backup_root / name)
    receipt = target_root / RECEIPT_NAME
    if receipt.is_file():
        copy_leaf(receipt, backup_root / RECEIPT_NAME)
        existing.add(RECEIPT_NAME)
    return existing


def restore(
    touched: set[str],
    existing: set[str],
    target_root: Path,
    backup_root: Path,
) -> None:
    for name in sorted(touched | {RECEIPT_NAME}, reverse=True):
        destination = target_root / name
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        if name in existing:
            copy_leaf(backup_root / name, destination)
        else:
            remove_empty_parents(destination, target_root)


def apply_staged(
    manifest: dict[str, Any],
    platform: str,
    stage_root: Path,
    target_root: Path,
) -> None:
    expected = tree_entries(stage_root)
    receipt = read_receipt(target_root)
    previous = dict(receipt["files"]) if receipt else {}
    stale, legacy_links = preflight(target_root, expected, previous)
    touched = set(expected) | set(stale) | set(legacy_links)
    shadowed = {
        name
        for name in expected
        if any(name.startswith(f"{link}/") for link in legacy_links)
    }
    target_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sk-skills-rollback-") as temporary:
        backup_root = Path(temporary)
        existing = snapshot(touched - shadowed, target_root, backup_root)
        try:
            for name in legacy_links:
                (target_root / name).unlink()
            for name in sorted(expected):
                copy_leaf(stage_root / name, target_root / name)
            for name in stale:
                destination = target_root / name
                if destination.is_symlink() or destination.is_file():
                    destination.unlink()
                    remove_empty_parents(destination, target_root)
            write_receipt(manifest, platform, target_root, expected)
        except Exception:
            restore(touched, existing, target_root, backup_root)
            raise


def install(manifest: dict[str, Any], platform: str, target_root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="sk-skills-stage-") as temporary:
        stage_root = Path(temporary)
        render_tree(manifest, platform, stage_root, target_root)
        apply_staged(manifest, platform, stage_root, target_root)


def compare_expected(
    manifest: dict[str, Any],
    platform: str,
    target_root: Path,
) -> list[Issue]:
    issues: list[Issue] = []
    try:
        receipt = read_receipt(target_root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [Issue("ERROR", str(error))]
    if receipt is None:
        return [Issue("ERROR", f"installation receipt missing: {target_root / RECEIPT_NAME}")]
    with tempfile.TemporaryDirectory(prefix="sk-skills-expected-") as temporary:
        stage_root = Path(temporary)
        render_tree(manifest, platform, stage_root, target_root)
        expected = tree_entries(stage_root)
    receipt_files = dict(receipt["files"])
    for name in sorted(set(expected) | set(receipt_files)):
        if expected.get(name) != receipt_files.get(name):
            issues.append(Issue("ERROR", f"receipt ownership/hash drift: {name}"))
    for name, expected_value in sorted(expected.items()):
        relative = safe_relative(name)
        reject_symlink_parents(target_root, relative)
        current = entry_value(target_root / relative)
        if current is None:
            issues.append(Issue("ERROR", f"installed file missing: {name}"))
        elif current != expected_value:
            issues.append(Issue("ERROR", f"installed file/link drift: {name}"))
    expected_metadata = {
        "manifest_version": manifest["version"],
        "platform": platform,
        "source_root": str(REPO_ROOT),
    }
    for field, value in expected_metadata.items():
        if receipt.get(field) != value:
            issues.append(Issue("ERROR", f"receipt {field} mismatch"))
    return issues


def uninstall(target_root: Path) -> list[Issue]:
    try:
        receipt = read_receipt(target_root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [Issue("ERROR", str(error))]
    if receipt is None:
        return [Issue("ERROR", f"refusing uninstall without receipt: {target_root}")]
    files = dict(receipt["files"])
    issues: list[Issue] = []
    for name, installed_value in sorted(files.items()):
        relative = safe_relative(name)
        reject_symlink_parents(target_root, relative)
        destination = target_root / relative
        current = entry_value(destination)
        if current is not None and current != installed_value:
            issues.append(
                Issue("ERROR", f"modified manifest-owned path preserved: {destination}")
            )
    if issues:
        return issues
    for name in sorted(files, reverse=True):
        destination = target_root / safe_relative(name)
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
            remove_empty_parents(destination, target_root)
    (target_root / RECEIPT_NAME).unlink(missing_ok=True)
    return []
