"""
PyAgent MCP协议支持 - MCP服务器管理器

管理MCP服务器的配置和连接状态。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .client import MCPClient, MCPConnectResult, MCPServerConfig, mcp_client


@dataclass
class ServerStatus:
    """服务器状态"""
    name: str
    configured: bool
    connected: bool
    tool_count: int
    error: str | None = None


class MCPManager:
    """MCP服务器管理器"""

    def __init__(self, client: MCPClient | None = None):
        self.client = client or mcp_client
        self._status: dict[str, ServerStatus] = {}

    def add_server(
        self,
        name: str,
        command: str = "",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        transport: str = "stdio",
        url: str = "",
        description: str = ""
    ) -> None:
        """添加服务器"""
        config = MCPServerConfig(
            name=name,
            command=command,
            args=args or [],
            env=env or {},
            transport=transport,
            url=url,
            description=description
        )
        self.client.add_server(config)
        self._status[name] = ServerStatus(
            name=name,
            configured=True,
            connected=False,
            tool_count=0
        )

    def remove_server(self, name: str) -> None:
        """移除服务器"""
        if name in self._status:
            del self._status[name]

    async def connect_server(self, name: str) -> MCPConnectResult:
        """连接服务器"""
        result = await self.client.connect(name)

        if name in self._status:
            self._status[name].connected = result.success
            self._status[name].tool_count = result.tool_count
            self._status[name].error = result.error

        return result

    async def connect_all(self) -> dict[str, MCPConnectResult]:
        """连接所有服务器"""
        results = {}
        for name in self.client.list_servers():
            results[name] = await self.connect_server(name)
        return results

    async def disconnect_server(self, name: str) -> None:
        """断开服务器"""
        await self.client.disconnect(name)
        if name in self._status:
            self._status[name].connected = False
            self._status[name].tool_count = 0

    async def disconnect_all(self) -> None:
        """断开所有服务器"""
        for name in list(self.client.list_connected()):
            await self.disconnect_server(name)

    def get_server_status(self, name: str) -> ServerStatus | None:
        """获取服务器状态"""
        return self._status.get(name)

    def get_all_status(self) -> dict[str, ServerStatus]:
        """获取所有服务器状态"""
        return self._status.copy()

    def list_tools(self, server_name: str | None = None) -> list[Any]:
        """列出工具"""
        return self.client.list_tools(server_name)

    def get_tool_count(self, server_name: str | None = None) -> int:
        """获取工具数量"""
        return len(self.list_tools(server_name))

    async def reload_config(self, config_path: Path) -> int:
        """重新加载配置"""
        await self.disconnect_all()
        self._status.clear()

        count = self.client.load_servers_from_config(config_path)

        for name in self.client.list_servers():
            self._status[name] = ServerStatus(
                name=name,
                configured=True,
                connected=False,
                tool_count=0
            )

        return count

    def get_summary(self) -> dict[str, Any]:
        """获取摘要信息"""
        connected = [s for s in self._status.values() if s.connected]
        total_tools = sum(s.tool_count for s in connected)

        return {
            "total_servers": len(self._status),
            "connected_servers": len(connected),
            "total_tools": total_tools,
            "servers": {
                name: {
                    "connected": status.connected,
                    "tool_count": status.tool_count,
                    "error": status.error
                }
                for name, status in self._status.items()
            }
        }


mcp_manager = MCPManager()
