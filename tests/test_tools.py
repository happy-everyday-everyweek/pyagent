"""
PyAgent 统一工具接口测试
"""

import pytest

from tools.base import (
    ToolContext,
    ToolLifecycle,
    ToolResult,
    ToolState,
    UnifiedTool,
)
from tools.registry import ToolRegistry, tool_registry


class MockTool(UnifiedTool):
    """测试用模拟工具"""

    name = "mock_tool"
    description = "A mock tool for testing"

    def __init__(self, device_id: str = ""):
        super().__init__(device_id)
        self._activate_count = 0
        self._execute_count = 0
        self._dormant_count = 0

    async def activate(self, context: ToolContext) -> bool:
        self._activate_count += 1
        self._state = ToolState.ACTIVE
        return True

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        self._execute_count += 1
        return ToolResult(
            success=True,
            output="Mock tool executed",
            data=kwargs
        )

    async def dormant(self, context: ToolContext) -> bool:
        self._dormant_count += 1
        self._state = ToolState.DORMANT
        return True


class FailingTool(UnifiedTool):
    """测试用失败工具"""

    name = "failing_tool"
    description = "A tool that always fails"

    async def activate(self, context: ToolContext) -> bool:
        return False

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        return ToolResult(success=False, error="Tool execution failed")

    async def dormant(self, context: ToolContext) -> bool:
        return False


class TestToolLifecycle:
    """测试工具生命周期枚举"""

    def test_lifecycle_values(self):
        assert ToolLifecycle.ACTIVATE.value == "activate"
        assert ToolLifecycle.EXECUTE.value == "execute"
        assert ToolLifecycle.DORMANT.value == "dormant"

    def test_lifecycle_count(self):
        assert len(ToolLifecycle) == 3


class TestToolState:
    """测试工具状态枚举"""

    def test_state_values(self):
        assert ToolState.IDLE.value == "idle"
        assert ToolState.ACTIVE.value == "active"
        assert ToolState.DORMANT.value == "dormant"
        assert ToolState.ERROR.value == "error"

    def test_state_count(self):
        assert len(ToolState) == 4


class TestToolContext:
    """测试工具上下文"""

    def test_context_creation(self):
        context = ToolContext(
            device_id="device_001",
            session_id="session_001",
            user_id="user_001"
        )
        assert context.device_id == "device_001"
        assert context.session_id == "session_001"
        assert context.user_id == "user_001"

    def test_context_defaults(self):
        context = ToolContext()
        assert context.device_id == ""
        assert context.session_id == ""
        assert context.user_id == ""
        assert context.metadata == {}

    def test_context_to_dict(self):
        context = ToolContext(
            device_id="device_001",
            metadata={"key": "value"}
        )
        data = context.to_dict()
        assert data["device_id"] == "device_001"
        assert data["metadata"] == {"key": "value"}


class TestToolResult:
    """测试工具结果"""

    def test_success_result(self):
        result = ToolResult(
            success=True,
            output="Operation completed",
            data={"key": "value"}
        )
        assert result.success is True
        assert result.output == "Operation completed"
        assert result.data == {"key": "value"}

    def test_error_result(self):
        result = ToolResult(
            success=False,
            error="Something went wrong"
        )
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_result_to_dict(self):
        result = ToolResult(
            success=True,
            output="Test",
            metadata={"duration": 1.5}
        )
        data = result.to_dict()
        assert data["success"] is True
        assert data["output"] == "Test"
        assert data["metadata"] == {"duration": 1.5}


class TestUnifiedTool:
    """测试统一工具基类"""

    def test_tool_creation(self):
        tool = MockTool("device_001")
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
        assert tool.state == ToolState.IDLE
        assert tool.device_id == "device_001"

    def test_tool_state_property(self):
        tool = MockTool()
        assert tool.state == ToolState.IDLE

    def test_device_id_setter(self):
        tool = MockTool()
        tool.device_id = "new_device"
        assert tool.device_id == "new_device"

    @pytest.mark.asyncio
    async def test_tool_call(self):
        tool = MockTool()
        context = ToolContext(device_id="device_001")

        result = await tool.call(context, param="value")
        assert result.success is True
        assert result.output == "Mock tool executed"
        assert tool._activate_count == 1
        assert tool._execute_count == 1

    @pytest.mark.asyncio
    async def test_tool_call_without_context(self):
        tool = MockTool("device_001")

        result = await tool.call(param="value")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_tool_sleep_and_wake(self):
        tool = MockTool()
        await tool.call()

        success = await tool.sleep()
        assert success is True
        assert tool.state == ToolState.DORMANT

        success = await tool.wake()
        assert success is True
        assert tool.state == ToolState.ACTIVE

    def test_tool_reset(self):
        tool = MockTool()
        tool._state = ToolState.ERROR
        tool._last_error = "Test error"

        tool.reset()
        assert tool.state == ToolState.IDLE
        assert tool._last_error is None

    def test_tool_get_info(self):
        tool = MockTool("device_001")
        info = tool.get_info()

        assert info["name"] == "mock_tool"
        assert info["description"] == "A mock tool for testing"
        assert info["state"] == "idle"
        assert info["device_id"] == "device_001"

    @pytest.mark.asyncio
    async def test_failing_tool(self):
        tool = FailingTool()
        result = await tool.call()

        assert result.success is False
        assert tool.state == ToolState.IDLE


class TestToolRegistry:
    """测试工具注册表"""

    def setup_method(self):
        self.registry = ToolRegistry()
        self.registry.clear()

    def test_register_tool(self):
        tool = MockTool("device_001")
        result = self.registry.register(tool)

        assert result is True
        assert self.registry.count() == 1

    def test_register_duplicate_tool(self):
        tool1 = MockTool("device_001")
        tool2 = MockTool("device_002")

        self.registry.register(tool1)
        result = self.registry.register(tool2)

        assert result is False

    def test_register_override(self):
        tool1 = MockTool("device_001")
        tool2 = MockTool("device_002")

        self.registry.register(tool1)
        result = self.registry.register(tool2, override=True)

        assert result is True
        assert self.registry.get_tool("mock_tool").device_id == "device_002"

    def test_unregister_tool(self):
        tool = MockTool("device_001")
        self.registry.register(tool)

        result = self.registry.unregister("mock_tool")
        assert result is True
        assert self.registry.count() == 0

    def test_unregister_nonexistent_tool(self):
        result = self.registry.unregister("nonexistent")
        assert result is False

    def test_get_tool(self):
        tool = MockTool("device_001")
        self.registry.register(tool)

        retrieved = self.registry.get_tool("mock_tool")
        assert retrieved is tool

    def test_get_nonexistent_tool(self):
        retrieved = self.registry.get_tool("nonexistent")
        assert retrieved is None

    def test_get_tools_by_device(self):
        tool1 = MockTool("device_001")
        tool2 = MockTool("device_002")

        self.registry.register(tool1)
        self.registry.register(tool2)

        tools = self.registry.get_tools_by_device("device_001")
        assert len(tools) == 1

    def test_get_tools_by_state(self):
        tool = MockTool("device_001")
        self.registry.register(tool)

        tools = self.registry.get_tools_by_state(ToolState.IDLE)
        assert len(tools) == 1

    def test_list_tools(self):
        tool = MockTool("device_001")
        self.registry.register(tool)

        tools = self.registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "mock_tool"

    def test_has_tool(self):
        tool = MockTool("device_001")
        self.registry.register(tool)

        assert self.registry.has_tool("mock_tool") is True
        assert self.registry.has_tool("nonexistent") is False

    def test_count_by_device(self):
        tool = MockTool("device_001")
        self.registry.register(tool)

        count = self.registry.count_by_device("device_001")
        assert count == 1

    def test_set_tool_state(self):
        tool = MockTool("device_001")
        self.registry.register(tool)

        result = self.registry.set_tool_state("mock_tool", ToolState.ACTIVE)
        assert result is True
        assert tool.state == ToolState.ACTIVE

    def test_reset_tool(self):
        tool = MockTool("device_001")
        self.registry.register(tool)
        tool._state = ToolState.ERROR

        result = self.registry.reset_tool("mock_tool")
        assert result is True
        assert tool.state == ToolState.IDLE

    def test_get_statistics(self):
        tool = MockTool("device_001")
        self.registry.register(tool)

        stats = self.registry.get_statistics()
        assert stats["total_tools"] == 1
        assert "state_distribution" in stats

    def test_clear(self):
        tool = MockTool("device_001")
        self.registry.register(tool)

        self.registry.clear()
        assert self.registry.count() == 0


class TestToolRegistryGlobal:
    """测试全局工具注册表实例"""

    def test_global_instance(self):
        assert tool_registry is not None
        assert isinstance(tool_registry, ToolRegistry)
