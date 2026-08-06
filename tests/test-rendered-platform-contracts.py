#!/usr/bin/env python3
"""Shared prompts must remain host-neutral after every platform render."""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_common import load_manifest, repo_source_path  # noqa: E402
from skills_render import RenderContext, render_tree  # noqa: E402


HOST_INVOCATION_RE = re.compile(
    r"(?<![<A-Za-z0-9_.-])(?:/skill:|/|\$)sk-[a-z0-9-]+"
)


def source_prompts(manifest: dict[str, object]) -> list[Path]:
    prompts: list[Path] = []
    for group in ("catalog", "onboarding", "agents", "review_steps"):
        for item in manifest[group]:
            source = repo_source_path(item["source"])
            prompts.append(source / "SKILL.md" if source.is_dir() else source)
    return prompts


def claude_prompts(
    manifest: dict[str, object],
    output: Path,
) -> list[Path]:
    prompts = [
        output / "skills" / item["name"] / "SKILL.md"
        for item in manifest["catalog"]
    ]
    prompts.extend(
        output / "commands" / f"{item['name']}.md"
        for item in manifest["onboarding"]
    )
    prompts.extend(
        output / "agents" / f"{item['name']}.md"
        for item in manifest["agents"]
    )
    prompts.extend(
        output / "agents" / "review-steps" / repo_source_path(item["source"]).name
        for item in manifest["review_steps"]
    )
    return prompts


def kimi_prompts(
    manifest: dict[str, object],
    output: Path,
) -> list[Path]:
    prompts = [
        output / "skills" / item["name"] / "SKILL.md"
        for item in (*manifest["catalog"], *manifest["onboarding"])
    ]
    prompts.extend(
        output / "agents" / "references" / f"{item['name']}.md"
        for item in manifest["agents"]
    )
    prompts.append(output / "agents" / "references" / "sk-team-feature.md")
    return prompts


def flat_prompts(
    manifest: dict[str, object],
    output: Path,
) -> list[Path]:
    prompts = [
        output / item["name"] / "SKILL.md"
        for item in (*manifest["catalog"], *manifest["onboarding"])
    ]
    prompts.extend(
        output / "agents" / f"{item['name']}.md"
        for item in manifest["agents"]
    )
    prompts.extend(
        output / "review-steps" / repo_source_path(item["source"]).name
        for item in manifest["review_steps"]
    )
    return prompts


def rendered_prompts(
    manifest: dict[str, object],
    platform: str,
    output: Path,
) -> list[Path]:
    renderer = {
        "claude": claude_prompts,
        "kimi": kimi_prompts,
    }.get(platform, flat_prompts)
    return renderer(manifest, output)


def assert_host_neutral(path: Path, label: str) -> None:
    match = HOST_INVOCATION_RE.search(path.read_text(encoding="utf-8"))
    assert match is None, f"{label}: host-specific invocation {match.group()!r} in {path}"


def shared_runtime_root(platform: str, output: Path) -> Path:
    if platform == "claude":
        return output / "agents" / "shared" / "runtime-state"
    if platform == "kimi":
        return output / "agents" / "references" / "shared" / "runtime-state"
    return output / "shared" / "runtime-state"


def assert_runtime_state_resources(platform: str, output: Path) -> None:
    runtime = shared_runtime_root(platform, output)
    helper = runtime / "sk_state.py"
    assert helper.is_file(), f"{platform}: missing runtime-state helper"
    assert helper.stat().st_mode & 0o111, f"{platform}: helper is not executable"
    for schema_name in ("state.schema.json", "event.schema.json"):
        schema = runtime / schema_name
        assert schema.is_file(), f"{platform}: missing {schema_name}"


def main() -> None:
    manifest = load_manifest()
    for path in source_prompts(manifest):
        assert_host_neutral(path, "source")

    with tempfile.TemporaryDirectory(prefix="sk-platform-contracts-") as temporary:
        root = Path(temporary)
        for platform in ("codex", "cursor", "claude", "kimi"):
            output = root / platform
            render_tree(
                manifest,
                RenderContext(platform, output, root / f"{platform}-installed"),
            )
            for path in rendered_prompts(manifest, platform, output):
                assert_host_neutral(path, platform)
            assert_runtime_state_resources(platform, output)
            if platform == "kimi":
                team_yaml = (output / "agents" / "sk-team.yaml").read_text(
                    encoding="utf-8"
                )
                team_prompt = (
                    output / "agents" / "references" / "sk-team-feature.md"
                ).read_text(encoding="utf-8")
                assert "review-security:" in team_yaml
                assert "review-instruction-quality:" in team_yaml
                assert "Kimi execution override" in team_prompt
                assert (output / "agents" / "sk-review-security.yaml").is_file()


if __name__ == "__main__":
    main()
    print("OK: rendered platform contracts")
