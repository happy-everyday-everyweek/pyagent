"""
PyAgent 浏览器自动化模块测试套件

测试事件系统、DOM 解析器、代理系统和循环检测器。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
sys.path.insert(0, '.')


class TestEvents:
    """事件系统测试"""

    def test_event_type_enum(self):
        """测试事件类型枚举"""
        from browser import EventType
        
        assert EventType.NAVIGATE_TO_URL.value == "navigate_to_url"
        assert EventType.CLICK_ELEMENT.value == "click_element"
        assert EventType.TYPE_TEXT.value == "type_text"
        assert EventType.SCROLL.value == "scroll"

    def test_browser_event_creation(self):
        """测试浏览器事件创建"""
        from browser import NavigateToUrlEvent, EventStatus
        
        event = NavigateToUrlEvent(
            url="https://example.com",
            target_id="test_target",
        )
        
        assert event.url == "https://example.com"
        assert event.target_id == "test_target"
        assert event.status == EventStatus.PENDING

    def test_event_serialization(self):
        """测试事件序列化"""
        from browser import ClickElementEvent
        
        event = ClickElementEvent(
            selector="#submit-btn",
            click_count=2,
        )
        
        data = event.model_dump()
        
        assert data["selector"] == "#submit-btn"
        assert data["click_count"] == 2
        assert "event_id" in data

    def test_create_event_factory(self):
        """测试事件工厂函数"""
        from browser import create_event, EventType, NavigateToUrlEvent
        
        event = create_event(
            EventType.NAVIGATE_TO_URL,
            url="https://test.com",
        )
        
        assert isinstance(event, NavigateToUrlEvent)
        assert event.url == "https://test.com"


class TestEventBus:
    """事件总线测试"""

    def test_event_bus_creation(self):
        """测试事件总线创建"""
        from browser import EventBus
        
        bus = EventBus(name="test_bus")
        
        assert bus.name == "test_bus"
        assert bus._handlers == {}

    def test_event_bus_subscribe(self):
        """测试事件订阅"""
        from browser import EventBus, BaseEvent
        
        bus = EventBus()
        handler_called = []
        
        def handler(event):
            handler_called.append(event)
        
        bus.on("test_event", handler)
        
        assert "test_event" in bus._handlers
        assert len(bus._handlers["test_event"]) == 1

    @pytest.mark.asyncio
    async def test_event_bus_dispatch(self):
        """测试事件分发"""
        from browser import EventBus, BaseEvent, EventState
        
        bus = EventBus()
        received_events = []
        
        async def handler(event):
            received_events.append(event)
        
        bus.on("test_event", handler)
        
        event = BaseEvent(event_type="test_event")
        await bus.dispatch(event)
        
        assert len(received_events) == 1

    def test_event_bus_unsubscribe(self):
        """测试取消订阅"""
        from browser import EventBus
        
        bus = EventBus()
        
        def handler(event):
            pass
        
        bus.on("test_event", handler)
        bus.off("test_event", handler)
        
        assert len(bus._handlers["test_event"]) == 0


class TestRegistry:
    """动作注册中心测试"""

    def test_registry_creation(self):
        """测试注册中心创建"""
        from browser import Registry
        
        registry = Registry()
        
        assert registry.list_actions() == []

    def test_action_registration(self):
        """测试动作注册"""
        from browser import Registry
        
        registry = Registry()
        
        @registry.action("Test action")
        def test_action():
            return "test"
        
        assert "test_action" in registry.list_actions()
        assert registry.get_action("test_action") is not None

    def test_action_with_params(self):
        """测试带参数的动作"""
        from browser import Registry
        from pydantic import BaseModel
        
        class TestParams(BaseModel):
            value: str
        
        registry = Registry()
        
        @registry.action("Test with params", param_model=TestParams)
        def test_with_params(params: TestParams):
            return params.value
        
        action = registry.get_action("test_with_params")
        assert action is not None
        assert action.param_model is not None

    def test_action_descriptions(self):
        """测试动作描述"""
        from browser import Registry
        
        registry = Registry()
        
        @registry.action("First action")
        def action1():
            pass
        
        @registry.action("Second action")
        def action2():
            pass
        
        descriptions = registry.get_action_descriptions()
        
        assert "action1" in descriptions
        assert "action2" in descriptions
        assert descriptions["action1"] == "First action"

    @pytest.mark.asyncio
    async def test_action_execution(self):
        """测试动作执行"""
        from browser import Registry
        
        registry = Registry()
        
        @registry.action("Test action")
        async def test_action():
            return "success"
        
        result = await registry.execute_action("test_action")
        
        assert result.extracted_content == "success"

    def test_action_exclusion(self):
        """测试动作排除"""
        from browser import Registry
        
        registry = Registry(exclude_actions=["excluded_action"])
        
        @registry.action("Excluded action")
        def excluded_action():
            pass
        
        assert "excluded_action" not in registry.list_actions()


class TestLoopDetector:
    """循环检测器测试"""

    def test_loop_detector_creation(self):
        """测试循环检测器创建"""
        from browser import LoopDetector, LoopDetectorConfig
        
        config = LoopDetectorConfig(max_action_repeat=5)
        detector = LoopDetector(config)
        
        assert detector.config.max_action_repeat == 5

    def test_action_loop_detection(self):
        """测试动作循环检测"""
        from browser import LoopDetector, LoopDetectorConfig
        
        config = LoopDetectorConfig(max_action_repeat=3)
        detector = LoopDetector(config)
        
        for _ in range(4):
            detector.record_action("click", {"index": 1}, "https://example.com")
        
        alerts = detector.detect()
        
        action_alerts = [a for a in alerts if a.loop_type.value == "action_repeat"]
        assert len(action_alerts) > 0

    def test_page_stagnant_detection(self):
        """测试页面停滞检测"""
        from browser import LoopDetector, LoopDetectorConfig
        
        config = LoopDetectorConfig(max_page_stagnant=3)
        detector = LoopDetector(config)
        
        for _ in range(4):
            detector.record_page(
                url="https://example.com",
                title="Test",
                content="same content",
                element_count=10,
                interactive_count=5,
            )
        
        alerts = detector.detect()
        
        stagnant_alerts = [a for a in alerts if a.loop_type.value == "page_stagnant"]
        assert len(stagnant_alerts) > 0

    def test_loop_detector_reset(self):
        """测试循环检测器重置"""
        from browser import LoopDetector
        
        detector = LoopDetector()
        
        detector.record_action("click", {"index": 1}, "https://example.com")
        detector.record_page("url", "title", "content", 10, 5)
        
        detector.reset()
        
        stats = detector.get_statistics()
        assert stats["total_actions"] == 0
        assert stats["total_pages"] == 0


class TestLocator:
    """元素定位器测试"""

    def test_locator_creation(self):
        """测试定位器创建"""
        from browser import ElementLocator
        
        locator = ElementLocator()
        
        assert locator._elements == []
        assert locator._selector_map == {}

    def test_element_update(self):
        """测试元素更新"""
        from browser import ElementLocator, ElementInfo
        
        locator = ElementLocator()
        
        elements = [
            ElementInfo(index=0, tag_name="button", text="Click me", is_clickable=True),
            ElementInfo(index=1, tag_name="input", is_input=True),
        ]
        
        locator.update_elements(elements)
        
        assert len(locator._elements) == 2
        assert locator.get_element_by_index(0) is not None

    def test_text_based_location(self):
        """测试基于文本的定位"""
        from browser import ElementLocator, ElementInfo
        
        locator = ElementLocator()
        
        elements = [
            ElementInfo(index=0, tag_name="button", text="Submit", is_clickable=True),
            ElementInfo(index=1, tag_name="button", text="Cancel", is_clickable=True),
        ]
        
        locator.update_elements(elements)
        
        result = locator.get_element_by_text("Submit")
        
        assert result is not None
        assert result.index == 0

    def test_coordinate_location(self):
        """测试坐标定位"""
        from browser import ElementLocator, LocatorType
        
        locator = ElementLocator()
        
        result = locator.locate(LocatorType.COORDINATE, (100, 200))
        
        assert result.success
        assert result.element is not None

    def test_llm_format(self):
        """测试 LLM 格式输出"""
        from browser import ElementLocator, ElementInfo
        
        locator = ElementLocator()
        
        elements = [
            ElementInfo(index=0, tag_name="button", text="Click", is_clickable=True, is_interactive=True),
        ]
        
        locator.update_elements(elements)
        
        llm_text = locator.to_llm_format()
        
        assert "[Interactive Elements]" in llm_text
        assert "[0]" in llm_text


class TestState:
    """状态管理测试"""

    def test_browser_state_creation(self):
        """测试浏览器状态创建"""
        from browser import BrowserState
        
        state = BrowserState(
            url="https://example.com",
            title="Example",
        )
        
        assert state.url == "https://example.com"
        assert state.title == "Example"

    def test_tab_state_creation(self):
        """测试标签页状态创建"""
        from browser import TabState
        
        tab = TabState(
            tab_id="tab_1",
            url="https://example.com",
            title="Example",
        )
        
        assert tab.tab_id == "tab_1"
        assert tab.url == "https://example.com"

    def test_state_diff(self):
        """测试状态差异检测"""
        from browser import StateDiff
        
        diff = StateDiff(
            url_changed=True,
            old_url="https://example.com",
            new_url="https://example.com/page2",
            title_changed=True,
            old_title="Example",
            new_title="Page 2",
        )
        
        assert diff.url_changed
        assert diff.title_changed
        assert diff.has_changes


class TestStructuredOutput:
    """结构化输出测试"""

    def test_processor_creation(self):
        """测试处理器创建"""
        from browser import StructuredOutputProcessor
        
        processor = StructuredOutputProcessor()
        
        assert processor._output_model is None
        assert processor._dedup_enabled

    def test_single_extraction(self):
        """测试单条提取"""
        from browser import StructuredOutputProcessor
        
        processor = StructuredOutputProcessor()
        
        result = processor.extract_single(
            {"name": "Test", "value": 123},
            validate=False,
        )
        
        assert result.success
        assert len(result.items) == 1

    def test_deduplication(self):
        """测试去重"""
        from browser import StructuredOutputProcessor
        
        processor = StructuredOutputProcessor(dedup_enabled=True)
        
        processor.extract_single({"id": 1, "name": "Test"}, validate=False)
        result = processor.extract_single({"id": 1, "name": "Test"}, validate=False)
        
        assert result.total_count == 1

    def test_batch_extraction(self):
        """测试批量提取"""
        from browser import StructuredOutputProcessor
        
        processor = StructuredOutputProcessor()
        
        result = processor.extract_batch(
            [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"},
            ],
            validate=False,
        )
        
        assert result.success
        assert len(result.items) == 2


class TestSensitiveData:
    """敏感数据处理测试"""

    def test_handler_creation(self):
        """测试处理器创建"""
        from browser import SensitiveDataHandler
        
        handler = SensitiveDataHandler()
        
        assert handler.config.enabled

    def test_redact_value(self):
        """测试值脱敏"""
        from browser import SensitiveDataHandler, SensitiveDataType
        
        handler = SensitiveDataHandler()
        handler.register_sensitive_field(
            "password",
            SensitiveDataType.PASSWORD,
            "[PASSWORD]",
        )
        
        redacted = handler.redact_value("password", "secret123")
        
        assert redacted == "[PASSWORD]"

    def test_redact_dict(self):
        """测试字典脱敏"""
        from browser import SensitiveDataHandler, SensitiveDataType
        
        handler = SensitiveDataHandler()
        handler.register_sensitive_field(
            "api_key",
            SensitiveDataType.API_KEY,
            "[API_KEY]",
        )
        
        data = {
            "username": "user",
            "api_key": "sk-123456",
        }
        
        redacted = handler.redact_dict(data)
        
        assert redacted["username"] == "user"
        assert redacted["api_key"] == "[API_KEY]"

    def test_string_redaction(self):
        """测试字符串脱敏"""
        from browser import SensitiveDataHandler
        
        handler = SensitiveDataHandler()
        
        text = "Contact me at test@example.com"
        redacted = handler.redact_string(text)
        
        assert "test@example.com" not in redacted


class TestPlanner:
    """任务规划器测试"""

    def test_planner_creation(self):
        """测试规划器创建"""
        from browser import TaskPlanner
        
        planner = TaskPlanner()
        
        assert planner._plans == {}

    def test_default_plan_creation(self):
        """测试默认计划创建"""
        from browser import TaskPlanner
        
        planner = TaskPlanner()
        
        plan = planner._create_default_plan("Test task")
        
        assert plan.task == "Test task"
        assert len(plan.steps) == 3

    def test_plan_progress(self):
        """测试计划进度"""
        from browser import Plan, StepStatus
        
        plan = Plan(task="Test task")
        plan.add_step("Step 1")
        plan.add_step("Step 2")
        
        plan.update_step_status(0, StepStatus.COMPLETED)
        
        progress = plan.get_progress()
        
        assert progress["completed"] == 1
        assert progress["total"] == 2


class TestAgent:
    """浏览器代理测试"""

    def test_agent_creation(self):
        """测试代理创建"""
        from browser import BrowserAgent, Registry, EventBus
        
        registry = Registry()
        event_bus = EventBus()
        
        agent = BrowserAgent(
            task="Test task",
            registry=registry,
            event_bus=event_bus,
        )
        
        assert agent.task == "Test task"
        assert agent.max_steps == 100

    def test_agent_status(self):
        """测试代理状态"""
        from browser import BrowserAgent, Registry, EventBus, AgentState
        
        registry = Registry()
        event_bus = EventBus()
        
        agent = BrowserAgent(
            task="Test task",
            registry=registry,
            event_bus=event_bus,
        )
        
        status = agent.get_status()
        
        assert status.state == AgentState.IDLE
        assert status.current_step == 0

    def test_agent_reset(self):
        """测试代理重置"""
        from browser import BrowserAgent, Registry, EventBus
        
        registry = Registry()
        event_bus = EventBus()
        
        agent = BrowserAgent(
            task="Test task",
            registry=registry,
            event_bus=event_bus,
        )
        agent.status.current_step = 10
        
        agent.reset()
        
        assert agent.status.current_step == 0

    def test_message_manager(self):
        """测试消息管理器"""
        from browser import MessageManager
        
        manager = MessageManager(task="Test task")
        
        messages = manager.build_initial_messages()
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
