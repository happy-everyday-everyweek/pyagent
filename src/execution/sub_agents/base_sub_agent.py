"""
PyAgent 执行模块子Agent系统 - 子Agent基类

定义子Agent的基类和接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SubAgentResult:
    """子Agent执行结果"""
    success: bool
    result: str = ""
    error: str = ""
    data: Any = None
    steps: list[dict[str, Any]] = field(default_factory=list)


class BaseSubAgent(ABC):
    """子Agent基类"""

    name: str = "base_sub_agent"
    description: str = "基础子Agent"

    def __init__(
        self,
        llm_client: Any | None = None,
        tool_registry: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.config = config or {}

    @abstractmethod
    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None
    ) -> SubAgentResult:
        """执行任务"""

    def get_info(self) -> dict[str, Any]:
        """获取Agent信息"""
        return {
            "name": self.name,
            "description": self.description
        }
