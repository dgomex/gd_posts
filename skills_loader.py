"""Load Cursor-style SKILL.md files (YAML frontmatter + markdown body)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class SkillDocument:
    name: str
    description: str
    body: str


def load_skill(path: Path) -> SkillDocument:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return SkillDocument(name="", description="", body=raw)

    fm_lines: list[str] = []
    i = 1
    while i < len(lines):
        if lines[i].strip() == "---":
            break
        fm_lines.append(lines[i])
        i += 1

    if i >= len(lines):
        return SkillDocument(name="", description="", body=raw)

    body = "\n".join(lines[i + 1 :]).lstrip("\n")
    meta = yaml.safe_load("\n".join(fm_lines)) or {}
    return SkillDocument(
        name=str(meta.get("name", "")),
        description=str(meta.get("description", "")),
        body=body,
    )
