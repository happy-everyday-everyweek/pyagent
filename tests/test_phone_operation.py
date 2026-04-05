"""
PyAgent 手机操作工具和 AutoGLM 子代理测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.mobile.tool_registry import (
    MobileToolRegistry,
    ToolCategory,
    ToolInfo,
    ToolParameter,
    ToolResult,
    ToolState,
    mobile_tool_registry,
)
from src.mobile.advanced_control.subagent import (
    ActionStep,
    MobileControlManager,
    MobileSubAgent,
    PlannedAction,
    ScreenAnalysis,
    SubAgentResult,
    SubAgentStatus,
    get_mobile_control_manager,
)


class TestPhoneOperationToolRegistered:
    """测试手机操作工具注册"""

    def test_phone_operation_tool_registered(self):
        """验证工具已注册"""
        registry = MobileToolRegistry()
        tool = registry.get_tool("phone_operation")
        
        assert tool is not None
        assert tool.name == "phone_operation"

    def test_phone_operation_tool_parameters(self):
        """验证工具参数定义"""
        registry = MobileToolRegistry()
        tool = registry.get_tool("phone_operation")
        
        assert tool is not None
        info = tool.info
        
        assert info.name == "phone_operation"
        assert info.category == ToolCategory.WORKFLOW
        assert "intent" in [p.name for p in info.parameters]
        
        intent_param = next((p for p in info.parameters if p.name == "intent"), None)
        assert intent_param is not None
        assert intent_param.required is True
        assert intent_param.type == "string"
        
        target_app_param = next((p for p in info.parameters if p.name == "target_app"), None)
        assert target_app_param is not None
        assert target_app_param.required is False
        
        max_steps_param = next((p for p in info.parameters if p.name == "max_steps"), None)
        assert max_steps_param is not None
        assert max_steps_param.default == 20
        
        virtual_display_param = next((p for p in info.parameters if p.name == "use_virtual_display"), None)
        assert virtual_display_param is not None
        assert virtual_display_param.default is False


class TestPhoneOperationToolExecution:
    """测试手机操作工具执行"""

    @pytest.mark.asyncio
    async def test_phone_operation_missing_intent(self):
        """测试缺少 intent 参数"""
        registry = MobileToolRegistry()
        
        result = await registry.execute_tool("phone_operation", {})
        
        assert result.success is False
        assert "intent" in result.error

    @pytest.mark.asyncio
    async def test_phone_operation_success(self):
        """测试成功执行（Mock LLM 响应）"""
        mock_result = SubAgentResult(
            success=True,
            message="操作成功完成",
            agent_id="test_agent",
            steps_taken=3,
            final_state="completed",
        )
        
        with patch("src.llm.get_default_client") as mock_client, \
             patch("src.mobile.advanced_control.subagent.get_mobile_control_manager") as mock_manager_factory:
            
            mock_manager = MagicMock()
            mock_manager.run_subagent_main = AsyncMock(return_value=mock_result)
            mock_manager_factory.return_value = mock_manager
            mock_client.return_value = MagicMock()
            
            registry = MobileToolRegistry()
            result = await registry.execute_tool("phone_operation", {
                "intent": "打开微信发送消息给张三",
                "max_steps": 10,
            })
            
            assert result.success is True
            assert result.data["success"] is True
            assert result.data["steps_taken"] == 3
            mock_manager.run_subagent_main.assert_called_once()

    @pytest.mark.asyncio
    async def test_phone_operation_with_virtual_display(self):
        """测试虚拟屏幕模式"""
        mock_result = SubAgentResult(
            success=True,
            message="虚拟屏幕操作完成",
            agent_id="virtual_agent",
            steps_taken=5,
            final_state="completed",
        )
        
        with patch("src.llm.get_default_client") as mock_client, \
             patch("src.mobile.advanced_control.subagent.get_mobile_control_manager") as mock_manager_factory:
            
            mock_manager = MagicMock()
            mock_manager.run_subagent_virtual = AsyncMock(return_value=mock_result)
            mock_manager_factory.return_value = mock_manager
            mock_client.return_value = MagicMock()
            
            registry = MobileToolRegistry()
            result = await registry.execute_tool("phone_operation", {
                "intent": "打开设置关闭蓝牙",
                "use_virtual_display": True,
                "target_app": "com.android.settings",
            })
            
            assert result.success is True
            assert result.data["success"] is True
            mock_manager.run_subagent_virtual.assert_called_once()
            
            call_args = mock_manager.run_subagent_virtual.call_args
            assert call_args.kwargs["intent"] == "打开设置关闭蓝牙"
            assert call_args.kwargs["target_app"] == "com.android.settings"

    @pytest.mark.asyncio
    async def test_phone_operation_with_target_app(self):
        """测试指定目标应用"""
        mock_result = SubAgentResult(
            success=True,
            message="操作完成",
            agent_id="test_agent",
            steps_taken=2,
        )
        
        with patch("src.llm.get_default_client") as mock_client, \
             patch("src.mobile.advanced_control.subagent.get_mobile_control_manager") as mock_manager_factory:
            
            mock_manager = MagicMock()
            mock_manager.run_subagent_main = AsyncMock(return_value=mock_result)
            mock_manager_factory.return_value = mock_manager
            mock_client.return_value = MagicMock()
            
            registry = MobileToolRegistry()
            result = await registry.execute_tool("phone_operation", {
                "intent": "查看余额",
                "target_app": "com.eg.android.AlipayGphone",
            })
            
            assert result.success is True
            
            call_args = mock_manager.run_subagent_main.call_args
            assert call_args.kwargs["target_app"] == "com.eg.android.AlipayGphone"


class TestSubAgentInitialization:
    """测试 AutoGLM 子代理"""

    def test_subagent_initialization(self):
        """测试子代理初始化"""
        agent = MobileSubAgent(
            agent_id="test_agent_001",
            target_app="com.tencent.mm",
            is_virtual=False,
            device_id="device_123"
        )
        
        assert agent.agent_id == "test_agent_001"
        assert agent.target_app == "com.tencent.mm"
        assert agent.is_virtual is False
        assert agent.device_id == "device_123"
        assert agent.status == SubAgentStatus.IDLE

    def test_subagent_virtual_mode(self):
        """测试虚拟模式子代理"""
        agent = MobileSubAgent(
            agent_id="virtual_agent_001",
            is_virtual=True,
        )
        
        assert agent.is_virtual is True
        assert agent.status == SubAgentStatus.IDLE

    def test_subagent_get_context(self):
        """测试获取上下文"""
        agent = MobileSubAgent(
            agent_id="context_test",
            target_app="com.test.app",
        )
        
        context = agent.get_context()
        
        assert context["agent_id"] == "context_test"
        assert context["target_app"] == "com.test.app"
        assert context["status"] == SubAgentStatus.IDLE.value
        assert "created_at" in context

    def test_subagent_pause_resume(self):
        """测试暂停和恢复"""
        agent = MobileSubAgent(agent_id="pause_test")
        
        assert agent.pause() is False
        
        agent._status = SubAgentStatus.RUNNING
        assert agent.pause() is True
        assert agent.status == SubAgentStatus.PAUSED
        
        assert agent.resume() is True
        assert agent.status == SubAgentStatus.RUNNING


class TestSubAgentScreenCapture:
    """测试子代理截图功能"""

    @pytest.mark.asyncio
    async def test_subagent_screen_capture(self):
        """测试截图功能（Mock）"""
        agent = MobileSubAgent(agent_id="capture_test")
        
        mock_screen_tools = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"image_base64": "base64_encoded_image_data"}
        mock_screen_tools.capture_screen = AsyncMock(return_value=mock_result)
        
        mock_context = MagicMock()
        
        with patch.object(agent, '_init_screen_tools', return_value=True):
            agent._screen_tools = mock_screen_tools
            agent._tool_context = mock_context
            
            result = await agent._capture_screen()
            
            assert result == "base64_encoded_image_data"
            mock_screen_tools.capture_screen.assert_called_once()

    @pytest.mark.asyncio
    async def test_subagent_screen_capture_failure(self):
        """测试截图失败情况"""
        agent = MobileSubAgent(agent_id="capture_fail_test")
        
        mock_screen_tools = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "截图失败"
        mock_screen_tools.capture_screen = AsyncMock(return_value=mock_result)
        
        agent._screen_tools = mock_screen_tools
        agent._tool_context = MagicMock()
        
        result = await agent._capture_screen()
        
        assert result is None


class TestSubAgentActionExecution:
    """测试子代理操作执行"""

    @pytest.mark.asyncio
    async def test_subagent_action_execution_tap(self):
        """测试点击操作执行（Mock）"""
        agent = MobileSubAgent(agent_id="action_test")
        
        mock_screen_tools = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.output = "点击成功"
        mock_screen_tools.tap = AsyncMock(return_value=mock_result)
        
        agent._screen_tools = mock_screen_tools
        agent._tool_context = MagicMock()
        
        action = PlannedAction(
            action_type="tap",
            params={"x": 100, "y": 200},
            description="点击按钮",
        )
        
        result = await agent._execute_action(action)
        
        assert result.success is True
        mock_screen_tools.tap.assert_called_once_with(100, 200)

    @pytest.mark.asyncio
    async def test_subagent_action_execution_swipe(self):
        """测试滑动操作执行（Mock）"""
        agent = MobileSubAgent(agent_id="swipe_test")
        
        mock_screen_tools = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_screen_tools.swipe = AsyncMock(return_value=mock_result)
        
        agent._screen_tools = mock_screen_tools
        agent._tool_context = MagicMock()
        
        action = PlannedAction(
            action_type="swipe",
            params={"x1": 100, "y1": 500, "x2": 100, "y2": 100, "duration": 300},
            description="向上滑动",
        )
        
        result = await agent._execute_action(action)
        
        assert result.success is True
        mock_screen_tools.swipe.assert_called_once_with(100, 500, 100, 100, 300)

    @pytest.mark.asyncio
    async def test_subagent_action_execution_input_text(self):
        """测试文本输入操作（Mock）"""
        agent = MobileSubAgent(agent_id="input_test")
        
        mock_screen_tools = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_screen_tools.input_text = AsyncMock(return_value=mock_result)
        
        agent._screen_tools = mock_screen_tools
        agent._tool_context = MagicMock()
        
        action = PlannedAction(
            action_type="input_text",
            params={"text": "Hello World"},
            description="输入文本",
        )
        
        result = await agent._execute_action(action)
        
        assert result.success is True
        mock_screen_tools.input_text.assert_called_once_with("Hello World")

    @pytest.mark.asyncio
    async def test_subagent_action_execution_complete(self):
        """测试任务完成操作"""
        agent = MobileSubAgent(agent_id="complete_test")
        
        agent._screen_tools = MagicMock()
        agent._tool_context = MagicMock()
        
        action = PlannedAction(
            action_type="complete",
            params={},
            description="任务完成",
            reason="目标已达成",
        )
        
        result = await agent._execute_action(action)
        
        assert result.success is True
        assert result.data["completed"] is True

    @pytest.mark.asyncio
    async def test_subagent_action_execution_press_key(self):
        """测试按键操作（Mock）"""
        agent = MobileSubAgent(agent_id="key_test")
        
        mock_screen_tools = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_screen_tools.press_key = AsyncMock(return_value=mock_result)
        
        agent._screen_tools = mock_screen_tools
        agent._tool_context = MagicMock()
        
        action = PlannedAction(
            action_type="press_key",
            params={"key": "back"},
            description="返回",
        )
        
        result = await agent._execute_action(action)
        
        assert result.success is True
        mock_screen_tools.press_key.assert_called_once_with("KEYCODE_BACK")


class TestMobileControlManager:
    """测试手机控制管理器"""

    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = MobileControlManager()
        
        assert manager is not None
        assert manager._virtual_displays == {}
        assert manager._cached_agent_id is None

    def test_get_cached_agent_id(self):
        """测试获取缓存的代理ID"""
        manager = MobileControlManager()
        
        assert manager.get_cached_agent_id() is None
        
        manager._cached_agent_id = "cached_agent_001"
        assert manager.get_cached_agent_id() == "cached_agent_001"

    def test_close_all_virtual_displays(self):
        """测试关闭所有虚拟屏幕"""
        manager = MobileControlManager()
        
        manager._virtual_displays = {
            "agent_1": MagicMock(),
            "agent_2": MagicMock(),
        }
        
        count = manager.close_all_virtual_displays()
        
        assert count == 2
        assert manager._virtual_displays == {}
        assert manager._cached_agent_id is None

    def test_get_status(self):
        """测试获取状态"""
        manager = MobileControlManager()
        
        status = manager.get_status()
        
        assert "virtual_displays" in status
        assert "cached_agent_id" in status
        assert "main_agent_status" in status
        assert "agents" in status

    @pytest.mark.asyncio
    async def test_run_subagent_main(self):
        """测试主屏幕执行"""
        manager = MobileControlManager()
        
        with patch.object(MobileSubAgent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = SubAgentResult(
                success=True,
                message="执行成功",
                agent_id="main",
                steps_taken=3,
            )
            
            with patch.object(MobileSubAgent, '_init_screen_tools', return_value=True):
                result = await manager.run_subagent_main(
                    intent="打开微信",
                    max_steps=10,
                )
            
            assert result.success is True
            assert result.agent_id == "main"
            assert manager._main_agent is not None

    @pytest.mark.asyncio
    async def test_run_subagent_virtual(self):
        """测试虚拟屏幕执行"""
        manager = MobileControlManager()
        
        with patch.object(MobileSubAgent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = SubAgentResult(
                success=True,
                message="虚拟执行成功",
                agent_id="virtual_001",
                steps_taken=5,
            )
            
            with patch.object(MobileSubAgent, '_init_screen_tools', return_value=True):
                result = await manager.run_subagent_virtual(
                    intent="测试操作",
                    agent_id="virtual_001",
                    max_steps=15,
                )
            
            assert result.success is True
            assert result.agent_id == "virtual_001"
            assert "virtual_001" in manager._virtual_displays

    @pytest.mark.asyncio
    async def test_run_subagent_parallel(self):
        """测试并行执行"""
        manager = MobileControlManager()
        
        mock_results = [
            SubAgentResult(success=True, message="任务1完成", agent_id="agent_1"),
            SubAgentResult(success=True, message="任务2完成", agent_id="agent_2"),
        ]
        
        with patch.object(manager, 'run_subagent_virtual', new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = mock_results
            
            intents = [
                {"intent": "任务1", "agent_id": "agent_1", "target_app": "com.app1"},
                {"intent": "任务2", "agent_id": "agent_2", "target_app": "com.app2"},
            ]
            
            results = await manager.run_subagent_parallel(intents)
            
            assert len(results) == 2
            assert all(r.success for r in results)


class TestSubAgentResult:
    """测试子代理结果"""

    def test_subagent_result_creation(self):
        """测试结果创建"""
        result = SubAgentResult(
            success=True,
            message="操作成功",
            agent_id="test_agent",
            steps_taken=5,
            final_state="completed",
        )
        
        assert result.success is True
        assert result.message == "操作成功"
        assert result.agent_id == "test_agent"
        assert result.steps_taken == 5
        assert result.final_state == "completed"

    def test_subagent_result_with_error(self):
        """测试错误结果"""
        result = SubAgentResult(
            success=False,
            message="操作失败",
            agent_id="error_agent",
            error="截图失败",
        )
        
        assert result.success is False
        assert result.error == "截图失败"


class TestActionStep:
    """测试操作步骤"""

    def test_action_step_creation(self):
        """测试步骤创建"""
        step = ActionStep(
            step_id=1,
            action_type="tap",
            params={"x": 100, "y": 200},
            description="点击按钮",
        )
        
        assert step.step_id == 1
        assert step.action_type == "tap"
        assert step.params == {"x": 100, "y": 200}
        assert step.description == "点击按钮"
        assert step.success is None

    def test_action_step_with_result(self):
        """测试带结果的步骤"""
        step = ActionStep(
            step_id=2,
            action_type="swipe",
            params={"x1": 0, "y1": 500, "x2": 0, "y2": 100},
            description="滑动屏幕",
            result="滑动成功",
            success=True,
        )
        
        assert step.result == "滑动成功"
        assert step.success is True


class TestScreenAnalysis:
    """测试屏幕分析"""

    def test_screen_analysis_creation(self):
        """测试屏幕分析创建"""
        analysis = ScreenAnalysis(
            description="微信聊天界面",
            interactive_elements=[
                {"type": "button", "text": "发送", "bounds": {"x": 900, "y": 1800}}
            ],
            current_app="com.tencent.mm",
            suggested_actions=[
                {"action": "tap", "params": {"x": 900, "y": 1800}, "description": "点击发送"}
            ],
        )
        
        assert analysis.description == "微信聊天界面"
        assert len(analysis.interactive_elements) == 1
        assert analysis.current_app == "com.tencent.mm"
        assert len(analysis.suggested_actions) == 1


class TestPlannedAction:
    """测试规划操作"""

    def test_planned_action_creation(self):
        """测试规划操作创建"""
        action = PlannedAction(
            action_type="tap",
            params={"x": 500, "y": 1000},
            description="点击中间位置",
            confidence=0.9,
            reason="目标元素在此位置",
        )
        
        assert action.action_type == "tap"
        assert action.confidence == 0.9
        assert action.reason == "目标元素在此位置"


class TestGetMobileControlManager:
    """测试获取管理器"""

    def test_get_mobile_control_manager_singleton(self):
        """测试单例模式"""
        from src.mobile.advanced_control.subagent import mobile_control_manager as global_manager
        
        manager1 = get_mobile_control_manager()
        manager2 = get_mobile_control_manager()
        
        assert manager1 is manager2
