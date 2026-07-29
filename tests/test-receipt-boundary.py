#!/usr/bin/env python3
"""Untrusted receipts must never authorize overwrite or deletion."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_common import RECEIPT_NAME, load_manifest, tree_entries  # noqa: E402
from skills_installation import (  # noqa: E402
    MAX_RECEIPT_BYTES,
    UninstallRequest,
    compare_expected,
    install,
    uninstall_many,
)


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def receipt_payload(
    manifest_version: int,
    files: dict[str, object],
    overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "receipt_version": 1,
        "suite": "sk-skills",
        "manifest_version": manifest_version,
        "platform": "codex",
        "source_root": str(REPO_ROOT),
        "source_commit": "test",
        "source_dirty": False,
        "files": files,
    }
    payload.update(overrides or {})
    return payload


def target_with_receipt(
    root: Path,
    name: str,
    payload: dict[str, object],
) -> Path:
    target = root / name
    owned = target / "sk-team-help" / "SKILL.md"
    owned.parent.mkdir(parents=True)
    owned.write_text("keep\n", encoding="utf-8")
    receipt = target / RECEIPT_NAME
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    receipt.write_text(serialized, encoding="utf-8")
    return target


def target_with_symlink_receipt(
    root: Path,
    name: str,
    payload: dict[str, object],
) -> Path:
    target = target_with_receipt(root, name, payload)
    receipt = target / RECEIPT_NAME
    outside = root / f"{name}-outside-receipt.json"
    outside.write_bytes(receipt.read_bytes())
    receipt.unlink()
    receipt.symlink_to(outside)
    return target


def assert_refuses_without_mutation(
    target: Path,
    action: Callable[[], object],
) -> None:
    before = tree_entries(target)
    try:
        result = action()
    except (OSError, ValueError, json.JSONDecodeError):
        result = None
    else:
        if isinstance(result, list):
            assert result, "unsafe receipt was accepted without an issue"
        else:
            raise AssertionError("unsafe receipt was accepted")
    assert tree_entries(target) == before


def owned_files() -> dict[str, object]:
    return {"sk-team-help/SKILL.md": digest(b"keep\n")}


def unsafe_install_receipts(manifest_version: int) -> dict[str, dict[str, object]]:
    owned = owned_files()
    return {
        "foreign": receipt_payload(
            manifest_version,
            owned,
            {"suite": "another-suite"},
        ),
        "wrong-platform": receipt_payload(
            manifest_version,
            owned,
            {"platform": "kimi"},
        ),
        "wrong-manifest": receipt_payload(manifest_version + 1, owned),
        "invalid-value": receipt_payload(
            manifest_version,
            {"sk-team-help/SKILL.md": 7},
        ),
        "invalid-link": receipt_payload(
            manifest_version,
            {"sk-team-help/SKILL.md": "symlink:"},
        ),
        "unsafe-key": receipt_payload(
            manifest_version,
            {"../outside.md": digest(b"keep\n")},
        ),
        "noncanonical-key": receipt_payload(
            manifest_version,
            {"sk-team-help//SKILL.md": digest(b"keep\n")},
        ),
        "invalid-dirty": receipt_payload(
            manifest_version,
            owned,
            {"source_dirty": "false"},
        ),
    }


def assert_install_receipts(
    root: Path,
    manifest: dict[str, object],
    manifest_version: int,
) -> None:
    for name, payload in unsafe_install_receipts(manifest_version).items():
        target = target_with_receipt(root, f"install-{name}", payload)
        assert_refuses_without_mutation(
            target,
            lambda target=target: install(
                copy.deepcopy(manifest),
                "codex",
                target,
            ),
        )

    symlink_target = target_with_symlink_receipt(
        root,
        "install-symlink",
        receipt_payload(manifest_version, owned_files()),
    )
    assert_refuses_without_mutation(
        symlink_target,
        lambda: install(copy.deepcopy(manifest), "codex", symlink_target),
    )


    nonregular_target = target_with_receipt(
        root,
        "install-nonregular",
        receipt_payload(manifest_version, owned_files()),
    )
    nonregular_receipt = nonregular_target / RECEIPT_NAME
    nonregular_receipt.unlink()
    nonregular_receipt.mkdir()
    assert_refuses_without_mutation(
        nonregular_target,
        lambda: install(copy.deepcopy(manifest), "codex", nonregular_target),
    )


def assert_verify_receipt(
    root: Path,
    manifest: dict[str, object],
    manifest_version: int,
) -> None:
    payload = receipt_payload(
        manifest_version,
        owned_files(),
        {"platform": "kimi"},
    )
    target = target_with_receipt(root, "verify-wrong-platform", payload)
    before = tree_entries(target)
    assert compare_expected(manifest, "codex", target)
    assert tree_entries(target) == before


def assert_uninstall_receipts(root: Path, manifest_version: int) -> None:
    cases = {
        "foreign": receipt_payload(
            manifest_version,
            owned_files(),
            {"suite": "another-suite"},
        ),
        "malformed": receipt_payload(
            manifest_version,
            {"sk-team-help/SKILL.md": "not-a-digest"},
        ),
    }
    for name, payload in cases.items():
        target = target_with_receipt(root, f"uninstall-{name}", payload)
        assert_refuses_without_mutation(
            target,
            lambda target=target: uninstall_many(
                [UninstallRequest("codex", target, manifest_version)]
            ),
        )

    target = target_with_symlink_receipt(
        root,
        "uninstall-symlink",
        receipt_payload(manifest_version, owned_files()),
    )
    assert_refuses_without_mutation(
        target,
        lambda: uninstall_many(
            [UninstallRequest("codex", target, manifest_version)]
        ),
    )

    wrong_platform = target_with_receipt(
        root,
        "uninstall-wrong-platform",
        receipt_payload(
            manifest_version,
            owned_files(),
            {"platform": "kimi"},
        ),
    )
    assert_refuses_without_mutation(
        wrong_platform,
        lambda: uninstall_many(
            [UninstallRequest("codex", wrong_platform, manifest_version)]
        ),
    )

    oversized = target_with_receipt(
        root,
        "uninstall-oversized",
        receipt_payload(manifest_version, owned_files()),
    )
    receipt = oversized / RECEIPT_NAME
    with receipt.open("wb") as receipt_file:
        receipt_file.truncate(MAX_RECEIPT_BYTES + 1)
    assert_refuses_without_mutation(
        oversized,
        lambda: uninstall_many(
            [UninstallRequest("codex", oversized, manifest_version)]
        ),
    )


def assert_wrong_platform_blocks_all(root: Path, manifest_version: int) -> None:
    valid = target_with_receipt(
        root,
        "uninstall-valid-first",
        receipt_payload(manifest_version, owned_files()),
    )
    wrong = target_with_receipt(
        root,
        "uninstall-wrong-second",
        receipt_payload(
            manifest_version,
            owned_files(),
            {"platform": "kimi"},
        ),
    )
    before = {path: tree_entries(path) for path in (valid, wrong)}
    requests = [
        UninstallRequest("codex", valid, manifest_version),
        UninstallRequest("codex", wrong, manifest_version),
    ]
    assert uninstall_many(requests)
    assert all(tree_entries(path) == entries for path, entries in before.items())


def main() -> None:
    manifest = load_manifest()
    manifest_version = manifest["version"]
    with tempfile.TemporaryDirectory(prefix="sk-receipt-boundary-") as temporary:
        root = Path(temporary)
        assert_install_receipts(root, manifest, manifest_version)
        assert_verify_receipt(root, manifest, manifest_version)
        assert_uninstall_receipts(root, manifest_version)
        assert_wrong_platform_blocks_all(root, manifest_version)


if __name__ == "__main__":
    main()
    print("OK: receipt trust boundary")
