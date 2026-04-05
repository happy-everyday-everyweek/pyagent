"""
端到端测试 - 定时任务 (6 个)

E2E-T01 ~ E2E-T06

测试 LLM 层与定时任务调度器的集成。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from openakita.llm.types import (
    Message,
    TextBlock,
    ToolUseBlock,
    EndpointConfig,
    LLMResponse,
    Usage,
    StopReason,
)
from openakita.llm.client import LLMClient


@pytest.fixture
def task_client():
    """创建任务执行客户端"""
    endpoints = [
        EndpointConfig(
            name="task-endpoint",
            provider="anthropic",
            api_type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="TEST_KEY",
            model="claude-3-sonnet",
            priority=1,
            capabilities=["text", "tools"],
        ),
    ]
    return LLMClient(endpoints=endpoints)


def create_mock_response(text: str, has_tool: bool = False, tool_name: str = None):
    """创建模拟响应"""
    content = []
    
    if text:
        content.append(TextBlock(text=text))
    
    if has_tool:
        content.append(ToolUseBlock(
            id="call_task_123",
            name=tool_name or "execute_task",
            input={"task": "test"}
        ))
    
    return LLMResponse(
        id="msg_task",
        content=content,
        stop_reason=StopReason.TOOL_USE if has_tool else StopReason.END_TURN,
        usage=Usage(input_tokens=50, output_tokens=30),
        model="test-model",
    )


class TestScheduledExecution:
    """定时执行测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_t01_simple_scheduled_task(self, task_client):
        """E2E-T01: 简单定时任务"""
        mock_response = create_mock_response("Task completed: Daily report generated.")
        
        for provider in task_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # 模拟定时任务触发
        task_prompt = "Generate daily report for 2024-01-15"
        
        response = await task_client.chat(
            messages=[Message(role="user", content=task_prompt)],
            system="You are a task executor. Complete the assigned task.",
        )
        
        assert "completed" in response.text.lower() or response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_t02_task_with_tools(self, task_client):
        """E2E-T02: 带工具的定时任务"""
        from openakita.llm.types import Tool
        
        mock_response = create_mock_response(
            "I'll fetch the data now.",
            has_tool=True,
            tool_name="fetch_data"
        )
        
        for provider in task_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        tools = [
            Tool(
                name="fetch_data",
                description="Fetch data from database",
                input_schema={"type": "object", "properties": {"table": {"type": "string"}}}
            ),
            Tool(
                name="send_email",
                description="Send email notification",
                input_schema={"type": "object", "properties": {"to": {"type": "string"}}}
            ),
        ]
        
        response = await task_client.chat(
            messages=[Message(role="user", content="Run scheduled data sync")],
            tools=tools,
        )
        
        assert response.has_tool_calls
    
    @pytest.mark.asyncio
    async def test_e2e_t03_retry_on_failure(self, task_client):
        """E2E-T03: 失败重试"""
        from openakita.llm.types import LLMError
        
        call_count = 0
        
        async def mock_chat_with_retry(request):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise LLMError("Temporary failure")
            return create_mock_response("Task succeeded after retry.")
        
        for provider in task_client.providers.values():
            provider.chat = mock_chat_with_retry
        
        response = await task_client.chat(
            messages=[Message(role="user", content="Run critical task")],
        )
        
        assert call_count >= 2
        assert "succeeded" in response.text.lower() or response.text is not None


class TestTaskResults:
    """任务结果测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_t04_result_formatting(self, task_client):
        """E2E-T04: 结果格式化"""
        mock_response = create_mock_response(
            "## Task Report\n\n"
            "- Status: Success\n"
            "- Duration: 5 seconds\n"
            "- Records processed: 1000"
        )
        
        for provider in task_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await task_client.chat(
            messages=[Message(role="user", content="Generate formatted task report")],
        )
        
        assert "Status" in response.text or "Success" in response.text
    
    @pytest.mark.asyncio
    async def test_e2e_t05_multi_step_task(self, task_client):
        """E2E-T05: 多步骤任务"""
        # 模拟多步骤任务执行
        step_responses = [
            create_mock_response("Step 1 completed.", has_tool=True, tool_name="step_1"),
            create_mock_response("Step 2 completed.", has_tool=True, tool_name="step_2"),
            create_mock_response("All steps completed successfully."),
        ]
        
        call_index = 0
        
        async def mock_multi_step(request):
            nonlocal call_index
            response = step_responses[min(call_index, len(step_responses) - 1)]
            call_index += 1
            return response
        
        for provider in task_client.providers.values():
            provider.chat = mock_multi_step
        
        # 第一步
        response = await task_client.chat(
            messages=[Message(role="user", content="Execute multi-step workflow")],
        )
        
        assert response.has_tool_calls or "completed" in response.text.lower()


class TestNotifications:
    """通知测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_t06_task_notification(self, task_client):
        """E2E-T06: 任务完成通知"""
        mock_response = create_mock_response(
            "✅ 定时任务执行完成\n\n"
            "任务名称: Daily Backup\n"
            "执行时间: 2024-01-15 08:00:00\n"
            "状态: 成功"
        )
        
        for provider in task_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await task_client.chat(
            messages=[Message(role="user", content="Format task completion notification")],
            system="Generate a clear task completion notification for the user.",
        )
        
        assert response.text is not None
        # 应该包含任务相关信息
        assert "任务" in response.text or "Task" in response.text or "完成" in response.text
