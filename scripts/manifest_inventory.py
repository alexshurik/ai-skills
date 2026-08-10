#!/usr/bin/env python3
"""Print manifest-owned public entries for documentation generators."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from skills_common import load_manifest, repo_source_path
from skills_validation import parse_frontmatter, validate

CATALOG_PREFIXES = {
    "workflow": "workflow/skills/",
    "utilities": "utilities/",
    "context": "context/",
}
AGENTS_SECTIONS = (
    ("workflow", "Workflow (Multi-Agent Team)"),
    ("onboarding", "Onboarding"),
    ("utilities", "Utilities"),
    ("context", "Context Management"),
)
CURSOR_SECTIONS = (
    ("workflow", "Workflow Commands"),
    ("onboarding", "Onboarding Commands"),
    ("utilities", "Utility Commands"),
    ("context", "Context Commands"),
)
OUTPUT_FORMATS = (
    "tsv",
    "agents-command",
    "cursor-command",
    "agent-section",
    "agents-document",
    "cursor-document",
)


def group_items(manifest: dict[str, Any], group: str) -> list[dict[str, Any]]:
    if group in CATALOG_PREFIXES:
        prefix = CATALOG_PREFIXES[group]
        return [item for item in manifest["catalog"] if item["source"].startswith(prefix)]
    if group == "onboarding":
        return list(manifest["onboarding"])
    if group == "agents":
        return list(manifest["agents"])
    raise ValueError(f"unsupported inventory group: {group}")


def prompt_path(item: dict[str, Any]) -> Path:
    source = repo_source_path(item["source"])
    return source / "SKILL.md" if source.is_dir() else source


def format_item(name: str, description: str, output_format: str) -> str:
    if output_format == "tsv":
        return f"{name}\t{description}"
    if output_format == "agents-command":
        return f"- `{name}` - {description}"
    heading = f"### /{name}" if output_format == "cursor-command" else f"### {name}"
    return f"{heading}\n{description}"


def render_group(
    manifest: dict[str, Any],
    group: str,
    output_format: str,
) -> str:
    entries = []
    for item in group_items(manifest, group):
        description = parse_frontmatter(prompt_path(item))["description"]
        entries.append(format_item(item["name"], description, output_format))
    separator = "\n" if output_format in {"tsv", "agents-command"} else "\n\n"
    return separator.join(entries)


def agents_document(manifest: dict[str, Any]) -> str:
    sections = [
        f"### {title}\n\n{render_group(manifest, group, 'agents-command')}"
        for group, title in AGENTS_SECTIONS
    ]
    sections.append(
        "## Agent Definitions\n\n"
        "The following agents are available for task delegation:\n\n"
        f"{render_group(manifest, 'agents', 'agent-section')}"
    )
    return "\n\n".join(sections)


def cursor_document(manifest: dict[str, Any]) -> str:
    sections = [
        f"## {title}\n\n{render_group(manifest, group, 'cursor-command')}"
        for group, title in CURSOR_SECTIONS
    ]
    sections.append(f"## Available Agents\n\n{render_group(manifest, 'agents', 'agent-section')}")
    return "\n\n".join(sections)


def render_output(
    manifest: dict[str, Any],
    group: str,
    output_format: str,
) -> str:
    if output_format == "agents-document":
        if group != "all":
            raise ValueError("agents-document requires the all group")
        return agents_document(manifest)
    if output_format == "cursor-document":
        if group != "all":
            raise ValueError("cursor-document requires the all group")
        return cursor_document(manifest)
    if group == "all":
        raise ValueError(f"{output_format} does not support the all group")
    return render_group(manifest, group, output_format)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "group",
        choices=(*CATALOG_PREFIXES, "onboarding", "agents", "all"),
    )
    parser.add_argument("--format", choices=OUTPUT_FORMATS, default="tsv")
    args = parser.parse_args()
    manifest = load_manifest()
    issues = validate(manifest)
    if issues:
        messages = "\n".join(issue.message for issue in issues)
        raise ValueError(f"manifest validation failed:\n{messages}")
    print(render_output(manifest, args.group, args.format))


if __name__ == "__main__":
    main()
