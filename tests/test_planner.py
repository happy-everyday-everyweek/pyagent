"""
PyAgent 规划智能体测试

测试任务分解、智能体分配和结果聚合功能。
"""

import pytest

from src.execution.planner import (
    AgentCapability,
    DecompositionStrategy,
    ExecutionPlan,
    PlannerAgent,
    SubTask,
    SubTaskStatus,
)
from src.execution.task import Task, TaskResult


class TestDecompositionStrategy:
    """测试分解策略枚举"""

    def test_strategy_values(self):
        """测试策略枚举值"""
        assert DecompositionStrategy.PARALLEL.value == "parallel"
        assert DecompositionStrategy.SEQUENTIAL.value == "sequential"
        assert DecompositionStrategy.HYBRID.value == "hybrid"


class TestSubTask:
    """测试子任务"""

    def test_subtask_creation(self):
        """测试子任务创建"""
        subtask = SubTask(
            parent_task_id="parent-1",
            prompt="测试子任务",
            priority=5
        )
        assert subtask.parent_task_id == "parent-1"
        assert subtask.prompt == "测试子任务"
        assert subtask.priority == 5
        assert subtask.status == SubTaskStatus.PENDING
        assert subtask.id is not None

    def test_subtask_with_dependencies(self):
        """测试带依赖的子任务"""
        subtask = SubTask(
            prompt="测试子任务",
            dependencies=["subtask_0", "subtask_1"]
        )
        assert len(subtask.dependencies) == 2
        assert "subtask_0" in subtask.dependencies

    def test_subtask_to_dict(self):
        """测试子任务序列化"""
        subtask = SubTask(
            id="subtask_0",
            parent_task_id="parent-1",
            prompt="测试子任务",
            priority=5,
            dependencies=["subtask_1"]
        )
        data = subtask.to_dict()

        assert data["id"] == "subtask_0"
        assert data["parent_task_id"] == "parent-1"
        assert data["prompt"] == "测试子任务"
        assert data["priority"] == 5
        assert data["dependencies"] == ["subtask_1"]
        assert data["status"] == "pending"

    def test_subtask_from_dict(self):
        """测试子任务反序列化"""
        data = {
            "id": "subtask_0",
            "parent_task_id": "parent-1",
            "prompt": "测试子任务",
            "priority": 5,
            "dependencies": ["subtask_1"],
            "status": "completed"
        }
        subtask = SubTask.from_dict(data)

        assert subtask.id == "subtask_0"
        assert subtask.parent_task_id == "parent-1"
        assert subtask.status == SubTaskStatus.COMPLETED


class TestExecutionPlan:
    """测试执行计划"""

    def test_plan_creation(self):
        """测试计划创建"""
        plan = ExecutionPlan(
            task_id="task-1",
            strategy=DecompositionStrategy.SEQUENTIAL
        )
        assert plan.task_id == "task-1"
        assert plan.strategy == DecompositionStrategy.SEQUENTIAL
        assert len(plan.subtasks) == 0

    def test_plan_with_subtasks(self):
        """测试带子任务的计划"""
        subtasks = [
            SubTask(id="subtask_0", prompt="步骤1"),
            SubTask(id="subtask_1", prompt="步骤2", dependencies=["subtask_0"])
        ]
        plan = ExecutionPlan(
            task_id="task-1",
            subtasks=subtasks,
            strategy=DecompositionStrategy.SEQUENTIAL
        )

        assert len(plan.subtasks) == 2
        assert plan.get_subtask("subtask_0") is not None
        assert plan.get_subtask("nonexistent") is None

    def test_plan_get_ready_subtasks(self):
        """测试获取可执行的子任务"""
        subtasks = [
            SubTask(id="subtask_0", prompt="步骤1", status=SubTaskStatus.COMPLETED),
            SubTask(id="subtask_1", prompt="步骤2", dependencies=["subtask_0"]),
            SubTask(id="subtask_2", prompt="步骤3", dependencies=["subtask_1"])
        ]
        plan = ExecutionPlan(
            task_id="task-1",
            subtasks=subtasks,
            strategy=DecompositionStrategy.SEQUENTIAL
        )

        ready = plan.get_ready_subtasks()
        assert len(ready) == 1
        assert ready[0].id == "subtask_1"

    def test_plan_is_complete(self):
        """测试计划是否完成"""
        subtasks = [
            SubTask(id="subtask_0", prompt="步骤1", status=SubTaskStatus.COMPLETED),
            SubTask(id="subtask_1", prompt="步骤2", status=SubTaskStatus.COMPLETED)
        ]
        plan = ExecutionPlan(
            task_id="task-1",
            subtasks=subtasks
        )

        assert plan.is_complete() is True

        subtasks[1].status = SubTaskStatus.PENDING
        assert plan.is_complete() is False

    def test_plan_get_progress(self):
        """测试获取执行进度"""
        subtasks = [
            SubTask(id="subtask_0", prompt="步骤1", status=SubTaskStatus.COMPLETED),
            SubTask(id="subtask_1", prompt="步骤2", status=SubTaskStatus.RUNNING),
            SubTask(id="subtask_2", prompt="步骤3", status=SubTaskStatus.PENDING),
            SubTask(id="subtask_3", prompt="步骤4", status=SubTaskStatus.FAILED)
        ]
        plan = ExecutionPlan(
            task_id="task-1",
            subtasks=subtasks
        )

        progress = plan.get_progress()
        assert progress["total"] == 4
        assert progress["completed"] == 1
        assert progress["running"] == 1
        assert progress["pending"] == 1
        assert progress["failed"] == 1
        assert progress["progress_percent"] == 25.0

    def test_plan_to_dict(self):
        """测试计划序列化"""
        plan = ExecutionPlan(
            task_id="task-1",
            subtasks=[SubTask(id="subtask_0", prompt="步骤1")],
            strategy=DecompositionStrategy.PARALLEL,
            estimated_duration=10.5
        )
        data = plan.to_dict()

        assert data["task_id"] == "task-1"
        assert data["strategy"] == "parallel"
        assert data["estimated_duration"] == 10.5
        assert len(data["subtasks"]) == 1

    def test_plan_from_dict(self):
        """测试计划反序列化"""
        data = {
            "task_id": "task-1",
            "subtasks": [
                {"id": "subtask_0", "prompt": "步骤1", "status": "pending"}
            ],
            "strategy": "sequential",
            "execution_order": [["subtask_0"]],
            "estimated_duration": 5.0
        }
        plan = ExecutionPlan.from_dict(data)

        assert plan.task_id == "task-1"
        assert plan.strategy == DecompositionStrategy.SEQUENTIAL
        assert len(plan.subtasks) == 1


class TestAgentCapability:
    """测试智能体能力描述"""

    def test_capability_creation(self):
        """测试能力创建"""
        capability = AgentCapability(
            name="search_agent",
            description="搜索智能体",
            skills=["search", "query"],
            max_concurrent_tasks=5,
            priority=10
        )
        assert capability.name == "search_agent"
        assert capability.description == "搜索智能体"
        assert "search" in capability.skills
        assert capability.max_concurrent_tasks == 5
        assert capability.priority == 10

    def test_capability_to_dict(self):
        """测试能力序列化"""
        capability = AgentCapability(
            name="browser_agent",
            description="浏览器智能体",
            skills=["browse", "click"]
        )
        data = capability.to_dict()

        assert data["name"] == "browser_agent"
        assert data["description"] == "浏览器智能体"
        assert data["skills"] == ["browse", "click"]


class TestPlannerAgent:
    """测试规划智能体"""

    def test_planner_creation(self):
        """测试规划器创建"""
        planner = PlannerAgent()
        assert planner.llm_client is None
        assert planner.max_subtasks == 10
        assert planner.enable_parallel is True
        assert planner.auto_assign is True

    def test_planner_with_config(self):
        """测试带配置的规划器"""
        config = {
            "max_subtasks": 5,
            "enable_parallel": False,
            "auto_assign": False
        }
        planner = PlannerAgent(config=config)
        assert planner.max_subtasks == 5
        assert planner.enable_parallel is False
        assert planner.auto_assign is False

    def test_register_agent(self):
        """测试注册智能体"""
        planner = PlannerAgent()
        capability = AgentCapability(
            name="search_agent",
            description="搜索智能体",
            skills=["search"]
        )

        planner.register_agent(capability)
        agents = planner.get_available_agents()

        assert len(agents) == 1
        assert agents[0].name == "search_agent"

    def test_unregister_agent(self):
        """测试注销智能体"""
        planner = PlannerAgent()
        capability = AgentCapability(
            name="search_agent",
            description="搜索智能体"
        )

        planner.register_agent(capability)
        planner.unregister_agent("search_agent")

        assert len(planner.get_available_agents()) == 0

    def test_determine_strategy_sequential(self):
        """测试确定串行策略"""
        planner = PlannerAgent()

        task = Task(prompt="先读取文件，然后处理数据，最后保存结果")
        strategy = planner.determine_strategy(task)
        assert strategy == DecompositionStrategy.SEQUENTIAL

        task2 = Task(prompt="执行步骤1，之后执行步骤2")
        strategy2 = planner.determine_strategy(task2)
        assert strategy2 == DecompositionStrategy.SEQUENTIAL

    def test_determine_strategy_parallel(self):
        """测试确定并行策略"""
        planner = PlannerAgent()

        task = Task(prompt="同时搜索多个网站")
        strategy = planner.determine_strategy(task)
        assert strategy == DecompositionStrategy.PARALLEL

        task2 = Task(prompt="并行处理这些文件")
        strategy2 = planner.determine_strategy(task2)
        assert strategy2 == DecompositionStrategy.PARALLEL

    def test_determine_strategy_hybrid(self):
        """测试确定混合策略"""
        planner = PlannerAgent()

        task = Task(prompt="处理这个任务")
        strategy = planner.determine_strategy(task)
        assert strategy == DecompositionStrategy.HYBRID

    def test_determine_strategy_with_tags(self):
        """测试带标签的策略确定"""
        planner = PlannerAgent()

        task = Task(prompt="处理任务", tags=["sequential"])
        strategy = planner.determine_strategy(task)
        assert strategy == DecompositionStrategy.SEQUENTIAL

        task2 = Task(prompt="处理任务", tags=["parallel"])
        strategy2 = planner.determine_strategy(task2)
        assert strategy2 == DecompositionStrategy.PARALLEL

    @pytest.mark.asyncio
    async def test_analyze_task(self):
        """测试分析任务"""
        planner = PlannerAgent()
        task = Task(prompt="测试任务")

        plan = await planner.analyze_task(task)

        assert plan is not None
        assert plan.task_id == task.id
        assert len(plan.subtasks) > 0
        assert planner.get_plan(task.id) == plan

    @pytest.mark.asyncio
    async def test_decompose_task_simple(self):
        """测试简单任务分解"""
        planner = PlannerAgent()
        task = Task(prompt="第一步。第二步。第三步。")

        subtasks = await planner.decompose_task(task, DecompositionStrategy.SEQUENTIAL)

        assert len(subtasks) == 3
        assert subtasks[0].prompt == "第一步"
        assert subtasks[1].dependencies == ["subtask_0"]

    @pytest.mark.asyncio
    async def test_decompose_task_parallel(self):
        """测试并行任务分解"""
        planner = PlannerAgent()
        task = Task(prompt="任务A。任务B。")

        subtasks = await planner.decompose_task(task, DecompositionStrategy.PARALLEL)

        assert len(subtasks) == 2
        assert len(subtasks[0].dependencies) == 0
        assert len(subtasks[1].dependencies) == 0

    def test_assign_agents(self):
        """测试智能体分配"""
        planner = PlannerAgent()

        planner.register_agent(AgentCapability(
            name="search_agent",
            description="搜索智能体",
            skills=["search", "query"]
        ))
        planner.register_agent(AgentCapability(
            name="browser_agent",
            description="浏览器智能体",
            skills=["browse", "click"]
        ))

        subtasks = [
            SubTask(id="subtask_0", prompt="搜索相关信息"),
            SubTask(id="subtask_1", prompt="浏览网页获取数据")
        ]

        assigned = planner.assign_agents(subtasks, ["search_agent", "browser_agent"])

        assert assigned[0].assigned_agent == "search_agent"
        assert assigned[1].assigned_agent == "browser_agent"

    def test_aggregate_results_all_success(self):
        """测试聚合结果 - 全部成功"""
        planner = PlannerAgent()

        results = {
            "subtask_0": TaskResult(success=True, data="结果1", duration=1.0),
            "subtask_1": TaskResult(success=True, data="结果2", duration=2.0)
        }

        aggregated = planner.aggregate_results(results)

        assert aggregated.success is True
        assert aggregated.duration == 3.0
        assert aggregated.metadata["total_subtasks"] == 2
        assert aggregated.metadata["successful"] == 2
        assert aggregated.metadata["failed"] == 0

    def test_aggregate_results_partial_failure(self):
        """测试聚合结果 - 部分失败"""
        planner = PlannerAgent()

        results = {
            "subtask_0": TaskResult(success=True, data="结果1", duration=1.0),
            "subtask_1": TaskResult(success=False, error="执行错误", duration=2.0)
        }

        aggregated = planner.aggregate_results(results)

        assert aggregated.success is False
        assert aggregated.error == "执行错误"
        assert aggregated.metadata["successful"] == 1
        assert aggregated.metadata["failed"] == 1

    def test_aggregate_results_empty(self):
        """测试聚合结果 - 空结果"""
        planner = PlannerAgent()

        aggregated = planner.aggregate_results({})

        assert aggregated.success is False
        assert aggregated.error == "没有子任务结果"

    def test_update_subtask_status(self):
        """测试更新子任务状态"""
        planner = PlannerAgent()
        task = Task(prompt="测试任务")

        plan = ExecutionPlan(
            task_id=task.id,
            subtasks=[SubTask(id="subtask_0", prompt="步骤1")]
        )
        planner._execution_plans[task.id] = plan

        result = planner.update_subtask_status(
            task.id,
            "subtask_0",
            SubTaskStatus.COMPLETED,
            TaskResult(success=True, data="完成")
        )

        assert result is True
        assert plan.subtasks[0].status == SubTaskStatus.COMPLETED
        assert plan.subtasks[0].result.data == "完成"

    def test_update_subtask_status_nonexistent(self):
        """测试更新不存在的子任务状态"""
        planner = PlannerAgent()

        result = planner.update_subtask_status(
            "nonexistent_task",
            "subtask_0",
            SubTaskStatus.COMPLETED
        )

        assert result is False

    def test_get_next_subtasks(self):
        """测试获取下一批可执行的子任务"""
        planner = PlannerAgent()
        task = Task(prompt="测试任务")

        plan = ExecutionPlan(
            task_id=task.id,
            subtasks=[
                SubTask(id="subtask_0", prompt="步骤1", status=SubTaskStatus.COMPLETED),
                SubTask(id="subtask_1", prompt="步骤2", dependencies=["subtask_0"]),
                SubTask(id="subtask_2", prompt="步骤3", dependencies=["subtask_1"])
            ]
        )
        planner._execution_plans[task.id] = plan

        next_subtasks = planner.get_next_subtasks(task.id)

        assert len(next_subtasks) == 1
        assert next_subtasks[0].id == "subtask_1"

    def test_clear_plan(self):
        """测试清除执行计划"""
        planner = PlannerAgent()
        task = Task(prompt="测试任务")

        planner._execution_plans[task.id] = ExecutionPlan(task_id=task.id)
        planner.clear_plan(task.id)

        assert planner.get_plan(task.id) is None
