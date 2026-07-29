"""Staged installation, receipts, verification, and safe uninstallation."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skills_common import (
    Issue,
    RECEIPT_NAME,
    REPO_ROOT,
    entry_value,
    safe_relative,
    source_revision,
    tree_entries,
)
from skills_render import RenderContext, render_tree


RECEIPT_VERSION = 1
SUITE_ID = "sk-skills"
MAX_RECEIPT_BYTES = 4 * 1024 * 1024
SUPPORTED_MANIFEST_VERSIONS = frozenset({1})
SUPPORTED_PLATFORMS = frozenset({"codex", "cursor", "claude", "kimi"})
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
RECEIPT_FIELDS = frozenset(
    {
        "receipt_version",
        "suite",
        "manifest_version",
        "platform",
        "source_root",
        "source_commit",
        "source_dirty",
        "files",
    }
)


@dataclass(frozen=True)
class InstallationReceipt:
    receipt_version: int
    suite: str
    manifest_version: int
    platform: str
    source_root: str
    source_commit: str
    source_dirty: bool
    files: dict[str, str]


@dataclass(frozen=True)
class ReceiptExpectation:
    platform: str
    manifest_version: int


@dataclass(frozen=True)
class UninstallPlan:
    target_root: Path
    files: dict[str, str]


@dataclass(frozen=True)
class UninstallRequest:
    platform: str
    target_root: Path
    manifest_version: int


@dataclass(frozen=True)
class InstallRequest:
    manifest: dict[str, Any]
    platform: str
    target_root: Path


@dataclass(frozen=True)
class StagedPlan:
    request: InstallRequest
    stage_root: Path
    expected: dict[str, str]
    stale: tuple[str, ...]
    legacy_links: tuple[str, ...]
    touched: frozenset[str]
    shadowed: frozenset[str]


@dataclass(frozen=True)
class RollbackSnapshot:
    target_root: Path
    backup_root: Path
    touched: frozenset[str]
    existing: frozenset[str]


def receipt_expectation(request: InstallRequest) -> ReceiptExpectation:
    return ReceiptExpectation(request.platform, request.manifest["version"])


def read_regular_json(path: Path) -> object:
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValueError(f"{path}: receipt must be a regular, non-symlink file")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as receipt_file:
        opened = os.fstat(receipt_file.fileno())
        identity = (before.st_dev, before.st_ino)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError(f"{path}: receipt changed while opening")
        if identity != (opened.st_dev, opened.st_ino):
            raise ValueError(f"{path}: receipt changed while opening")
        if opened.st_size > MAX_RECEIPT_BYTES:
            raise ValueError(f"{path}: receipt exceeds the size limit")
        content = receipt_file.read(MAX_RECEIPT_BYTES + 1)
        if len(content) > MAX_RECEIPT_BYTES:
            raise ValueError(f"{path}: receipt exceeds the size limit")
        return json.loads(content)


def validate_receipt_path(name: object, path: Path) -> str:
    if not isinstance(name, str) or not name or "\\" in name or "\0" in name:
        raise ValueError(f"{path}: receipt contains an unsafe file key")
    relative = safe_relative(name)
    if relative.as_posix() != name:
        raise ValueError(f"{path}: receipt contains a non-canonical file key: {name!r}")
    return name


def validate_receipt_value(value: object, path: Path) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path}: receipt ownership values must be strings")
    if HASH_RE.fullmatch(value):
        return value
    if value.startswith("symlink:"):
        target = value.removeprefix("symlink:")
        if target and not any(marker in target for marker in ("\0", "\r", "\n")):
            return value
    raise ValueError(f"{path}: receipt contains an invalid hash/symlink value")


def validate_receipt_files(value: object, path: Path) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{path}: receipt has no file ownership map")
    return {
        validate_receipt_path(name, path): validate_receipt_value(item, path)
        for name, item in value.items()
    }


def receipt_versions(data: dict[object, object], path: Path) -> tuple[int, int]:
    integers = ("receipt_version", "manifest_version")
    if any(
        not isinstance(data[field], int) or isinstance(data[field], bool)
        for field in integers
    ):
        raise ValueError(f"{path}: receipt versions must be integers")
    return data["receipt_version"], data["manifest_version"]


def receipt_strings(data: dict[object, object], path: Path) -> tuple[str, ...]:
    strings = ("suite", "platform", "source_root", "source_commit")
    if any(not isinstance(data[field], str) or not data[field] for field in strings):
        raise ValueError(f"{path}: receipt identity/provenance fields must be strings")
    return tuple(data[field] for field in strings)


def typed_receipt(data: object, path: Path) -> InstallationReceipt:
    if not isinstance(data, dict) or set(data) != RECEIPT_FIELDS:
        raise ValueError(f"{path}: receipt schema fields are incomplete or unknown")
    receipt_version, manifest_version = receipt_versions(data, path)
    suite, platform, source_root, source_commit = receipt_strings(data, path)
    source_dirty = data["source_dirty"]
    if not isinstance(source_dirty, bool):
        raise ValueError(f"{path}: receipt source_dirty must be a boolean")
    return InstallationReceipt(
        receipt_version,
        suite,
        manifest_version,
        platform,
        source_root,
        source_commit,
        source_dirty,
        validate_receipt_files(data["files"], path),
    )


def validate_receipt_identity(
    receipt: InstallationReceipt,
    path: Path,
    expected: ReceiptExpectation | None,
) -> None:
    if receipt.receipt_version != RECEIPT_VERSION or receipt.suite != SUITE_ID:
        raise ValueError(f"{path}: receipt is not owned by this suite/version")
    if receipt.manifest_version not in SUPPORTED_MANIFEST_VERSIONS:
        raise ValueError(f"{path}: unsupported receipt manifest version")
    if receipt.platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"{path}: unsupported receipt platform")
    if expected is None:
        return
    if receipt.manifest_version != expected.manifest_version:
        raise ValueError(f"{path}: receipt manifest version does not match request")
    if receipt.platform != expected.platform:
        raise ValueError(f"{path}: receipt platform does not match request")


def read_receipt(
    target_root: Path,
    expected: ReceiptExpectation | None = None,
) -> InstallationReceipt | None:
    path = target_root / RECEIPT_NAME
    if expected is not None:
        if expected.platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"{path}: unsupported requested platform")
        if expected.manifest_version not in SUPPORTED_MANIFEST_VERSIONS:
            raise ValueError(f"{path}: unsupported requested manifest version")
    try:
        data = read_regular_json(path)
    except FileNotFoundError:
        return None
    receipt = typed_receipt(data, path)
    validate_receipt_identity(receipt, path, expected)
    return receipt


def write_receipt(
    request: InstallRequest,
    files: dict[str, str],
) -> None:
    commit, dirty = source_revision()
    receipt = {
        "receipt_version": RECEIPT_VERSION,
        "suite": SUITE_ID,
        "manifest_version": request.manifest["version"],
        "platform": request.platform,
        "source_root": str(REPO_ROOT),
        "source_commit": commit,
        "source_dirty": dirty,
        "files": files,
    }
    request.target_root.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=".sk-skills-receipt-",
        dir=request.target_root,
        text=True,
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as temporary:
            json.dump(receipt, temporary, indent=2, sort_keys=True)
            temporary.write("\n")
        os.replace(temporary_name, request.target_root / RECEIPT_NAME)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


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


def expected_leaf_legacy_links(
    target_root: Path,
    name: str,
    previous: dict[str, str],
) -> list[str]:
    relative = safe_relative(name)
    parent_links = legacy_parent_links(target_root, relative)
    if parent_links:
        return parent_links
    destination = target_root / relative
    if destination.exists() and destination.is_dir() and not destination.is_symlink():
        raise ValueError(f"refusing to replace unowned/non-leaf directory: {destination}")
    if name not in previous and entry_value(destination) is not None:
        raise ValueError(f"refusing to replace unowned leaf: {destination}")
    return []


def validate_stale_leaf(
    target_root: Path,
    name: str,
    installed_value: str,
) -> None:
    relative = safe_relative(name)
    reject_symlink_parents(target_root, relative)
    destination = target_root / relative
    current = entry_value(destination)
    if current is not None and current != installed_value:
        raise ValueError(f"stale manifest-owned path was modified; preserving it: {destination}")


def preflight(
    target_root: Path,
    expected: dict[str, str],
    previous: dict[str, str],
) -> tuple[list[str], list[str]]:
    if target_root.exists() and not target_root.is_dir():
        raise ValueError(f"install target is not a directory: {target_root}")
    legacy_links = {
        link
        for name in expected
        for link in expected_leaf_legacy_links(target_root, name, previous)
    }
    stale = sorted(set(previous) - set(expected))
    for name in stale:
        validate_stale_leaf(target_root, name, previous[name])
    return stale, sorted(legacy_links)


def copy_leaf(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=".sk-skills-file-",
        dir=destination.parent,
    )
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        if source.is_symlink():
            temporary.unlink()
            temporary.symlink_to(source.readlink())
        else:
            shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


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


def restore(rollback: RollbackSnapshot) -> None:
    for name in sorted(rollback.touched | {RECEIPT_NAME}, reverse=True):
        destination = rollback.target_root / name
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        if name in rollback.existing:
            copy_leaf(rollback.backup_root / name, destination)
        else:
            remove_empty_parents(destination, rollback.target_root)


def build_staged_plan(
    request: InstallRequest,
    stage_root: Path,
) -> StagedPlan:
    expected = tree_entries(stage_root)
    receipt = read_receipt(request.target_root, receipt_expectation(request))
    previous = dict(receipt.files) if receipt else {}
    stale, legacy_links = preflight(request.target_root, expected, previous)
    touched = set(expected) | set(stale) | set(legacy_links)
    shadowed = {
        name
        for name in expected
        if any(name.startswith(f"{link}/") for link in legacy_links)
    }
    return StagedPlan(
        request,
        stage_root,
        expected,
        tuple(stale),
        tuple(legacy_links),
        frozenset(touched),
        frozenset(shadowed),
    )


def apply_plan_files(plan: StagedPlan) -> None:
    target_root = plan.request.target_root
    for name in plan.legacy_links:
        (target_root / name).unlink()
    for name in sorted(plan.expected):
        copy_leaf(plan.stage_root / name, target_root / name)
    for name in plan.stale:
        destination = target_root / name
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
            remove_empty_parents(destination, target_root)


def apply_staged(request: InstallRequest, stage_root: Path) -> None:
    plan = build_staged_plan(request, stage_root)
    request.target_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sk-skills-rollback-") as temporary:
        backup_root = Path(temporary)
        existing = snapshot(
            set(plan.touched - plan.shadowed),
            request.target_root,
            backup_root,
        )
        rollback = RollbackSnapshot(
            request.target_root,
            backup_root,
            plan.touched,
            frozenset(existing),
        )
        try:
            apply_plan_files(plan)
            write_receipt(request, plan.expected)
        except (OSError, TypeError, ValueError):
            restore(rollback)
            raise


def install(manifest: dict[str, Any], platform: str, target_root: Path) -> None:
    request = InstallRequest(manifest, platform, target_root)
    with tempfile.TemporaryDirectory(prefix="sk-skills-stage-") as temporary:
        stage_root = Path(temporary)
        context = RenderContext(platform, stage_root, target_root)
        render_tree(manifest, context)
        apply_staged(request, stage_root)


def expected_tree(request: InstallRequest) -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="sk-skills-expected-") as temporary:
        stage_root = Path(temporary)
        context = RenderContext(request.platform, stage_root, request.target_root)
        render_tree(request.manifest, context)
        return tree_entries(stage_root)


def receipt_drift(
    expected: dict[str, str],
    receipt_files: dict[str, str],
) -> list[Issue]:
    return [
        Issue("ERROR", f"receipt ownership/hash drift: {name}")
        for name in sorted(set(expected) | set(receipt_files))
        if expected.get(name) != receipt_files.get(name)
    ]


def installed_tree_drift(
    target_root: Path,
    expected: dict[str, str],
) -> list[Issue]:
    issues: list[Issue] = []
    for name, expected_value in sorted(expected.items()):
        relative = safe_relative(name)
        reject_symlink_parents(target_root, relative)
        current = entry_value(target_root / relative)
        if current is None:
            issues.append(Issue("ERROR", f"installed file missing: {name}"))
        elif current != expected_value:
            issues.append(Issue("ERROR", f"installed file/link drift: {name}"))
    return issues


def receipt_metadata_drift(
    request: InstallRequest,
    receipt: InstallationReceipt,
) -> list[Issue]:
    expected = {
        "source_root": str(REPO_ROOT),
    }
    return [
        Issue("ERROR", f"receipt {field} mismatch")
        for field, value in expected.items()
        if getattr(receipt, field) != value
    ]


def compare_expected(
    manifest: dict[str, Any],
    platform: str,
    target_root: Path,
) -> list[Issue]:
    request = InstallRequest(manifest, platform, target_root)
    try:
        receipt = read_receipt(target_root, receipt_expectation(request))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [Issue("ERROR", str(error))]
    if receipt is None:
        return [Issue("ERROR", f"installation receipt missing: {target_root / RECEIPT_NAME}")]
    expected = expected_tree(request)
    receipt_files = dict(receipt.files)
    return [
        *receipt_drift(expected, receipt_files),
        *installed_tree_drift(target_root, expected),
        *receipt_metadata_drift(request, receipt),
    ]


def plan_uninstall(
    request: UninstallRequest,
    missing_ok: bool,
) -> tuple[UninstallPlan | None, list[Issue]]:
    target_root = request.target_root
    expected = ReceiptExpectation(request.platform, request.manifest_version)
    try:
        receipt = read_receipt(target_root, expected)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [Issue("ERROR", str(error))]
    if receipt is None:
        if missing_ok:
            return None, []
        message = f"refusing uninstall without receipt: {target_root}"
        return None, [Issue("ERROR", message)]
    files = dict(receipt.files)
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
    return UninstallPlan(target_root, files), issues


def apply_uninstall(plan: UninstallPlan) -> None:
    for name in sorted(plan.files, reverse=True):
        destination = plan.target_root / safe_relative(name)
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
            remove_empty_parents(destination, plan.target_root)
    (plan.target_root / RECEIPT_NAME).unlink(missing_ok=True)


def uninstall_many(
    requests: list[UninstallRequest],
    missing_ok: bool = False,
) -> list[Issue]:
    plans: list[UninstallPlan] = []
    issues: list[Issue] = []
    for request in requests:
        plan, target_issues = plan_uninstall(request, missing_ok)
        issues.extend(target_issues)
        if plan is not None:
            plans.append(plan)
    if issues:
        return issues
    for plan in plans:
        apply_uninstall(plan)
    return []
