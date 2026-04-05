"""
PyAgent Skills技能系统 - 技能解析器

解析SKILL.md文件，提取技能元数据和指令。
"""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillMetadata:
    """技能元数据"""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    handler: str = ""
    tool_name: str = ""
    system: bool = False
    enabled: bool = True
    supported_os: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ParsedSkill:
    """解析后的技能"""
    skill_dir: Path
    metadata: SkillMetadata
    body: str = ""
    scripts_dir: Path | None = None
    references_dir: Path | None = None


class SkillParser:
    """技能解析器"""

    def __init__(self):
        self._metadata_patterns = {
            "name": r"^name:\s*(.+)$",
            "description": r"^description:\s*(.+)$",
            "version": r"^version:\s*(.+)$",
            "author": r"^author:\s*(.+)$",
            "handler": r"^handler:\s*(.+)$",
            "tool_name": r"^tool_name:\s*(.+)$",
            "system": r"^system:\s*(true|false)$",
            "enabled": r"^enabled:\s*(true|false)$",
            "supported_os": r"^supported_os:\s*\[(.+)\]$",
            "dependencies": r"^dependencies:\s*\[(.+)\]$",
            "tags": r"^tags:\s*\[(.+)\]$",
        }

    def parse_directory(self, skill_dir: Path) -> ParsedSkill:
        """解析技能目录"""
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

        content = skill_md.read_text(encoding="utf-8")

        metadata = self._parse_metadata(content)
        if not metadata.name:
            metadata.name = skill_dir.name

        body = self._extract_body(content)

        scripts_dir = skill_dir / "scripts"
        references_dir = skill_dir / "references"

        return ParsedSkill(
            skill_dir=skill_dir,
            metadata=metadata,
            body=body,
            scripts_dir=scripts_dir if scripts_dir.exists() else None,
            references_dir=references_dir if references_dir.exists() else None
        )

    def _parse_metadata(self, content: str) -> SkillMetadata:
        """解析元数据"""
        metadata = SkillMetadata()

        lines = content.split("\n")
        in_frontmatter = False

        for line in lines:
            line = line.strip()

            if line == "---":
                in_frontmatter = not in_frontmatter
                continue

            if not in_frontmatter:
                continue

            for key, pattern in self._metadata_patterns.items():
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()

                    if key == "system":
                        metadata.system = value.lower() == "true"
                    elif key == "enabled":
                        metadata.enabled = value.lower() == "true"
                    elif key in ("supported_os", "dependencies", "tags"):
                        items = [item.strip().strip("\"'") for item in value.split(",")]
                        setattr(metadata, key, items)
                    else:
                        setattr(metadata, key, value)
                    break

        return metadata

    def _extract_body(self, content: str) -> str:
        """提取技能主体"""
        lines = content.split("\n")
        body_lines = []
        in_body = False
        frontmatter_count = 0

        for line in lines:
            if line.strip() == "---":
                frontmatter_count += 1
                if frontmatter_count == 2:
                    in_body = True
                continue

            if in_body:
                body_lines.append(line)

        return "\n".join(body_lines).strip()

    def validate(self, skill: ParsedSkill) -> list[str]:
        """验证技能"""
        errors = []

        if not skill.metadata.name:
            errors.append("Skill name is required")

        if not skill.metadata.description:
            errors.append("Skill description is recommended")

        if not skill.body:
            errors.append("Skill body is empty")

        return errors
