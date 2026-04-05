"""
L4 E2E Tests: Interrupt control full pipeline.

Tests cancel, skip, and insert-message flows via AgentState.
"""

import asyncio

import pytest

from openakita.core.agent_state import AgentState, TaskState, TaskStatus


class TestCancelFlow:
    def test_cancel_sets_event(self):
        """Cancel sets the cancel_event so the loop can check it."""
        state = AgentState()
        ts = state.begin_task(session_id="s1")
        ts.transition(TaskStatus.REASONING)

        assert not ts.cancel_event.is_set()
        state.cancel_task("user pressed stop")

        assert ts.cancel_event.is_set()
        assert ts.cancelled is True
        assert ts.cancel_reason == "user pressed stop"

    def test_cancel_marks_task_cancelled(self):
        state = AgentState()
        ts = state.begin_task(session_id="s1")
        ts.transition(TaskStatus.REASONING)
        state.cancel_task("stop")

        assert state.is_task_cancelled is True
        assert state.task_cancel_reason == "stop"

    def test_cancel_after_complete_is_noop(self):
        state = AgentState()
        ts = state.begin_task(session_id="s1")
        ts.transition(TaskStatus.REASONING)
        ts.transition(TaskStatus.COMPLETED)
        state.reset_task()

        state.cancel_task("late cancel")
        assert state.is_task_cancelled is False


class TestSkipFlow:
    def test_skip_sets_event(self):
        state = AgentState()
        ts = state.begin_task(session_id="s1")
        ts.transition(TaskStatus.REASONING)

        state.skip_current_step("skip this tool")
        assert ts.skip_event.is_set()
        assert ts.skip_reason == "skip this tool"

    def test_clear_skip_resets(self):
        state = AgentState()
        ts = state.begin_task(session_id="s1")
        ts.transition(TaskStatus.REASONING)
        ts.transition(TaskStatus.ACTING)

        ts.request_skip("skip")
        ts.clear_skip()
        assert not ts.skip_event.is_set()
        assert ts.skip_reason == ""

    def test_multiple_skips(self):
        state = AgentState()
        ts = state.begin_task(session_id="s1")
        ts.transition(TaskStatus.REASONING)

        for i in range(3):
            ts.request_skip(f"skip {i}")
            assert ts.skip_event.is_set()
            ts.clear_skip()
            assert not ts.skip_event.is_set()


class TestInsertMessageFlow:
    async def test_insert_message_during_task(self):
        state = AgentState()
        ts = state.begin_task(session_id="s1")
        ts.transition(TaskStatus.REASONING)
        ts.transition(TaskStatus.ACTING)

        await state.insert_user_message("Please also check X")
        inserts = await ts.drain_user_inserts()
        assert inserts == ["Please also check X"]

    async def test_multiple_inserts(self):
        state = AgentState()
        ts = state.begin_task(session_id="s1")
        ts.transition(TaskStatus.REASONING)

        await state.insert_user_message("msg1")
        await state.insert_user_message("msg2")
        await state.insert_user_message("msg3")

        inserts = await ts.drain_user_inserts()
        assert len(inserts) == 3
        assert inserts == ["msg1", "msg2", "msg3"]

    async def test_drain_clears_queue(self):
        state = AgentState()
        ts = state.begin_task(session_id="s1")
        ts.transition(TaskStatus.REASONING)

        await ts.add_user_insert("hello")
        batch1 = await ts.drain_user_inserts()
        batch2 = await ts.drain_user_inserts()
        assert len(batch1) == 1
        assert len(batch2) == 0

    async def test_process_post_tool_signals(self):
        """post_tool_signals should inject insert messages into working_messages."""
        ts = TaskState(task_id="t1")
        ts.transition(TaskStatus.REASONING)
        ts.transition(TaskStatus.ACTING)
        await ts.add_user_insert("New info from user")

        working = [
            {"role": "user", "content": "original"},
            {"role": "assistant", "content": "response"},
        ]
        await ts.process_post_tool_signals(working)

        user_contents = [m["content"] for m in working if m["role"] == "user"]
        assert any("New info from user" in str(c) for c in user_contents)


class TestTaskStateTransitions:
    def test_valid_transition_chain(self):
        """IDLE → REASONING → ACTING → OBSERVING → REASONING → COMPLETED"""
        ts = TaskState(task_id="t1")
        ts.transition(TaskStatus.REASONING)
        ts.transition(TaskStatus.ACTING)
        ts.transition(TaskStatus.OBSERVING)
        ts.transition(TaskStatus.REASONING)
        ts.transition(TaskStatus.COMPLETED)
        assert ts.is_terminal is True

    def test_invalid_transition_raises(self):
        ts = TaskState(task_id="t1")
        with pytest.raises(ValueError, match="非法状态转换"):
            ts.transition(TaskStatus.COMPLETED)

    def test_cancel_from_any_active_state(self):
        for chain in [
            [TaskStatus.REASONING],
            [TaskStatus.REASONING, TaskStatus.ACTING],
            [TaskStatus.REASONING, TaskStatus.ACTING, TaskStatus.OBSERVING],
        ]:
            ts = TaskState(task_id="t1")
            for status in chain:
                ts.transition(status)
            ts.cancel("user stop")
            assert ts.cancelled is True

    def test_model_switch_reset(self):
        ts = TaskState(task_id="t1")
        ts.transition(TaskStatus.REASONING)
        ts.no_tool_call_count = 5
        ts.verify_incomplete_count = 3
        ts.reset_for_model_switch()
        assert ts.no_tool_call_count == 0
        assert ts.verify_incomplete_count == 0
