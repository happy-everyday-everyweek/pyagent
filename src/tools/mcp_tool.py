"""
PyAgent MCP工具包装器

将MCP工具包装为UnifiedTool，支持三阶段调用流程。
"""

import logging
from typing import Any

from src.device import device_id_manager
from src.mcp import call_mcp_tool, mcp_client
from src.tools.base import ToolContext, ToolResult, ToolState, UnifiedTool

logger = logging.getLogger(__name__)


class MCPToolWrapper(UnifiedTool):
    """MCP工具包装器

    将MCP工具包装为UnifiedTool，支持三阶段调用流程。
    """

    def __init__(
        self,
        server_name: str,
        tool_name: str,
        tool_description: str = "",
        tool_schema: dict[str, Any] | None = None,
        device_id: str | None = None,
    ):
        """初始化MCP工具包装器

        Args:
            server_name: MCP服务器名称
            tool_name: 工具名称
            tool_description: 工具描述
            tool_schema: 工具schema
            device_id: 设备ID
        """
        super().__init__(
            name=f"mcp_{server_name}_{tool_name}",
            description=tool_description or f"MCP工具: {tool_name}",
            device_id=device_id or device_id_manager.get_device_id(),
        )
        self._server_name = server_name
        self._tool_name = tool_name
        self._tool_schema = tool_schema
        self._activated = False

    async def activate(self, context: ToolContext) -> bool:
        """激活工具

        Args:
            context: 工具上下文

        Returns:
            是否激活成功
        """
        logger.debug(f"激活MCP工具: {self._server_name}.{self._tool_name}")

        try:
            if not mcp_client.is_connected(self._server_name):
                logger.info(f"MCP服务器 '{self._server_name}' 未连接，尝试连接...")
                connected = await mcp_client.connect(self._server_name)
                if not connected:
                    logger.error(f"无法连接到MCP服务器: {self._server_name}")
                    return False

            self._activated = True
            self._state = ToolState.ACTIVE
            return True

        except Exception as e:
            logger.error(f"激活MCP工具失败: {e}")
            self._state = ToolState.ERROR
            return False

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
            result = await call_mcp_tool(
                server_name=self._server_name,
                tool_name=self._tool_name,
                arguments=kwargs,
            )

            if result.isError:
                return ToolResult(
                    success=False,
                    error=result.content[0].text if result.content else "MCP工具执行错误",
                )

            output = ""
            if result.content:
                for content in result.content:
                    if hasattr(content, "text"):
                        output += content.text
                    elif hasattr(content, "data"):
                        output += str(content.data)

            return ToolResult(
                success=True,
                output=output,
                data={"raw_result": result},
            )

        except Exception as e:
            logger.error(f"执行MCP工具 '{self._server_name}.{self._tool_name}' 失败: {e}")
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
        logger.debug(f"MCP工具进入休眠: {self._server_name}.{self._tool_name}")
        self._activated = False
        self._state = ToolState.DORMANT
        return True

    @property
    def server_name(self) -> str:
        """MCP服务器名称"""
        return self._server_name

    @property
    def tool_name(self) -> str:
        """工具名称"""
        return self._tool_name

    @property
    def tool_schema(self) -> dict[str, Any] | None:
        """工具schema"""
        return self._tool_schema


def wrap_mcp_tool(
    server_name: str,
    tool_name: str,
    tool_description: str = "",
    tool_schema: dict[str, Any] | None = None,
    device_id: str | None = None,
) -> MCPToolWrapper:
    """将MCP工具包装为UnifiedTool

    Args:
        server_name: MCP服务器名称
        tool_name: 工具名称
        tool_description: 工具描述
        tool_schema: 工具schema
        device_id: 设备ID

    Returns:
        MCPToolWrapper实例
    """
    return MCPToolWrapper(
        server_name=server_name,
        tool_name=tool_name,
        tool_description=tool_description,
        tool_schema=tool_schema,
        device_id=device_id,
    )


async def create_mcp_tools_from_server(server_name: str) -> list[MCPToolWrapper]:
    """从MCP服务器创建所有工具包装器

    Args:
        server_name: MCP服务器名称

    Returns:
        MCPToolWrapper列表
    """
    tools = []

    try:
        if not mcp_client.is_connected(server_name):
            await mcp_client.connect(server_name)

        mcp_tools = await mcp_client.list_tools(server_name)

        device_id = device_id_manager.get_device_id()

        for tool in mcp_tools:
            wrapper = MCPToolWrapper(
                server_name=server_name,
                tool_name=tool.name,
                tool_description=tool.description or "",
                tool_schema=tool.inputSchema if hasattr(tool, "inputSchema") else None,
                device_id=device_id,
            )
            tools.append(wrapper)

        logger.info(f"从MCP服务器 '{server_name}' 创建了 {len(tools)} 个工具")

    except Exception as e:
        logger.error(f"从MCP服务器 '{server_name}' 创建工具失败: {e}")

    return tools
