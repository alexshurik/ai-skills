"""Render platform-specific install trees without touching live targets."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from skills_common import REPO_ROOT, TEXT_SUFFIXES


def replace_paths(text: str, platform: str, installed_root: Path) -> str:
    if platform == "codex":
        replacements = (
            ("~/.claude/agents/best-practices", str(installed_root / "best-practices")),
            ("~/.claude/agents/review-steps", str(installed_root / "review-steps")),
            ("~/.claude/agents/shared", str(installed_root / "shared")),
            ("~/.claude/agents/", f"{installed_root / 'agents'}/"),
        )
    elif platform == "kimi":
        references = installed_root / "agents" / "references"
        replacements = (
            ("~/.claude/agents/best-practices", str(references / "best-practices")),
            ("~/.claude/agents/review-steps", str(references / "review-steps")),
            ("~/.claude/agents/shared", str(references / "shared")),
            ("~/.claude/agents/", f"{references}/"),
        )
    else:
        return text
    for original, replacement in replacements:
        text = text.replace(original, replacement)
    return text


def copy_rendered(
    source: Path,
    destination: Path,
    platform: str,
    installed_root: Path,
) -> None:
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for child in sorted(source.iterdir()):
            copy_rendered(child, destination / child.name, platform, installed_root)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() in TEXT_SUFFIXES or source.name == "SKILL.md":
        destination.write_text(
            replace_paths(source.read_text(encoding="utf-8"), platform, installed_root),
            encoding="utf-8",
        )
    else:
        shutil.copy2(source, destination)
    if os.access(source, os.X_OK):
        destination.chmod(destination.stat().st_mode | 0o111)


def render_review_steps(
    manifest: dict[str, Any],
    destination: Path,
    platform: str,
    installed_root: Path,
) -> None:
    for item in manifest["review_steps"]:
        copy_rendered(
            REPO_ROOT / item["source"],
            destination / Path(item["source"]).name,
            platform,
            installed_root,
        )


def render_codex(manifest: dict[str, Any], output: Path, installed_root: Path) -> None:
    for item in manifest["catalog"]:
        copy_rendered(
            REPO_ROOT / item["source"], output / item["name"], "codex", installed_root
        )
    for item in manifest["onboarding"]:
        copy_rendered(
            REPO_ROOT / item["source"],
            output / item["name"] / "SKILL.md",
            "codex",
            installed_root,
        )
    for item in manifest["agents"]:
        copy_rendered(
            REPO_ROOT / item["source"],
            output / "agents" / f"{item['name']}.md",
            "codex",
            installed_root,
        )
    render_review_steps(manifest, output / "review-steps", "codex", installed_root)
    for item in manifest["resources"]:
        copy_rendered(
            REPO_ROOT / item["source"],
            output / item["codex_target"],
            "codex",
            installed_root,
        )


def link(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(source)


def render_claude(manifest: dict[str, Any], output: Path) -> None:
    for item in manifest["catalog"]:
        link(REPO_ROOT / item["source"], output / "skills" / item["name"])
    for item in manifest["onboarding"]:
        link(REPO_ROOT / item["source"], output / "commands" / f"{item['name']}.md")
    for item in manifest["agents"]:
        link(REPO_ROOT / item["source"], output / "agents" / f"{item['name']}.md")
    for item in manifest["review_steps"]:
        link(
            REPO_ROOT / item["source"],
            output / "agents/review-steps" / Path(item["source"]).name,
        )
    for item in manifest["resources"]:
        link(REPO_ROOT / item["source"], output / item["claude_target"])


def kimi_agent_yaml(name: str) -> str:
    return (
        "version: 1\nagent:\n  extend: ./sk-team.yaml\n"
        f"  system_prompt_path: ./references/{name}.md\n"
        "  exclude_tools:\n"
        '    - "kimi_cli.tools.multiagent:Task"\n'
    )


def kimi_team_yaml(manifest: dict[str, Any]) -> str:
    lines = [
        "version: 1",
        "agent:",
        "  name: sk-team",
        "  extend: default",
        "  system_prompt_path: ./references/sk-team-feature.md",
        "  subagents:",
    ]
    for item in manifest["agents"]:
        short_name = item["name"].removeprefix("sk-")
        lines += [
            f"    {short_name}:",
            f"      path: ./{item['name']}.yaml",
            f'      description: "Internal role: {item["name"]}"',
        ]
    return "\n".join(lines) + "\n"


def render_kimi(manifest: dict[str, Any], output: Path, installed_root: Path) -> None:
    skills = output / "skills"
    references = output / "agents" / "references"
    for item in manifest["catalog"]:
        copy_rendered(
            REPO_ROOT / item["source"], skills / item["name"], "kimi", installed_root
        )
    for item in manifest["onboarding"]:
        copy_rendered(
            REPO_ROOT / item["source"],
            skills / item["name"] / "SKILL.md",
            "kimi",
            installed_root,
        )
    copy_rendered(
        REPO_ROOT / "workflow/skills/sk-team-feature/SKILL.md",
        references / "sk-team-feature.md",
        "kimi",
        installed_root,
    )
    agents = output / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    (agents / "sk-team.yaml").write_text(kimi_team_yaml(manifest), encoding="utf-8")
    for item in manifest["agents"]:
        copy_rendered(
            REPO_ROOT / item["source"],
            references / f"{item['name']}.md",
            "kimi",
            installed_root,
        )
        (agents / f"{item['name']}.yaml").write_text(
            kimi_agent_yaml(item["name"]), encoding="utf-8"
        )
    render_review_steps(manifest, references / "review-steps", "kimi", installed_root)
    for item in manifest["resources"]:
        copy_rendered(
            REPO_ROOT / item["source"],
            output / item["kimi_target"],
            "kimi",
            installed_root,
        )


def render_tree(
    manifest: dict[str, Any],
    platform: str,
    output: Path,
    installed_root: Path,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    if platform == "codex":
        render_codex(manifest, output, installed_root)
    elif platform == "claude":
        render_claude(manifest, output)
    elif platform == "kimi":
        render_kimi(manifest, output, installed_root)
    else:
        raise ValueError(f"unsupported platform: {platform}")
