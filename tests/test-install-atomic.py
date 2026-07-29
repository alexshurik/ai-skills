#!/usr/bin/env python3
"""A failed replacement must leave the previous live leaf intact."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_installation import copy_leaf  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sk-install-atomic-") as temporary:
        root = Path(temporary)
        source = root / "source.md"
        destination = root / "destination.md"
        source.write_text("new\n", encoding="utf-8")
        destination.write_text("existing\n", encoding="utf-8")

        with mock.patch(
            "skills_installation.shutil.copy2",
            side_effect=OSError("injected copy failure"),
        ):
            try:
                copy_leaf(source, destination)
            except OSError as error:
                assert "injected copy failure" in str(error)
            else:
                raise AssertionError("expected injected copy failure")

        assert destination.read_text(encoding="utf-8") == "existing\n"


if __name__ == "__main__":
    main()
    print("OK: atomic leaf replacement")
