"""
PyAgent 统一工具调用接口 - 工具注册表

管理工具的注册、发现和状态管理。
"""

from typing import Any

from .base import ToolContext, ToolState, UnifiedTool


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: dict[str, UnifiedTool] = {}
        self._device_tools: dict[str, list[str]] = {}

    def register(self, tool: UnifiedTool, override: bool = False) -> bool:
        """
        注册工具
        
        Args:
            tool: 工具实例
            override: 是否覆盖已存在的工具
            
        Returns:
            注册是否成功
        """
        if tool.name in self._tools and not override:
            return False

        self._tools[tool.name] = tool

        if tool.device_id:
            if tool.device_id not in self._device_tools:
                self._device_tools[tool.device_id] = []
            if tool.name not in self._device_tools[tool.device_id]:
                self._device_tools[tool.device_id].append(tool.name)

        return True

    def unregister(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            注销是否成功
        """
        if name not in self._tools:
            return False

        tool = self._tools[name]

        if tool.device_id and tool.device_id in self._device_tools:
            if name in self._device_tools[tool.device_id]:
                self._device_tools[tool.device_id].remove(name)
            if not self._device_tools[tool.device_id]:
                del self._device_tools[tool.device_id]

        del self._tools[name]
        return True

    def get_tool(self, name: str) -> UnifiedTool | None:
        """
        获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例或None
        """
        return self._tools.get(name)

    def get_tools_by_device(self, device_id: str) -> list[UnifiedTool]:
        """
        按设备ID获取工具列表
        
        Args:
            device_id: 设备ID
            
        Returns:
            工具列表
        """
        tool_names = self._device_tools.get(device_id, [])
        return [
            self._tools[name]
            for name in tool_names
            if name in self._tools
        ]

    def get_tools_by_state(self, state: ToolState) -> list[UnifiedTool]:
        """
        按状态获取工具列表
        
        Args:
            state: 工具状态
            
        Returns:
            工具列表
        """
        return [
            tool for tool in self._tools.values()
            if tool.state == state
        ]

    def list_tools(self) -> list[dict[str, Any]]:
        """
        获取所有工具信息列表
        
        Returns:
            工具信息列表，包含device_id
        """
        return [tool.get_info() for tool in self._tools.values()]

    def list_tools_by_device(self, device_id: str) -> list[dict[str, Any]]:
        """
        获取指定设备的工具信息列表
        
        Args:
            device_id: 设备ID
            
        Returns:
            工具信息列表
        """
        tools = self.get_tools_by_device(device_id)
        return [tool.get_info() for tool in tools]

    def get_all_tools(self) -> dict[str, UnifiedTool]:
        """获取所有工具"""
        return self._tools.copy()

    def get_tool_names(self) -> list[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def count(self) -> int:
        """获取工具数量"""
        return len(self._tools)

    def count_by_device(self, device_id: str) -> int:
        """获取指定设备的工具数量"""
        return len(self._device_tools.get(device_id, []))

    def set_tool_state(self, name: str, state: ToolState) -> bool:
        """
        设置工具状态
        
        Args:
            name: 工具名称
            state: 目标状态
            
        Returns:
            设置是否成功
        """
        tool = self.get_tool(name)
        if tool is None:
            return False
        tool._state = state
        return True

    async def activate_tool(
        self,
        name: str,
        context: ToolContext | None = None
    ) -> bool:
        """
        激活指定工具
        
        Args:
            name: 工具名称
            context: 工具上下文
            
        Returns:
            激活是否成功
        """
        tool = self.get_tool(name)
        if tool is None:
            return False
        return await tool.wake(context)

    async def dormant_tool(
        self,
        name: str,
        context: ToolContext | None = None
    ) -> bool:
        """
        休眠指定工具
        
        Args:
            name: 工具名称
            context: 工具上下文
            
        Returns:
            休眠是否成功
        """
        tool = self.get_tool(name)
        if tool is None:
            return False
        return await tool.sleep(context)

    async def dormant_all(self, device_id: str | None = None) -> int:
        """
        休眠所有工具或指定设备的工具
        
        Args:
            device_id: 设备ID，为None时休眠所有工具
            
        Returns:
            成功休眠的工具数量
        """
        count = 0
        tools = (
            self.get_tools_by_device(device_id)
            if device_id
            else list(self._tools.values())
        )

        for tool in tools:
            if await tool.sleep():
                count += 1

        return count

    def reset_tool(self, name: str) -> bool:
        """
        重置指定工具状态
        
        Args:
            name: 工具名称
            
        Returns:
            重置是否成功
        """
        tool = self.get_tool(name)
        if tool is None:
            return False
        tool.reset()
        return True

    def reset_all(self, device_id: str | None = None) -> int:
        """
        重置所有工具或指定设备的工具状态
        
        Args:
            device_id: 设备ID，为None时重置所有工具
            
        Returns:
            成功重置的工具数量
        """
        count = 0
        tools = (
            self.get_tools_by_device(device_id)
            if device_id
            else list(self._tools.values())
        )

        for tool in tools:
            tool.reset()
            count += 1

        return count

    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        self._device_tools.clear()

    def get_statistics(self) -> dict[str, Any]:
        """
        获取工具统计信息
        
        Returns:
            统计信息字典
        """
        state_counts = {}
        for state in ToolState:
            state_counts[state.value] = len(self.get_tools_by_state(state))

        return {
            "total_tools": self.count(),
            "devices": len(self._device_tools),
            "state_distribution": state_counts,
            "tools_per_device": {
                device_id: len(tools)
                for device_id, tools in self._device_tools.items()
            }
        }


tool_registry = ToolRegistry()


def register_tool(tool: UnifiedTool, override: bool = False) -> bool:
    """注册工具到全局注册表"""
    return tool_registry.register(tool, override)


def get_tool(name: str) -> UnifiedTool | None:
    """从全局注册表获取工具"""
    return tool_registry.get_tool(name)


def get_all_tools() -> dict[str, UnifiedTool]:
    """获取全局注册表的所有工具"""
    return tool_registry.get_all_tools()


def list_tools() -> list[dict[str, Any]]:
    """获取全局注册表的所有工具信息"""
    return tool_registry.list_tools()
