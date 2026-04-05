"""
PyAgent Skills技能系统 - 技能执行器

执行技能脚本和指令。
"""

from typing import Any

from .loader import SkillLoader, skill_loader
from .parser import ParsedSkill


class SkillExecutor:
    """技能执行器"""

    def __init__(self, loader: SkillLoader | None = None):
        self.loader = loader or skill_loader

    async def execute(
        self,
        skill_name: str,
        action: str = "run",
        params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """执行技能"""
        skill = self.loader.get_skill(skill_name)
        if not skill:
            return {
                "success": False,
                "error": f"Skill not found: {skill_name}"
            }

        params = params or {}

        if action == "run":
            return await self._run_skill(skill, params)
        elif action == "info":
            return self._get_skill_info(skill)
        elif action == "script":
            return await self._run_script(skill, params)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }

    async def _run_skill(
        self,
        skill: ParsedSkill,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """运行技能"""
        body = skill.body
        if not body:
            return {
                "success": False,
                "error": "Skill has no body content"
            }

        return {
            "success": True,
            "result": body,
            "instruction": body
        }

    def _get_skill_info(self, skill: ParsedSkill) -> dict[str, Any]:
        """获取技能信息"""
        return {
            "success": True,
            "info": {
                "name": skill.metadata.name,
                "description": skill.metadata.description,
                "version": skill.metadata.version,
                "author": skill.metadata.author,
                "system": skill.metadata.system,
                "enabled": skill.metadata.enabled,
                "handler": skill.metadata.handler,
                "tool_name": skill.metadata.tool_name
            }
        }

    async def _run_script(
        self,
        skill: ParsedSkill,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """运行脚本"""
        script_name = params.get("script")
        if not script_name:
            return {
                "success": False,
                "error": "Script name required"
            }

        args = params.get("args", [])

        success, output = self.loader.run_script(
            skill.metadata.name,
            script_name,
            args
        )

        return {
            "success": success,
            "output": output
        }

    def get_skill_instruction(self, skill_name: str) -> str | None:
        """获取技能指令"""
        return self.loader.get_skill_body(skill_name)

    def list_available_skills(self) -> list[str]:
        """列出可用技能"""
        return self.loader.list_skills()

    def get_skill_metadata(
        self,
        skill_name: str
    ) -> dict[str, Any] | None:
        """获取技能元数据"""
        skill = self.loader.get_skill(skill_name)
        if not skill:
            return None

        return {
            "name": skill.metadata.name,
            "description": skill.metadata.description,
            "version": skill.metadata.version,
            "author": skill.metadata.author,
            "system": skill.metadata.system,
            "handler": skill.metadata.handler,
            "tool_name": skill.metadata.tool_name
        }


skill_executor = SkillExecutor()
