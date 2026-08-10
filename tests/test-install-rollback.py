#!/usr/bin/env python3
"""Verify receipt-write failure restores prior files, stale paths, and receipt."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import skills_installation  # noqa: E402
from skills_common import RECEIPT_NAME, load_manifest, tree_entries  # noqa: E402


def main() -> None:
    manifest = load_manifest()
    with tempfile.TemporaryDirectory(prefix="sk-install-rollback-") as temporary:
        target = Path(temporary) / "skills"
        skills_installation.install(manifest, "codex", target)

        edited = target / "sk-team-help" / "SKILL.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nlocal edit\n")
        stale = target / "agents" / "stale-owned.md"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale\n", encoding="utf-8")

        receipt_path = target / RECEIPT_NAME
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["files"]["agents/stale-owned.md"] = hashlib.sha256(b"stale\n").hexdigest()
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        before_entries = tree_entries(target)
        before_receipt = receipt_path.read_bytes()

        with mock.patch.object(
            skills_installation,
            "write_receipt",
            side_effect=OSError("injected receipt failure"),
        ):
            try:
                skills_installation.install(manifest, "codex", target)
            except OSError as error:
                assert "injected receipt failure" in str(error)
            else:
                raise AssertionError("expected injected install failure")

        assert tree_entries(target) == before_entries
        assert receipt_path.read_bytes() == before_receipt


if __name__ == "__main__":
    main()
    print("OK: install rollback")
