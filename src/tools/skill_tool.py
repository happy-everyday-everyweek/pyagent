"""
PyAgent Skill工具包装器

将Skill包装为UnifiedTool，支持三阶段调用流程。
"""

import logging
from typing import Any

from src.device import device_id_manager
from src.tools.base import ToolContext, ToolResult, ToolState, UnifiedTool

logger = logging.getLogger(__name__)


class SkillTool(UnifiedTool):
    """Skill工具包装器

    将Skill包装为UnifiedTool，支持三阶段调用流程。
    """

    def __init__(
        self,
        skill_name: str,
        skill_description: str,
        skill_executor: Any = None,
        device_id: str | None = None,
    ):
        """初始化Skill工具

        Args:
            skill_name: Skill名称
            skill_description: Skill描述
            skill_executor: Skill执行器
            device_id: 设备ID
        """
        super().__init__(
            name=f"skill_{skill_name}",
            description=skill_description,
            device_id=device_id or device_id_manager.get_device_id(),
        )
        self._skill_name = skill_name
        self._skill_executor = skill_executor
        self._activated = False

    async def activate(self, context: ToolContext) -> bool:
        """激活工具

        Args:
            context: 工具上下文

        Returns:
            是否激活成功
        """
        logger.debug(f"激活Skill工具: {self._skill_name}")
        self._activated = True
        self._state = ToolState.ACTIVE
        return True

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """执行工具

        Args:
            context: 工具上下文
            **kwargs: 执行参数

        Returns:
            执行结果
        """
        if not self._activated:
            return ToolResult(
                success=False,
                error="工具未激活，请先调用activate()",
            )

        try:
            if self._skill_executor is None:
                return ToolResult(
                    success=False,
                    error=f"Skill '{self._skill_name}' 没有配置执行器",
                )

            if hasattr(self._skill_executor, "execute"):
                result = await self._skill_executor.execute(**kwargs)
            elif callable(self._skill_executor):
                result = self._skill_executor(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Skill '{self._skill_name}' 执行器不可调用",
                )

            if isinstance(result, ToolResult):
                return result
            elif isinstance(result, dict):
                return ToolResult(
                    success=result.get("success", True),
                    output=result.get("output", ""),
                    error=result.get("error", ""),
                    data=result.get("data"),
                )
            else:
                return ToolResult(
                    success=True,
                    output=str(result) if result else "",
                )

        except Exception as e:
            logger.error(f"执行Skill '{self._skill_name}' 失败: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )

    async def dormant(self, context: ToolContext) -> bool:
        """使工具进入休眠状态

        Args:
            context: 工具上下文

        Returns:
            是否成功进入休眠
        """
        logger.debug(f"Skill工具进入休眠: {self._skill_name}")
        self._activated = False
        self._state = ToolState.DORMANT
        return True


def wrap_skill(
    skill_name: str,
    skill_description: str,
    skill_executor: Any = None,
    device_id: str | None = None,
) -> SkillTool:
    """将Skill包装为UnifiedTool

    Args:
        skill_name: Skill名称
        skill_description: Skill描述
        skill_executor: Skill执行器
        device_id: 设备ID

    Returns:
        SkillTool实例
    """
    return SkillTool(
        skill_name=skill_name,
        skill_description=skill_description,
        skill_executor=skill_executor,
        device_id=device_id,
    )
