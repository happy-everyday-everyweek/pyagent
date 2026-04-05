"""
PyAgent 智能体系统测试
"""

import pytest

from agents.base import (
    AgentCapability,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseVerticalAgent,
)
from agents.registry import AgentInfo, AgentRegistry


class MockVerticalAgent(BaseVerticalAgent):
    """测试用模拟智能体"""

    def __init__(self, name: str = "test_agent"):
        capabilities = [
            AgentCapability(
                name="test_action",
                description="Test action capability",
                parameters={"param1": "string"}
            )
        ]
        super().__init__(
            name=name,
            description="Test agent for unit tests",
            capabilities=capabilities
        )

    def _setup_handlers(self) -> None:
        self.register_handler("test_action", self._handle_test_action)

    async def _handle_test_action(self, params: dict) -> dict:
        return {"result": "success", "params": params}


class TestAgentStatus:
    """测试智能体状态枚举"""

    def test_status_values(self):
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.BUSY.value == "busy"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.OFFLINE.value == "offline"

    def test_status_count(self):
        assert len(AgentStatus) == 4


class TestAgentCapability:
    """测试智能体能力"""

    def test_capability_creation(self):
        cap = AgentCapability(
            name="test_cap",
            description="Test capability",
            parameters={"key": "value"}
        )
        assert cap.name == "test_cap"
        assert cap.description == "Test capability"
        assert cap.parameters == {"key": "value"}

    def test_capability_default_parameters(self):
        cap = AgentCapability(name="simple", description="Simple")
        assert cap.parameters == {}


class TestAgentRequest:
    """测试智能体请求"""

    def test_request_creation(self):
        request = AgentRequest(
            request_id="req_001",
            action="test_action",
            parameters={"param": "value"}
        )
        assert request.request_id == "req_001"
        assert request.action == "test_action"
        assert request.parameters == {"param": "value"}
        assert request.timestamp is not None


class TestAgentResponse:
    """测试智能体响应"""

    def test_success_response(self):
        response = AgentResponse(
            request_id="req_001",
            success=True,
            data={"result": "ok"}
        )
        assert response.success is True
        assert response.data == {"result": "ok"}
        assert response.error == ""

    def test_error_response(self):
        response = AgentResponse(
            request_id="req_001",
            success=False,
            error="Something went wrong"
        )
        assert response.success is False
        assert response.error == "Something went wrong"


class TestBaseVerticalAgent:
    """测试智能体基类"""

    def test_agent_creation(self):
        agent = MockVerticalAgent("test_agent")
        assert agent.name == "test_agent"
        assert agent.description == "Test agent for unit tests"
        assert agent.status == AgentStatus.IDLE
        assert len(agent.capabilities) == 1

    def test_get_capabilities(self):
        agent = MockVerticalAgent()
        caps = agent.get_capabilities()
        assert len(caps) == 1
        assert caps[0].name == "test_action"

    def test_has_capability(self):
        agent = MockVerticalAgent()
        assert agent.has_capability("test_action") is True
        assert agent.has_capability("nonexistent") is False

    def test_initialize(self):
        agent = MockVerticalAgent()
        assert agent.initialize() is True
        assert agent.status == AgentStatus.IDLE

    def test_initialize_twice(self):
        agent = MockVerticalAgent()
        assert agent.initialize() is True
        assert agent.initialize() is True

    def test_shutdown(self):
        agent = MockVerticalAgent()
        agent.initialize()
        agent.shutdown()
        assert agent.status == AgentStatus.OFFLINE

    def test_validate_request(self):
        agent = MockVerticalAgent()
        agent.initialize()

        valid_request = AgentRequest(
            request_id="req_001",
            action="test_action",
            parameters={}
        )
        assert agent.validate_request(valid_request) is True

        invalid_request = AgentRequest(
            request_id="req_002",
            action="unknown_action",
            parameters={}
        )
        assert agent.validate_request(invalid_request) is False

    def test_validate_request_not_initialized(self):
        agent = MockVerticalAgent()
        request = AgentRequest(
            request_id="req_001",
            action="test_action",
            parameters={}
        )
        assert agent.validate_request(request) is False

    @pytest.mark.asyncio
    async def test_process_request(self):
        agent = MockVerticalAgent()
        agent.initialize()

        request = AgentRequest(
            request_id="req_001",
            action="test_action",
            parameters={"param1": "value1"}
        )

        response = await agent.process_request(request)
        assert response.success is True
        assert response.data["result"] == "success"

    @pytest.mark.asyncio
    async def test_process_invalid_request(self):
        agent = MockVerticalAgent()
        agent.initialize()

        request = AgentRequest(
            request_id="req_001",
            action="unknown_action",
            parameters={}
        )

        response = await agent.process_request(request)
        assert response.success is False
        assert "Invalid request" in response.error

    def test_to_dict(self):
        agent = MockVerticalAgent()
        agent.initialize()

        data = agent.to_dict()
        assert data["name"] == "test_agent"
        assert data["status"] == "idle"
        assert data["initialized"] is True
        assert len(data["capabilities"]) == 1


class TestAgentRegistry:
    """测试智能体注册中心"""

    def setup_method(self):
        self.registry = AgentRegistry()
        self.registry._agents.clear()
        self.registry._capability_index.clear()

    def test_registry_singleton(self):
        registry1 = AgentRegistry()
        registry2 = AgentRegistry()
        assert registry1 is registry2

    def test_register_agent(self):
        agent = MockVerticalAgent("agent1")
        result = self.registry.register_agent(agent)
        assert result is True
        assert self.registry.get_agent_count() == 1

    def test_register_duplicate_agent(self):
        agent1 = MockVerticalAgent("agent1")
        agent2 = MockVerticalAgent("agent1")

        self.registry.register_agent(agent1)
        result = self.registry.register_agent(agent2)
        assert result is False

    def test_unregister_agent(self):
        agent = MockVerticalAgent("agent1")
        self.registry.register_agent(agent)

        result = self.registry.unregister_agent("agent1")
        assert result is True
        assert self.registry.get_agent_count() == 0

    def test_unregister_nonexistent_agent(self):
        result = self.registry.unregister_agent("nonexistent")
        assert result is False

    def test_get_agent(self):
        agent = MockVerticalAgent("agent1")
        self.registry.register_agent(agent)

        retrieved = self.registry.get_agent("agent1")
        assert retrieved is agent

    def test_get_nonexistent_agent(self):
        retrieved = self.registry.get_agent("nonexistent")
        assert retrieved is None

    def test_list_agents(self):
        agent1 = MockVerticalAgent("agent1")
        agent2 = MockVerticalAgent("agent2")

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)

        agents = self.registry.list_agents()
        assert len(agents) == 2

    def test_get_agents_by_capability(self):
        agent = MockVerticalAgent("agent1")
        self.registry.register_agent(agent)

        agents = self.registry.get_agents_by_capability("test_action")
        assert len(agents) == 1

    def test_get_capabilities(self):
        agent = MockVerticalAgent("agent1")
        self.registry.register_agent(agent)

        capabilities = self.registry.get_capabilities()
        assert "test_action" in capabilities

    def test_initialize_all(self):
        agent1 = MockVerticalAgent("agent1")
        agent2 = MockVerticalAgent("agent2")

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)

        results = self.registry.initialize_all()
        assert results["agent1"] is True
        assert results["agent2"] is True

    def test_shutdown_all(self):
        agent = MockVerticalAgent("agent1")
        self.registry.register_agent(agent)
        agent.initialize()

        self.registry.shutdown_all()
        assert agent.status == AgentStatus.OFFLINE

    def test_to_dict(self):
        agent = MockVerticalAgent("agent1")
        self.registry.register_agent(agent)

        data = self.registry.to_dict()
        assert data["agent_count"] == 1
        assert len(data["agents"]) == 1


class TestAgentInfo:
    """测试智能体信息"""

    def test_agent_info_creation(self):
        info = AgentInfo(
            name="test_agent",
            description="Test description",
            capabilities=["cap1", "cap2"],
            status="idle"
        )
        assert info.name == "test_agent"
        assert info.description == "Test description"
        assert info.capabilities == ["cap1", "cap2"]
        assert info.status == "idle"
