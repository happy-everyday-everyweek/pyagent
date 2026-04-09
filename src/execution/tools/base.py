"""
PyAgent 执行模块工具系统 - 工具基类

定义执行模块工具的基类和接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolCategory(Enum):
    """工具类别"""
    SHELL = "shell"
    FILE = "file"
    BROWSER = "browser"
    WEB = "web"
    SEARCH = "search"
    SCHEDULE = "schedule"
    MCP = "mcp"
    KNOWLEDGE = "knowledge"
    MAP = "map"
    CUSTOM = "custom"


class RiskLevel(Enum):
    """风险等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str = ""
    error: str = ""
    data: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str
    description: str = ""
    required: bool = True
    default: Any = None
    enum: list[str] = field(default_factory=list)


class BaseTool(ABC):
    """工具基类"""

    name: str = "base_tool"
    description: str = "基础工具"
    category: ToolCategory = ToolCategory.CUSTOM
    risk_level: RiskLevel = RiskLevel.SAFE

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._parameters: list[ToolParameter] = []

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""

    def get_parameters(self) -> list[ToolParameter]:
        """获取参数定义"""
        return self._parameters

    def get_parameter_schema(self) -> dict[str, Any]:
        """获取参数Schema"""
        properties = {}
        required = []

        for param in self._parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def get_info(self) -> dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "parameters": self.get_parameter_schema()
        }

    def validate_parameters(self, **kwargs) -> tuple:
        """验证参数"""
        errors = []

        for param in self._parameters:
            if param.required and param.name not in kwargs:
                errors.append(f"缺少必需参数: {param.name}")
            elif param.name in kwargs:
                value = kwargs[param.name]
                if param.enum and value not in param.enum:
                    errors.append(f"参数 {param.name} 的值必须是: {param.enum}")

        return len(errors) == 0, errors
