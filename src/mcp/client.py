"""
PyAgent MCP协议支持 - MCP客户端

参考OpenAkita的MCP设计，支持MCP协议连接和工具调用。
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from mcp.client.stdio import stdio_client

    from mcp import ClientSession, StdioServerParameters
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False
    logger.warning("MCP SDK not installed. Run: pip install mcp")

MCP_HTTP_AVAILABLE = False
try:
    from mcp.client.streamable_http import streamablehttp_client
    MCP_HTTP_AVAILABLE = True
except ImportError:
    pass

MCP_SSE_AVAILABLE = False
try:
    from mcp.client.sse import sse_client
    MCP_SSE_AVAILABLE = True
except ImportError:
    pass


@dataclass
class MCPTool:
    """MCP工具"""
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResource:
    """MCP资源"""
    uri: str
    name: str
    description: str = ""
    mime_type: str = ""


@dataclass
class MCPPrompt:
    """MCP提示词"""
    name: str
    description: str
    arguments: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MCPServerConfig:
    """MCP服务器配置"""
    name: str
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    description: str = ""
    transport: str = "stdio"
    url: str = ""
    cwd: str = ""


@dataclass
class MCPCallResult:
    """MCP调用结果"""
    success: bool
    data: Any = None
    error: str | None = None


@dataclass
class MCPConnectResult:
    """MCP连接结果"""
    success: bool
    error: str | None = None
    tool_count: int = 0


class MCPClient:
    """MCP客户端"""

    def __init__(self):
        self._servers: dict[str, MCPServerConfig] = {}
        self._connections: dict[str, Any] = {}
        self._tools: dict[str, MCPTool] = {}
        self._resources: dict[str, MCPResource] = {}
        self._prompts: dict[str, MCPPrompt] = {}

        self._connect_timeout = 30
        self._call_timeout = 60

    def add_server(self, config: MCPServerConfig) -> None:
        """添加服务器配置"""
        self._servers[config.name] = config
        logger.info(f"Added MCP server config: {config.name}")

    def load_servers_from_config(self, config_path: Path) -> int:
        """从配置文件加载服务器"""
        if not config_path.exists():
            logger.warning(f"MCP config not found: {config_path}")
            return 0

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            servers = data.get("mcpServers", {})

            for name, server_data in servers.items():
                transport = server_data.get("transport", "stdio")
                config = MCPServerConfig(
                    name=name,
                    command=server_data.get("command", ""),
                    args=server_data.get("args", []),
                    env=server_data.get("env", {}),
                    description=server_data.get("description", ""),
                    transport=transport,
                    url=server_data.get("url", ""),
                )
                self.add_server(config)

            logger.info(f"Loaded {len(servers)} MCP servers from {config_path}")
            return len(servers)

        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            return 0

    async def connect(self, server_name: str) -> MCPConnectResult:
        """连接到MCP服务器"""
        if not MCP_SDK_AVAILABLE:
            return MCPConnectResult(
                success=False,
                error="MCP SDK not installed. Run: pip install mcp"
            )

        if server_name not in self._servers:
            return MCPConnectResult(
                success=False,
                error=f"Server not configured: {server_name}"
            )

        if server_name in self._connections:
            tool_count = len(self.list_tools(server_name))
            return MCPConnectResult(success=True, tool_count=tool_count)

        config = self._servers[server_name]

        try:
            if config.transport == "streamable_http":
                return await self._connect_http(server_name, config)
            if config.transport == "sse":
                return await self._connect_sse(server_name, config)
            return await self._connect_stdio(server_name, config)

        except Exception as e:
            return MCPConnectResult(
                success=False,
                error=f"Connection failed: {type(e).__name__}: {e}"
            )

    async def _connect_stdio(
        self,
        server_name: str,
        config: MCPServerConfig
    ) -> MCPConnectResult:
        """通过stdio连接"""
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env or None,
        )

        try:
            read, write = await asyncio.wait_for(
                stdio_client(server_params).__aenter__(),
                timeout=self._connect_timeout
            )

            client = ClientSession(read, write)
            await asyncio.wait_for(
                client.__aenter__(),
                timeout=self._connect_timeout
            )
            await asyncio.wait_for(
                client.initialize(),
                timeout=self._connect_timeout
            )

            await self._discover_capabilities(server_name, client)

            self._connections[server_name] = {
                "client": client,
                "transport": "stdio"
            }

            tool_count = len(self.list_tools(server_name))
            logger.info(f"Connected to MCP server: {server_name} ({tool_count} tools)")
            return MCPConnectResult(success=True, tool_count=tool_count)

        except asyncio.TimeoutError:
            return MCPConnectResult(
                success=False,
                error=f"Connection timeout ({self._connect_timeout}s)"
            )
        except Exception as e:
            return MCPConnectResult(
                success=False,
                error=f"stdio connection failed: {e}"
            )

    async def _connect_http(
        self,
        server_name: str,
        config: MCPServerConfig
    ) -> MCPConnectResult:
        """通过HTTP连接"""
        if not MCP_HTTP_AVAILABLE:
            return MCPConnectResult(
                success=False,
                error="HTTP transport not available. Upgrade MCP SDK: pip install 'mcp>=1.2.0'"
            )

        if not config.url:
            return MCPConnectResult(
                success=False,
                error="URL not configured for HTTP transport"
            )

        try:
            read, write, _ = await asyncio.wait_for(
                streamablehttp_client(url=config.url).__aenter__(),
                timeout=self._connect_timeout
            )

            client = ClientSession(read, write)
            await asyncio.wait_for(
                client.__aenter__(),
                timeout=self._connect_timeout
            )
            await asyncio.wait_for(
                client.initialize(),
                timeout=self._connect_timeout
            )

            await self._discover_capabilities(server_name, client)

            self._connections[server_name] = {
                "client": client,
                "transport": "streamable_http"
            }

            tool_count = len(self.list_tools(server_name))
            return MCPConnectResult(success=True, tool_count=tool_count)

        except Exception as e:
            return MCPConnectResult(
                success=False,
                error=f"HTTP connection failed: {e}"
            )

    async def _connect_sse(
        self,
        server_name: str,
        config: MCPServerConfig
    ) -> MCPConnectResult:
        """通过SSE连接"""
        if not MCP_SSE_AVAILABLE:
            return MCPConnectResult(
                success=False,
                error="SSE transport not available"
            )

        if not config.url:
            return MCPConnectResult(
                success=False,
                error="URL not configured for SSE transport"
            )

        try:
            read, write = await asyncio.wait_for(
                sse_client(url=config.url).__aenter__(),
                timeout=self._connect_timeout
            )

            client = ClientSession(read, write)
            await asyncio.wait_for(
                client.__aenter__(),
                timeout=self._connect_timeout
            )
            await asyncio.wait_for(
                client.initialize(),
                timeout=self._connect_timeout
            )

            await self._discover_capabilities(server_name, client)

            self._connections[server_name] = {
                "client": client,
                "transport": "sse"
            }

            tool_count = len(self.list_tools(server_name))
            return MCPConnectResult(success=True, tool_count=tool_count)

        except Exception as e:
            return MCPConnectResult(
                success=False,
                error=f"SSE connection failed: {e}"
            )

    async def _discover_capabilities(
        self,
        server_name: str,
        client: Any
    ) -> None:
        """发现服务器能力"""
        tools_result = await client.list_tools()
        for tool in tools_result.tools:
            self._tools[f"{server_name}:{tool.name}"] = MCPTool(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema or {},
            )

        try:
            resources_result = await client.list_resources()
            for resource in resources_result.resources:
                self._resources[f"{server_name}:{resource.uri}"] = MCPResource(
                    uri=resource.uri,
                    name=resource.name,
                    description=resource.description or "",
                    mime_type=resource.mimeType or "",
                )
        except Exception:
            pass

        try:
            prompts_result = await client.list_prompts()
            for prompt in prompts_result.prompts:
                self._prompts[f"{server_name}:{prompt.name}"] = MCPPrompt(
                    name=prompt.name,
                    description=prompt.description or "",
                    arguments=prompt.arguments or [],
                )
        except Exception:
            pass

    async def disconnect(self, server_name: str) -> None:
        """断开连接"""
        if server_name in self._connections:
            del self._connections[server_name]

            prefix = f"{server_name}:"
            self._tools = {k: v for k, v in self._tools.items() if not k.startswith(prefix)}
            self._resources = {k: v for k, v in self._resources.items() if not k.startswith(prefix)}
            self._prompts = {k: v for k, v in self._prompts.items() if not k.startswith(prefix)}

            logger.info(f"Disconnected from MCP server: {server_name}")

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> MCPCallResult:
        """调用MCP工具"""
        if not MCP_SDK_AVAILABLE:
            return MCPCallResult(
                success=False,
                error="MCP SDK not available"
            )

        if server_name not in self._connections:
            return MCPCallResult(
                success=False,
                error=f"Not connected to server: {server_name}"
            )

        tool_key = f"{server_name}:{tool_name}"
        if tool_key not in self._tools:
            return MCPCallResult(
                success=False,
                error=f"Tool not found: {tool_name}"
            )

        try:
            conn = self._connections[server_name]
            client = conn.get("client")

            result = await asyncio.wait_for(
                client.call_tool(tool_name, arguments),
                timeout=self._call_timeout
            )

            content = []
            for item in result.content:
                if hasattr(item, "text"):
                    content.append(item.text)
                elif hasattr(item, "data"):
                    content.append(item.data)

            return MCPCallResult(
                success=True,
                data=content[0] if len(content) == 1 else content
            )

        except Exception as e:
            return MCPCallResult(
                success=False,
                error=f"{type(e).__name__}: {e}"
            )

    def list_servers(self) -> list[str]:
        """列出所有服务器"""
        return list(self._servers.keys())

    def list_connected(self) -> list[str]:
        """列出已连接的服务器"""
        return list(self._connections.keys())

    def list_tools(self, server_name: str | None = None) -> list[MCPTool]:
        """列出工具"""
        if server_name:
            prefix = f"{server_name}:"
            return [t for k, t in self._tools.items() if k.startswith(prefix)]
        return list(self._tools.values())

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """获取工具Schema"""
        schemas = []
        for key, tool in self._tools.items():
            server_name = key.split(":")[0]
            schemas.append({
                "name": f"mcp_{server_name}_{tool.name}".replace("-", "_"),
                "description": f"[MCP:{server_name}] {tool.description}",
                "input_schema": tool.input_schema,
            })
        return schemas


mcp_client = MCPClient()


async def connect_mcp_server(name: str) -> MCPConnectResult:
    """连接MCP服务器"""
    return await mcp_client.connect(name)


async def call_mcp_tool(
    server: str,
    tool: str,
    args: dict[str, Any]
) -> MCPCallResult:
    """调用MCP工具"""
    return await mcp_client.call_tool(server, tool, args)


def get_mcp_tool_schemas() -> list[dict[str, Any]]:
    """获取MCP工具Schema"""
    return mcp_client.get_tool_schemas()
