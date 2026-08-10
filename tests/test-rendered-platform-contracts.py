#!/usr/bin/env python3
"""Shared prompts must remain host-neutral after every platform render."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_common import load_manifest, repo_source_path  # noqa: E402
from skills_render import RenderContext, render_tree  # noqa: E402

HOST_INVOCATION_RE = re.compile(r"(?<![<A-Za-z0-9_.-])(?:/skill:|/|\$)sk-[a-z0-9-]+")
ORCHESTRATOR_REFERENCES = {
    "~/.claude/agents/shared/orchestration-policy.md": (
        "workflow/agents/shared/orchestration-policy.md"
    ),
    "~/.claude/agents/shared/handoff-protocol.md": ("workflow/agents/shared/handoff-protocol.md"),
    "~/.claude/agents/shared/scope-governance.md": ("workflow/agents/shared/scope-governance.md"),
    "~/.claude/agents/references/review-tooling.md": (
        "workflow/agents/references/review-tooling.md"
    ),
    "~/.claude/agents/references/review-verdict-policy.md": (
        "workflow/agents/references/review-verdict-policy.md"
    ),
    "~/.claude/agents/best-practices/resolver.md": "shared/best-practices/resolver.md",
    "~/.claude/agents/review-evidence/collect-change-evidence.sh": (
        "shared/review-evidence/collect-change-evidence.sh"
    ),
    "~/.claude/agents/review-evidence/review-map.sh": ("shared/review-evidence/review-map.sh"),
    "~/.claude/agents/review-steps/architecture-design.md": (
        "workflow/agents/review-steps/architecture-design.md"
    ),
    "~/.claude/agents/review-steps/correctness-safety.md": (
        "workflow/agents/review-steps/correctness-safety.md"
    ),
    "~/.claude/agents/review-steps/engineering-quality.md": (
        "workflow/agents/review-steps/engineering-quality.md"
    ),
}


def source_prompts(manifest: dict[str, Any]) -> list[Path]:
    prompts: list[Path] = []
    for group in ("catalog", "onboarding", "agents", "review_steps"):
        for item in manifest[group]:
            source = repo_source_path(item["source"])
            prompts.append(source / "SKILL.md" if source.is_dir() else source)
    return prompts


def claude_prompts(
    manifest: dict[str, Any],
    output: Path,
) -> list[Path]:
    prompts = [output / "skills" / item["name"] / "SKILL.md" for item in manifest["catalog"]]
    prompts.extend(output / "commands" / f"{item['name']}.md" for item in manifest["onboarding"])
    prompts.extend(output / "agents" / f"{item['name']}.md" for item in manifest["agents"])
    prompts.extend(
        output / "agents" / "review-steps" / repo_source_path(item["source"]).name
        for item in manifest["review_steps"]
    )
    return prompts


def kimi_prompts(
    manifest: dict[str, Any],
    output: Path,
) -> list[Path]:
    prompts = [
        output / "skills" / item["name"] / "SKILL.md"
        for item in (*manifest["catalog"], *manifest["onboarding"])
    ]
    prompts.extend(
        output / "agents" / f"{item['name']}.md"
        for item in (*manifest["agents"], *manifest["review_steps"])
    )
    prompts.append(output / "agents" / "sk-team.md")
    return prompts


def flat_prompts(
    manifest: dict[str, Any],
    output: Path,
) -> list[Path]:
    prompts = [
        output / item["name"] / "SKILL.md"
        for item in (*manifest["catalog"], *manifest["onboarding"])
    ]
    prompts.extend(output / "agents" / f"{item['name']}.md" for item in manifest["agents"])
    prompts.extend(
        output / "review-steps" / repo_source_path(item["source"]).name
        for item in manifest["review_steps"]
    )
    return prompts


def rendered_prompts(
    manifest: dict[str, Any],
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
    package = runtime / "_sk_runtime" / "__init__.py"
    assert package.is_file(), f"{platform}: missing runtime-state implementation package"
    completed = subprocess.run(
        [sys.executable, str(helper), "--help"],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, f"{platform}: rendered helper failed: {completed.stderr}"
    for schema_name in ("state.schema.json", "event.schema.json"):
        schema = runtime / schema_name
        assert schema.is_file(), f"{platform}: missing {schema_name}"


def installed_reference(platform: str, output: Path, canonical: str) -> tuple[str, Path]:
    relative = canonical.removeprefix("~/.claude/")
    if platform == "claude":
        return canonical, output / relative

    if platform == "kimi":
        if relative.startswith("agents/review-steps/"):
            filename = Path(relative).name
            installed = output / "agents" / f"sk-review-{filename}"
            return str(installed), installed
        relative = relative.removeprefix("agents/")
        installed = output / "agents" / "references" / relative
        return str(installed), installed

    installed_relative = relative.removeprefix("agents/")
    if installed_relative.startswith(("references/", "review-evidence/")):
        installed_relative = f"agents/{installed_relative}"
    installed = output / installed_relative
    return str(installed), installed


def orchestrator_prompt(platform: str, output: Path) -> Path:
    if platform == "kimi":
        return output / "agents" / "sk-review-orchestrator.md"
    return output / "agents" / "sk-review-orchestrator.md"


def lens_prompts(platform: str, output: Path) -> list[Path]:
    directory = output / "review-steps"
    if platform == "claude":
        directory = output / "agents" / "review-steps"
    elif platform == "kimi":
        return [
            output / "agents" / f"sk-review-{name}"
            for name in (
                "architecture-design.md",
                "correctness-safety.md",
                "engineering-quality.md",
            )
        ]
    return [
        directory / name
        for name in ("architecture-design.md", "correctness-safety.md", "engineering-quality.md")
    ]


def assert_reference_closure(platform: str, output: Path) -> None:
    orchestrator = orchestrator_prompt(platform, output).read_text(encoding="utf-8")
    for canonical, source_fallback in ORCHESTRATOR_REFERENCES.items():
        rendered, installed_path = installed_reference(platform, output, canonical)
        assert rendered in orchestrator, f"{platform}: missing installed locator {rendered}"
        assert source_fallback in orchestrator, f"{platform}: missing source fallback"
        assert installed_path.exists(), (
            f"{platform}: unresolved installed reference {installed_path}"
        )
        assert (REPO_ROOT / source_fallback).exists(), f"missing source fallback {source_fallback}"

    canonical_scope = "~/.claude/agents/shared/scope-governance.md"
    rendered_scope, installed_scope = installed_reference(platform, output, canonical_scope)
    for prompt in lens_prompts(platform, output):
        content = prompt.read_text(encoding="utf-8")
        assert rendered_scope in content, f"{platform}: missing installed scope locator in {prompt}"
        assert ORCHESTRATOR_REFERENCES[canonical_scope] in content
        assert installed_scope.exists()


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
                RenderContext(platform, output, output),
            )
            for path in rendered_prompts(manifest, platform, output):
                assert_host_neutral(path, platform)
            assert_runtime_state_resources(platform, output)
            assert_reference_closure(platform, output)
            if platform == "kimi":
                team_prompt = (output / "agents" / "sk-team.md").read_text(encoding="utf-8")
                reviewer = (output / "agents" / "sk-review-orchestrator.md").read_text(
                    encoding="utf-8"
                )
                assert "  - sk-review-orchestrator" in team_prompt
                assert "  - sk-review-architecture-design" not in team_prompt
                assert "  - sk-review-architecture-design" in reviewer
                assert "  - sk-review-correctness-safety" in reviewer
                assert "  - sk-review-engineering-quality" in reviewer
                assert "${base_prompt}" in team_prompt
                assert "Kimi execution override" not in team_prompt
                architect = (output / "agents" / "sk-architect.md").read_text(encoding="utf-8")
                assert "  - FetchURL" in architect
                assert "  - WebFetch" not in architect
                lens = output / "agents" / "sk-review-correctness-safety.md"
                assert lens.is_file()
                assert "subagents: []" in lens.read_text(encoding="utf-8")


if __name__ == "__main__":
    main()
    print("OK: rendered platform contracts")
