"""MCP Gateway for unified MCP server management.

This module provides a unified interface for managing multiple MCP servers,
supporting HTTP, SSE, and stdio transports with OAuth authentication.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class MCPTransportType(Enum):
    """Transport types for MCP servers."""

    HTTP = "http"
    SSE = "sse"
    STDIO = "stdio"


class MCPAuthType(Enum):
    """Authentication types for MCP servers."""

    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BEARER = "bearer"
    AWS_SIGV4 = "aws_sigv4"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    server_id: str
    name: str
    transport: MCPTransportType
    url: str | None = None
    auth_type: MCPAuthType = MCPAuthType.NONE
    api_key: str | None = None
    extra_headers: dict[str, str] = field(default_factory=dict)
    allowed_tools: list[str] | None = None
    disallowed_tools: list[str] | None = None
    timeout: int = 30
    retry_count: int = 3

    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)

    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] = field(default_factory=list)
    authorization_url: str | None = None
    token_url: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_expires_at: datetime | None = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_id": self.server_id,
            "name": self.name,
            "transport": self.transport.value,
            "url": self.url,
            "auth_type": self.auth_type.value,
            "extra_headers": self.extra_headers,
            "allowed_tools": self.allowed_tools,
            "disallowed_tools": self.disallowed_tools,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class MCPTool:
    """Represents an MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    server_id: str
    display_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "server_id": self.server_id,
            "display_name": self.display_name or self.name,
        }


@dataclass
class MCPToolResult:
    """Result of an MCP tool call."""

    tool_name: str
    server_id: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time_ms: int = 0


class MCPGateway:
    """Gateway for managing MCP servers and tool calls.

    Provides a unified interface for:
    - Registering and managing MCP servers
    - Discovering tools from servers
    - Executing tool calls with authentication
    - Health checking and monitoring
    """

    def __init__(self):
        self._servers: dict[str, MCPServerConfig] = {}
        self._tools: dict[str, MCPTool] = {}
        self._clients: dict[str, Any] = {}
        self._on_tool_call: Callable | None = None
        self._on_server_error: Callable | None = None

    def register_server(self, config: MCPServerConfig) -> None:
        """Register an MCP server.

        Args:
            config: Server configuration.
        """
        config.updated_at = datetime.now()
        self._servers[config.server_id] = config
        logger.info("Registered MCP server: %s (%s)", config.name, config.server_id)

    def unregister_server(self, server_id: str) -> bool:
        """Unregister an MCP server.

        Args:
            server_id: Server ID to unregister.

        Returns:
            True if server was found and removed.
        """
        if server_id in self._servers:
            del self._servers[server_id]
            self._tools = {k: v for k, v in self._tools.items() if v.server_id != server_id}
            if server_id in self._clients:
                del self._clients[server_id]
            logger.info("Unregistered MCP server: %s", server_id)
            return True
        return False

    def get_server(self, server_id: str) -> MCPServerConfig | None:
        """Get a server configuration.

        Args:
            server_id: Server ID.

        Returns:
            Server configuration or None.
        """
        return self._servers.get(server_id)

    def list_servers(self) -> list[MCPServerConfig]:
        """List all registered servers.

        Returns:
            List of server configurations.
        """
        return list(self._servers.values())

    async def discover_tools(self, server_id: str | None = None) -> list[MCPTool]:
        """Discover tools from MCP servers.

        Args:
            server_id: Specific server ID, or None for all servers.

        Returns:
            List of discovered tools.
        """
        tools = []
        servers = [self._servers[server_id]] if server_id else list(self._servers.values())

        for server in servers:
            try:
                server_tools = await self._fetch_tools_from_server(server)
                for tool_data in server_tools:
                    tool = MCPTool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        input_schema=tool_data.get("inputSchema", {}),
                        server_id=server.server_id,
                        display_name=tool_data.get("displayName"),
                    )
                    self._tools[tool.name] = tool
                    tools.append(tool)
            except Exception as e:
                logger.warning("Failed to discover tools from %s: %s", server.name, e)
                if self._on_server_error:
                    self._on_server_error(server, e)

        return tools

    async def _fetch_tools_from_server(self, server: MCPServerConfig) -> list[dict[str, Any]]:
        """Fetch tools from a server.

        Args:
            server: Server configuration.

        Returns:
            List of tool definitions.
        """
        if server.transport == MCPTransportType.STDIO:
            return await self._fetch_tools_stdio(server)
        elif server.transport == MCPTransportType.HTTP:
            return await self._fetch_tools_http(server)
        elif server.transport == MCPTransportType.SSE:
            return await self._fetch_tools_sse(server)
        return []

    async def _fetch_tools_http(self, server: MCPServerConfig) -> list[dict[str, Any]]:
        """Fetch tools via HTTP transport."""
        import httpx

        url = f"{server.url}/tools" if server.url else None
        if not url:
            return []

        headers = self._build_headers(server)
        async with httpx.AsyncClient(timeout=server.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])

    async def _fetch_tools_sse(self, server: MCPServerConfig) -> list[dict[str, Any]]:
        """Fetch tools via SSE transport."""
        return await self._fetch_tools_http(server)

    async def _fetch_tools_stdio(self, server: MCPServerConfig) -> list[dict[str, Any]]:
        """Fetch tools via stdio transport."""
        if not server.command:
            return []

        proc = await asyncio.create_subprocess_exec(
            server.command,
            *server.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**dict(server.env), "PYTHONIOENCODING": "utf-8"},
        )

        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        proc.stdin.write((str(request) + "\n").encode())
        await proc.stdin.drain()

        response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=server.timeout)
        response = eval(response_line.decode().strip())

        proc.terminate()
        await proc.wait()

        return response.get("result", {}).get("tools", [])

    def _build_headers(self, server: MCPServerConfig) -> dict[str, str]:
        """Build request headers for a server.

        Args:
            server: Server configuration.

        Returns:
            Headers dictionary.
        """
        headers = {"Content-Type": "application/json", **server.extra_headers}

        if server.auth_type == MCPAuthType.API_KEY and server.api_key:
            headers["X-API-Key"] = server.api_key
        elif server.auth_type == MCPAuthType.BEARER and server.api_key:
            headers["Authorization"] = f"Bearer {server.api_key}"
        elif server.auth_type == MCPAuthType.OAUTH2 and server.access_token:
            headers["Authorization"] = f"Bearer {server.access_token}"

        return headers

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        server_id: str | None = None,
    ) -> MCPToolResult:
        """Call an MCP tool.

        Args:
            tool_name: Name of the tool to call.
            arguments: Tool arguments.
            server_id: Optional server ID to use specific server.

        Returns:
            Tool call result.
        """
        start_time = datetime.now()

        tool = self._tools.get(tool_name)
        if not tool:
            return MCPToolResult(
                tool_name=tool_name,
                server_id=server_id or "",
                success=False,
                error=f"Tool not found: {tool_name}",
            )

        server = self._servers.get(server_id or tool.server_id)
        if not server:
            return MCPToolResult(
                tool_name=tool_name,
                server_id=server_id or tool.server_id,
                success=False,
                error=f"Server not found: {server_id or tool.server_id}",
            )

        if server.allowed_tools and tool_name not in server.allowed_tools:
            return MCPToolResult(
                tool_name=tool_name,
                server_id=server.server_id,
                success=False,
                error=f"Tool not allowed: {tool_name}",
            )

        if server.disallowed_tools and tool_name in server.disallowed_tools:
            return MCPToolResult(
                tool_name=tool_name,
                server_id=server.server_id,
                success=False,
                error=f"Tool is disallowed: {tool_name}",
            )

        try:
            result = await self._execute_tool_call(server, tool_name, arguments)
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return MCPToolResult(
                tool_name=tool_name,
                server_id=server.server_id,
                success=True,
                result=result,
                execution_time_ms=int(execution_time),
            )
        except Exception as e:
            logger.error("Tool call failed: %s - %s", tool_name, e)
            return MCPToolResult(
                tool_name=tool_name,
                server_id=server.server_id,
                success=False,
                error=str(e),
            )

    async def _execute_tool_call(
        self,
        server: MCPServerConfig,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Execute a tool call on a server.

        Args:
            server: Server configuration.
            tool_name: Tool name.
            arguments: Tool arguments.

        Returns:
            Tool result.
        """
        if server.transport == MCPTransportType.STDIO:
            return await self._execute_stdio(server, tool_name, arguments)
        else:
            return await self._execute_http(server, tool_name, arguments)

    async def _execute_http(
        self,
        server: MCPServerConfig,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Execute tool call via HTTP."""
        import httpx

        url = f"{server.url}/tools/call" if server.url else None
        if not url:
            raise ValueError("Server URL not configured")

        headers = self._build_headers(server)
        payload = {"name": tool_name, "arguments": arguments}

        async with httpx.AsyncClient(timeout=server.timeout) as client:
            for attempt in range(server.retry_count):
                try:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    return data.get("content", data)
                except httpx.HTTPError as e:
                    if attempt == server.retry_count - 1:
                        raise
                    await asyncio.sleep(2**attempt)

    async def _execute_stdio(
        self,
        server: MCPServerConfig,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Execute tool call via stdio."""
        if not server.command:
            raise ValueError("Server command not configured")

        proc = await asyncio.create_subprocess_exec(
            server.command,
            *server.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**dict(server.env), "PYTHONIOENCODING": "utf-8"},
        )

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": 1,
        }
        proc.stdin.write((str(request) + "\n").encode())
        await proc.stdin.drain()

        response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=server.timeout)
        response = eval(response_line.decode().strip())

        proc.terminate()
        await proc.wait()

        if "error" in response:
            raise Exception(response["error"].get("message", "Unknown error"))
        return response.get("result", {}).get("content")

    async def health_check(self, server_id: str | None = None) -> dict[str, bool]:
        """Check health of MCP servers.

        Args:
            server_id: Specific server ID, or None for all servers.

        Returns:
            Dictionary of server_id -> healthy status.
        """
        results = {}
        servers = [self._servers[server_id]] if server_id else list(self._servers.values())

        for server in servers:
            try:
                if server.transport == MCPTransportType.STDIO:
                    tools = await self._fetch_tools_stdio(server)
                    results[server.server_id] = len(tools) >= 0
                else:
                    tools = await self._fetch_tools_http(server)
                    results[server.server_id] = len(tools) >= 0
            except Exception as e:
                logger.warning("Health check failed for %s: %s", server.name, e)
                results[server.server_id] = False

        return results

    def get_tool(self, tool_name: str) -> MCPTool | None:
        """Get a tool by name.

        Args:
            tool_name: Tool name.

        Returns:
            Tool or None if not found.
        """
        return self._tools.get(tool_name)

    def list_tools(self, server_id: str | None = None) -> list[MCPTool]:
        """List available tools.

        Args:
            server_id: Optional server ID to filter.

        Returns:
            List of tools.
        """
        if server_id:
            return [t for t in self._tools.values() if t.server_id == server_id]
        return list(self._tools.values())

    def on_tool_call(self, callback: Callable) -> None:
        """Set callback for tool calls.

        Args:
            callback: Callback function.
        """
        self._on_tool_call = callback

    def on_server_error(self, callback: Callable) -> None:
        """Set callback for server errors.

        Args:
            callback: Callback function.
        """
        self._on_server_error = callback


_gateway: MCPGateway | None = None


def get_mcp_gateway() -> MCPGateway:
    """Get the global MCP gateway instance.

    Returns:
        MCPGateway instance.
    """
    global _gateway
    if _gateway is None:
        _gateway = MCPGateway()
    return _gateway
