#!/usr/bin/env python3
"""Evidence reads must fail closed on ancestor symlinks and large files."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "shared" / "review-evidence"))

from collect_change_evidence import (  # noqa: E402
    MAX_EVIDENCE_FILE_BYTES,
    inspect_current_entry,
)


def assert_ancestor_symlink_rejected(root: Path, label: str, outside: Path) -> None:
    parent = root / label
    parent.symlink_to(outside, target_is_directory=True)
    entry = inspect_current_entry(root, f"{label}/secret.py")
    assert entry.kind == "ancestor-symlink"
    assert entry.content is None
    assert entry.symlink_target is None
    assert "EXTERNAL_SECRET" not in repr(entry)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sk-evidence-safe-") as temporary:
        root = Path(temporary) / "repo"
        outside = Path(temporary) / "outside"
        root.mkdir()
        outside.mkdir()
        (outside / "secret.py").write_text(
            "EXTERNAL_SECRET = True\n    from outside import secret\n",
            encoding="utf-8",
        )
        assert_ancestor_symlink_rejected(root, "tracked-parent", outside)
        assert_ancestor_symlink_rejected(root, "untracked-parent", outside)

        oversized = root / "oversized.py"
        with oversized.open("wb") as oversized_file:
            oversized_file.truncate(MAX_EVIDENCE_FILE_BYTES + 1)
        entry = inspect_current_entry(root, "oversized.py")
        assert entry.kind == "regular"
        assert entry.content is None
        assert entry.read_status == "size-limit"


if __name__ == "__main__":
    main()
    print("OK: evidence path safety")
