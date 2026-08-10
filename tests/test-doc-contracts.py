#!/usr/bin/env python3
"""Keep public documentation aligned with the manifest and platform contracts."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def main() -> None:
    manifest = json.loads(read("skills-manifest.yaml"))
    public_names = {item["name"] for group in ("catalog", "onboarding") for item in manifest[group]}
    inventory_docs = (
        "README.md",
        "AGENTS.md",
        "adapters/kimi/README.md",
        "adapters/cursor/.cursorrules",
        "adapters/cursor/.cursor/rules/sk-skills.mdc",
    )
    for relative in inventory_docs:
        missing = sorted(name for name in public_names if name not in read(relative))
        assert missing == [], f"{relative} omits manifest skills: {missing}"

    codex_readme = read("adapters/codex/README.md")
    codex_template = read("adapters/codex/skill-template.md")
    assert "$sk-team-feature" in codex_readme
    assert "/sk-team-feature" not in codex_readme
    assert "allowed-tools" not in codex_template
    assert "$sk-example" in codex_template

    kimi_readme = read("adapters/kimi/README.md")
    kimi_renderer = read("scripts/skills_render.py")
    assert "Via the current `Agent` tool" in kimi_readme
    assert (
        "dispatches architecture-design, correctness-safety, and engineering-quality" in kimi_readme
    )
    assert "No hard-coded Kimi plan path" in kimi_readme
    assert "older than 1.25" in kimi_readme
    assert "kimi_cli.tools.agent:Agent" in kimi_renderer
    assert "kimi_cli.tools.multiagent:Task" not in kimi_renderer

    cursor_readme = read("adapters/cursor/README.md")
    assert ".cursor/skills" in cursor_readme
    assert ".cursor/rules" in cursor_readme
    assert "Legacy Compatibility" in cursor_readme

    root_readme = read("README.md")
    assert "register the source" in root_readme
    assert "skills-manifest.yaml" in root_readme
    assert "events.jsonl" in root_readme
    assert "derived" in root_readme.lower()
    assert "Resume and troubleshoot" in root_readme
    assert "sk-team-status" in root_readme
    assert "recover-journal-or-reinitialize" in root_readme
    assert "require-compatible-helper" in root_readme
    assert "review step 4" not in root_readme.lower()

    status = read("workflow/skills/sk-team-status/SKILL.md")
    assert "npm test 2>&1" not in status
    assert "4/6 phases" not in status
    assert "In Acceptance" in status

    help_text = read("workflow/skills/sk-team-help/SKILL.md")
    assert "Task tool" not in help_text
    assert "openspec/completed/" in help_text
    assert "events.jsonl" in help_text
    assert "runtime-state" in help_text

    inlined_protocols = (
        "workflow/agents/sk-doc-reviewer.md",
        "workflow/agents/sk-product-analyst.md",
        "workflow/agents/sk-researcher.md",
        "workflow/agents/sk-tester.md",
    )
    for relative in inlined_protocols:
        prompt = read(relative)
        protocol_start = prompt.index("<interaction_protocol>")
        protocol_end = prompt.index("</interaction_protocol>")
        ignore_start = prompt.index("jscpd:ignore-start")
        ignore_end = prompt.index("jscpd:ignore-end")
        assert ignore_start < protocol_start < protocol_end < ignore_end


if __name__ == "__main__":
    main()
    print("OK: documentation contracts")
