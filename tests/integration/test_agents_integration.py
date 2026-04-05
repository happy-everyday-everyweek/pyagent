"""
PyAgent 集成测试 - 智能体系统集成测试

测试智能体注册中心、执行器和多智能体协作。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agents.base import (
    AgentCapability,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseVerticalAgent,
)
from agents.registry import AgentRegistry, AgentInfo
from agents.executor import AgentExecutor


class MockAnalysisAgent(BaseVerticalAgent):
    """模拟分析智能体"""

    def __init__(self):
        capabilities = [
            AgentCapability(
                name="analyze",
                description="Analyze data",
                parameters={"data": "object"}
            )
        ]
        super().__init__(
            name="analysis_agent",
            description="Agent for data analysis",
            capabilities=capabilities
        )

    def _setup_handlers(self) -> None:
        self.register_handler("analyze", self._handle_analyze)

    async def _handle_analyze(self, params: dict) -> dict:
        return {"analysis_result": "processed", "input_size": len(str(params))}


class MockWriterAgent(BaseVerticalAgent):
    """模拟写作智能体"""

    def __init__(self):
        capabilities = [
            AgentCapability(
                name="write",
                description="Write content",
                parameters={"topic": "string"}
            )
        ]
        super().__init__(
            name="writer_agent",
            description="Agent for content writing",
            capabilities=capabilities
        )

    def _setup_handlers(self) -> None:
        self.register_handler("write", self._handle_write)

    async def _handle_write(self, params: dict) -> dict:
        return {"content": f"Article about {params.get('topic', 'unknown')}"}


class TestAgentRegistryIntegration:
    """智能体注册中心集成测试"""

    def setup_method(self):
        self.registry = AgentRegistry()
        self.registry._agents.clear()
        self.registry._capability_index.clear()

    def test_register_multiple_agents(self):
        """测试注册多个智能体"""
        agent1 = MockAnalysisAgent()
        agent2 = MockWriterAgent()

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)

        assert self.registry.get_agent_count() == 2

    def test_capability_indexing(self):
        """测试能力索引"""
        agent1 = MockAnalysisAgent()
        agent2 = MockWriterAgent()

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)

        analysis_agents = self.registry.get_agents_by_capability("analyze")
        assert len(analysis_agents) == 1
        assert analysis_agents[0].name == "analysis_agent"

        writer_agents = self.registry.get_agents_by_capability("write")
        assert len(writer_agents) == 1
        assert writer_agents[0].name == "writer_agent"

    def test_list_all_capabilities(self):
        """测试列出所有能力"""
        agent1 = MockAnalysisAgent()
        agent2 = MockWriterAgent()

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)

        capabilities = self.registry.get_capabilities()
        assert "analyze" in capabilities
        assert "write" in capabilities

    @pytest.mark.asyncio
    async def test_initialize_all_agents(self):
        """测试初始化所有智能体"""
        agent1 = MockAnalysisAgent()
        agent2 = MockWriterAgent()

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)

        results = self.registry.initialize_all()
        assert all(results.values())

        assert agent1.status == AgentStatus.IDLE
        assert agent2.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_shutdown_all_agents(self):
        """测试关闭所有智能体"""
        agent1 = MockAnalysisAgent()
        agent2 = MockWriterAgent()

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        self.registry.initialize_all()

        self.registry.shutdown_all()

        assert agent1.status == AgentStatus.OFFLINE
        assert agent2.status == AgentStatus.OFFLINE


class TestAgentExecutorIntegration:
    """智能体执行器集成测试"""

    def setup_method(self):
        self.registry = AgentRegistry()
        self.registry._agents.clear()
        self.executor = AgentExecutor(registry=self.registry)

    def test_executor_creation(self):
        """测试执行器创建"""
        assert self.executor.registry == self.registry

    @pytest.mark.asyncio
    async def test_execute_single_agent(self):
        """测试执行单个智能体"""
        agent = MockAnalysisAgent()
        self.registry.register_agent(agent)
        agent.initialize()

        request = AgentRequest(
            request_id="req_001",
            action="analyze",
            parameters={"data": {"key": "value"}}
        )

        response = await agent.process_request(request)
        assert response.success is True
        assert "analysis_result" in response.data

    @pytest.mark.asyncio
    async def test_execute_multiple_agents_sequentially(self):
        """测试顺序执行多个智能体"""
        agent1 = MockAnalysisAgent()
        agent2 = MockWriterAgent()

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        self.registry.initialize_all()

        request1 = AgentRequest(
            request_id="req_001",
            action="analyze",
            parameters={"data": "test data"}
        )

        response1 = await agent1.process_request(request1)
        assert response1.success is True

        request2 = AgentRequest(
            request_id="req_002",
            action="write",
            parameters={"topic": "analysis results"}
        )

        response2 = await agent2.process_request(request2)
        assert response2.success is True
        assert "Article about" in response2.data["content"]


class TestMultiAgentCollaboration:
    """多智能体协作集成测试"""

    def setup_method(self):
        self.registry = AgentRegistry()
        self.registry._agents.clear()

    @pytest.mark.asyncio
    async def test_pipeline_execution(self):
        """测试流水线执行"""
        agent1 = MockAnalysisAgent()
        agent2 = MockWriterAgent()

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        self.registry.initialize_all()

        request1 = AgentRequest(
            request_id="req_001",
            action="analyze",
            parameters={"data": "sample"}
        )

        response1 = await agent1.process_request(request1)

        request2 = AgentRequest(
            request_id="req_002",
            action="write",
            parameters={"topic": response1.data["analysis_result"]}
        )

        response2 = await agent2.process_request(request2)

        assert response1.success is True
        assert response2.success is True

    @pytest.mark.asyncio
    async def test_capability_based_routing(self):
        """测试基于能力的路由"""
        agent1 = MockAnalysisAgent()
        agent2 = MockWriterAgent()

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        self.registry.initialize_all()

        agents = self.registry.get_agents_by_capability("analyze")
        assert len(agents) == 1

        selected_agent = agents[0]
        request = AgentRequest(
            request_id="req_001",
            action="analyze",
            parameters={"data": "test"}
        )

        response = await selected_agent.process_request(request)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_error_handling_in_pipeline(self):
        """测试流水线中的错误处理"""
        agent = MockAnalysisAgent()
        self.registry.register_agent(agent)
        agent.initialize()

        request = AgentRequest(
            request_id="req_001",
            action="unknown_action",
            parameters={}
        )

        response = await agent.process_request(request)
        assert response.success is False
        assert "Invalid request" in response.error


class TestAgentLifecycleIntegration:
    """智能体生命周期集成测试"""

    def test_full_lifecycle(self):
        """测试完整生命周期"""
        agent = MockAnalysisAgent()

        assert agent.status == AgentStatus.IDLE

        agent.initialize()
        assert agent.status == AgentStatus.IDLE
        assert agent._initialized is True

        agent.shutdown()
        assert agent.status == AgentStatus.OFFLINE

    def test_multiple_initialize_shutdown_cycles(self):
        """测试多次初始化和关闭循环"""
        agent = MockAnalysisAgent()

        for _ in range(3):
            agent.initialize()
            assert agent._initialized is True

            agent.shutdown()
            assert agent.status == AgentStatus.OFFLINE

    @pytest.mark.asyncio
    async def test_request_after_shutdown(self):
        """测试关闭后的请求处理"""
        agent = MockAnalysisAgent()
        agent.initialize()
        agent.shutdown()

        request = AgentRequest(
            request_id="req_001",
            action="analyze",
            parameters={"data": "test"}
        )

        response = await agent.process_request(request)
        assert response.success is False
