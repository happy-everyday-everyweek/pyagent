"""
PyAgent 执行模块测试

测试任务执行、上下文管理和结果返回机制。
"""

import pytest
from src.execution.task import Task, TaskStatus, TaskResult, TaskState, WaitingType
from src.execution.task_context import TaskContext
from src.execution.executor_agent import ExecutorAgent


class TestTask:
    """Task类测试"""

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(prompt="测试任务")
        assert task.prompt == "测试任务"
        assert task.status == TaskStatus.PENDING
        assert task.id is not None
        assert task.context == {}

    def test_task_with_context(self):
        """测试带上下文的任务"""
        context = {"key": "value", "count": 42}
        task = Task(prompt="测试任务", context=context)
        assert task.context == context

    def test_task_status_transitions(self):
        """测试任务状态转换"""
        task = Task(prompt="测试任务")
        
        assert task.is_pending()
        
        task.mark_running()
        assert task.is_running()
        
        task.mark_completed(result="完成")
        assert task.is_completed()
        assert task.result == "完成"

    def test_task_failure(self):
        """测试任务失败"""
        task = Task(prompt="测试任务")
        task.mark_running()
        task.mark_failed(error="执行错误")
        
        assert task.is_failed()
        assert task.error == "执行错误"

    def test_task_to_dict(self):
        """测试任务序列化"""
        task = Task(
            prompt="测试任务",
            context={"key": "value"},
            priority=1
        )
        data = task.to_dict()
        
        assert data["prompt"] == "测试任务"
        assert data["context"] == {"key": "value"}
        assert data["priority"] == 1
        assert data["status"] == "pending"

    def test_task_from_dict(self):
        """测试任务反序列化"""
        data = {
            "id": "test-id",
            "prompt": "测试任务",
            "context": {"key": "value"},
            "status": "completed",
            "result": "完成"
        }
        task = Task.from_dict(data)
        
        assert task.id == "test-id"
        assert task.prompt == "测试任务"
        assert task.status == TaskStatus.COMPLETED

    def test_task_state_creation(self):
        """测试任务创建时默认状态为ACTIVE"""
        task = Task(prompt="测试任务")
        assert task.state == TaskState.ACTIVE
        assert task.is_active()

    def test_task_pause_resume(self):
        """测试暂停和恢复功能"""
        task = Task(prompt="测试任务")
        
        task.pause()
        assert task.is_paused()
        assert task.state == TaskState.PAUSED
        
        task.resume()
        assert task.is_active()
        assert task.state == TaskState.ACTIVE

    def test_task_error_state(self):
        """测试异常状态（多次重试后）"""
        task = Task(prompt="测试任务", max_retries=3)
        
        for i in range(3):
            task.mark_failed(error=f"错误{i+1}")
        
        assert task.retry_count == 3
        assert task.is_error()
        assert task.state == TaskState.ERROR

    def test_task_waiting_state(self):
        """测试等待用户操作状态"""
        task = Task(prompt="测试任务")
        
        task.wait_for_user(WaitingType.CONFIRM, "请确认是否继续")
        assert task.is_waiting()
        assert task.state == TaskState.WAITING
        assert task.waiting_type == WaitingType.CONFIRM
        assert task.waiting_message == "请确认是否继续"
        
        task.user_responded()
        assert task.is_active()
        assert task.waiting_type is None

    def test_task_waiting_types(self):
        """测试WaitingType枚举"""
        task = Task(prompt="测试任务")
        
        task.wait_for_user(WaitingType.CONFIRM, "确认")
        assert task.waiting_type == WaitingType.CONFIRM
        
        task.user_responded()
        task.wait_for_user(WaitingType.ASSIST, "协助")
        assert task.waiting_type == WaitingType.ASSIST

    def test_task_display_status(self):
        """测试get_display_status()方法返回正确的显示文本"""
        task = Task(prompt="测试任务")
        
        assert task.get_display_status() == "执行｜待处理"
        
        task.mark_running()
        assert task.get_display_status() == "执行｜规划中"
        
        task.set_progress(45)
        assert task.get_display_status() == "执行｜45%"
        
        task.mark_completed()
        assert task.get_display_status() == "执行｜完成"
        
        task2 = Task(prompt="测试任务2")
        task2.mark_running()
        task2.mark_failed("错误")
        assert task2.get_display_status() == "执行｜失败"
        
        task3 = Task(prompt="测试任务3")
        task3.pause()
        assert task3.get_display_status() == "执行｜已暂停"
        
        task4 = Task(prompt="测试任务4")
        task4.wait_for_user(WaitingType.CONFIRM, "确认")
        assert task4.get_display_status() == "执行｜须您确认"
        
        task5 = Task(prompt="测试任务5")
        task5.wait_for_user(WaitingType.ASSIST, "协助")
        assert task5.get_display_status() == "执行｜须您协助"

    def test_task_progress(self):
        """测试进度设置功能"""
        task = Task(prompt="测试任务")
        
        task.set_progress(50)
        assert task.progress == 50.0
        
        task.set_progress(150)
        assert task.progress == 100.0
        
        task.set_progress(-10)
        assert task.progress == 0.0

    def test_task_state_change_callback(self):
        """测试状态变更回调"""
        task = Task(prompt="测试任务")
        callback_results = []
        
        def on_state_change(t, old_state, new_state):
            callback_results.append((old_state, new_state))
        
        task.on_state_change(on_state_change)
        
        task.pause()
        assert len(callback_results) == 1
        assert callback_results[0] == (TaskState.ACTIVE, TaskState.PAUSED)
        
        task.resume()
        assert len(callback_results) == 2
        assert callback_results[1] == (TaskState.PAUSED, TaskState.ACTIVE)


class TestTaskContext:
    """TaskContext类测试"""

    def test_context_creation(self):
        """测试上下文创建"""
        ctx = TaskContext(task_id="test-task")
        assert ctx.task_id == "test-task"
        assert ctx.data == {}

    def test_context_get_set(self):
        """测试上下文读写"""
        ctx = TaskContext(task_id="test-task")
        
        ctx.set("key", "value")
        assert ctx.get("key") == "value"
        assert ctx.get("missing", "default") == "default"

    def test_context_update(self):
        """测试上下文批量更新"""
        ctx = TaskContext(task_id="test-task")
        ctx.update({"a": 1, "b": 2})
        
        assert ctx.get("a") == 1
        assert ctx.get("b") == 2

    def test_context_delete(self):
        """测试上下文删除"""
        ctx = TaskContext(task_id="test-task")
        ctx.set("key", "value")
        
        assert ctx.delete("key") is True
        assert ctx.get("key") is None
        assert ctx.delete("missing") is False

    def test_context_has(self):
        """测试上下文存在检查"""
        ctx = TaskContext(task_id="test-task")
        ctx.set("key", "value")
        
        assert ctx.has("key") is True
        assert ctx.has("missing") is False

    def test_context_parent(self):
        """测试父子上下文"""
        parent = TaskContext(task_id="parent", data={"parent_key": "parent_value"})
        child = parent.create_child("child")
        
        child.set("child_key", "child_value")
        
        assert child.get("child_key") == "child_value"
        assert child.get("parent_key") == "parent_value"
        assert parent.get("child_key") is None

    def test_context_to_dict(self):
        """测试上下文序列化"""
        ctx = TaskContext(
            task_id="test-task",
            data={"key": "value"},
            metadata={"meta": "data"}
        )
        data = ctx.to_dict()
        
        assert data["task_id"] == "test-task"
        assert data["data"] == {"key": "value"}
        assert data["metadata"] == {"meta": "data"}

    def test_context_dict_access(self):
        """测试字典式访问"""
        ctx = TaskContext(task_id="test-task")
        
        ctx["key"] = "value"
        assert ctx["key"] == "value"
        assert "key" in ctx


class TestTaskResult:
    """TaskResult类测试"""

    def test_result_creation_success(self):
        """测试成功结果创建"""
        result = TaskResult(
            success=True,
            data="执行结果",
            duration=1.5
        )
        assert result.success is True
        assert result.data == "执行结果"
        assert result.duration == 1.5

    def test_result_creation_failure(self):
        """测试失败结果创建"""
        result = TaskResult(
            success=False,
            error="执行错误"
        )
        assert result.success is False
        assert result.error == "执行错误"

    def test_result_to_dict(self):
        """测试结果序列化"""
        result = TaskResult(
            success=True,
            data="结果",
            steps=[{"type": "think", "content": "思考"}]
        )
        data = result.to_dict()
        
        assert data["success"] is True
        assert data["data"] == "结果"
        assert len(data["steps"]) == 1

    def test_result_from_dict(self):
        """测试结果反序列化"""
        data = {
            "success": False,
            "error": "错误",
            "duration": 2.0
        }
        result = TaskResult.from_dict(data)
        
        assert result.success is False
        assert result.error == "错误"
        assert result.duration == 2.0


class TestExecutorAgent:
    """ExecutorAgent类测试"""

    def test_agent_creation(self):
        """测试Agent创建"""
        agent = ExecutorAgent()
        assert agent.llm_client is None
        assert agent.tool_registry is None
        assert agent._current_task is None
        assert agent._context is None

    def test_agent_with_config(self):
        """测试带配置的Agent"""
        config = {
            "max_concurrent_tasks": 10,
            "default_timeout": 600
        }
        agent = ExecutorAgent(config=config)
        
        assert agent.max_concurrent_tasks == 10
        assert agent.default_timeout == 600

    def test_agent_context_management(self):
        """测试上下文管理"""
        agent = ExecutorAgent()
        
        assert agent.get_context() is None
        
        task = Task(prompt="测试", context={"key": "value"})
        agent._current_task = task
        agent._context = TaskContext(task_id=task.id, data=task.context.copy())
        
        assert agent.get_context() is not None
        assert agent.get_context().get("key") == "value"
        
        agent.update_context("new_key", "new_value")
        assert agent.get_context().get("new_key") == "new_value"

    def test_agent_current_task(self):
        """测试当前任务管理"""
        agent = ExecutorAgent()
        
        assert agent.get_current_task() is None
        
        task = Task(prompt="测试任务")
        agent._current_task = task
        
        assert agent.get_current_task() == task

    def test_agent_sub_agent_management(self):
        """测试子Agent管理"""
        agent = ExecutorAgent()
        
        class MockSubAgent:
            pass
        
        mock_agent = MockSubAgent()
        agent.register_sub_agent("mock", mock_agent)
        
        assert agent.get_sub_agent("mock") == mock_agent
        
        agent.unregister_sub_agent("mock")
        assert agent.get_sub_agent("mock") is None

    @pytest.mark.asyncio
    async def test_agent_execute_task(self):
        """测试任务执行"""
        agent = ExecutorAgent()
        task = Task(prompt="测试任务", context={"key": "value"})
        
        result = await agent.execute(task)
        
        assert isinstance(result, TaskResult)
        assert agent.get_current_task() == task
        assert agent.get_context() is not None
        assert agent.get_context().task_id == task.id

    @pytest.mark.asyncio
    async def test_agent_execute_task_status_update(self):
        """测试任务执行状态更新"""
        agent = ExecutorAgent()
        task = Task(prompt="测试任务")
        
        assert task.status == TaskStatus.PENDING
        
        await agent.execute(task)
        
        assert task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]

    @pytest.mark.asyncio
    async def test_agent_delegate_to_sub_agent(self):
        """测试委派给子Agent"""
        agent = ExecutorAgent()
        
        class MockSubAgent:
            async def execute(self, task, context):
                return "子Agent执行结果"
        
        mock_agent = MockSubAgent()
        agent.register_sub_agent("mock", mock_agent)
        
        result = await agent.delegate_to_sub_agent("mock", "测试任务")
        
        assert result["success"] is True
        assert result["result"] == "子Agent执行结果"

    @pytest.mark.asyncio
    async def test_agent_delegate_to_nonexistent_sub_agent(self):
        """测试委派给不存在的子Agent"""
        agent = ExecutorAgent()
        
        result = await agent.delegate_to_sub_agent("nonexistent", "测试任务")
        
        assert result["success"] is False
        assert "不存在" in result["error"]
