"""
测试多智能体协作管理器
"""

import asyncio
import sys
sys.path.insert(0, "d:/agent/src")

from execution.collaboration import (
    CollaborationConfig,
    CollaborationManager,
    CollaborationMode,
    ExecutionStatistics,
)
from execution.task import Task, TaskStatus


def test_config():
    """测试配置类"""
    print("测试 CollaborationConfig...")

    config = CollaborationConfig()
    assert config.mode == CollaborationMode.SINGLE
    assert config.max_agents == 3
    assert config.parallel_timeout == 300.0
    assert config.retry_count == 2
    assert config.failover_enabled is True

    config.mode = CollaborationMode.MULTI
    assert config.mode == CollaborationMode.MULTI

    config_dict = config.to_dict()
    assert config_dict["mode"] == "multi"

    config2 = CollaborationConfig.from_dict(config_dict)
    assert config2.mode == CollaborationMode.MULTI

    print("  CollaborationConfig 测试通过")


def test_manager_creation():
    """测试管理器创建"""
    print("测试 CollaborationManager 创建...")

    manager = CollaborationManager()
    assert manager.is_multi_agent_enabled() is False
    assert manager.get_config().mode == CollaborationMode.SINGLE

    manager.set_mode(CollaborationMode.MULTI)
    assert manager.is_multi_agent_enabled() is True

    print("  CollaborationManager 创建测试通过")


def test_statistics():
    """测试统计信息"""
    print("测试 ExecutionStatistics...")

    stats = ExecutionStatistics()
    assert stats.total_tasks == 0
    assert stats.completed_tasks == 0

    stats.total_tasks = 5
    stats.completed_tasks = 3
    stats.failed_tasks = 1

    stats_dict = stats.to_dict()
    assert stats_dict["total_tasks"] == 5
    assert stats_dict["completed_tasks"] == 3

    print("  ExecutionStatistics 测试通过")


async def test_single_mode_execution():
    """测试单智能体模式执行"""
    print("测试单智能体模式执行...")

    config = CollaborationConfig(mode=CollaborationMode.SINGLE)
    manager = CollaborationManager(config=config)

    task = Task(
        id="test_task_1",
        prompt="测试任务",
        context={}
    )

    result = await manager.execute(task)

    assert result is not None
    assert hasattr(result, "success")
    assert hasattr(result, "duration")

    stats = manager.get_statistics()
    assert stats.total_tasks == 1

    print("  单智能体模式执行测试通过")


async def test_mode_switching():
    """测试模式切换"""
    print("测试模式切换...")

    manager = CollaborationManager()

    assert manager.is_multi_agent_enabled() is False

    manager.set_mode(CollaborationMode.MULTI)
    assert manager.is_multi_agent_enabled() is True

    manager.set_mode(CollaborationMode.SINGLE)
    assert manager.is_multi_agent_enabled() is False

    print("  模式切换测试通过")


def test_executor_management():
    """测试执行器管理"""
    print("测试执行器管理...")

    manager = CollaborationManager()

    executor = manager._get_or_create_executor("test_agent")
    assert executor is not None

    all_executors = manager.get_all_executors()
    assert "test_agent" in all_executors

    same_executor = manager.get_executor("test_agent")
    assert same_executor is executor

    print("  执行器管理测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试多智能体协作管理器")
    print("=" * 60)

    test_config()
    test_manager_creation()
    test_statistics()
    test_executor_management()

    asyncio.run(test_single_mode_execution())
    asyncio.run(test_mode_switching())

    print("=" * 60)
    print("所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
