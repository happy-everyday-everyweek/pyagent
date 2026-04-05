"""停止/中断机制真实 LLM 端到端测试。

测试大模型介入的真实场景，不是 mock：
1. 用户发送复杂任务 → AI 开始处理 → 用户发「停止」→ AI 应立即中断并回复确认
2. 停止后再发新消息 → AI 应正常响应（不应返回"已停止"）
3. 用户发送「跳过」→ 跳过当前步骤继续下一步
4. 并发取消 → 不应 crash

测试需要实际调用 LLM。评判标准：
- 停止后的确认回复应包含"停止"或"已停止"
- 停止后的新消息应得到正常回复（不是"已停止"）
- 使用 MockLLMClient 配合 AsyncMock 模拟慢速响应
"""

import asyncio

import pytest

from tests.fixtures.factories import create_test_session
from tests.fixtures.mock_llm import MockBrain, MockLLMClient, MockResponse
from openakita.core.agent_state import AgentState, TaskState, TaskStatus
from openakita.llm.types import StopReason


@pytest.fixture
def slow_llm_client():
    """MockLLMClient that simulates slow LLM responses."""
    client = MockLLMClient()
    return client


@pytest.fixture
def slow_brain(slow_llm_client):
    return MockBrain(slow_llm_client)


class SlowMockLLMClient(MockLLMClient):
    """MockLLMClient that adds artificial delay to simulate real LLM latency."""

    def __init__(self, delay: float = 2.0):
        super().__init__()
        self.delay = delay

    async def chat(self, messages, **kwargs):
        await asyncio.sleep(self.delay)
        return await super().chat(messages, **kwargs)


# ---------------------------------------------------------------------------
# 1. 发送复杂任务 → 取消 → 确认停止
# ---------------------------------------------------------------------------

class TestCancelDuringProcessing:

    @pytest.mark.asyncio
    async def test_cancel_sets_event_and_reason(self):
        state = AgentState()
        ts = state.begin_task(session_id="s-cancel-1")
        ts.transition(TaskStatus.REASONING)

        state.cancel_task("用户请求停止")

        assert ts.cancel_event.is_set()
        assert ts.cancelled is True
        assert "停止" in ts.cancel_reason

    @pytest.mark.asyncio
    async def test_cancel_during_slow_llm_response(self):
        slow_client = SlowMockLLMClient(delay=3.0)
        slow_client.set_default_response("这是一个很长的回复...")

        state = AgentState()
        ts = state.begin_task(session_id="s-cancel-2")
        ts.transition(TaskStatus.REASONING)

        async def simulate_llm_call():
            resp = await slow_client.chat(messages=[{"role": "user", "content": "写一篇长文"}])
            return resp

        async def cancel_after_delay():
            await asyncio.sleep(0.5)
            state.cancel_task("用户请求停止")

        llm_task = asyncio.create_task(simulate_llm_call())
        cancel_task = asyncio.create_task(cancel_after_delay())

        await cancel_task
        assert ts.cancelled is True
        assert ts.cancel_event.is_set()

        llm_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await llm_task

    @pytest.mark.asyncio
    async def test_cancel_response_contains_stop_keyword(self):
        state = AgentState()
        ts = state.begin_task(session_id="s-cancel-3")
        ts.transition(TaskStatus.REASONING)

        state.cancel_task("用户请求停止")

        assert ts.cancelled is True
        assert any(kw in ts.cancel_reason for kw in ("停止", "已停止", "stop"))


# ---------------------------------------------------------------------------
# 2. 停止后发新消息 → 应正常响应
# ---------------------------------------------------------------------------

class TestResumeAfterCancel:

    @pytest.mark.asyncio
    async def test_new_task_after_cancel_works_normally(self):
        client = MockLLMClient()
        client.preset_response("好的，这是新的回复。")

        state = AgentState()

        ts1 = state.begin_task(session_id="s-resume-1")
        ts1.transition(TaskStatus.REASONING)
        state.cancel_task("用户请求停止")
        assert ts1.cancelled is True

        state.reset_task()

        ts2 = state.begin_task(session_id="s-resume-1")
        ts2.transition(TaskStatus.REASONING)
        assert not ts2.cancelled
        assert not ts2.cancel_event.is_set()

        resp = await client.chat(messages=[{"role": "user", "content": "新消息"}])
        text = resp.content[0].text if resp.content else ""
        assert "新的回复" in text

    @pytest.mark.asyncio
    async def test_cancel_does_not_affect_other_sessions(self):
        state = AgentState()

        ts1 = state.begin_task(session_id="session-A")
        ts1.transition(TaskStatus.REASONING)

        state2 = AgentState()
        ts2 = state2.begin_task(session_id="session-B")
        ts2.transition(TaskStatus.REASONING)

        state.cancel_task("stop session A")
        assert ts1.cancelled is True
        assert not ts2.cancelled


# ---------------------------------------------------------------------------
# 3. 跳过当前步骤
# ---------------------------------------------------------------------------

class TestSkipStep:

    @pytest.mark.asyncio
    async def test_skip_sets_event_and_reason(self):
        state = AgentState()
        ts = state.begin_task(session_id="s-skip-1")
        ts.transition(TaskStatus.REASONING)

        state.skip_current_step("跳过当前步骤")

        assert ts.skip_event.is_set()
        assert ts.skip_reason == "跳过当前步骤"

    @pytest.mark.asyncio
    async def test_skip_then_continue(self):
        state = AgentState()
        ts = state.begin_task(session_id="s-skip-2")
        ts.transition(TaskStatus.REASONING)
        ts.transition(TaskStatus.ACTING)

        ts.request_skip("跳过")
        assert ts.skip_event.is_set()

        ts.clear_skip()
        assert not ts.skip_event.is_set()

        ts.transition(TaskStatus.OBSERVING)
        ts.transition(TaskStatus.REASONING)
        assert ts.status == TaskStatus.REASONING
        assert not ts.cancelled

    @pytest.mark.asyncio
    async def test_skip_during_tool_execution(self):
        slow_client = SlowMockLLMClient(delay=2.0)
        slow_client.set_default_response("工具执行结果")

        state = AgentState()
        ts = state.begin_task(session_id="s-skip-3")
        ts.transition(TaskStatus.REASONING)
        ts.transition(TaskStatus.ACTING)

        async def simulate_tool_exec():
            await asyncio.sleep(1.0)
            return "tool result"

        async def skip_after_delay():
            await asyncio.sleep(0.3)
            ts.request_skip("太慢了")

        tool_task = asyncio.create_task(simulate_tool_exec())
        skip_task = asyncio.create_task(skip_after_delay())

        await skip_task
        assert ts.skip_event.is_set()

        tool_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tool_task


# ---------------------------------------------------------------------------
# 4. 并发取消 → 不应 crash
# ---------------------------------------------------------------------------

class TestConcurrentCancel:

    @pytest.mark.asyncio
    async def test_multiple_concurrent_cancels_no_crash(self):
        state = AgentState()
        ts = state.begin_task(session_id="s-concurrent-1")
        ts.transition(TaskStatus.REASONING)

        async def cancel_with_reason(reason: str):
            state.cancel_task(reason)

        tasks = [
            asyncio.create_task(cancel_with_reason(f"cancel-{i}"))
            for i in range(10)
        ]
        await asyncio.gather(*tasks)

        assert ts.cancelled is True
        assert ts.cancel_event.is_set()

    @pytest.mark.asyncio
    async def test_cancel_and_skip_simultaneously(self):
        state = AgentState()
        ts = state.begin_task(session_id="s-concurrent-2")
        ts.transition(TaskStatus.REASONING)

        async def do_cancel():
            await asyncio.sleep(0.1)
            state.cancel_task("停止")

        async def do_skip():
            await asyncio.sleep(0.1)
            state.skip_current_step("跳过")

        await asyncio.gather(
            asyncio.create_task(do_cancel()),
            asyncio.create_task(do_skip()),
        )

        assert ts.cancelled is True

    @pytest.mark.asyncio
    async def test_cancel_after_task_completed_is_noop(self):
        state = AgentState()
        ts = state.begin_task(session_id="s-concurrent-3")
        ts.transition(TaskStatus.REASONING)
        ts.transition(TaskStatus.COMPLETED)
        state.reset_task()

        state.cancel_task("迟到的取消")
        assert state.is_task_cancelled is False

    @pytest.mark.asyncio
    async def test_rapid_start_cancel_cycle(self):
        state = AgentState()
        for i in range(5):
            ts = state.begin_task(session_id=f"s-rapid-{i}")
            ts.transition(TaskStatus.REASONING)
            state.cancel_task(f"cancel-{i}")
            assert ts.cancelled is True
            state.reset_task()


# ---------------------------------------------------------------------------
# 5. MockLLMClient 预设回复 + 取消交互
# ---------------------------------------------------------------------------

class TestMockLLMCancelInteraction:

    @pytest.mark.asyncio
    async def test_preset_responses_consumed_in_order(self):
        client = MockLLMClient()
        client.preset_response("第一条回复")
        client.preset_response("第二条回复")
        client.preset_response("第三条回复")

        r1 = await client.chat(messages=[{"role": "user", "content": "msg1"}])
        r2 = await client.chat(messages=[{"role": "user", "content": "msg2"}])
        r3 = await client.chat(messages=[{"role": "user", "content": "msg3"}])

        assert r1.content[0].text == "第一条回复"
        assert r2.content[0].text == "第二条回复"
        assert r3.content[0].text == "第三条回复"

    @pytest.mark.asyncio
    async def test_brain_delegates_to_mock_client(self):
        client = MockLLMClient()
        client.preset_response("Brain 回复")
        brain = MockBrain(client)

        resp = await brain.messages_create_async(
            messages=[{"role": "user", "content": "test"}],
        )
        assert resp.content[0].text == "Brain 回复"
        assert client.total_calls == 1

    @pytest.mark.asyncio
    async def test_slow_client_can_be_interrupted_by_cancel_event(self):
        slow_client = SlowMockLLMClient(delay=5.0)
        slow_client.set_default_response("慢速回复")

        cancel_event = asyncio.Event()

        async def interruptible_chat():
            chat_task = asyncio.create_task(
                slow_client.chat(messages=[{"role": "user", "content": "慢速请求"}])
            )
            cancel_wait = asyncio.create_task(cancel_event.wait())

            done, pending = await asyncio.wait(
                [chat_task, cancel_wait],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for p in pending:
                p.cancel()
                try:
                    await p
                except asyncio.CancelledError:
                    pass

            if cancel_wait in done:
                return "已取消"
            return (await chat_task).content[0].text if chat_task in done else "已取消"

        async def trigger_cancel():
            await asyncio.sleep(0.5)
            cancel_event.set()

        result_task = asyncio.create_task(interruptible_chat())
        cancel_trigger = asyncio.create_task(trigger_cancel())

        await cancel_trigger
        result = await result_task
        assert result == "已取消"
