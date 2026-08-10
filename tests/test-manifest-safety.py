#!/usr/bin/env python3
"""Regression checks for manifest path confinement and rendered reference closure."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_common import load_manifest  # noqa: E402
from skills_validation import validate  # noqa: E402


def error_messages(manifest: Any) -> list[str]:
    return [issue.message for issue in validate(manifest) if issue.level == "ERROR"]


def main() -> None:
    manifest = load_manifest()
    assert error_messages(manifest) == []

    escaping_source = copy.deepcopy(manifest)
    escaping_source["catalog"][0]["source"] = "../outside"
    assert any(
        "unsafe manifest/receipt path" in message for message in error_messages(escaping_source)
    )

    escaping_target = copy.deepcopy(manifest)
    escaping_target["resources"][0]["codex_target"] = "../../outside"
    assert any(
        "unsafe manifest/receipt path" in message for message in error_messages(escaping_target)
    )

    absolute_target = copy.deepcopy(manifest)
    absolute_target["resources"][0]["kimi_target"] = "/tmp/outside"
    assert any(
        "unsafe manifest/receipt path" in message for message in error_messages(absolute_target)
    )

    missing_version = copy.deepcopy(manifest)
    del missing_version["version"]
    assert any("manifest version" in message for message in error_messages(missing_version))

    missing_limit = copy.deepcopy(manifest)
    del missing_limit["limits"]["catalog_skill_lines"]
    assert any("catalog_skill_lines" in message for message in error_messages(missing_limit))

    malformed_item = copy.deepcopy(manifest)
    malformed_item["catalog"][0] = "not an object"
    assert any(
        "manifest catalog item 0 must be an object" in message
        for message in error_messages(malformed_item)
    )

    assert "manifest root must be an object" in error_messages([])


if __name__ == "__main__":
    main()
    print("OK: manifest safety")
