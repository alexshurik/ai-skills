#!/usr/bin/env python3
"""Legacy migration must rollback failures and resist backup redirection."""

from __future__ import annotations

import sys
import tempfile
import os
import stat
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import skills_tool  # noqa: E402
from skills_common import load_manifest, tree_entries  # noqa: E402


SKILLS = ("sk-code-review", "sk-copy-context")


def make_legacy(root: Path) -> None:
    for name in SKILLS:
        skill = root / name / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(f"{name}\n", encoding="utf-8")


def assert_legacy_intact(root: Path) -> None:
    for name in SKILLS:
        assert (root / name / "SKILL.md").read_text() == f"{name}\n"


def assert_no_owned_backup_files(root: Path) -> None:
    if root.is_dir() and not root.is_symlink():
        assert tree_entries(root) == {}


def assert_later_failure_rolls_back(manifest: dict[str, object], root: Path) -> None:
    legacy = root / "legacy-failure"
    backup = root / "backup-failure"
    legacy.mkdir()
    make_legacy(legacy)
    original = skills_tool.move_candidate
    calls = 0

    def fail_second(*args: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("injected later-candidate failure")
        original(*args)

    with mock.patch.object(skills_tool, "move_candidate", side_effect=fail_second):
        try:
            skills_tool.migrate_legacy(manifest, legacy, backup)
        except ValueError as error:
            assert "injected later-candidate failure" in str(error)
        else:
            raise AssertionError("expected injected migration failure")
    assert_legacy_intact(legacy)
    assert_no_owned_backup_files(backup)


def assert_redirect_rolls_back(manifest: dict[str, object], root: Path) -> None:
    legacy = root / "legacy-redirect"
    backup = root / "redirect-parent" / "backup"
    displaced = root / "displaced-parent"
    outside = root / "outside"
    legacy.mkdir()
    outside.mkdir()
    make_legacy(legacy)
    original = skills_tool.move_candidate
    redirected = False

    def redirect_once(*args: object) -> None:
        nonlocal redirected
        original(*args)
        if not redirected:
            backup.parent.rename(displaced)
            backup.parent.symlink_to(outside, target_is_directory=True)
            redirected = True

    with mock.patch.object(skills_tool, "move_candidate", side_effect=redirect_once):
        try:
            skills_tool.migrate_legacy(manifest, legacy, backup)
        except ValueError as error:
            assert "backup root changed" in str(error)
        else:
            raise AssertionError("expected redirected backup failure")
    assert_legacy_intact(legacy)
    assert tree_entries(outside) == {}
    assert_no_owned_backup_files(displaced / "backup")


def assert_static_symlink_rejected(manifest: dict[str, object], root: Path) -> None:
    legacy = root / "legacy-static"
    outside = root / "outside-static"
    backup = root / "backup-static"
    legacy.mkdir()
    outside.mkdir()
    make_legacy(legacy)
    backup.symlink_to(outside, target_is_directory=True)
    try:
        skills_tool.migrate_legacy(manifest, legacy, backup)
    except (OSError, ValueError):
        pass
    else:
        raise AssertionError("expected static backup symlink rejection")
    assert_legacy_intact(legacy)
    assert tree_entries(outside) == {}


def assert_invalid_resource_leaves(
    manifest: dict[str, object],
    root: Path,
) -> None:
    for kind in ("directory", "fifo"):
        legacy = root / f"legacy-resource-{kind}"
        leaf = legacy / "best-practices" / "resolver.md"
        leaf.parent.mkdir(parents=True)
        if kind == "directory":
            leaf.mkdir()
        else:
            os.mkfifo(leaf)
        backup = root / f"backup-resource-{kind}"
        try:
            skills_tool.migrate_legacy(manifest, legacy, backup)
        except ValueError as error:
            assert "regular file or symlink" in str(error)
        else:
            raise AssertionError(f"expected {kind} resource leaf rejection")
        metadata = leaf.lstat()
        expected = stat.S_ISDIR if kind == "directory" else stat.S_ISFIFO
        assert expected(metadata.st_mode)
        assert not backup.exists()


def assert_invalid_skill_shapes(
    manifest: dict[str, object],
    root: Path,
) -> None:
    outside = root / "outside-skill"
    outside.mkdir()
    (outside / "SKILL.md").write_text("outside\n", encoding="utf-8")
    cases = ("symlink-directory", "missing-skill", "symlink-skill")
    for kind in cases:
        legacy = root / f"legacy-skill-{kind}"
        legacy.mkdir()
        skill = legacy / "sk-code-review"
        if kind == "symlink-directory":
            skill.symlink_to(outside, target_is_directory=True)
        else:
            skill.mkdir()
            if kind == "symlink-skill":
                (skill / "SKILL.md").symlink_to(outside / "SKILL.md")
        backup = root / f"backup-skill-{kind}"
        try:
            skills_tool.migrate_legacy(manifest, legacy, backup)
        except ValueError as error:
            assert "legacy skill" in str(error)
        else:
            raise AssertionError(f"expected {kind} skill rejection")
        assert not backup.exists()
        assert (outside / "SKILL.md").read_text() == "outside\n"


def main() -> None:
    manifest = load_manifest()
    with tempfile.TemporaryDirectory(prefix="sk-migration-atomic-") as temporary:
        root = Path(temporary).resolve()
        assert_later_failure_rolls_back(manifest, root)
        assert_redirect_rolls_back(manifest, root)
        assert_static_symlink_rejected(manifest, root)
        assert_invalid_resource_leaves(manifest, root)
        assert_invalid_skill_shapes(manifest, root)


if __name__ == "__main__":
    main()
    print("OK: migration atomicity")
