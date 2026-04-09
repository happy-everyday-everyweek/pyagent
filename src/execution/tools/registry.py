"""
PyAgent 执行模块工具系统 - 工具注册中心

管理工具的注册、发现和调用。
"""

from typing import Any

from .base import BaseTool, RiskLevel, ToolCategory


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._categories: dict[ToolCategory, list[str]] = {
            cat: [] for cat in ToolCategory
        }

    def register(
        self,
        tool: BaseTool,
        override: bool = False
    ) -> bool:
        """注册工具"""
        if tool.name in self._tools and not override:
            return False

        self._tools[tool.name] = tool

        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)

        return True

    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name not in self._tools:
            return False

        tool = self._tools[name]
        self._categories[tool.category].remove(name)
        del self._tools[name]

        return True

    def get_tool(self, name: str) -> BaseTool | None:
        """获取工具"""
        return self._tools.get(name)

    def get_tools_by_category(self, category: ToolCategory) -> list[BaseTool]:
        """按类别获取工具"""
        return [
            self._tools[name]
            for name in self._categories.get(category, [])
            if name in self._tools
        ]

    def get_tools_by_risk_level(self, risk_level: RiskLevel) -> list[BaseTool]:
        """按风险等级获取工具"""
        return [
            tool for tool in self._tools.values()
            if tool.risk_level == risk_level
        ]

    def get_all_tools(self) -> dict[str, BaseTool]:
        """获取所有工具"""
        return self._tools.copy()

    def get_tool_names(self) -> list[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())

    def get_tool_info(self, name: str) -> dict[str, Any] | None:
        """获取工具信息"""
        tool = self.get_tool(name)
        if tool:
            return tool.get_info()
        return None

    def get_all_tool_info(self) -> list[dict[str, Any]]:
        """获取所有工具信息"""
        return [tool.get_info() for tool in self._tools.values()]

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def count(self) -> int:
        """获取工具数量"""
        return len(self._tools)

    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        for cat in self._categories:
            self._categories[cat] = []


tool_registry = ToolRegistry()


def register_tool(tool: BaseTool, override: bool = False) -> bool:
    """注册工具到全局注册中心"""
    return tool_registry.register(tool, override)


def get_tool(name: str) -> BaseTool | None:
    """从全局注册中心获取工具"""
    return tool_registry.get_tool(name)


def get_all_tools() -> dict[str, BaseTool]:
    """获取全局注册中心的所有工具"""
    return tool_registry.get_all_tools()


def _register_default_tools():
    """注册默认工具"""
    from .knowledge import KnowledgeTool
    from .map import OfflineMapTool

    tool_registry.register(KnowledgeTool())
    tool_registry.register(OfflineMapTool())


_register_default_tools()
