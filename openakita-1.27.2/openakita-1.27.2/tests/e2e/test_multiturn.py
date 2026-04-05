"""
L4 E2E Tests: Multi-turn conversation context preservation.

These tests use MockLLMClient with preset sequences to simulate multi-turn
conversations. In `RECORD=1` mode, they would use real LLM and record responses.

Run with:  pytest tests/e2e/test_multiturn.py -v
Record:    LLM_TEST_MODE=record pytest tests/e2e/test_multiturn.py -v
"""

import os

import pytest

from tests.fixtures.mock_llm import MockBrain, MockLLMClient, MockResponse


@pytest.fixture
def multi_turn_brain():
    """Brain with pre-programmed multi-turn responses."""
    client = MockLLMClient()
    return MockBrain(client), client


class TestContextMemory:
    async def test_remember_user_name(self, multi_turn_brain):
        """Agent should remember user's name across turns."""
        brain, client = multi_turn_brain
        client.preset_sequence([
            MockResponse(content="你好小明！很高兴认识你。"),
            MockResponse(content="你叫小明呀，你之前告诉我的。"),
        ])

        r1 = await brain.messages_create_async(
            messages=[{"role": "user", "content": "我叫小明"}],
        )
        assert "小明" in r1.content[0].text

        r2 = await brain.messages_create_async(
            messages=[
                {"role": "user", "content": "我叫小明"},
                {"role": "assistant", "content": r1.content[0].text},
                {"role": "user", "content": "我叫什么名字？"},
            ],
        )
        assert "小明" in r2.content[0].text

    async def test_remember_number(self, multi_turn_brain):
        """Agent should remember a number and compute with it."""
        brain, client = multi_turn_brain
        client.preset_sequence([
            MockResponse(content="好的，我记住了42。"),
            MockResponse(content="42乘以2等于84。"),
        ])

        r1 = await brain.messages_create_async(
            messages=[{"role": "user", "content": "记住这个数字：42"}],
        )

        r2 = await brain.messages_create_async(
            messages=[
                {"role": "user", "content": "记住这个数字：42"},
                {"role": "assistant", "content": r1.content[0].text},
                {"role": "user", "content": "刚才那个数字乘以2是多少？"},
            ],
        )
        assert "84" in r2.content[0].text


class TestTopicTracking:
    async def test_topic_continuation(self, multi_turn_brain):
        """Agent should maintain topic context."""
        brain, client = multi_turn_brain
        client.preset_sequence([
            MockResponse(content="机器学习是人工智能的一个分支，通过数据训练模型。"),
            MockResponse(content="深度学习是机器学习的子集，使用多层神经网络。主要区别在于模型的复杂度和特征提取方式。"),
        ])

        r1 = await brain.messages_create_async(
            messages=[{"role": "user", "content": "给我讲讲机器学习"}],
        )

        r2 = await brain.messages_create_async(
            messages=[
                {"role": "user", "content": "给我讲讲机器学习"},
                {"role": "assistant", "content": r1.content[0].text},
                {"role": "user", "content": "它和深度学习有什么区别？"},
            ],
        )
        assert len(r2.content[0].text) >= 20

    async def test_topic_switch(self, multi_turn_brain):
        """Agent should handle topic switches gracefully."""
        brain, client = multi_turn_brain
        client.preset_sequence([
            MockResponse(content="抱歉，我无法获取实时天气信息。"),
            MockResponse(content='```python\nprint("hello")\n```'),
        ])

        await brain.messages_create_async(
            messages=[{"role": "user", "content": "今天天气怎么样？"}],
        )
        r2 = await brain.messages_create_async(
            messages=[
                {"role": "user", "content": "今天天气怎么样？"},
                {"role": "assistant", "content": "抱歉，我无法获取实时天气信息。"},
                {"role": "user", "content": "那帮我写一段Python代码打印hello"},
            ],
        )
        assert "print" in r2.content[0].text


class TestToolContextContinuity:
    async def test_tool_result_referenced_later(self, multi_turn_brain):
        """Tool call results should be referenceable in subsequent turns."""
        brain, client = multi_turn_brain
        client.preset_sequence([
            MockResponse(
                content="我来搜索一下。",
                tool_calls=[{"name": "search_memory", "input": {"query": "Python"}}],
            ),
            MockResponse(content="刚才搜索到了3条关于Python的记忆。"),
        ])

        r1 = await brain.messages_create_async(
            messages=[{"role": "user", "content": "帮我搜索关于Python的记忆"}],
        )

        r2 = await brain.messages_create_async(
            messages=[
                {"role": "user", "content": "帮我搜索关于Python的记忆"},
                {"role": "assistant", "content": [
                    {"type": "text", "text": "我来搜索一下。"},
                    {"type": "tool_use", "id": "t1", "name": "search_memory", "input": {"query": "Python"}},
                ]},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": "t1", "content": "Found 3 memories about Python."},
                ]},
                {"role": "user", "content": "刚才搜索到了几条结果？"},
            ],
        )
        assert "3" in r2.content[0].text


class TestConversationLength:
    async def test_long_conversation_preserved(self, multi_turn_brain):
        """Messages should be preserved in long conversations."""
        brain, client = multi_turn_brain

        messages = []
        for i in range(10):
            client.preset_response(f"Round {i} response")
            messages.append({"role": "user", "content": f"Question {i}"})
            r = await brain.messages_create_async(messages=list(messages))
            messages.append({"role": "assistant", "content": r.content[0].text})

        assert len(messages) == 20
        assert client.total_calls == 10
        last_call = client.last_call
        assert len(last_call["messages"]) == 19  # 10 user + 9 assistant (last user is the 10th)
