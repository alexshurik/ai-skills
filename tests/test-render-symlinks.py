#!/usr/bin/env python3
"""Rendered source trees must not follow nested symlinks."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_render import (  # noqa: E402
    MAX_RENDER_SOURCE_BYTES,
    RenderContext,
    copy_rendered,
    link,
)


def assert_rejected(source: Path, destination: Path, operation: str) -> None:
    context = RenderContext("codex", destination.parent, destination.parent)
    try:
        if operation == "copy":
            copy_rendered(source, destination, context)
        else:
            link(source, destination)
    except ValueError as error:
        assert "source symlink" in str(error)
    else:
        raise AssertionError(f"nested source symlink was followed during {operation}")
    assert not destination.exists()
    assert not destination.is_symlink()


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sk-render-symlink-") as temporary:
        root = Path(temporary)
        outside_file = root / "outside.md"
        outside_file.write_text("outside\n", encoding="utf-8")
        outside_dir = root / "outside-dir"
        outside_dir.mkdir()
        (outside_dir / "secret.md").write_text("secret\n", encoding="utf-8")

        file_source = root / "file-source"
        file_source.mkdir()
        (file_source / "nested.md").symlink_to(outside_file)
        assert_rejected(file_source, root / "file-output", "copy")

        directory_source = root / "directory-source"
        directory_source.mkdir()
        (directory_source / "nested").symlink_to(outside_dir, target_is_directory=True)
        assert_rejected(directory_source, root / "directory-output", "copy")
        assert_rejected(directory_source, root / "claude-link", "link")

        oversized = root / "oversized.md"
        with oversized.open("wb") as oversized_file:
            oversized_file.truncate(MAX_RENDER_SOURCE_BYTES + 1)
        context = RenderContext("codex", root, root)
        try:
            copy_rendered(oversized, root / "oversized-output.md", context)
        except ValueError as error:
            assert "size limit" in str(error)
        else:
            raise AssertionError("oversized render source was read")
        assert not (root / "oversized-output.md").exists()

        assert outside_file.read_text(encoding="utf-8") == "outside\n"
        assert (outside_dir / "secret.md").read_text(encoding="utf-8") == "secret\n"


if __name__ == "__main__":
    main()
    print("OK: rendered source symlinks")
