"""
PyAgent 集成测试 - 工具系统集成测试

测试工具注册表、工具生命周期和工具链执行。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from tools.base import (
    ToolContext,
    ToolLifecycle,
    ToolResult,
    ToolState,
    UnifiedTool,
)
from tools.registry import ToolRegistry


class MockFileTool(UnifiedTool):
    """模拟文件工具"""

    name = "file_tool"
    description = "Tool for file operations"

    def __init__(self, device_id: str = ""):
        super().__init__(device_id)
        self._file_operations = []

    async def activate(self, context: ToolContext) -> bool:
        self._state = ToolState.ACTIVE
        return True

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        operation = kwargs.get("operation", "unknown")
        self._file_operations.append(operation)
        return ToolResult(
            success=True,
            output=f"File operation '{operation}' completed",
            data={"operation": operation}
        )

    async def dormant(self, context: ToolContext) -> bool:
        self._state = ToolState.DORMANT
        return True


class MockNetworkTool(UnifiedTool):
    """模拟网络工具"""

    name = "network_tool"
    description = "Tool for network operations"

    def __init__(self, device_id: str = ""):
        super().__init__(device_id)
        self._network_requests = []

    async def activate(self, context: ToolContext) -> bool:
        self._state = ToolState.ACTIVE
        return True

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        url = kwargs.get("url", "unknown")
        self._network_requests.append(url)
        return ToolResult(
            success=True,
            output=f"Network request to '{url}' completed",
            data={"url": url, "status": 200}
        )

    async def dormant(self, context: ToolContext) -> bool:
        self._state = ToolState.DORMANT
        return True


class TestToolRegistryIntegration:
    """工具注册表集成测试"""

    def setup_method(self):
        self.registry = ToolRegistry()
        self.registry.clear()

    def test_register_multiple_tools(self):
        """测试注册多个工具"""
        tool1 = MockFileTool("device_001")
        tool2 = MockNetworkTool("device_001")

        self.registry.register(tool1)
        self.registry.register(tool2)

        assert self.registry.count() == 2

    def test_tool_isolation_by_device(self):
        """测试按设备隔离工具"""
        tool1 = MockFileTool("device_001")
        tool2 = MockFileTool("device_002")

        self.registry.register(tool1)
        self.registry.register(tool2, override=False)

        tools_device1 = self.registry.get_tools_by_device("device_001")
        tools_device2 = self.registry.get_tools_by_device("device_002")

        assert len(tools_device1) == 1
        assert len(tools_device2) == 0

    def test_tool_state_management(self):
        """测试工具状态管理"""
        tool = MockFileTool("device_001")
        self.registry.register(tool)

        self.registry.set_tool_state("file_tool", ToolState.ACTIVE)
        assert tool.state == ToolState.ACTIVE

        self.registry.set_tool_state("file_tool", ToolState.DORMANT)
        assert tool.state == ToolState.DORMANT


class TestToolLifecycleIntegration:
    """工具生命周期集成测试"""

    def setup_method(self):
        self.registry = ToolRegistry()
        self.registry.clear()

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """测试完整生命周期"""
        tool = MockFileTool("device_001")

        assert tool.state == ToolState.IDLE

        context = ToolContext(device_id="device_001")
        result = await tool.call(context, operation="read")

        assert result.success is True
        assert tool.state == ToolState.ACTIVE

        await tool.sleep()
        assert tool.state == ToolState.DORMANT

    @pytest.mark.asyncio
    async def test_multiple_executions(self):
        """测试多次执行"""
        tool = MockFileTool("device_001")
        context = ToolContext(device_id="device_001")

        for i in range(5):
            result = await tool.call(context, operation=f"op_{i}")
            assert result.success is True

        assert len(tool._file_operations) == 5

    @pytest.mark.asyncio
    async def test_sleep_and_wake_cycle(self):
        """测试休眠和唤醒循环"""
        tool = MockFileTool("device_001")

        context = ToolContext(device_id="device_001")
        await tool.call(context, operation="test")

        for _ in range(3):
            await tool.sleep()
            assert tool.state == ToolState.DORMANT

            await tool.wake()
            assert tool.state == ToolState.ACTIVE


class TestToolChainIntegration:
    """工具链集成测试"""

    def setup_method(self):
        self.registry = ToolRegistry()
        self.registry.clear()

    @pytest.mark.asyncio
    async def test_sequential_tool_execution(self):
        """测试顺序工具执行"""
        file_tool = MockFileTool("device_001")
        network_tool = MockNetworkTool("device_001")

        self.registry.register(file_tool)
        self.registry.register(network_tool)

        context = ToolContext(device_id="device_001")

        result1 = await file_tool.call(context, operation="read")
        assert result1.success is True

        result2 = await network_tool.call(
            context,
            url="https://example.com/upload"
        )
        assert result2.success is True

        assert len(file_tool._file_operations) == 1
        assert len(network_tool._network_requests) == 1

    @pytest.mark.asyncio
    async def test_tool_output_as_input(self):
        """测试工具输出作为输入"""
        file_tool = MockFileTool("device_001")
        network_tool = MockNetworkTool("device_001")

        self.registry.register(file_tool)
        self.registry.register(network_tool)

        context = ToolContext(device_id="device_001")

        file_result = await file_tool.call(context, operation="read")
        assert file_result.success is True

        network_result = await network_tool.call(
            context,
            url=f"https://example.com/process?data={file_result.data['operation']}"
        )
        assert network_result.success is True

    @pytest.mark.asyncio
    async def test_error_recovery_in_chain(self):
        """测试链中的错误恢复"""
        file_tool = MockFileTool("device_001")
        network_tool = MockNetworkTool("device_001")

        self.registry.register(file_tool)
        self.registry.register(network_tool)

        context = ToolContext(device_id="device_001")

        result1 = await file_tool.call(context, operation="read")
        assert result1.success is True

        result2 = await network_tool.call(context, url="https://example.com")
        assert result2.success is True


class TestToolContextIntegration:
    """工具上下文集成测试"""

    def test_context_propagation(self):
        """测试上下文传播"""
        context = ToolContext(
            device_id="device_001",
            session_id="session_001",
            user_id="user_001",
            metadata={"key": "value"}
        )

        assert context.device_id == "device_001"
        assert context.session_id == "session_001"
        assert context.user_id == "user_001"
        assert context.metadata == {"key": "value"}

    def test_context_serialization(self):
        """测试上下文序列化"""
        context = ToolContext(
            device_id="device_001",
            session_id="session_001",
            metadata={"key": "value"}
        )

        data = context.to_dict()

        new_context = ToolContext.from_dict(data)
        assert new_context.device_id == context.device_id
        assert new_context.session_id == context.session_id
        assert new_context.metadata == context.metadata


class TestToolStatisticsIntegration:
    """工具统计集成测试"""

    def setup_method(self):
        self.registry = ToolRegistry()
        self.registry.clear()

    def test_statistics_collection(self):
        """测试统计收集"""
        tool1 = MockFileTool("device_001")
        tool2 = MockNetworkTool("device_001")

        self.registry.register(tool1)
        self.registry.register(tool2)

        self.registry.set_tool_state("file_tool", ToolState.ACTIVE)

        stats = self.registry.get_statistics()
        assert stats["total_tools"] == 2
        assert "state_distribution" in stats

    def test_statistics_by_device(self):
        """测试按设备统计"""
        tool1 = MockFileTool("device_001")
        tool2 = MockNetworkTool("device_002")

        self.registry.register(tool1)
        self.registry.register(tool2)

        count_device1 = self.registry.count_by_device("device_001")
        count_device2 = self.registry.count_by_device("device_002")

        assert count_device1 == 1
        assert count_device2 == 1
