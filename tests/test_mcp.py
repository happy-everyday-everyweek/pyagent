"""
PyAgent MCP协议测试
"""

import pytest
from pathlib import Path

from mcp.client import (
    MCPClient,
    MCPCallResult,
    MCPConnectResult,
    MCPServerConfig,
    MCPPrompt,
    MCPResource,
    MCPTool,
    mcp_client,
)


class TestMCPTool:
    """测试MCP工具"""

    def test_tool_creation(self):
        tool = MCPTool(
            name="test_tool",
            description="Test tool description",
            input_schema={"type": "object"}
        )
        assert tool.name == "test_tool"
        assert tool.description == "Test tool description"
        assert tool.input_schema == {"type": "object"}

    def test_tool_defaults(self):
        tool = MCPTool(name="simple", description="Simple tool")
        assert tool.input_schema == {}


class TestMCPResource:
    """测试MCP资源"""

    def test_resource_creation(self):
        resource = MCPResource(
            uri="file:///test.txt",
            name="test.txt",
            description="Test file",
            mime_type="text/plain"
        )
        assert resource.uri == "file:///test.txt"
        assert resource.name == "test.txt"
        assert resource.description == "Test file"
        assert resource.mime_type == "text/plain"

    def test_resource_defaults(self):
        resource = MCPResource(uri="file:///test.txt", name="test.txt")
        assert resource.description == ""
        assert resource.mime_type == ""


class TestMCPPrompt:
    """测试MCP提示词"""

    def test_prompt_creation(self):
        prompt = MCPPrompt(
            name="test_prompt",
            description="Test prompt",
            arguments=[{"name": "arg1", "type": "string"}]
        )
        assert prompt.name == "test_prompt"
        assert prompt.description == "Test prompt"
        assert len(prompt.arguments) == 1

    def test_prompt_defaults(self):
        prompt = MCPPrompt(name="simple", description="Simple prompt")
        assert prompt.arguments == []


class TestMCPServerConfig:
    """测试MCP服务器配置"""

    def test_config_creation(self):
        config = MCPServerConfig(
            name="test_server",
            command="python",
            args=["-m", "test_server"],
            env={"API_KEY": "test"},
            description="Test server",
            transport="stdio"
        )
        assert config.name == "test_server"
        assert config.command == "python"
        assert config.args == ["-m", "test_server"]
        assert config.transport == "stdio"

    def test_config_defaults(self):
        config = MCPServerConfig(name="simple")
        assert config.command == ""
        assert config.args == []
        assert config.env == {}
        assert config.transport == "stdio"


class TestMCPConnectResult:
    """测试MCP连接结果"""

    def test_success_result(self):
        result = MCPConnectResult(success=True, tool_count=5)
        assert result.success is True
        assert result.tool_count == 5
        assert result.error is None

    def test_error_result(self):
        result = MCPConnectResult(
            success=False,
            error="Connection failed"
        )
        assert result.success is False
        assert result.error == "Connection failed"


class TestMCPCallResult:
    """测试MCP调用结果"""

    def test_success_result(self):
        result = MCPCallResult(success=True, data="result data")
        assert result.success is True
        assert result.data == "result data"
        assert result.error is None

    def test_error_result(self):
        result = MCPCallResult(success=False, error="Call failed")
        assert result.success is False
        assert result.error == "Call failed"


class TestMCPClient:
    """测试MCP客户端"""

    def setup_method(self):
        self.client = MCPClient()

    def test_client_creation(self):
        assert self.client._servers == {}
        assert self.client._connections == {}
        assert self.client._tools == {}

    def test_add_server(self):
        config = MCPServerConfig(
            name="test_server",
            command="python"
        )
        self.client.add_server(config)

        assert "test_server" in self.client._servers
        assert self.client._servers["test_server"] == config

    def test_list_servers(self):
        config = MCPServerConfig(name="server1")
        self.client.add_server(config)

        servers = self.client.list_servers()
        assert len(servers) == 1
        assert "server1" in servers

    def test_list_connected(self):
        connected = self.client.list_connected()
        assert connected == []

    def test_list_tools(self):
        tools = self.client.list_tools()
        assert tools == []

    def test_get_tool_schemas(self):
        schemas = self.client.get_tool_schemas()
        assert schemas == []

    @pytest.mark.asyncio
    async def test_connect_nonexistent_server(self):
        result = await self.client.connect("nonexistent")
        assert result.success is False
        assert "not configured" in result.error.lower() or "not installed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self):
        result = await self.client.call_tool(
            "server1",
            "tool1",
            {}
        )
        assert result.success is False
        assert "not available" in result.error.lower() or "not connected" in result.error.lower()

    def test_disconnect(self):
        self.client._connections["test_server"] = {"client": None}
        self.client._tools["test_server:tool1"] = MCPTool(
            name="tool1",
            description="Test"
        )

        import asyncio
        asyncio.get_event_loop().run_until_complete(self.client.disconnect("test_server"))

        assert "test_server" not in self.client._connections
        assert len(self.client._tools) == 0


class TestMCPClientGlobal:
    """测试全局MCP客户端实例"""

    def test_global_instance(self):
        assert mcp_client is not None
        assert isinstance(mcp_client, MCPClient)
