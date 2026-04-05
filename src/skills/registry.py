"""
PyAgent Skills技能系统 - 技能注册中心

管理技能的注册、发现和查询。
"""

from dataclasses import dataclass

from .parser import ParsedSkill


@dataclass
class SkillInfo:
    """技能信息"""
    skill_id: str
    name: str
    description: str
    enabled: bool = True
    system: bool = False
    handler: str = ""
    tool_name: str = ""


class SkillRegistry:
    """技能注册中心"""

    def __init__(self):
        self._skills: dict[str, ParsedSkill] = {}
        self._disabled: set = set()

    def register(
        self,
        skill: ParsedSkill,
        skill_id: str | None = None
    ) -> None:
        """注册技能"""
        sid = skill_id or skill.skill_dir.name
        self._skills[sid] = skill

    def unregister(self, skill_id: str) -> None:
        """注销技能"""
        self._skills.pop(skill_id, None)
        self._disabled.discard(skill_id)

    def get_skill(self, skill_id: str) -> ParsedSkill | None:
        """获取技能"""
        return self._skills.get(skill_id)

    def get_skill_info(self, skill_id: str) -> SkillInfo | None:
        """获取技能信息"""
        skill = self._skills.get(skill_id)
        if not skill:
            return None

        return SkillInfo(
            skill_id=skill_id,
            name=skill.metadata.name,
            description=skill.metadata.description,
            enabled=skill_id not in self._disabled,
            system=skill.metadata.system,
            handler=skill.metadata.handler,
            tool_name=skill.metadata.tool_name
        )

    def list_skills(self) -> list[str]:
        """列出所有技能ID"""
        return list(self._skills.keys())

    def list_enabled_skills(self) -> list[str]:
        """列出启用的技能"""
        return [sid for sid in self._skills if sid not in self._disabled]

    def list_system_skills(self) -> list[str]:
        """列出系统技能"""
        return [
            sid for sid, skill in self._skills.items()
            if skill.metadata.system
        ]

    def list_external_skills(self) -> list[str]:
        """列出外部技能"""
        return [
            sid for sid, skill in self._skills.items()
            if not skill.metadata.system
        ]

    def set_disabled(self, skill_id: str, disabled: bool) -> None:
        """设置技能禁用状态"""
        if disabled:
            self._disabled.add(skill_id)
        else:
            self._disabled.discard(skill_id)

    def is_enabled(self, skill_id: str) -> bool:
        """检查技能是否启用"""
        return skill_id not in self._disabled

    def get_all_skills(self) -> dict[str, ParsedSkill]:
        """获取所有技能"""
        return self._skills.copy()

    def count(self) -> int:
        """获取技能数量"""
        return len(self._skills)

    def clear(self) -> None:
        """清空所有技能"""
        self._skills.clear()
        self._disabled.clear()


skill_registry = SkillRegistry()
