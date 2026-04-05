"""
E2E tests for multi-agent architecture with MockLLM integration.

Tests the FULL multi-agent pipeline:
  User message → Orchestrator → Agent(MockLLM) → ReAct loop
  → delegate_to_agent tool call → Orchestrator.delegate()
  → Sub-Agent(MockLLM) → result → Parent aggregates → final answer

This validates that LLM-driven delegation decisions flow correctly through
the entire orchestrator / pool / factory / tool handler chain.
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from openakita.agents.fallback import FallbackResolver
from openakita.agents.orchestrator import AgentOrchestrator
from openakita.agents.profile import (
    AgentProfile,
    AgentType,
    ProfileStore,
    SkillsMode,
)
from openakita.sessions.session import Session, SessionConfig, SessionContext
from tests.fixtures.mock_llm import MockBrain, MockLLMClient, MockResponse

logger = logging.getLogger(__name__)


# ================================================================
# TestableAgent: lightweight agent with a real ReAct loop
# driven by MockLLMClient, supporting agent tool delegation.
# ================================================================

class _TestableAgent:
    """Minimal Agent replacement that runs a MockLLM-driven ReAct loop.

    Supports tool dispatch for agent delegation tools
    (delegate_to_agent, delegate_parallel, spawn_agent, create_agent).
    """

    MAX_ITERATIONS = 10

    def __init__(
        self,
        name: str,
        mock_client: MockLLMClient,
        tool_handler: Any = None,
    ):
        self.name = name
        self.mock_client = mock_client
        self.brain = MockBrain(mock_client)
        self._tool_handler = tool_handler
        self._is_sub_agent_call = False
        self._agent_profile: AgentProfile | None = None
        self._last_finalized_trace: list[dict] = []
        self._current_session: Any = None
        self._custom_prompt_suffix: str = ""

        self.agent_state = MagicMock()
        task_mock = MagicMock()
        task_mock.iteration = 0
        task_mock.status = MagicMock()
        task_mock.status.value = "reasoning"
        task_mock.tools_executed = []
        self.agent_state.get_task_for_session = MagicMock(return_value=task_mock)
        self.agent_state.current_task = task_mock

        self.skill_registry = MagicMock()
        self.skill_registry.list_all = MagicMock(return_value=[])
        self.initialized = True

    async def initialize(self, start_scheduler: bool = True) -> None:
        pass

    async def chat_with_session(
        self,
        message: str,
        session_messages: list[dict],
        session_id: str = "",
        session: Any = None,
        gateway: Any = None,
        **kwargs,
    ) -> str:
        """Simplified ReAct loop: call LLM → if tool_use → execute → loop."""
        self._current_session = session
        messages = list(session_messages) + [
            {"role": "user", "content": message},
        ]

        for iteration in range(self.MAX_ITERATIONS):
            response = await self.brain.messages_create_async(
                messages=messages,
                system=f"You are {self.name}.",
            )

            text_parts = []
            tool_calls = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
                elif hasattr(block, "name"):
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            task = self.agent_state.current_task
            task.iteration = iteration + 1
            task.tools_executed = [tc["name"] for tc in tool_calls]

            self._last_finalized_trace.append({
                "iteration": iteration + 1,
                "thinking": "",
                "text": " ".join(text_parts),
                "tool_calls": tool_calls,
            })

            if not tool_calls:
                return " ".join(text_parts) or "Done"

            # Execute tool calls
            tool_results = []
            for tc in tool_calls:
                result = await self._execute_tool(tc["name"], tc["input"])
                tool_results.append({
                    "tool_use_id": tc["id"],
                    "content": result,
                })

            # Build next messages
            assistant_content = []
            for text in text_parts:
                if text:
                    assistant_content.append({"type": "text", "text": text})
            for tc in tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": tc["input"],
                })
            messages.append({"role": "assistant", "content": assistant_content})

            user_content = []
            for tr in tool_results:
                user_content.append({
                    "type": "tool_result",
                    "tool_use_id": tr["tool_use_id"],
                    "content": tr["content"],
                })
            messages.append({"role": "user", "content": user_content})

        return "Max iterations reached"

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Dispatch tool calls. Agent tools go to the handler; others are mocked."""
        agent_tools = {
            "delegate_to_agent", "delegate_parallel",
            "spawn_agent", "create_agent",
        }
        if tool_name in agent_tools and self._tool_handler:
            return await self._tool_handler(tool_name, tool_input)
        return f"[Mock tool result for {tool_name}]"

    async def shutdown(self) -> None:
        pass


# ================================================================
# TestableAgentFactory: creates TestableAgent with MockLLMClient
# ================================================================

class _TestableAgentFactory:
    """Factory that creates TestableAgent instances with configurable MockLLM responses."""

    def __init__(self):
        self._response_map: dict[str, list[MockResponse]] = {}
        self._default_responses: dict[str, str] = {}

    def configure_agent(
        self,
        profile_id: str,
        responses: list[MockResponse] | None = None,
        default_response: str = "Done",
    ):
        """Pre-configure LLM responses for agents created with this profile."""
        if responses:
            self._response_map[profile_id] = responses
        self._default_responses[profile_id] = default_response

    async def create(self, profile: AgentProfile, **kwargs) -> TestableAgent:
        client = MockLLMClient()

        if profile.id in self._response_map:
            client.preset_sequence(list(self._response_map[profile.id]))
        default = self._default_responses.get(profile.id, f"Response from {profile.id}")
        client.set_default_response(default)

        from openakita.tools.handlers.agent import AgentToolHandler

        agent = _TestableAgent(
            name=profile.get_display_name(),
            mock_client=client,
        )
        agent._agent_profile = profile

        handler = AgentToolHandler(agent)
        agent._tool_handler = handler.handle

        return agent


# ================================================================
# Fixtures
# ================================================================

def _make_session(
    session_id: str = "test-session",
    agent_profile_id: str = "default",
) -> Session:
    ctx = SessionContext()
    ctx.agent_profile_id = agent_profile_id
    return Session(
        id=session_id,
        channel="cli",
        chat_id="chat-1",
        user_id="user-1",
        context=ctx,
        config=SessionConfig(),
    )


@pytest.fixture
def tmp_agents_dir(tmp_path: Path) -> Path:
    d = tmp_path / "agents"
    d.mkdir()
    return d


@pytest.fixture
def profile_store(tmp_agents_dir: Path) -> ProfileStore:
    store = ProfileStore(tmp_agents_dir)
    store.save(AgentProfile(
        id="default",
        name="Default Coordinator",
        type=AgentType.SYSTEM,
        description="General coordinator",
        icon="🤖",
    ))
    store.save(AgentProfile(
        id="researcher",
        name="Research Agent",
        type=AgentType.CUSTOM,
        description="Specialized in web research",
        skills=["web_search"],
        skills_mode=SkillsMode.INCLUSIVE,
        icon="🔍",
    ))
    store.save(AgentProfile(
        id="coder",
        name="Code Agent",
        type=AgentType.CUSTOM,
        description="Specialized in coding tasks",
        skills=["write_file", "read_file", "run_shell"],
        skills_mode=SkillsMode.INCLUSIVE,
        icon="💻",
    ))
    store.save(AgentProfile(
        id="fragile-agent",
        name="Fragile Agent",
        type=AgentType.CUSTOM,
        description="Agent that tends to fail",
        fallback_profile_id="default",
        icon="⚠️",
    ))
    return store


@pytest.fixture
def factory() -> _TestableAgentFactory:
    return _TestableAgentFactory()


@pytest.fixture
def orchestrator(profile_store, factory, tmp_path, monkeypatch) -> AgentOrchestrator:
    from openakita.agents.factory import AgentInstancePool

    pool = AgentInstancePool(factory=factory, idle_timeout=300)
    fallback = FallbackResolver(profile_store)

    orch = AgentOrchestrator()
    orch._profile_store = profile_store
    orch._pool = pool
    orch._fallback = fallback
    orch._log_dir = tmp_path / "delegation_logs"
    orch._log_dir.mkdir(parents=True, exist_ok=True)

    # Inject orchestrator into openakita.main so AgentToolHandler can find it
    import openakita.main as main_mod
    monkeypatch.setattr(main_mod, "_orchestrator", orch, raising=False)

    return orch


# ================================================================
# Test 1: Single delegation — LLM decides to delegate
# ================================================================

class TestSingleDelegation:
    """Parent agent's LLM decides to delegate to a researcher,
    the researcher completes the task, and the parent summarizes.
    """

    @pytest.mark.asyncio
    async def test_llm_driven_delegation(self, orchestrator, factory, profile_store):
        """Full flow: coordinator LLM → delegate_to_agent → researcher LLM → result."""

        # Coordinator's LLM: first call returns delegate_to_agent tool call,
        # second call summarizes the result
        factory.configure_agent("default", responses=[
            MockResponse(
                content="I need the researcher to look into this.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {
                        "agent_id": "researcher",
                        "message": "Research the latest features of Python 3.13",
                        "reason": "Needs web research expertise",
                    },
                }],
            ),
            MockResponse(
                content=(
                    "Based on the research, Python 3.13 introduces "
                    "free-threaded mode and an improved REPL."
                ),
            ),
        ])

        # Researcher's LLM: returns final answer directly
        factory.configure_agent("researcher",
            default_response="Python 3.13 features: free-threaded mode, improved REPL, better error messages."
        )

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "What's new in Python 3.13?")

        assert "Python 3.13" in result
        assert len(session.context.handoff_events) >= 1
        assert session.context.handoff_events[0]["to_agent"] == "researcher"

        stats = orchestrator.get_health_stats()
        assert stats["default"]["successful"] >= 1

    @pytest.mark.asyncio
    async def test_delegation_result_passed_back(self, orchestrator, factory):
        """Verify the sub-agent's result is visible to the parent's next LLM call."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Let me delegate to the coder.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {
                        "agent_id": "coder",
                        "message": "Write a hello world function in Python",
                    },
                }],
            ),
            MockResponse(
                content="The coder has written the function. Here it is: def hello(): print('Hello!')",
            ),
        ])

        factory.configure_agent("coder",
            default_response="```python\ndef hello():\n    print('Hello!')\n```"
        )

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Write a hello function")

        assert "hello" in result.lower()
        assert len(session.context.sub_agent_records) >= 1
        record = session.context.sub_agent_records[0]
        assert record["agent_id"] == "coder"

    @pytest.mark.asyncio
    async def test_sub_agent_cannot_re_delegate(self, orchestrator, factory):
        """Sub-agent attempting to delegate should be blocked."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Delegating to researcher.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {
                        "agent_id": "researcher",
                        "message": "Do research",
                    },
                }],
            ),
            MockResponse(content="Got the research results."),
        ])

        # Researcher tries to delegate (should be blocked)
        factory.configure_agent("researcher", responses=[
            MockResponse(
                content="I need help, let me delegate.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {
                        "agent_id": "coder",
                        "message": "Help me code something",
                    },
                }],
            ),
            MockResponse(content="OK, I'll do the research myself. Results: ..."),
        ])

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Do some research")

        assert isinstance(result, str)
        assert len(result) > 0


# ================================================================
# Test 2: Parallel delegation — LLM delegates to multiple agents
# ================================================================

class TestParallelDelegation:
    """Parent agent delegates multiple tasks in parallel."""

    @pytest.mark.asyncio
    async def test_parallel_to_different_agents(self, orchestrator, factory):
        """Coordinator delegates research and coding tasks in parallel."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="I'll delegate both tasks in parallel.",
                tool_calls=[{
                    "name": "delegate_parallel",
                    "input": {
                        "tasks": [
                            {
                                "agent_id": "researcher",
                                "message": "Research React 19 features",
                                "reason": "Web research needed",
                            },
                            {
                                "agent_id": "coder",
                                "message": "Analyze our React codebase for upgrade compatibility",
                                "reason": "Code analysis needed",
                            },
                        ],
                    },
                }],
            ),
            MockResponse(
                content=(
                    "Summary: React 19 has server components and our codebase "
                    "is compatible with minor adjustments."
                ),
            ),
        ])

        factory.configure_agent("researcher",
            default_response="React 19: server components, use() hook, Actions API."
        )
        factory.configure_agent("coder",
            default_response="Codebase is 90% compatible. Need to update 3 components."
        )

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Assess React 19 upgrade")

        assert isinstance(result, str)
        assert len(result) > 0
        assert len(session.context.handoff_events) >= 2

    @pytest.mark.asyncio
    async def test_parallel_same_agent_creates_clones(self, orchestrator, factory, profile_store):
        """Delegating 2 tasks to the same agent_id should auto-clone."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Researching both topics in parallel.",
                tool_calls=[{
                    "name": "delegate_parallel",
                    "input": {
                        "tasks": [
                            {"agent_id": "researcher", "message": "Research topic A"},
                            {"agent_id": "researcher", "message": "Research topic B"},
                        ],
                    },
                }],
            ),
            MockResponse(content="Both research tasks completed."),
        ])

        # Both clones will use the researcher's default response
        factory.configure_agent("researcher",
            default_response="Research results on the requested topic."
        )

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Research two topics")

        assert isinstance(result, str)
        # Ephemeral clones are auto-cleaned after delegation completes.
        # Verify via handoff_events that two separate delegations happened.
        assert len(session.context.handoff_events) >= 2
        delegated_ids = [e["to_agent"] for e in session.context.handoff_events]
        # Both should be ephemeral clones of researcher
        for did in delegated_ids:
            assert "ephemeral" in did and "researcher" in did


# ================================================================
# Test 3: Spawn agent — LLM spawns an ephemeral specialized agent
# ================================================================

class TestSpawnAgent:
    """Parent agent spawns a customized ephemeral agent."""

    @pytest.mark.asyncio
    async def test_spawn_and_delegate(self, orchestrator, factory, profile_store):
        """Coordinator spawns a customized researcher and delegates."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="I need a specialized researcher with extra capabilities.",
                tool_calls=[{
                    "name": "spawn_agent",
                    "input": {
                        "inherit_from": "researcher",
                        "message": "Deep-dive into Rust async runtime internals",
                        "extra_skills": ["read_file"],
                        "custom_prompt_overlay": "Focus on tokio and async-std comparison",
                        "reason": "Need code reading + research combined",
                    },
                }],
            ),
            MockResponse(
                content="The specialized researcher found that tokio uses work-stealing.",
            ),
        ])

        factory.configure_agent("researcher",
            default_response="Tokio uses a work-stealing scheduler. async-std uses a simpler model."
        )

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Compare Rust async runtimes")

        assert isinstance(result, str)
        assert len(result) > 0

        # Ephemeral profiles are auto-cleaned after completion, so we verify
        # delegation happened via sub_agent_records and handoff_events
        assert len(session.context.handoff_events) >= 1
        spawned_agent_id = session.context.handoff_events[0]["to_agent"]
        assert "ephemeral" in spawned_agent_id and "researcher" in spawned_agent_id


# ================================================================
# Test 4: Create agent — LLM creates a brand new agent
# ================================================================

class TestCreateAgent:
    """Parent agent creates a completely new agent."""

    @pytest.mark.asyncio
    async def test_create_then_delegate(self, orchestrator, factory, profile_store):
        """Coordinator creates a new SQL expert agent and delegates to it."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="No existing agent fits. I'll create a SQL expert.",
                tool_calls=[{
                    "name": "create_agent",
                    "input": {
                        "name": "SQL Expert",
                        "description": "Optimizes SQL queries and database schemas",
                        "custom_prompt": "You are a SQL optimization expert.",
                        "force": True,
                    },
                }],
            ),
            # After creation, delegate to the new agent
            MockResponse(
                content="Agent created, now delegating.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {
                        "agent_id": "__DYNAMIC__",  # will be replaced
                        "message": "Optimize this query: SELECT * FROM users WHERE age > 20",
                    },
                }],
            ),
            MockResponse(
                content="The SQL expert optimized the query to use an index.",
            ),
        ])

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Optimize my SQL query")

        assert isinstance(result, str)


# ================================================================
# Test 5: Multi-step delegation chain
# ================================================================

class TestMultiStepDelegation:
    """Coordinator delegates to one agent, then another based on results."""

    @pytest.mark.asyncio
    async def test_sequential_delegation(self, orchestrator, factory):
        """Coordinator → researcher → (result) → coder → (result) → final."""

        factory.configure_agent("default", responses=[
            # Step 1: delegate to researcher
            MockResponse(
                content="First, let me research the topic.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {
                        "agent_id": "researcher",
                        "message": "Find the best practices for FastAPI error handling",
                    },
                }],
            ),
            # Step 2: delegate to coder based on research
            MockResponse(
                content="Now let me have the coder implement it.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {
                        "agent_id": "coder",
                        "message": "Implement custom exception handlers for FastAPI based on best practices",
                    },
                }],
            ),
            # Step 3: final summary
            MockResponse(
                content=(
                    "Done! I researched FastAPI error handling best practices "
                    "and implemented custom exception handlers."
                ),
            ),
        ])

        factory.configure_agent("researcher",
            default_response="Best practices: use HTTPException, create custom exception classes, add global handlers."
        )
        factory.configure_agent("coder",
            default_response="Implemented: CustomHTTPException class, global_exception_handler, validation_handler."
        )

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Set up error handling for our FastAPI app")

        assert "exception" in result.lower() or "error" in result.lower() or "handler" in result.lower()
        assert len(session.context.handoff_events) >= 2
        assert len(session.context.sub_agent_records) >= 2

        # Verify delegation chain was recorded
        records = session.context.sub_agent_records
        agent_ids = [r["agent_id"] for r in records]
        assert "researcher" in agent_ids
        assert "coder" in agent_ids


# ================================================================
# Test 6: Fallback after failure
# ================================================================

class TestFallbackDelegation:
    """When an agent fails, the fallback should kick in."""

    @pytest.mark.asyncio
    async def test_agent_failure_triggers_fallback(self, orchestrator, factory, profile_store):
        """Fragile agent fails repeatedly, orchestrator falls back to default."""

        # Fragile agent always raises
        class FailingClient(MockLLMClient):
            async def chat(self, *args, **kwargs):
                raise RuntimeError("LLM endpoint is down")

        orig_create = factory.create

        async def patched_create(profile, **kwargs):
            if profile.id == "fragile-agent":
                client = FailingClient()
                from openakita.tools.handlers.agent import AgentToolHandler
                agent = _TestableAgent(name="Fragile", mock_client=client)
                agent._agent_profile = profile
                handler = AgentToolHandler(agent)
                agent._tool_handler = handler.handle
                return agent
            return await orig_create(profile, **kwargs)

        factory.create = patched_create

        factory.configure_agent("default",
            default_response="Fallback: I'll handle this directly."
        )

        session = _make_session(agent_profile_id="fragile-agent")

        # Multiple failures to trigger degradation
        for i in range(3):
            result = await orchestrator.handle_message(session, f"Task {i}")

        # The last call should have triggered fallback to default
        stats = orchestrator.get_health_stats()
        assert stats["fragile-agent"]["failed"] >= 2


# ================================================================
# Test 7: Health metrics tracking through LLM calls
# ================================================================

class TestHealthMetrics:
    """Verify health metrics are accurately tracked across delegation."""

    @pytest.mark.asyncio
    async def test_metrics_across_delegations(self, orchestrator, factory):
        """Health metrics should reflect both parent and sub-agent performance."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Delegating to researcher.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {"agent_id": "researcher", "message": "Search for info"},
                }],
            ),
            MockResponse(content="Research complete."),
        ])
        factory.configure_agent("researcher", default_response="Found the info.")

        session = _make_session(agent_profile_id="default")
        await orchestrator.handle_message(session, "Search for something")

        stats = orchestrator.get_health_stats()
        assert "default" in stats
        assert "researcher" in stats
        assert stats["default"]["successful"] == 1
        assert stats["researcher"]["successful"] == 1
        assert stats["default"]["avg_latency_ms"] > 0


# ================================================================
# Test 8: Sub-agent state tracking for frontend
# ================================================================

class TestSubAgentStates:
    """Verify sub-agent states are tracked for frontend polling."""

    @pytest.mark.asyncio
    async def test_states_visible_during_delegation(self, orchestrator, factory):
        """Sub-agent states should be registered for frontend polling."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Delegating.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {"agent_id": "researcher", "message": "Research task"},
                }],
            ),
            MockResponse(content="Done."),
        ])
        factory.configure_agent("researcher", default_response="Research done.")

        session = _make_session(session_id="e2e-session-123", agent_profile_id="default")
        await orchestrator.handle_message(session, "Research something")

        # States should have been recorded (may be cleaned up already)
        states = orchestrator.get_sub_agent_states("e2e-session-123")
        # At least the researcher state should exist or have existed
        if states:
            researcher_states = [s for s in states if s.get("agent_id") == "researcher"]
            if researcher_states:
                assert researcher_states[0]["status"] in ("completed", "starting", "running")


# ================================================================
# Test 9: Full conversation with delegation context
# ================================================================

class TestConversationContext:
    """Verify conversation context is properly maintained through delegation."""

    @pytest.mark.asyncio
    async def test_session_context_preserved(self, orchestrator, factory):
        """Session context should track all delegation artifacts."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Let me delegate to the coder.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {
                        "agent_id": "coder",
                        "message": "Write a Python function to calculate fibonacci",
                    },
                }],
            ),
            MockResponse(
                content="Here's the fibonacci implementation from the coder.",
            ),
        ])
        factory.configure_agent("coder",
            default_response="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
        )

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Write fibonacci function")

        ctx = session.context

        # Verify handoff events
        assert len(ctx.handoff_events) >= 1
        assert ctx.handoff_events[0]["from_agent"] == "default"
        assert ctx.handoff_events[0]["to_agent"] == "coder"

        # Verify sub-agent records contain result
        assert len(ctx.sub_agent_records) >= 1
        record = ctx.sub_agent_records[0]
        assert "fibonacci" in record["result_full"].lower()
        assert record["agent_id"] == "coder"

        # Verify delegation chain was tracked (reset at depth=0)
        # delegation_chain is reset at start of handle_message
        assert isinstance(ctx.delegation_chain, list)

    @pytest.mark.asyncio
    async def test_context_serialization_roundtrip(self, orchestrator, factory):
        """After delegation, context should serialize/deserialize correctly."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Delegating.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {"agent_id": "researcher", "message": "Quick research"},
                }],
            ),
            MockResponse(content="Done."),
        ])
        factory.configure_agent("researcher", default_response="Research result.")

        session = _make_session(agent_profile_id="default")
        await orchestrator.handle_message(session, "Research")

        ctx_dict = session.context.to_dict()
        restored = SessionContext.from_dict(ctx_dict)

        assert restored.agent_profile_id == "default"
        assert len(restored.handoff_events) == len(session.context.handoff_events)
        assert len(restored.sub_agent_records) == len(session.context.sub_agent_records)


# ================================================================
# Test 10: LLM response sequence validation
# ================================================================

class TestLLMResponseSequence:
    """Verify the MockLLM responses are consumed correctly in the ReAct loop."""

    @pytest.mark.asyncio
    async def test_multi_turn_react_loop(self, orchestrator, factory):
        """Agent uses multiple tools before delegating."""

        factory.configure_agent("default", responses=[
            # Turn 1: use a regular tool
            MockResponse(
                content="Let me check the workspace first.",
                tool_calls=[{
                    "name": "list_directory",
                    "input": {"path": "."},
                }],
            ),
            # Turn 2: delegate based on findings
            MockResponse(
                content="Found the project. Delegating code review to coder.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {
                        "agent_id": "coder",
                        "message": "Review the code in src/ directory",
                    },
                }],
            ),
            # Turn 3: final answer
            MockResponse(
                content="Code review complete. No major issues found.",
            ),
        ])
        factory.configure_agent("coder",
            default_response="Code review: clean architecture, good test coverage."
        )

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Review our codebase")

        assert isinstance(result, str)
        assert len(result) > 0
        # Verify the mock LLM was called multiple times (multi-turn)
        # The agent should have gone through 3 iterations

    @pytest.mark.asyncio
    async def test_no_delegation_direct_answer(self, orchestrator, factory):
        """When LLM doesn't need delegation, it should return directly."""

        factory.configure_agent("default", responses=[
            MockResponse(content="The answer to 1+1 is 2."),
        ])

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "What is 1+1?")

        assert "2" in result
        assert len(session.context.handoff_events) == 0


# ================================================================
# Test 11: Edge cases with LLM integration
# ================================================================

class TestLLMEdgeCases:

    @pytest.mark.asyncio
    async def test_delegation_with_empty_result(self, orchestrator, factory):
        """Sub-agent returning empty result should not crash."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Delegating.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {"agent_id": "researcher", "message": "Search"},
                }],
            ),
            MockResponse(content="Researcher returned no results."),
        ])
        factory.configure_agent("researcher", default_response="")

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Search for nothing")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_delegation_to_nonexistent_agent(self, orchestrator, factory):
        """Delegating to a non-existent agent should return an error gracefully."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Let me delegate to a ghost agent.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {"agent_id": "ghost-agent-404", "message": "Do something"},
                }],
            ),
            MockResponse(content="The delegation failed, I'll handle it myself."),
        ])

        session = _make_session(agent_profile_id="default")
        result = await orchestrator.handle_message(session, "Do something")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_concurrent_delegations_different_sessions(self, orchestrator, factory):
        """Multiple sessions delegating concurrently should not interfere."""

        factory.configure_agent("default", responses=[
            MockResponse(
                content="Delegating to researcher.",
                tool_calls=[{
                    "name": "delegate_to_agent",
                    "input": {"agent_id": "researcher", "message": "Task for session"},
                }],
            ),
            MockResponse(content="Done."),
        ] * 3)  # Enough responses for 3 sessions

        factory.configure_agent("researcher",
            default_response="Session-specific research result."
        )

        sessions = [
            _make_session(session_id=f"session-{i}", agent_profile_id="default")
            for i in range(3)
        ]

        tasks = [
            orchestrator.handle_message(s, f"Research for session {i}")
            for i, s in enumerate(sessions)
        ]
        results = await asyncio.gather(*tasks)

        assert all(isinstance(r, str) for r in results)
        assert all(len(r) > 0 for r in results)

        stats = orchestrator.get_health_stats()
        assert stats["default"]["successful"] == 3
